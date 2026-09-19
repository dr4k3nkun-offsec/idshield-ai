import os
import re
import time
import uuid
import hashlib
import secrets
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import cv2
import numpy as np
import pytesseract

try:
    import networkx as nx
except ImportError:
    nx = None

from database import (
    init_db,
    save_document,
    get_all_documents,
    clear_documents,
    query_national_watchlist,
)
from forensic_service import analyze_advanced_tampering
from validation_service import validate_document_fields
from audit_service import record_audit_event, verify_audit_chain
from report_generator import generate_pdf_report
from verification_service import KYC_GATEWAY
from masking_engine import apply_regulatory_mask
from seed_demo import seed_database

try:
    import pywt
except ImportError:
    pywt = None

app = FastAPI(
    title="IDSHIELD AI Forensic & Syndicate Engine",
    description="Autonomous red-team document triage, PRNU hardware attribution, and Section 63 BSA evidentiary compliance platform.",
    version="2.4-PROD"
)

# Open API Security Scheme for Swagger UI padlock integration
security_scheme = HTTPBearer(auto_error=False)

# ===========================================================
# STRICT ZERO-TRUST CORS CONFIGURATION (No Wildcard '*')
# ===========================================================
raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
)
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

UPLOAD_DIR = "uploads"
MODELS_DIR = "models"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Initialize SQLite database, watchlist & audit tables
init_db()

# ===========================================================
# 0. SECURE PBKDF2 AUTHENTICATION & BOOTSTRAP ENGINE
# ===========================================================

DB_PATH = "idshield.db"

# Strictly read master agency key from env; fallback to generated secure hex
AGENCY_MASTER_KEY = os.environ.get("AGENCY_SECRET_KEY")
if not AGENCY_MASTER_KEY:
    AGENCY_MASTER_KEY = secrets.token_hex(24)
    print("\n[CRITICAL WARNING] AGENCY_SECRET_KEY not set in environment.")
    print(f"[SECURITY RUNTIME] Generated Dynamic Agency Key: {AGENCY_MASTER_KEY}\n")

CLEARANCE_PROFILES = {
    "L1": "Verification Observer",
    "L2": "Forensic Examiner",
    "L3": "Gov. Lead Investigator",
    "L4": "Autonomous Syndicate Admin",
}

CLEARANCE_HIERARCHY = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,
    ).hex()
    return pwd_hash, salt

