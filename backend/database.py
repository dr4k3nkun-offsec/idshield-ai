import sqlite3
import json
import re
from typing import List, Dict, Any, Optional

DB_FILE = "idshield.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates the persistent document, watchlist, and tamper-evident audit tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Scanned Documents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            doc_type TEXT,
            subject_masked_id TEXT,
            risk_score INTEGER,
            status TEXT,
            tampering_detected INTEGER,
            qr_status TEXT,
            face_detected INTEGER,
            processing_time_seconds REAL,
            timestamp TEXT,
            raw_json TEXT
        )
    """)

    # 2. Watchlist Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_entries (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            document_number TEXT,
            reason TEXT NOT NULL,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 3. Tamper-Evident SHA-256 Audit Chain Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            case_id TEXT,
            event_type TEXT NOT NULL,
            event_data TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            hash TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Seed default law enforcement watchlist entries if empty
    cursor.execute("SELECT COUNT(*) FROM watchlist_entries")
    if cursor.fetchone()[0] == 0:
        seed_watchlist = [
            ("WL-IND-01", "VIKRAM ADITYA SINGHANIA", "ABCDE1234F", "Hawala & Multi-State Financial Laundering", "CRITICAL", "Economic Offense"),
            ("WL-IND-02", "MOHAMMED REHAN KHAN", "P1234567", "Interpol Red Notice // Cross-Border Passport Forgery", "CRITICAL", "Border Security"),
            ("WL-IND-03", "RAJESH KUMAR SHARMA", "DL0420190012345", "Multiple Impersonations & Commercial Driver License Fraud", "HIGH", "Identity Theft"),
            ("WL-IND-04", "ANIL SURESH PATEL", "DL0120150098765", "Suspended Motor Transit Record & Stolen Identity", "SUSPICIOUS", "Traffic Enforcement"),
            ("WL-IND-05", "PAGI ATHARVA BHARATBHAI", "SAMPLE-ALERT-DOC", "Demonstration Watchlist Clearance Test", "LOW", "Regulatory Audit"),
        ]
        cursor.executemany("""
            INSERT INTO watchlist_entries (id, full_name, document_number, reason, severity, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, seed_watchlist)

    conn.commit()
    conn.close()

def clean_image_url(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures image URLs use relative /uploads paths rather than localhost."""
    if "imageUrl" in doc and isinstance(doc["imageUrl"], str):
        doc["imageUrl"] = re.sub(r"^https?://(localhost|127\.0\.0\.1):8000", "", doc["imageUrl"])
    return doc

def save_document(doc: Dict[str, Any]):
    doc = clean_image_url(doc)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO documents (
            id, doc_type, subject_masked_id, risk_score, status,
            tampering_detected, qr_status, face_detected,
            processing_time_seconds, timestamp, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc.get("id"),
        doc.get("docType"),
        doc.get("subjectMaskedId"),
        doc.get("riskScore"),
        doc.get("status"),
        1 if doc.get("tamperingDetected") else 0,
        doc.get("qrStatus"),
        1 if doc.get("faceDetected") else 0,
        doc.get("processingTimeSeconds", 0.0),
        doc.get("timestamp"),
        json.dumps(doc)
    ))
    conn.commit()
    conn.close()

def get_all_documents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT raw_json FROM documents ORDER BY rowid DESC")
    rows = cursor.fetchall()
    conn.close()
    
    records = []
    for row in rows:
        try:
            data = json.loads(row["raw_json"])
            data = clean_image_url(data)
            records.append(data)
        except Exception:
            continue
    return records

def clear_documents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents")
    cursor.execute("DELETE FROM audit_logs")
    conn.commit()
    conn.close()

def calculate_token_similarity(a: str, b: str) -> float:
    """Computes tokenized Jaccard similarity across whitespace-delimited word tokens."""
    def tokenize(s: str):
        return set(re.findall(r'\b[A-Za-z0-9]+\b', s.upper()))

    set_a = tokenize(a)
    set_b = tokenize(b)
    if not set_a or not set_b:
        return 0.0
    if set_a == set_b:
        return 1.0

    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return round(float(intersection / union), 3) if union > 0 else 0.0

def query_national_watchlist(full_name: Optional[str] = None, document_number: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlist_entries")
    records = cursor.fetchall()
    conn.close()

    clean_doc = re.sub(r'[^A-Za-z0-9]', '', str(document_number or '').upper())

    if clean_doc:
        for r in records:
            db_doc = re.sub(r'[^A-Za-z0-9]', '', str(r["document_number"] or '').upper())
            if db_doc and db_doc == clean_doc:
                return {
                    "result": "MATCH_FOUND",
                    "matchScore": 1.0,
                    "matchedEntryId": r["id"],
                    "matchedEntry": {
                        "id": r["id"],
                        "fullName": r["full_name"],
                        "documentNumber": r["document_number"],
                        "reason": r["reason"],
                        "severity": r["severity"],
                        "category": r["category"]
                    }
                }

    if full_name and len(full_name.strip()) > 3:
        best_score = 0.0
        best_entry = None

        for r in records:
            score = calculate_token_similarity(full_name, r["full_name"])
            if score > best_score:
                best_score = score
                best_entry = r

        if best_entry and best_score >= 0.80:
            return {
                "result": "MATCH_FOUND",
                "matchScore": round(best_score, 2),
                "matchedEntryId": best_entry["id"],
                "matchedEntry": {
                    "id": best_entry["id"],
                    "fullName": best_entry["full_name"],
                    "documentNumber": best_entry["document_number"],
                    "reason": best_entry["reason"],
                    "severity": best_entry["severity"],
                    "category": best_entry["category"]
                }
            }
        elif best_entry and best_score >= 0.40:
            return {
                "result": "REVIEW_REQUIRED",
                "matchScore": round(best_score, 2),
                "matchedEntryId": best_entry["id"],
                "matchedEntry": {
                    "id": best_entry["id"],
                    "fullName": best_entry["full_name"],
                    "documentNumber": best_entry["document_number"],
                    "reason": best_entry["reason"],
                    "severity": best_entry["severity"],
                    "category": best_entry["category"]
                }
            }

    return {
        "result": "CLEAR",
        "matchScore": 0.0,
        "matchedEntryId": None,
        "matchedEntry": None
    }