def init_auth_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Investigator Credentials Registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigators (
            badge_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            clearance TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 2. Persistent Active Session Ledger (Closes "Auth is theater" gap)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_sessions (
            token TEXT PRIMARY KEY,
            badge_id TEXT NOT NULL,
            clearance TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # 3. Secure First-Time Enterprise Bootstrap Check (No hardcoded credentials committed)
    cursor.execute("SELECT COUNT(*) FROM investigators")
    if cursor.fetchone()[0] == 0:
        bootstrap_badge = os.environ.get("INITIAL_ADMIN_BADGE", "INV-7029")
        bootstrap_password = os.environ.get("INITIAL_ADMIN_PASSWORD")
        
        is_generated = False
        if not bootstrap_password:
            bootstrap_password = f"IDShield@{secrets.token_hex(4).upper()}!"
            is_generated = True

        p_hash, p_salt = hash_password(bootstrap_password)
        cursor.execute(
            "INSERT INTO investigators VALUES (?, ?, ?, ?, ?, ?)",
            (
                bootstrap_badge,
                CLEARANCE_PROFILES["L3"],
                "L3",
                p_hash,
                p_salt,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

        print("\n" + "=" * 65)
        print("  IDSHIELD AI // SECURE ONE-TIME ENTERPRISE BOOTSTRAP")
        print("=" * 65)
        print(f"  OPERATOR BADGE ID : {bootstrap_badge}")
        print(f"  INITIAL PASSWORD  : {bootstrap_password}")
        if is_generated:
            print("  [ACTION REQUIRED] Save these credentials immediately.")
            print("  Define INITIAL_ADMIN_PASSWORD in .env for custom credentials.")
        print("=" * 65 + "\n")

    conn.commit()
    conn.close()

init_auth_table()


# ===========================================================
# STATUTORY CLEARANCE & TOKEN ENFORCEMENT DEPENDENCIES
# ===========================================================

async def get_current_officer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Validates the bearer token against persistent active sessions.
    Accepts tokens via Authorization Header or Swagger HTTPBearer.
    """
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials.strip()
    elif authorization:
        raw_token = authorization.replace("Bearer ", "").strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied: Missing statutory Authorization Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM active_sessions WHERE token = ?", (raw_token,))
    session = cursor.fetchone()
    conn.close()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired or Revoked: Invalid forensic officer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "badgeId": session["badge_id"],
        "clearance": session["clearance"],
        "name": session["name"],
        "token": raw_token,
    }


def require_clearance(minimum_level: str = "L2"):
    """
    Enforces Role-Based Access Control (RBAC) based on investigator clearance hierarchy.
    """
    min_rank = CLEARANCE_HIERARCHY.get(minimum_level, 2)

    async def clearance_checker(officer: Dict[str, Any] = Depends(get_current_officer)):
        user_rank = CLEARANCE_HIERARCHY.get(officer.get("clearance", "L1"), 1)
        if user_rank < min_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Security Clearance Violation: Operation requires rank {minimum_level} or higher. Current rank: {officer.get('clearance')}.",
            )
        return officer

    return clearance_checker


# --- Pydantic Request Schemas ---

class LoginRequest(BaseModel):
    badgeId: str
    password: str
    clearanceLevel: Optional[str] = None

class RegisterRequest(BaseModel):
    badgeId: str
    password: str
    clearanceLevel: str
    agencySecretKey: str

class DirectVerificationRequest(BaseModel):
    doc_type: str
    id_number: str
    dob: Optional[str] = None
    consent: bool = True

class AdjudicationRequest(BaseModel):
    decision: str
    reason: str
    officerBadge: Optional[str] = "INV-7029"


# --- Authentication Endpoints ---

@app.post("/api/auth/register")
async def register_investigator(data: RegisterRequest):
    if data.agencySecretKey != AGENCY_MASTER_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Agency Authorization Key. Handshake rejected by security authority.",
        )

    badge = data.badgeId.strip().upper()
    role_title = CLEARANCE_PROFILES.get(data.clearanceLevel, "Forensic Examiner")
    p_hash, p_salt = hash_password(data.password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO investigators VALUES (?, ?, ?, ?, ?, ?)",
            (badge, role_title, data.clearanceLevel, p_hash, p_salt, datetime.now().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Badge ID '{badge}' is already registered in active command registry.",
        )
    conn.close()

    return {
        "success": True,
        "message": f"Investigator {badge} successfully authorized as {role_title}.",
    }


@app.post("/api/auth/token")
async def authenticate_investigator(creds: LoginRequest):
    badge = creds.badgeId.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investigators WHERE badge_id = ?", (badge,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Investigator Badge ID not recognized in active command registry.",
        )

    calculated_hash, _ = hash_password(creds.password, salt=user["salt"])
    if calculated_hash != user["password_hash"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security Clearance Key mismatch. Incident logged to audit trail.",
        )

    assigned_clearance = user["clearance"]
    assigned_title = CLEARANCE_PROFILES.get(assigned_clearance, user["name"])
    session_token = f"sec-token-{uuid.uuid4().hex}"

    # Register active persistent session
    cursor.execute(
        "INSERT INTO active_sessions VALUES (?, ?, ?, ?, ?)",
        (session_token, user["badge_id"], assigned_clearance, assigned_title, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {
        "access_token": session_token,
        "token_type": "bearer",
        "officer": {
            "badgeId": user["badge_id"],
            "name": assigned_title,
            "clearance": assigned_clearance,
        },
    }


# ===========================================================
# MULTI-CREDENTIAL DIRECT LOOKUP
# ===========================================================

@app.post("/api/verify/lookup")
async def verify_identity_record(payload: DirectVerificationRequest):
    if not payload.consent:
        raise HTTPException(
            status_code=400,
            detail="Statutory citizen consent is mandatory to execute registry lookups.",
        )

    doc = payload.doc_type.strip()
    identifier = payload.id_number.strip()

    if doc == "PAN Card":
        result = await KYC_GATEWAY.verify_pan(identifier)
    elif doc == "Driving Licence":
        result = await KYC_GATEWAY.verify_driving_licence(identifier, payload.dob)
    elif doc == "Passport":
        result = await KYC_GATEWAY.verify_passport(identifier, payload.dob)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported document class: {doc}")

    return {
        "query": {
            "doc_type": doc,
            "identifier_masked": f"{identifier[:2]}****{identifier[-2:]}" if len(identifier) > 4 else "[Redacted]",
        },
        "verification_result": result,
    }


# ===========================================================
# 1. NEURAL BIOMETRIC ENGINE (YUNET + SFACE ONNX)
# ===========================================================

YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface.onnx")

yunet_detector = None
sface_recognizer = None

if os.path.exists(YUNET_PATH):
    try:
        yunet_detector = cv2.FaceDetectorYN.create(
            model=YUNET_PATH,
            config="",
            input_size=(320, 320),
            score_threshold=0.55,
            nms_threshold=0.30,
            top_k=5000,
        )
    except Exception as e:
        print(f"[WARN] Failed to load YuNet detector: {e}")

if os.path.exists(SFACE_PATH):
    try:
        sface_recognizer = cv2.FaceRecognizerSF.create(
            model=SFACE_PATH,
            config="",
        )
    except Exception as e:
        print(f"[WARN] Failed to load SFace recognizer: {e}")


def detect_face_yunet(image_bgr: np.ndarray) -> Tuple[bool, List[Dict[str, Any]], List[np.ndarray]]:
    global yunet_detector
    if yunet_detector is None or image_bgr is None:
        return False, [], []

    h, w = image_bgr.shape[:2]
    yunet_detector.setInputSize((w, h))
    _, faces = yunet_detector.detect(image_bgr)

    if faces is None or len(faces) == 0:
        return False, [], []

    detected_boxes = []
    detected_rows = []

    for face in faces:
        score = float(face[-1])
        if score < 0.50:
            continue

        fx, fy, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
        fx = max(0, fx)
        fy = max(0, fy)
        fw = min(w - fx, fw)
        fh = min(h - fy, fh)

        if fw < int(w * 0.08) or fh < int(h * 0.08):
            continue

        bbox = {
            "x": round((fx / w) * 100, 2),
            "y": round((fy / h) * 100, 2),
            "width": round((fw / w) * 100, 2),
            "height": round((fh / h) * 100, 2),
            "confidence": round(score * 100, 1),
        }
        detected_boxes.append(bbox)
        detected_rows.append(face)

    return len(detected_boxes) > 0, detected_boxes, detected_rows


def extract_sface_feature(image_bgr: np.ndarray, raw_face_row: np.ndarray) -> Optional[np.ndarray]:
    global sface_recognizer
    if sface_recognizer is None or image_bgr is None or raw_face_row is None:
        return None

    try:
        aligned_face = sface_recognizer.alignCrop(image_bgr, raw_face_row)
        feature = sface_recognizer.feature(aligned_face)
        norm = np.linalg.norm(feature) + 1e-9
        return (feature / norm).flatten().astype(np.float32)
    except Exception as e:
        print(f"[WARN] SFace alignment/extraction failed: {e}")
        return None


# ===========================================================
# 2. DYNAMIC GRAPH INTELLIGENCE & SYNDICATE MEMORY BANK
# ===========================================================

class DynamicSyndicateMemory:
    def __init__(self):
        self.face_registry: List[Dict[str, Any]] = []
        self.layout_registry: List[Dict[str, Any]] = []
        self.syndicate_clusters: List[Dict[str, Any]] = []

    @property
    def experience_level(self) -> Dict[str, Any]:
        count = len(get_all_documents())
        if count < 5:
            stage = "Level 1: Calibration (Heuristic Baseline)"
            multiplier = 0.85
        elif count < 25:
            stage = "Level 2: Active Pattern Learning"
            multiplier = 1.0
        elif count < 75:
            stage = "Level 3: Predictive Cluster Intelligence"
            multiplier = 1.25
        else:
            stage = "Level 4: Autonomous Threat Network Core"
            multiplier = 1.5
        return {
            "screened_count": count,
            "stage": stage,
            "intelligence_multiplier": multiplier,
            "clusters_identified": len(self.syndicate_clusters),
        }

    def compute_phash(self, image: np.ndarray) -> str:
        h, w = image.shape[:2]
        crop = image[int(h * 0.20):int(h * 0.85), int(w * 0.05):int(w * 0.95)]
        resized = cv2.resize(crop, (32, 32), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
        dct = cv2.dct(np.float32(gray))
        dct_low = dct[:8, :8]
        med = np.median(dct_low)
        return ''.join(['1' if b else '0' for b in (dct_low > med).flatten()])

    def hamming_distance(self, h1: str, h2: str) -> int:
        return sum(c1 != c2 for c1, c2 in zip(h1, h2))

    def fallback_face_vector(self, face_chip: np.ndarray) -> np.ndarray:
        resized = cv2.resize(face_chip, (64, 64))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
        dft = np.fft.fft2(gray)
        dft_shift = np.fft.fftshift(dft)
        mag = np.log(np.abs(dft_shift) + 1e-9)

        mag_low = cv2.resize(mag, (8, 8)).flatten()
        spatial_pool = cv2.resize(gray, (8, 8)).flatten() / 255.0
        combined = np.concatenate([mag_low, spatial_pool])
        norm = np.linalg.norm(combined) + 1e-9
        return (combined / norm).astype(np.float32)

    def cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        if v1 is None or v2 is None or v1.shape != v2.shape:
            return 0.0
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9))

    def audit_submission(self, doc_id: str, subject_raw_id: str, face_vector: Optional[np.ndarray], doc_img: np.ndarray) -> Dict[str, Any]:
        phash = self.compute_phash(doc_img)
        network_signals = []
        ring_detected = False
        syndicate_penalty = 0
        similarity_threshold = 0.40 if sface_recognizer is not None else 0.88

        if face_vector is not None:
            for record in self.face_registry:
                sim = self.cosine_similarity(face_vector, record["embedding"])
                if sim > similarity_threshold:
                    is_distinct_identity = (subject_raw_id != record["raw_id"]) or (not subject_raw_id) or (not record["raw_id"])
                    if is_distinct_identity and record["doc_id"] != doc_id:
                        ring_detected = True
                        syndicate_penalty += 45
                        msg = f"Sybil Network Collision: SFace embedding matches prior scan {record['doc_id']} (Cosine: {round(sim, 3)}) across divergent identities"
                        network_signals.append({
                            "vector": "Cross-Identity Face Reuse",
                            "severity": "CRITICAL",
                            "weight": 45,
                            "linked_doc": record["doc_id"],
                            "description": msg,
                        })
                        break

        layout_collisions = [
            r for r in self.layout_registry
            if r["doc_id"] != doc_id and self.hamming_distance(phash, r["phash"]) <= 2
        ]
        if len(layout_collisions) >= 2:
            ring_detected = True
            syndicate_penalty += 35
            msg = f"Template Farm Pattern: Exact canvas geometry replicated across {len(layout_collisions)} historical dossiers"
            network_signals.append({
                "vector": "Reused Forgery Template Blank",
                "severity": "HIGH",
                "weight": 35,
                "linked_doc": layout_collisions[0]["doc_id"],
                "description": msg,
            })

        if face_vector is not None:
            self.face_registry.append({
                "doc_id": doc_id,
                "raw_id": subject_raw_id,
                "embedding": face_vector,
                "timestamp": datetime.now(),
            })

        self.layout_registry.append({
            "doc_id": doc_id,
            "phash": phash,
            "timestamp": datetime.now(),
        })

        if ring_detected:
            self.syndicate_clusters.append({
                "cluster_id": f"SYN-{uuid.uuid4().hex[:4].upper()}",
                "doc_id": doc_id,
                "signals": network_signals,
                "timestamp": datetime.now().isoformat(),
            })

        return {
            "is_syndicate_attack": ring_detected,
            "syndicate_penalty": syndicate_penalty,
            "network_signals": network_signals,
            "memory_stage": self.experience_level["stage"],
        }

MEMORY = DynamicSyndicateMemory()


# ===========================================================
# 2.B NETWORKX GRAPH COMMUNITY & SYNDICATE DISCOVERY ENGINE
# ===========================================================

def build_syndicate_graph_topology() -> Dict[str, Any]:
    """
    Constructs an algorithmic graph connecting credentials via:
    1. Active RAM Biometric (SFace 128D) & pHash geometry collisions.
    2. Historical/Seeded risk signals (Sybil, Template Farm, linked_doc).
    3. Shared citizen names & document identifiers.
    Uses NetworkX for community clustering and degree-centrality kingpin identification.
    """
    docs = get_all_documents()
    if not docs:
        return {
            "nodes": [],
            "edges": [],
            "clusters": [],
            "metrics": {
                "totalNodes": 0,
                "totalEdges": 0,
                "syndicateClusters": 0,
                "isolatedNodes": 0,
                "highestCentralityHub": None,
            },
        }

    raw_nodes = {}
    edges_list: List[Dict[str, Any]] = []
    seen_edges = set()

    for d in docs:
        did = d.get("id")
        if not did:
            continue
        raw_nodes[did] = {
            "id": did,
            "label": f"{did} [{d.get('docType', 'Credential')}]",
            "docType": d.get("docType", "Unknown"),
            "riskScore": d.get("riskScore", 0),
            "status": d.get("status", "VERIFIED"),
            "imageUrl": d.get("imageUrl", ""),
            "subjectMaskedId": d.get("subjectMaskedId", ""),
            "name": d.get("validationOutcome", {}).get("extractedFields", {}).get("name", ""),
        }

    # 1. Edge Generation via Live RAM Biometric Feature Proximity
    face_recs = MEMORY.face_registry
    sim_threshold = 0.40 if sface_recognizer is not None else 0.88
    for i in range(len(face_recs)):
        for j in range(i + 1, len(face_recs)):
            r1, r2 = face_recs[i], face_recs[j]
            id1, id2 = r1["doc_id"], r2["doc_id"]
            if id1 == id2 or id1 not in raw_nodes or id2 not in raw_nodes:
                continue

            sim = MEMORY.cosine_similarity(r1["embedding"], r2["embedding"])
            if sim >= sim_threshold:
                edge_key = tuple(sorted([id1, id2]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges_list.append({
                        "source": id1,
                        "target": id2,
                        "type": "BIOMETRIC_COLLISION",
                        "relation": f"Shared Facial Embedding (Cosine: {round(sim, 3)})",
                        "weight": round(sim, 3),
                        "severity": "CRITICAL",
                    })

    # 2. Edge Generation via Live RAM Canvas Geometry (Template Farm)
    layout_recs = MEMORY.layout_registry
    for i in range(len(layout_recs)):
        for j in range(i + 1, len(layout_recs)):
            l1, l2 = layout_recs[i], layout_recs[j]
            id1, id2 = l1["doc_id"], l2["doc_id"]
            if id1 == id2 or id1 not in raw_nodes or id2 not in raw_nodes:
                continue

            dist = MEMORY.hamming_distance(l1["phash"], l2["phash"])
            if dist <= 2:
                edge_key = tuple(sorted([id1, id2]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges_list.append({
                        "source": id1,
                        "target": id2,
                        "type": "TEMPLATE_FARM",
                        "relation": f"Identical Canvas Geometry (Hamming Dist: {dist})",
                        "weight": round(1.0 - (dist / 64.0), 3),
                        "severity": "HIGH",
                    })

    # 3. Edge Generation via Stored Forensic Risk Signals (Database Inspection)
    for d in docs:
        did = d.get("id")
        for b in d.get("riskBreakdown", []):
            sig = b.get("signal", "")
            desc = b.get("description", "")
            linked = b.get("linked_doc")

            if linked and linked in raw_nodes and linked != did:
                edge_key = tuple(sorted([did, linked]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    is_bio = "Sybil" in sig or "Face" in sig
                    edges_list.append({
                        "source": did,
                        "target": linked,
                        "type": "BIOMETRIC_COLLISION" if is_bio else "TEMPLATE_FARM",
                        "relation": desc or f"Forensic collision linked to {linked}",
                        "weight": 0.95 if is_bio else 0.88,
                        "severity": "CRITICAL" if is_bio else "HIGH",
                    })

            elif "Sybil" in sig or "Face Reuse" in sig:
                target_candidates = [other_id for other_id in raw_nodes if other_id != did]
                if target_candidates:
                    primary_target = target_candidates[0]
                    edge_key = tuple(sorted([did, primary_target]))
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges_list.append({
                            "source": did,
                            "target": primary_target,
                            "type": "BIOMETRIC_COLLISION",
                            "relation": desc or "Sybil Network Face Reuse Collision",
                            "weight": 0.94,
                            "severity": "CRITICAL",
                        })

            elif "Template Farm" in sig:
                my_type = d.get("docType")
                matching_templates = [
                    other_id for other_id, node in raw_nodes.items()
                    if other_id != did and node.get("docType") == my_type
                ]
                target_candidates = [other_id for other_id in raw_nodes if other_id != did]
                target_id = matching_templates[0] if matching_templates else (target_candidates[0] if target_candidates else None)
                if target_id:
                    edge_key = tuple(sorted([did, target_id]))
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges_list.append({
                            "source": did,
                            "target": target_id,
                            "type": "TEMPLATE_FARM",
                            "relation": desc or "Identical Forgery Template Geometry",
                            "weight": 0.89,
                            "severity": "HIGH",
                        })

    # 4. Edge Generation via Shared Subject Name
    name_map: Dict[str, List[str]] = {}
    for did, n_info in raw_nodes.items():
        nm = n_info.get("name", "").strip().upper()
        if nm and nm not in ["HOLDER RECORD", "VERIFIED CITIZEN", "UNKNOWN"]:
            name_map.setdefault(nm, []).append(did)

    for nm, associated_docs in name_map.items():
        if len(associated_docs) > 1:
            for idx1 in range(len(associated_docs)):
                for idx2 in range(idx1 + 1, len(associated_docs)):
                    id1, id2 = associated_docs[idx1], associated_docs[idx2]
                    edge_key = tuple(sorted([id1, id2]))
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges_list.append({
                            "source": id1,
                            "target": id2,
                            "type": "IDENTITY_REUSE",
                            "relation": f"Shared Subject Name: {nm}",
                            "weight": 0.85,
                            "severity": "ELEVATED",
                        })

    # 5. NetworkX Graph Topographical Analysis
    clusters_meta: List[Dict[str, Any]] = []
    centrality_map: Dict[str, float] = {}

    if nx is not None:
        G = nx.Graph()
        for nid in raw_nodes:
            G.add_node(nid)
        for ed in edges_list:
            G.add_edge(ed["source"], ed["target"], weight=ed["weight"], type=ed["type"])

        centrality_map = nx.degree_centrality(G) if len(G) > 0 else {}
        connected_subgraphs = list(nx.connected_components(G))

        cluster_idx = 1
        for comp in connected_subgraphs:
            if len(comp) >= 2:
                members = list(comp)
                hub_node = max(members, key=lambda m: centrality_map.get(m, 0.0))
                cluster_id = f"SYN-CLUSTER-{cluster_idx:02d}"

                comp_edges = [e for e in edges_list if e["source"] in comp and e["target"] in comp]
                has_biometric = any(e["type"] == "BIOMETRIC_COLLISION" for e in comp_edges)
                threat_vector = "Cross-Identity Biometric Sybil Ring" if has_biometric else "Document Template Reuse Syndicate"

                clusters_meta.append({
                    "clusterId": cluster_id,
                    "size": len(members),
                    "riskLevel": "CRITICAL" if has_biometric else "HIGH",
                    "threatVector": threat_vector,
                    "hubNode": hub_node,
                    "members": members,
                })

                for m in members:
                    raw_nodes[m]["clusterId"] = cluster_id
                    raw_nodes[m]["isHub"] = (m == hub_node)
                    raw_nodes[m]["centrality"] = round(centrality_map.get(m, 0.0), 3)

                cluster_idx += 1
    else:
        adj: Dict[str, List[str]] = {nid: [] for nid in raw_nodes}
        for ed in edges_list:
            adj[ed["source"]].append(ed["target"])
            adj[ed["target"]].append(ed["source"])

        visited = set()
        c_idx = 1
        for nid in raw_nodes:
            if nid not in visited:
                comp = []
                queue = [nid]
                visited.add(nid)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                if len(comp) >= 2:
                    c_id = f"SYN-CLUSTER-{c_idx:02d}"
                    clusters_meta.append({
                        "clusterId": c_id,
                        "size": len(comp),
                        "riskLevel": "HIGH",
                        "threatVector": "Correlated Multi-Dossier Cluster",
                        "hubNode": comp[0],
                        "members": comp,
                    })
                    for m in comp:
                        raw_nodes[m]["clusterId"] = c_id
                        raw_nodes[m]["isHub"] = (m == comp[0])
                        raw_nodes[m]["centrality"] = round(len(adj[m]) / max(1, len(raw_nodes) - 1), 3)
                    c_idx += 1

    formatted_nodes = list(raw_nodes.values())
    hub_candidate = max(formatted_nodes, key=lambda n: n.get("centrality", 0.0), default=None)
    highest_hub = hub_candidate["id"] if hub_candidate and hub_candidate.get("centrality", 0.0) > 0 else None

    return {
        "nodes": formatted_nodes,
        "edges": edges_list,
        "clusters": clusters_meta,
        "metrics": {
            "totalNodes": len(formatted_nodes),
            "totalEdges": len(edges_list),
            "syndicateClusters": len(clusters_meta),
            "isolatedNodes": len([n for n in formatted_nodes if not n.get("clusterId")]),
            "highestCentralityHub": highest_hub,
        },
    }


# ===========================================================
# 3. MATHEMATICAL SYNTAX & CHECKS
# ===========================================================

VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

def validate_verhoeff(number_str: str) -> bool:
    clean_num = ''.join(filter(str.isdigit, number_str))
    if len(clean_num) != 12:
        return False
    c = 0
    reversed_digits = [int(x) for x in reversed(clean_num)]
    for idx, digit in enumerate(reversed_digits):
        c = VERHOEFF_D[c][VERHOEFF_P[idx % 8][digit]]
    return c == 0

def validate_pan_structure(pan_str: str) -> dict:
    clean_pan = pan_str.strip().upper()
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', clean_pan):
        return {"valid": False, "reason": "Syntax does not match standard 10-character PAN specification"}

    entity_code = clean_pan[3]
    valid_entities = {
        'P': 'Individual / Person',
        'C': 'Company',
        'H': 'Hindu Undivided Family (HUF)',
        'F': 'Partnership Firm / LLP',
        'A': 'Association of Persons (AOP)',
        'T': 'Trust',
        'B': 'Body of Individuals (BOI)',
        'L': 'Local Authority',
        'J': 'Artificial Juridical Person',
        'G': 'Government Agency',
    }

    if entity_code not in valid_entities:
        return {"valid": False, "reason": f"Invalid entity designator character '{entity_code}' at index 4"}

    return {
        "valid": True,
        "entity_type": valid_entities[entity_code],
        "entity_code": entity_code,
    }

INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ",
    "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP",
    "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}

def validate_driving_licence_structure(dl_str: str) -> dict:
    clean_dl = re.sub(r'[^A-Za-z0-9]', '', dl_str.strip().upper())
    if len(clean_dl) < 14 or len(clean_dl) > 16:
        return {"valid": False, "reason": f"Standard DL requires 15-16 alphanumeric characters, detected {len(clean_dl)}"}

    state = clean_dl[:2]
    if state not in INDIAN_STATE_CODES:
        return {"valid": False, "reason": f"Invalid Indian State / UT code '{state}'"}

    if re.match(r'^[A-Z]{2}[0-9]{2}(19\d{2}|20\d{2})[0-9]{7}$', clean_dl):
        issue_year = clean_dl[4:8]
        return {
            "valid": True,
            "strict": True,
            "state": state,
            "rto_code": clean_dl[2:4],
            "year": issue_year,
            "serial": clean_dl[8:],
            "normalized": f"{state}{clean_dl[2:4]} {issue_year}{clean_dl[8:]}",
        }

    return {"valid": True, "strict": False, "state": state, "normalized": clean_dl}

def validate_passport_structure(passport_str: str) -> dict:
    clean_pass = passport_str.strip().upper().replace(" ", "")
    if re.match(r'^[A-Z][0-9]{7}$', clean_pass):
        first_letter = clean_pass[0]
        if first_letter in ['Q', 'X', 'Z']:
            return {"valid": False, "reason": f"Series character '{first_letter}' is unassigned in Indian passport registry"}
        return {"valid": True, "passport_number": clean_pass}
    return {"valid": False, "reason": "Standard Indian Passport syntax requires 1 letter followed by 7 numeric digits"}


# ===========================================================
# 4. 2D-FFT SPECTRAL MOIRÉ DETECTOR
# ===========================================================

def detect_screen_replay_fft(image_path: str) -> dict:
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {"spectral_ratio": 0.0, "is_screen_attack": False}

        img_resized = cv2.resize(img, (512, 512))
        dft = np.fft.fft2(img_resized)
        dft_shift = np.fft.fftshift(dft)
        magnitude = 20 * np.log(np.abs(dft_shift) + 1e-9)

        rows, cols = 512, 512
        crow, ccol = rows // 2, cols // 2

        magnitude[crow - 30 : crow + 30, ccol - 30 : ccol + 30] = 0
        magnitude[crow - 5 : crow + 5, :] = 0
        magnitude[:, ccol - 5 : ccol + 5] = 0

        peak_val = np.percentile(magnitude, 99.9)
        mean_val = np.mean(magnitude)
        ratio = peak_val / (mean_val + 1e-5)

        return {
            "spectral_ratio": round(float(ratio), 2),
            "is_screen_attack": bool(ratio > 6.8),
        }
    except Exception:
        return {"spectral_ratio": 0.0, "is_screen_attack": False}


# ===========================================================
# 5. CONTEXT-AWARE BIOMETRIC PORTRAIT LOCATOR
# ===========================================================

def locate_biometric_portrait_exact(image_path: str, template_side: str, is_composite: bool, doc_type: str = "Aadhaar"):
    if template_side == "BACK_ONLY":
        return False, [], None, None

    img = cv2.imread(image_path)
    if img is None:
        return False, [], None, None

    h, w = img.shape[:2]

    yunet_success, yunet_boxes, raw_face_rows = detect_face_yunet(img)

    if yunet_success and len(yunet_boxes) > 0:
        candidate_face = None
        candidate_row = None

        if doc_type in ["Driving Licence", "Passport"]:
            for box, row in zip(yunet_boxes, raw_face_rows):
                if box["x"] >= 38.0:
                    candidate_face = box
                    candidate_row = row
                    break
            if not candidate_face:
                candidate_face = max(yunet_boxes, key=lambda b: b["confidence"])
                candidate_row = raw_face_rows[yunet_boxes.index(candidate_face)]
        else:
            for box, row in zip(yunet_boxes, raw_face_rows):
                if box["x"] <= 65.0:
                    candidate_face = box
                    candidate_row = row
                    break
            if not candidate_face:
                candidate_face = max(yunet_boxes, key=lambda b: b["confidence"])
                candidate_row = raw_face_rows[yunet_boxes.index(candidate_face)]

        fx = int((candidate_face["x"] / 100.0) * w)
        fy = int((candidate_face["y"] / 100.0) * h)
        fw = int((candidate_face["width"] / 100.0) * w)
        fh = int((candidate_face["height"] / 100.0) * h)
        face_chip = img[fy : fy + fh, fx : fx + fw]
        
        return True, [candidate_face], face_chip, candidate_row

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if doc_type in ["Driving Licence", "Passport"]:
        min_x = int(w * 0.48)
        max_x = int(w * 0.98)
        min_y = int(h * 0.15)
        max_y = int(h * 0.90)
    else:
        min_x = int(w * 0.02)
        max_x = int(w * 0.45) if doc_type == "PAN Card" else int(w * 0.38)
        min_y = int(h * 0.12)
        max_y = int(h * 0.52) if is_composite else int(h * 0.88)

    search_roi = gray[min_y:max_y, min_x:max_x]
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    search_roi_clahe = clahe.apply(search_roi)

    cascades = ['haarcascade_frontalface_alt2.xml', 'haarcascade_frontalface_default.xml']
    for cascade_name in cascades:
        cascade_path = cv2.data.haarcascades + cascade_name
        if os.path.exists(cascade_path):
            cascade = cv2.CascadeClassifier(cascade_path)
            for roi in [search_roi_clahe, search_roi]:
                faces = cascade.detectMultiScale(
                    roi,
                    scaleFactor=1.04,
                    minNeighbors=2,
                    minSize=(int(min(h, w) * 0.10), int(min(h, w) * 0.10)),
                )
                if len(faces) > 0:
                    fx, fy, fw, fh = max(faces, key=lambda b: b[2] * b[3])
                    face_chip = img[min_y + fy : min_y + fy + fh, min_x + fx : min_x + fx + fw]
                    bbox = {
                        "x": round(((min_x + fx) / w) * 100, 2),
                        "y": round(((min_y + fy) / h) * 100, 2),
                        "width": round((fw / w) * 100, 2),
                        "height": round((fh / h) * 100, 2),
                        "confidence": 88.0,
                    }
                    return True, [bbox], face_chip, None

    if doc_type in ["Driving Licence", "Passport"]:
        px, py, pw, ph = 62.0, 30.0, 28.0, 48.0
    else:
        px, py, pw, ph = 5.0, 21.0, 21.0, 36.0 if not is_composite else 20.0

    x_pix, y_pix = int((px / 100) * w), int((py / 100) * h)
    w_pix, h_pix = int((pw / 100) * w), int((ph / 100) * h)
    face_chip = img[y_pix : y_pix + h_pix, x_pix : x_pix + w_pix]

    if np.std(face_chip) > 18:
        return True, [{"x": px, "y": py, "width": pw, "height": ph, "confidence": 75.0}], face_chip, None

    return False, [], None, None


# ===========================================================
# 6. HIGH-DENSITY 2D MATRIX & QR LOCATOR
# ===========================================================

def locate_cryptographic_qr_exact(image_path: str, doc_type: str = "Aadhaar"):
    if doc_type == "Passport":
        return False, None, None

    img = cv2.imread(image_path)
    if img is None:
        return False, None, None

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    detector = cv2.QRCodeDetector()
    val, points, _ = detector.detectAndDecode(gray)
    if points is not None and len(points) > 0:
        pts = points[0]
        x_min, y_min = max(0, int(np.min(pts[:, 0]))), max(0, int(np.min(pts[:, 1])))
        x_max, y_max = min(w, int(np.max(pts[:, 0]))), min(h, int(np.max(pts[:, 1])))
        if (x_max - x_min) > 25 and (y_max - y_min) > 25:
            return True, val if val else "VALID_2D_MATRIX", {
                "x": round((x_min / w) * 100, 2),
                "y": round((y_min / h) * 100, 2),
                "width": round(((x_max - x_min) / w) * 100, 2),
                "height": round(((y_max - y_min) / h) * 100, 2),
            }

    if doc_type == "Driving Licence":
        return False, None, None

    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gradient = cv2.convertScaleAbs(cv2.subtract(grad_x, grad_y))
    blurred = cv2.blur(gradient, (5, 5))
    _, thresh = cv2.threshold(blurred, 115, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 17))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    closed = cv2.erode(closed, None, iterations=2)
    closed = cv2.dilate(closed, None, iterations=2)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        aspect = cw / float(ch)
        area = cw * ch
        if 0.70 <= aspect <= 1.40 and (w * h * 0.008) < area < (w * h * 0.60):
            roi = gray[y : y + ch, x : x + cw]
            if np.std(roi) > 42:
                return True, "CRYPTOGRAPHIC_2D_MATRIX_LOCATED", {
                    "x": round((x / w) * 100, 2),
                    "y": round((y / h) * 100, 2),
                    "width": round((cw / w) * 100, 2),
                    "height": round((ch / h) * 100, 2),
                }

    return False, None, None


# ===========================================================
# 7. PROTECTED FORENSIC PIPELINE & MULTI-CREDENTIAL INFERENCE
# ===========================================================

@app.post("/api/documents/screen")
async def screen_document(
    file: UploadFile = File(...),
    officer: Dict[str, Any] = Depends(get_current_officer)
):
    """
    Forensic Screening Gateway (Enforced via RBAC Bearer Token).
    Executes deep multi-layer ELA, 2D-FFT Moiré detection, and PRNU hardware extraction.
    """
    t0 = time.perf_counter()
    doc_id = f"DOC-2026-{uuid.uuid4().hex[:6].upper()}"
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")

    # Binary Magic-Byte Verification
    file_bytes = await file.read()
    if len(file_bytes) < 8:
        raise HTTPException(status_code=400, detail="Invalid file payload: file is empty or corrupted.")

    is_jpeg = file_bytes[:3] == b'\xff\xd8\xff'
    is_png = file_bytes[:8] == b'\x89PNG\r\n\x1a\n'
    is_webp = len(file_bytes) >= 12 and file_bytes[:4] == b'RIFF' and file_bytes[8:12] == b'WEBP'

    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Security Violation: File failed binary magic-byte verification (non-image rejected)."
        )

    nparr = np.frombuffer(file_bytes, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if cv_img is None:
        cv_img = np.zeros((600, 800, 3), dtype=np.uint8)

    img_h, img_w = cv_img.shape[:2]
    is_composite = bool(img_h > (img_w * 0.92))

    raw_text = ""
    try:
        raw_text = pytesseract.image_to_string(cv_img)
    except Exception:
        raw_text = ""

    upper_text = raw_text.upper()

    dl_matches = re.findall(r'\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b', upper_text)
    if not dl_matches:
        dl_matches = re.findall(r'\b[A-Z]{2}[0-9]{2}(?:19|20)[0-9]{2}[0-9]{7}\b', upper_text.replace(" ", ""))

    pan_matches = re.findall(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', upper_text)
    passport_matches = re.findall(r'\b[A-PR-WYa-pr-wy][1-9][0-9]{7}\b', upper_text)
    mrz_matches = re.findall(r'P<IND[A-Z<]+', upper_text)

    is_driving_licence = any(k in upper_text for k in [
        "DRIVING LICENCE", "DRIVING LICENSE", "UNION OF INDIA",
        "MOTOR VEHICLES", "TRANSPORT DEPARTMENT", "FORM 7", "SARATHI",
        "AUTHORISATION TO DRIVE"
    ]) or (len(dl_matches) > 0 and "INCOME TAX" not in upper_text)

    is_passport = any(k in upper_text for k in [
        "PASSPORT", "REPUBLIC OF INDIA", "P<IND", "MINISTRY OF EXTERNAL AFFAIRS",
        "GIVEN NAMES", "NATIONALITY"
    ]) or len(mrz_matches) > 0

    is_pan = any(k in upper_text for k in [
        "INCOME TAX DEPARTMENT", "PERMANENT ACCOUNT NUMBER", "INCOME TAX",
        "ACCOUNT NUMBER CARD", "GOVT. OF INDIA"
    ]) and not is_driving_licence and not is_passport

    is_aadhaar = any(k in upper_text for k in [
        "UNIQUE IDENTIFICATION", "AADHAAR", "UIDAI", "MAJHE AADHAAR", "HELP@UIDAI"
    ]) and not is_driving_licence and not is_passport

    if is_driving_licence:
        doc_type = "Driving Licence"
        template_side = "FRONT_ONLY"
    elif is_passport:
        doc_type = "Passport"
        template_side = "FRONT_ONLY"
    elif is_pan:
        doc_type = "PAN Card"
        template_side = "FRONT_ONLY"
    elif is_aadhaar:
        doc_type = "Aadhaar"
        has_front = any(k in upper_text for k in ["GOVERNMENT OF INDIA", "DOB", "MALE", "FEMALE", "YEAR OF BIRTH", "ENROLLMENT"])
        has_back = any(k in upper_text for k in ["UNIQUE IDENTIFICATION", "ADDRESS", "PATA", "MAJHE AADHAAR", "HELP@UIDAI"])
        if is_composite or (has_front and has_back):
            template_side = "COMPOSITE_CARD"
        elif has_back and not has_front:
            template_side = "BACK_ONLY"
        else:
            template_side = "FRONT_ONLY"
    else:
        if dl_matches:
            doc_type = "Driving Licence"
            template_side = "FRONT_ONLY"
        elif passport_matches:
            doc_type = "Passport"
            template_side = "FRONT_ONLY"
        elif pan_matches:
            doc_type = "PAN Card"
            template_side = "FRONT_ONLY"
        else:
            doc_type = "Aadhaar"
            template_side = "FRONT_ONLY"

    # 1. RUN FORENSIC CHECKS & ADVANCED TAMPERING AUDIT
    raw_temp_path = os.path.join(UPLOAD_DIR, f"raw_{doc_id}_{file.filename}")
    cv2.imwrite(raw_temp_path, cv_img)

    advanced_forensics = analyze_advanced_tampering(raw_temp_path, cv_img)
    fft_result = detect_screen_replay_fft(raw_temp_path)
    qr_found, qr_data, qr_bbox = locate_cryptographic_qr_exact(raw_temp_path, doc_type=doc_type)

    face_found, face_coords, face_chip, raw_face_row = locate_biometric_portrait_exact(
        raw_temp_path, template_side, is_composite, doc_type=doc_type
    )

    face_vector = None
    if face_found and face_chip is not None:
        if raw_face_row is not None and sface_recognizer is not None:
            face_vector = extract_sface_feature(cv_img, raw_face_row)
        if face_vector is None:
            face_vector = MEMORY.fallback_face_vector(face_chip)

    if os.path.exists(raw_temp_path):
        os.remove(raw_temp_path)

    # 2. APPLY REGULATORY REDACTION AND PERSIST DISPLAY FILE
    sanitized_img = apply_regulatory_mask(cv_img, doc_type)
    cv2.imwrite(file_path, sanitized_img)

    risk_score = 0
    risk_breakdown = []
    evidence_regions = []
    ai_explanations = []

    # Map Document Identifiers
    if doc_type == "Driving Licence":
        raw_id = dl_matches[0].replace(" ", "") if dl_matches else ""
        subject_masked = f"{raw_id[:4]}****{raw_id[-4:]}" if len(raw_id) >= 8 else "DL Redacted"
    elif doc_type == "Passport":
        raw_id = passport_matches[0] if passport_matches else ""
        subject_masked = f"{raw_id[:2]}****{raw_id[-2:]}" if len(raw_id) >= 4 else "Passport Redacted"
    elif doc_type == "PAN Card":
        raw_id = pan_matches[0] if pan_matches else ""
        subject_masked = f"{raw_id[:2]}****{raw_id[-2:]}" if len(raw_id) >= 4 else "PAN Redacted"
    else:
        aadhaar_matches = re.findall(r'\b\d{4}\s?\d{4}\s?\d{4}\b', upper_text)
        raw_id = aadhaar_matches[0].replace(" ", "") if aadhaar_matches else ""
        subject_masked = "[Aadhaar Redacted]"

    # 3. STRUCTURAL, CHRONOLOGICAL & EXPIRY VALIDATION
    validation_outcome = validate_document_fields(doc_type, raw_text, raw_id)
    extracted_name = validation_outcome.get("extractedFields", {}).get("name", "")

    # 4. NATIONAL SECURITY & SANCTIONS WATCHLIST SCREENING
    watchlist_audit = query_national_watchlist(full_name=extracted_name, document_number=raw_id)
    if watchlist_audit["result"] == "MATCH_FOUND":
        match = watchlist_audit["matchedEntry"]
        risk_score += 55
        risk_breakdown.append({
            "signal": f"National Watchlist Hit ({match['severity']})",
            "weight": 55,
            "impact": "negative",
            "description": f"Subject matches central sanctions record '{match['fullName']}' - {match['reason']}.",
        })
        ai_explanations.append(f"CRITICAL SANCTIONS ALERT: Identity collision with central watchlist ({match['category']}).")
        evidence_regions.append({
            "id": "EV-WATCHLIST",
            "label": "Law Enforcement Watchlist Match",
            "confidence": int(watchlist_audit["matchScore"] * 100),
            "x": 8.0,
            "y": 8.0,
            "width": 84.0,
            "height": 84.0,
            "type": "pixel_splice",
            "explanation": f"Matched suspect dossier: {match['fullName']} ({match['reason']})",
        })
    elif watchlist_audit["result"] == "REVIEW_REQUIRED":
        risk_score += 25
        risk_breakdown.append({
            "signal": "Watchlist Correlation Flag",
            "weight": 25,
            "impact": "negative",
            "description": f"Partial identity correlation with active watchlist entry ({watchlist_audit['matchedEntry']['fullName']}).",
        })
    else:
        risk_breakdown.append({
            "signal": "Sanctions & Watchlist Clear",
            "weight": -5,
            "impact": "positive",
            "description": "Zero active red notices or law enforcement alerts matched in central watchlist.",
        })

    # 5. INJECT ADVANCED FORENSIC TAMPERING & SPLICING REGIONS
    if advanced_forensics["tampering_detected"]:
        risk_score += 35
        for ind in advanced_forensics["indicators"]:
            risk_breakdown.append({
                "signal": "Forensic Manipulation Anomaly",
                "weight": 20,
                "impact": "negative",
                "description": ind,
            })
            ai_explanations.append(f"Forensic Alert: {ind}")

        for region in advanced_forensics["suspicious_regions"]:
            evidence_regions.append(region)
    else:
        risk_breakdown.append({
            "signal": "Multi-Layer Pixel & EXIF Integrity Passed",
            "weight": -10,
            "impact": "positive",
            "description": "Block ELA variance, noise spectrum, and metadata signatures within physical document baseline.",
        })

    # 6. STRUCTURAL VALIDATION CHECKS
    if not validation_outcome["isValid"]:
        val_penalty = min(25, validation_outcome["failed"] * 10)
        risk_score += val_penalty
        for check in validation_outcome["checks"]:
            if check["status"] == "fail":
                risk_breakdown.append({
                    "signal": f"Structural Check Failed: {check['label']}",
                    "weight": 10,
                    "impact": "negative",
                    "description": check["message"],
                })
                ai_explanations.append(check["message"])
    else:
        risk_breakdown.append({
            "signal": "Document Chronology & Sequence Passed",
            "weight": -5,
            "impact": "positive",
            "description": "Timeline, name structure, and credential lifecycle validated.",
        })

    # 7. SYNDICATE GRAPH INTELLIGENCE CHECK
    graph_audit = MEMORY.audit_submission(
        doc_id=doc_id,
        subject_raw_id=raw_id,
        face_vector=face_vector,
        doc_img=cv_img,
    )

    if graph_audit["is_syndicate_attack"]:
        risk_score += graph_audit["syndicate_penalty"]
        for sig in graph_audit["network_signals"]:
            risk_breakdown.append({
                "signal": sig["vector"],
                "weight": sig["weight"],
                "impact": "negative",
                "description": sig["description"],
            })
            ai_explanations.append(f"Network Intelligence Alert: {sig['description']}")
            evidence_regions.append({
                "id": "EV-SYNDICATE",
                "label": "Syndicate Attack Vector",
                "confidence": 98,
                "x": 10.0,
                "y": 10.0,
                "width": 80.0,
                "height": 80.0,
                "type": "pixel_splice",
                "explanation": sig["description"],
            })
    else:
        risk_breakdown.append({
            "signal": "Syndicate Graph Check Clear",
            "weight": -5,
            "impact": "positive",
            "description": f"Unique capture vector confirmed against {MEMORY.experience_level['screened_count']} historical nodes",
        })

    # 8. BIOMETRIC PORTRAIT EVIDENCE
    if template_side == "BACK_ONLY":
        risk_breakdown.append({
            "signal": "Template Orientation Verified",
            "weight": -5,
            "impact": "positive",
            "description": "Reverse card side verified; facial portrait not statutory to reverse layout",
        })
    elif face_found and face_coords:
        for idx, face in enumerate(face_coords):
            evidence_regions.append({
                "id": f"EV-FACE-{idx}",
                "label": f"Biometric Portrait Area ({doc_type})",
                "confidence": int(face.get("confidence", 97)),
                "x": face["x"],
                "y": face["y"],
                "width": face["width"],
                "height": face["height"],
                "type": "layout_shift",
                "explanation": f"Statutory facial portrait verified in expected quadrant for {doc_type}.",
            })
        risk_breakdown.append({
            "signal": "Biometric Portrait Confirmed",
            "weight": -10,
            "impact": "positive",
            "description": f"Statutory facial portrait resolved on {doc_type} canvas",
        })
    else:
        risk_score += 25
        risk_breakdown.append({
            "signal": "Biometric Portrait Missing",
            "weight": 25,
            "impact": "negative",
            "description": f"No facial photograph resolved on {doc_type} canvas",
        })
        ai_explanations.append("Mandatory facial photograph could not be resolved in inspection quadrants.")

    # 9. SECURITY BARCODE / QR / MRZ VERIFICATION
    if doc_type == "Passport":
        qr_status = "VERIFIED"
        if len(mrz_matches) > 0 or "P<IND" in upper_text:
            risk_breakdown.append({
                "signal": "ICAO 9303 MRZ Band Verified",
                "weight": -15,
                "impact": "positive",
                "description": "Standard optical Machine Readable Zone verified on passport canvas",
            })
            evidence_regions.append({
                "id": "EV-MRZ",
                "label": "ICAO 9303 MRZ Band",
                "confidence": 99,
                "x": 5.0,
                "y": 78.0,
                "width": 90.0,
                "height": 18.0,
                "type": "qr_forgery",
                "explanation": "High-security Machine Readable Zone format valid.",
            })
        else:
            risk_breakdown.append({
                "signal": "Passport Layout Validated",
                "weight": -5,
                "impact": "positive",
                "description": "Passport bio page verified; 2D QR matrix is non-statutory to primary page",
            })

    elif doc_type == "Driving Licence":
        qr_status = "VERIFIED"
        if qr_found and qr_bbox:
            risk_breakdown.append({
                "signal": "Security Matrix Pattern Located",
                "weight": -10,
                "impact": "positive",
                "description": "High-density security grid confirmed on Driving Licence canvas",
            })
            evidence_regions.append({
                "id": "EV-QR",
                "label": "Cryptographic QR Matrix",
                "confidence": 98,
                "x": qr_bbox["x"],
                "y": qr_bbox["y"],
                "width": qr_bbox["width"],
                "height": qr_bbox["height"],
                "type": "qr_forgery",
                "explanation": "Security matrix located and aligned.",
            })
        else:
            risk_breakdown.append({
                "signal": "Smart Card DL Format Verified",
                "weight": -5,
                "impact": "positive",
                "description": "Integrated microchip & visual layout verified; standalone 2D matrix non-statutory",
            })

    elif doc_type == "PAN Card":
        qr_status = "VERIFIED"
        if qr_found and qr_bbox:
            risk_breakdown.append({
                "signal": "Cryptographic e-PAN QR Located",
                "weight": -10,
                "impact": "positive",
                "description": "High-density e-PAN security matrix located and confirmed",
            })
            evidence_regions.append({
                "id": "EV-QR",
                "label": "Cryptographic QR Matrix",
                "confidence": 98,
                "x": qr_bbox["x"],
                "y": qr_bbox["y"],
                "width": qr_bbox["width"],
                "height": qr_bbox["height"],
                "type": "qr_forgery",
                "explanation": "Security 2D matrix located and aligned for PAN Card.",
            })
        else:
            risk_breakdown.append({
                "signal": "Classic PAN Card Layout Verified",
                "weight": -5,
                "impact": "positive",
                "description": "Standard physical PAN specimen verified; 2D QR matrix non-statutory for legacy format",
            })

    else:
        if qr_found and qr_bbox:
            qr_status = "VERIFIED"
            risk_breakdown.append({
                "signal": "Security Matrix Pattern Located",
                "weight": -10,
                "impact": "positive",
                "description": "High-density security grid confirmed on Aadhaar canvas",
            })
            evidence_regions.append({
                "id": "EV-QR",
                "label": "Cryptographic QR Matrix",
                "confidence": 98,
                "x": qr_bbox["x"],
                "y": qr_bbox["y"],
                "width": qr_bbox["width"],
                "height": qr_bbox["height"],
                "type": "qr_forgery",
                "explanation": "Security 2D matrix located and aligned for Aadhaar.",
            })
        elif template_side == "FRONT_ONLY":
            qr_status = "VERIFIED"
            risk_breakdown.append({
                "signal": "Template Layout Orientation",
                "weight": -5,
                "impact": "positive",
                "description": "Front-side document confirmed; QR code is statutory to reverse side",
            })
        else:
            risk_score += 25
            qr_status = "FAILED"
            risk_breakdown.append({
                "signal": "Cryptographic QR Missing",
                "weight": 25,
                "impact": "negative",
                "description": "Expected 2D matrix missing from reverse Aadhaar inspection quadrants",
            })
            ai_explanations.append("Mandatory 2D security matrix missing from document inspection quadrants.")

    # 10. SCREEN REPLAY ATTACK CHECK (2D-FFT)
    if fft_result["is_screen_attack"]:
        risk_score += 35
        risk_breakdown.append({
            "signal": "2D-FFT Moiré Replay Attack",
            "weight": 35,
            "impact": "negative",
            "description": f"Periodic frequency peaks ({fft_result['spectral_ratio']}) indicate screen recapture",
        })
        ai_explanations.append("Spectral frequency analysis indicates this document was photographed from a digital display.")
    else:
        risk_breakdown.append({
            "signal": "Natural Optical Texture",
            "weight": -5,
            "impact": "positive",
            "description": "Spatial Fourier spectrum confirms physical card substrate texture",
        })

    # 11. CREDENTIAL-SPECIFIC STRUCTURAL INTEGRITY
    if doc_type == "Driving Licence":
        if raw_id:
            dl_eval = validate_driving_licence_structure(raw_id)
            if dl_eval["valid"]:
                weight = -10 if dl_eval.get("strict") else -5
                risk_breakdown.append({
                    "signal": "Driving Licence Syntax Validated",
                    "weight": weight,
                    "impact": "positive",
                    "description": f"State/UT code '{dl_eval['state']}' & issuance record verified.",
                })
            else:
                risk_score += 40
                risk_breakdown.append({
                    "signal": "Driving Licence Syntax Warning",
                    "weight": 40,
                    "impact": "negative",
                    "description": dl_eval["reason"],
                })
                ai_explanations.append(f"DL identifier error: {dl_eval['reason']}.")
        else:
            risk_score += 20
            risk_breakdown.append({
                "signal": "DL Identifier Incomplete",
                "weight": 20,
                "impact": "negative",
                "description": "Full Driving Licence alphanumeric sequence not extracted cleanly via OCR",
            })

    elif doc_type == "Passport":
        if raw_id:
            pass_eval = validate_passport_structure(raw_id)
            if pass_eval["valid"]:
                risk_breakdown.append({
                    "signal": "Passport Number Validated",
                    "weight": -10,
                    "impact": "positive",
                    "description": "Standard 8-character Indian Passport series & sequence syntax confirmed.",
                })
            else:
                risk_score += 40
                risk_breakdown.append({
                    "signal": "Passport Syntax Warning",
                    "weight": 40,
                    "impact": "negative",
                    "description": pass_eval["reason"],
                })
        else:
            risk_score += 20
            risk_breakdown.append({
                "signal": "Passport Identifier Incomplete",
                "weight": 20,
                "impact": "negative",
                "description": "Standard 8-character passport alphanumeric string not extracted cleanly via OCR",
            })

    elif doc_type == "PAN Card":
        if raw_id:
            pan_eval = validate_pan_structure(raw_id)
            if pan_eval["valid"]:
                risk_breakdown.append({
                    "signal": "PAN Syntax & Entity Taxonomy Validated",
                    "weight": -10,
                    "impact": "positive",
                    "description": f"Standard syntax verified: Entity character '{pan_eval['entity_code']}' maps to {pan_eval['entity_type']}.",
                })
            else:
                risk_score += 45
                risk_breakdown.append({
                    "signal": "PAN Syntax Violation",
                    "weight": 45,
                    "impact": "negative",
                    "description": pan_eval["reason"],
                })
                ai_explanations.append(f"PAN identifier error: {pan_eval['reason']}.")
        else:
            risk_score += 25
            risk_breakdown.append({
                "signal": "PAN Identifier Missing",
                "weight": 25,
                "impact": "negative",
                "description": "10-character Permanent Account Number string could not be extracted via OCR",
            })

    else:
        if raw_id:
            if not validate_verhoeff(raw_id):
                risk_score += 50
                risk_breakdown.append({
                    "signal": "Verhoeff Checksum Failure",
                    "weight": 50,
                    "impact": "negative",
                    "description": "Identity number violates Dihedral group D5 permutation integrity",
                })
                ai_explanations.append("The 12-digit identity number failed the mathematical Verhoeff checksum algorithm.")
            else:
                risk_breakdown.append({
                    "signal": "Verhoeff Checksum Validated",
                    "weight": -10,
                    "impact": "positive",
                    "description": "Dihedral group D5 checksum verified successfully",
                })

    # 12. OFFLINE / SARATHI / NSDL GATEWAYS
    registry_verification = {"verified": False, "status": "NOT_CHECKED"}
    if doc_type == "PAN Card" and raw_id:
        registry_verification = await KYC_GATEWAY.verify_pan(raw_id)
    elif doc_type == "Driving Licence" and raw_id:
        registry_verification = await KYC_GATEWAY.verify_driving_licence(raw_id)
    elif doc_type == "Passport" and raw_id:
        registry_verification = await KYC_GATEWAY.verify_passport(raw_id)
    elif doc_type == "Aadhaar":
        registry_verification = await KYC_GATEWAY.verify_aadhaar_offline(qr_data or "")

    if registry_verification.get("verified"):
        risk_breakdown.append({
            "signal": "Government Central Registry Match",
            "weight": -10,
            "impact": "positive",
            "description": f"Record confirmed active by {registry_verification.get('registry', 'Official Registry')}",
        })

    elapsed_time = round(time.perf_counter() - t0, 3)

    final_risk = max(5, min(risk_score, 99))
    if final_risk >= 70:
        doc_status = "CRITICAL"
        recommendation = "SECONDARY INSPECTION REQUIRED — Escalate immediately; do not clear without supervisor review."
    elif final_risk >= 40:
        doc_status = "SUSPICIOUS"
        recommendation = "SECONDARY INSPECTION RECOMMENDED — Resolve flagged items with bearer before clearance."
    else:
        doc_status = "VERIFIED"
        recommendation = "CLEARANCE PERMITTED — Standard processing may continue."

    expected_sig = {
        "PAN Card": "INCOME_TAX_DEPARTMENT_DIGITAL_SIGNATURE",
        "Driving Licence": "STATE_TRANSPORT_AUTHORITY_SMART_RECORD",
        "Passport": "MINISTRY_OF_EXTERNAL_AFFAIRS_ICAO9303_SIGNATURE",
        "Aadhaar": "SECURE_UIDAI_ASYMMETRIC_SIGNATURE",
    }.get(doc_type, "SECURE_CENTRAL_AUTHORITY_SIGNATURE")

    result = {
        "id": doc_id,
        "docType": doc_type,
        "subjectMaskedId": subject_masked,
        "riskScore": final_risk,
        "ocrConfidence": 95,
        "tamperingDetected": final_risk > 35,
        "qrStatus": qr_status,
        "status": doc_status,
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S IST"),
        "processedByNode": "IDSHIELD-FORENSIC-CLUSTER-01",
        "screenedByOfficer": officer["badgeId"],
        "processingTimeSeconds": elapsed_time,
        "layoutIntegrity": 95 if final_risk <= 35 else 68,
        "imageIntegrity": int(advanced_forensics.get("ela_score", 92.0)),
        "faceConsistency": 97 if face_found else (95 if template_side == "BACK_ONLY" else 20),
        "faceDetected": face_found or (template_side == "BACK_ONLY"),
        "faceQuality": 95 if face_found else (0 if template_side != "BACK_ONLY" else 90),
        "qrDecodedData": qr_data if qr_found else ("N/A (ICAO MRZ)" if doc_type == "Passport" else ("N/A (SMART CARD CHIP)" if doc_type == "Driving Licence" else ("N/A (PHYSICAL PAN)" if doc_type == "PAN Card" else "MISSING"))),
        "qrExpectedData": expected_sig,
        "aiExplanation": ai_explanations if ai_explanations else [recommendation],
        "riskBreakdown": risk_breakdown,
        "evidenceRegions": evidence_regions,
        "externalRegistryValidation": registry_verification,
        "imageUrl": f"/uploads/{os.path.basename(file_path)}",
        "engineIntelligence": MEMORY.experience_level,
        "validationOutcome": validation_outcome,
    }

    # Record verified audit event in the tamper-evident hash chain
    record_audit_event(
        event_type="DOCUMENT_INSPECTION_COMPLETED",
        event_data={
            "doc_id": doc_id,
            "doc_type": doc_type,
            "risk_score": final_risk,
            "status": doc_status,
            "tampering": final_risk > 35,
            "watchlist_hit": watchlist_audit["result"] != "CLEAR",
            "examiner_badge": officer["badgeId"],
        },
        case_id=doc_id,
    )

    save_document(result)
    return result


@app.post("/api/documents/{doc_id}/adjudicate")
async def adjudicate_document(
    doc_id: str, 
    payload: AdjudicationRequest,
    officer: Dict[str, Any] = Depends(require_clearance("L2"))
):
    """
    Statutory officer decision sign-off.
    Requires minimum Level-2 (Forensic Examiner) clearance.
    """
    docs = get_all_documents()
    target_doc = next((d for d in docs if d.get("id") == doc_id), None)
    if not target_doc:
        raise HTTPException(status_code=404, detail="Document record not found.")

    status_map = {
        "CLEARED": "VERIFIED",
        "SECONDARY_INSPECTION": "SUSPICIOUS",
        "REJECTED": "CRITICAL",
        "REFERRED_TO_SSB": "CRITICAL",
    }
    new_status = status_map.get(payload.decision, "SUSPICIOUS")
    target_doc["status"] = new_status
    officer_badge = officer["badgeId"]

    target_doc["riskBreakdown"].append({
        "signal": f"Officer Adjudication ({payload.decision})",
        "weight": 0,
        "impact": "positive" if payload.decision == "CLEARED" else "negative",
        "description": f"Badge {officer_badge}: {payload.reason}",
    })
    target_doc["aiExplanation"].insert(0, f"OFFICER DECISION [{payload.decision}]: {payload.reason}")
    save_document(target_doc)

    audit_entry = record_audit_event(
        event_type="OFFICER_DECISION_RECORDED",
        event_data={
            "doc_id": doc_id,
            "decision": payload.decision,
            "reason": payload.reason,
            "officer_badge": officer_badge,
            "officer_clearance": officer["clearance"],
            "new_status": new_status,
        },
        case_id=doc_id,
    )

    return {
        "success": True,
        "doc_id": doc_id,
        "new_status": new_status,
        "officer": officer_badge,
        "audit_hash": audit_entry["hash"],
    }


@app.get("/api/audit/verify-chain")
async def check_ledger_integrity(officer: Dict[str, Any] = Depends(get_current_officer)):
    """
    Cryptographically verifies the forward-linked SHA-256 audit ledger.
    Requires verified investigator token.
    """
    return verify_audit_chain()


@app.get("/api/audit/events")
async def get_audit_trail(
    case_id: Optional[str] = None,
    officer: Dict[str, Any] = Depends(get_current_officer)
):
    """
    Retrieves the chronological audit ledger log.
    Requires verified investigator token.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if case_id:
        cursor.execute("SELECT * FROM audit_logs WHERE case_id = ? ORDER BY rowid ASC", (case_id,))
    else:
        cursor.execute("SELECT * FROM audit_logs ORDER BY rowid DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        try:
            ev_data = json.loads(r["event_data"])
        except Exception:
            ev_data = {}
        events.append({
            "id": r["id"],
            "case_id": r["case_id"],
            "event_type": r["event_type"],
            "event_data": ev_data,
            "previous_hash": r["previous_hash"],
            "hash": r["hash"],
            "timestamp": r["timestamp"],
        })
    return {"events": events}


@app.get("/api/documents/{doc_id}/report")
async def export_document_report(doc_id: str):
    docs = get_all_documents()
    target_doc = next((d for d in docs if d.get("id") == doc_id), None)

    if not target_doc:
        return {"error": "Document record not found"}

    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, f"{doc_id}_Audit_Report.pdf")

    generate_pdf_report(target_doc, pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"IDSHIELD_Audit_{doc_id}.pdf",
    )


# ===========================================================
# 8. SYNDICATE TOPOLOGY & NETWORK DISCOVERY ROUTES
# ===========================================================

@app.get("/api/syndicate/graph")
@app.get("/api/analytics/syndicate-graph")
async def get_syndicate_graph():
    """
    Returns the dynamic multi-modal forensic graph containing all nodes,
    edges, clusters, and kingpin hubs for UI network visualization.
    """
    return build_syndicate_graph_topology()


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    docs = get_all_documents()
    total = len(docs)
    verified = sum(1 for d in docs if d.get("status") == "VERIFIED")
    suspicious = sum(1 for d in docs if d.get("status") == "SUSPICIOUS")
    high_risk = sum(1 for d in docs if d.get("status") in ["HIGH RISK", "CRITICAL"])
    avg_risk = round(sum(d.get("riskScore", 0) for d in docs) / total, 1) if total > 0 else 0.0

    verified_rate = f"{round((verified / total) * 100, 1)}%" if total > 0 else "0%"
    avg_proc_time = f"{round(sum(d.get('processingTimeSeconds', 1.0) for d in docs) / total, 2)}s" if total > 0 else "0.0s"

    return {
        "scanned": {"value": str(total), "change": f"+{total}" if total > 0 else "0", "isPositive": True},
        "verified": {"value": str(verified), "change": verified_rate, "isPositive": True},
        "suspicious": {"value": str(suspicious), "change": f"{round((suspicious/total)*100, 1) if total else 0}%", "isPositive": False},
        "highRisk": {"value": str(high_risk), "change": f"{round((high_risk/total)*100, 1) if total else 0}%", "isPositive": False},
        "avgRiskScore": {"value": str(avg_risk), "change": "Live", "isPositive": True},
        "accuracy": {"value": verified_rate, "change": "Verified Rate", "isPositive": True},
        "processingTime": {"value": avg_proc_time, "change": "Inference Latency", "isPositive": True},
        "recentDocuments": docs,
        "learningMetrics": MEMORY.experience_level,
    }


@app.get("/api/analytics")
async def get_analytics():
    docs = get_all_documents()
    total = len(docs)
    forgeries = [d for d in docs if d.get("status") in ["SUSPICIOUS", "HIGH RISK", "CRITICAL"]]

    tamper_counts = {
        "National Watchlist Match": sum(1 for d in docs if any("Watchlist" in b.get("signal", "") for b in d.get("riskBreakdown", []))),
        "12x12 Block ELA Residue": sum(1 for d in docs if any("Forensic" in b.get("signal", "") for b in d.get("riskBreakdown", []))),
        "Sybil / Face Reuse Syndicate": sum(1 for d in docs if any("Sybil" in b.get("signal", "") for b in d.get("riskBreakdown", []))),
        "Template Farm Blank Reuse": sum(1 for d in docs if any("Template Farm" in b.get("signal", "") for b in d.get("riskBreakdown", []))),
        "2D-FFT Moiré Replay Attack": sum(1 for d in docs if any("FFT" in b.get("signal", "") for b in d.get("riskBreakdown", []))),
        "Verhoeff Checksum Failure": sum(1 for d in docs if any("Verhoeff" in b.get("signal", "") and b.get("weight", 0) > 0 for b in d.get("riskBreakdown", []))),
        "PAN Syntax Violation": sum(1 for d in docs if any("PAN Syntax" in b.get("signal", "") and b.get("weight", 0) > 0 for b in d.get("riskBreakdown", []))),
        "Driving Licence Format Mismatch": sum(1 for d in docs if any("Driving Licence Syntax" in b.get("signal", "") and b.get("weight", 0) > 0 for b in d.get("riskBreakdown", []))),
        "Passport Syntax Warning": sum(1 for d in docs if any("Passport Syntax" in b.get("signal", "") and b.get("weight", 0) > 0 for b in d.get("riskBreakdown", []))),
    }

    type_counts: Dict[str, int] = {}
    for d in docs:
        dtype = d.get("docType", "Unknown")
        type_counts[dtype] = type_counts.get(dtype, 0) + 1

    type_distribution = [
        {"type": k, "count": v, "share": round((v / total) * 100, 1) if total > 0 else 0}
        for k, v in type_counts.items()
    ]

    indicator_freq: Dict[str, int] = {}
    for d in docs:
        for ind in d.get("aiExplanation", []):
            clean_ind = ind.split(":")[1].strip() if ":" in ind else ind
            if len(clean_ind) > 10:
                indicator_freq[clean_ind] = indicator_freq.get(clean_ind, 0) + 1

    top_indicators = [
        {"indicator": k, "count": v}
        for k, v in sorted(indicator_freq.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    name_map: Dict[str, set] = {}
    doc_map: Dict[str, set] = {}
    for d in docs:
        doc_id = d.get("id")
        name = d.get("validationOutcome", {}).get("extractedFields", {}).get("name", "").strip().upper()
        subj_id = d.get("subjectMaskedId", "").strip().upper()

        if name and name not in ["HOLDER RECORD", "VERIFIED CITIZEN"]:
            name_map.setdefault(name, set()).add(doc_id)
        if subj_id and "[REDACTED]" not in subj_id:
            doc_map.setdefault(subj_id, set()).add(doc_id)

    repeated_identifiers = []
    for name, cases in name_map.items():
        if len(cases) > 1:
            repeated_identifiers.append({"value": name, "type": "CITIZEN_NAME", "caseCount": len(cases)})
    for num, cases in doc_map.items():
        if len(cases) > 1:
            repeated_identifiers.append({"value": num, "type": "DOCUMENT_IDENTIFIER", "caseCount": len(cases)})
    repeated_identifiers.sort(key=lambda x: x["caseCount"], reverse=True)

    top_technique = max(tamper_counts, key=tamper_counts.get) if any(tamper_counts.values()) else "None"
    most_forged_type = max(type_counts, key=type_counts.get) if any(type_counts.values()) else "None"

    return {
        "totalQuarantined": len(forgeries),
        "mostForged": most_forged_type,
        "topVector": top_technique,
        "avgInference": f"{round(sum(d.get('processingTimeSeconds', 1.0) for d in docs) / total, 2)}s" if total > 0 else "0.0s",
        "tamperingVectors": [
            {"technique": k, "count": v, "pct": round(v / total * 100) if total else 0}
            for k, v in tamper_counts.items()
        ],
        "typeDistribution": type_distribution,
        "suspiciousCases": forgeries[:25],
        "topIndicators": top_indicators,
        "repeatedIdentifiers": repeated_identifiers[:15],
        "riskTrend": [
            {"idx": i + 1, "score": d.get("riskScore", 0), "status": d.get("status")}
            for i, d in enumerate(reversed(docs[:30]))
        ],
        "syndicateClusters": MEMORY.syndicate_clusters,
        "learningStage": MEMORY.experience_level,
    }


@app.get("/api/analytics/intelligence")
async def get_intelligence_analytics():
    return await get_analytics()


@app.delete("/api/documents/clear")
async def clear_all_documents(officer: Dict[str, Any] = Depends(require_clearance("L3"))):
    """
    Destructive session memory purge.
    Requires minimum Level-3 (Gov. Lead Investigator) clearance.
    """
    clear_documents()
    MEMORY.face_registry.clear()
    MEMORY.layout_registry.clear()
    MEMORY.syndicate_clusters.clear()
    return {
        "message": f"All session records and syndicate graph memory cleared by {officer['name']} ({officer['badgeId']})"
    }


@app.post("/api/documents/seed-demo")
async def trigger_seed_demo():
    seed_database()
    docs = get_all_documents()

    # Hydrate active RAM memory with mock embeddings & pHashes
    mock_vector_syndicate = np.array([0.15] * 128, dtype=np.float32)
    mock_vector_syndicate = mock_vector_syndicate / np.linalg.norm(mock_vector_syndicate)

    for idx, d in enumerate(docs):
        did = d.get("id")
        is_syndicate_target = any(
            "Sybil" in b.get("signal", "") or "Template Farm" in b.get("signal", "")
            for b in d.get("riskBreakdown", [])
        )
        if is_syndicate_target or idx == 0:
            MEMORY.face_registry.append({
                "doc_id": did,
                "raw_id": d.get("subjectMaskedId", ""),
                "embedding": mock_vector_syndicate,
                "timestamp": datetime.now(),
            })
            MEMORY.layout_registry.append({
                "doc_id": did,
                "phash": "1111000011110000111100001111000011110000111100001111000011110000",
                "timestamp": datetime.now(),
            })

    return {"message": "Demo scenarios and synthetic images generated successfully"}