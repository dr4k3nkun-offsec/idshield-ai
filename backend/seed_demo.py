import os
import json
import sqlite3
import cv2
import numpy as np
from datetime import datetime
from audit_service import record_audit_event
from database import init_db, save_document

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
init_db()

def create_synthetic_id_card(filename: str, doc_type: str, name: str, masked_id: str, is_tampered: bool = False) -> str:
    """Generates a realistic physical image specimen in uploads/ for demo inspection."""
    h, w = 500, 800
    canvas = np.full((h, w, 3), 245, dtype=np.uint8)

    # Background gradient / security substrate tint
    if doc_type == "Passport":
        header_color = (60, 40, 15)      # Deep blue/brown
        accent_color = (210, 180, 140)
    elif doc_type == "PAN Card":
        header_color = (30, 80, 120)     # Navy / Gold
        accent_color = (180, 220, 240)
    else:  # Driving Licence
        header_color = (40, 90, 40)      # Forest Green
        accent_color = (190, 230, 190)

    # Draw security border and header bar
    cv2.rectangle(canvas, (10, 10), (w - 10, h - 10), accent_color, 2)
    cv2.rectangle(canvas, (10, 10), (w - 10, 75), header_color, -1)

    # Header Text
    title_text = f"REPUBLIC OF INDIA // {doc_type.upper()}"
    cv2.putText(canvas, title_text, (30, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

    # Security guilloche wave pattern simulation
    for y in range(90, h - 30, 20):
        cv2.line(canvas, (20, y), (w - 20, y), (235, 235, 235), 1)

    # Biometric Portrait Box
    if doc_type == "Passport":
        px, py, pw, ph = int(w * 0.62), int(h * 0.25), int(w * 0.28), int(h * 0.48)
    else:
        px, py, pw, ph = int(w * 0.06), int(h * 0.24), int(w * 0.25), int(h * 0.50)

    cv2.rectangle(canvas, (px, py), (px + pw, py + ph), (180, 180, 180), -1)
    cv2.rectangle(canvas, (px, py), (px + pw, py + ph), (80, 80, 80), 2)
    cv2.circle(canvas, (px + pw // 2, py + int(ph * 0.38)), int(pw * 0.22), (130, 130, 130), -1)
    cv2.ellipse(canvas, (px + pw // 2, py + ph), (int(pw * 0.38), int(ph * 0.40)), 0, 180, 360, (130, 130, 130), -1)
    cv2.putText(canvas, "PORTRAIT", (px + 15, py + ph - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Text Field Details
    tx = 40 if doc_type == "Passport" else int(w * 0.36)
    cv2.putText(canvas, f"NAME: {name}", (tx, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    cv2.putText(canvas, f"IDENTIFIER: {masked_id}", (tx, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
    cv2.putText(canvas, "NATIONALITY: INDIAN", (tx, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 60, 60), 1)
    cv2.putText(canvas, "STATUS: OFFICIAL CITIZEN RECORD", (tx, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 1)

    # 2D Security Matrix / Cryptographic Barcode Box
    qx, qy, qw, qh = int(w * 0.68) if doc_type != "Passport" else int(w * 0.06), int(h * 0.58), 120, 120
    cv2.rectangle(canvas, (qx, qy), (qx + qw, qy + qh), (255, 255, 255), -1)
    cv2.rectangle(canvas, (qx, qy), (qx + qw, qy + qh), (0, 0, 0), 2)
    for bx in range(qx + 10, qx + qw - 10, 15):
        for by in range(qy + 10, qy + qh - 10, 15):
            if (bx + by) % 30 == 0:
                cv2.rectangle(canvas, (bx, by), (bx + 10, by + 10), (0, 0, 0), -1)
    cv2.putText(canvas, "SECURE MATRIX", (qx - 5, qy + qh + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1)

    # Inject visible tampering artifacts for Scenario 02 (Photoshop clone/splice)
    if is_tampered:
        splice_box = canvas[170:210, tx:tx + 220]
        noise = np.random.randint(0, 75, splice_box.shape, dtype=np.uint8)
        canvas[170:210, tx:tx + 220] = cv2.add(splice_box, noise)
        cv2.rectangle(canvas, (tx - 5, 165), (tx + 225, 215), (0, 140, 255), 2)

    # Machine Readable Zone (MRZ) on Passports
    if doc_type == "Passport":
        mrz_bg = np.full((70, w - 20, 3), 230, dtype=np.uint8)
        canvas[h - 85:h - 15, 10:w - 10] = mrz_bg
        cv2.putText(canvas, "P<INDVERMA<<ROHAN<<<<<<<<<<<<<<<<<<<<<<<<<<", (25, h - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 1)
        cv2.putText(canvas, f"{masked_id.replace('*', '0')}3IND9003142M3106108<<<<<<<<<<<<<<<4", (25, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 1)

    target_path = os.path.join(UPLOAD_DIR, filename)
    cv2.imwrite(target_path, canvas)
    # After
    return f"/uploads/{filename}"
    # return f"http://localhost:8000/uploads/{filename}"

DEMO_SCENARIOS = [
    {
        "id": "DOC-2026-DEMO-01",
        "docType": "Passport",
        "subjectMaskedId": "M4****78",
        "riskScore": 12,
        "ocrConfidence": 96,
        "tamperingDetected": False,
        "qrStatus": "VERIFIED",
        "status": "VERIFIED",
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S IST"),
        "processedByNode": "IDSHIELD-FORENSIC-NODE-01",
        "processingTimeSeconds": 0.28,
        "layoutIntegrity": 98,
        "imageIntegrity": 95,
        "faceConsistency": 94,
        "faceDetected": True,
        "faceQuality": 95,
        "qrDecodedData": "ICAO_9303_VALIDATED",
        "qrExpectedData": "MINISTRY_OF_EXTERNAL_AFFAIRS_ICAO9303_SIGNATURE",
        "aiExplanation": ["All optical, facial biometric, and chronological checks verified within genuine tolerances."],
        "riskBreakdown": [
            {"signal": "Sanctions & Watchlist Clear", "weight": -5, "impact": "positive", "description": "No active red notices matched in national database."},
            {"signal": "Biometric Portrait Confirmed", "weight": -10, "impact": "positive", "description": "YuNet + SFace neural embedding matched high-confidence photo."},
            {"signal": "ICAO 9303 MRZ Band Verified", "weight": -15, "impact": "positive", "description": "Machine Readable Zone syntax conforms to international passport standards."},
            {"signal": "Document Chronology & Sequence Passed", "weight": -5, "impact": "positive", "description": "Holder date of birth precedes valid expiry date."}
        ],
        "evidenceRegions": [
            {"id": "EV-FACE-0", "label": "Biometric Portrait Area (Passport)", "confidence": 98, "x": 62.0, "y": 25.0, "width": 28.0, "height": 48.0, "type": "layout_shift", "explanation": "Statutory facial portrait verified in expected quadrant."}
        ],
        "validationOutcome": {
            "checks": [
                {"code": "STRUCT_ID_PRESENT", "label": "Passport Number", "status": "pass", "message": "Standard 8-character Indian passport series confirmed."},
                {"code": "CONS_NAME_TOKENS", "label": "Holder Name Structure", "status": "pass", "message": "Full legal name verified: 'Rohan Verma'"},
                {"code": "LOGIC_DOB_OK", "label": "Date of Birth Validity", "status": "pass", "message": "Date of birth validated (Age: 34 yrs)"},
                {"code": "EXP_VALID", "label": "Document Expiration Status", "status": "pass", "message": "Credential active and valid for 1740 days"}
            ],
            "passed": 4, "warnings": 0, "failed": 0, "isValid": True,
            "extractedFields": {"name": "Rohan Verma", "dob": "14/03/1990", "gender": "M", "expiry": "10/06/2031"}
        }
    },
    {
        "id": "DOC-2026-DEMO-02",
        "docType": "Driving Licence",
        "subjectMaskedId": "DL04****2345",
        "riskScore": 88,
        "ocrConfidence": 78,
        "tamperingDetected": True,
        "qrStatus": "FAILED",
        "status": "CRITICAL",
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S IST"),
        "processedByNode": "IDSHIELD-FORENSIC-NODE-01",
        "processingTimeSeconds": 0.31,
        "layoutIntegrity": 52,
        "imageIntegrity": 38,
        "faceConsistency": 62,
        "faceDetected": True,
        "faceQuality": 70,
        "qrDecodedData": "NOT_DECODABLE",
        "qrExpectedData": "STATE_TRANSPORT_AUTHORITY_SMART_RECORD",
        "aiExplanation": [
            "CRITICAL ALERT: Multi-layer localized Error Level Analysis (ELA) anomalies detected.",
            "EXIF metadata indicates image alteration in Adobe Photoshop 24.0."
        ],
        "riskBreakdown": [
            {"signal": "Forensic Manipulation Anomaly", "weight": 35, "impact": "negative", "description": "4 image blocks exhibit elevated Error Level Analysis residue consistent with splicing."},
            {"signal": "Digital Smoothing / Cloning", "weight": 20, "impact": "negative", "description": "Texture variance suggests digital clone stamp manipulation over credential identifier."},
            {"signal": "Editing Software Signature", "weight": 25, "impact": "negative", "description": "EXIF metadata records external image modification in 'Adobe Photoshop 24.0'."},
            {"signal": "Cryptographic QR Missing", "weight": 25, "impact": "negative", "description": "Security microchip and 2D matrix occluded or digitally excised."}
        ],
        "evidenceRegions": [
            {"id": "EV-ELA-1", "label": "Elevated Compression Residue", "confidence": 96, "x": 36.0, "y": 32.0, "width": 30.0, "height": 14.0, "type": "pixel_splice", "explanation": "Localized DCT variance indicates modified date and serial fields."}
        ],
        "validationOutcome": {
            "checks": [
                {"code": "STRUCT_ID_PRESENT", "label": "Document Identifier", "status": "pass", "message": "DL string located."},
                {"code": "CONS_NAME_TOKENS", "label": "Holder Name Structure", "status": "pass", "message": "Name: 'Suresh Thapa'"},
                {"code": "EXP_VALID", "label": "Document Expiration Status", "status": "warn", "message": "Expiry date modified with anomalous font kerning."}
            ],
            "passed": 2, "warnings": 1, "failed": 0, "isValid": True,
            "extractedFields": {"name": "Suresh Thapa", "dob": "22/11/1985", "gender": "M", "expiry": "05/02/2029"}
        }
    },
    {
        "id": "DOC-2026-DEMO-03",
        "docType": "PAN Card",
        "subjectMaskedId": "AB****4F",
        "riskScore": 95,
        "ocrConfidence": 94,
        "tamperingDetected": False,
        "qrStatus": "VERIFIED",
        "status": "CRITICAL",
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S IST"),
        "processedByNode": "IDSHIELD-FORENSIC-NODE-01",
        "processingTimeSeconds": 0.25,
        "layoutIntegrity": 95,
        "imageIntegrity": 92,
        "faceConsistency": 96,
        "faceDetected": True,
        "faceQuality": 95,
        "qrDecodedData": "INCOME_TAX_DEPARTMENT_VALIDATED",
        "qrExpectedData": "INCOME_TAX_DEPARTMENT_DIGITAL_SIGNATURE",
        "aiExplanation": [
            "CRITICAL SANCTIONS WARNING: Identity matches active law enforcement sanctions record.",
            "Subject flagged for multi-state financial fraud and money laundering."
        ],
        "riskBreakdown": [
            {"signal": "National Watchlist Hit (CRITICAL)", "weight": 55, "impact": "negative", "description": "Subject matches suspect record 'VIKRAM ADITYA SINGHANIA' - Hawala & Financial Laundering."},
            {"signal": "Sybil Network Collision", "weight": 45, "impact": "negative", "description": "Neural face embedding correlates with previously quarantined fraudulent credential."},
            {"signal": "Biometric Portrait Confirmed", "weight": -10, "impact": "positive", "description": "High-resolution portrait resolved in standard quadrant."}
        ],
        "evidenceRegions": [
            {"id": "EV-WATCHLIST", "label": "Law Enforcement Watchlist Match", "confidence": 100, "x": 5.0, "y": 5.0, "width": 90.0, "height": 90.0, "type": "pixel_splice", "explanation": "Matched Central Advisory Alert: VIKRAM ADITYA SINGHANIA"}
        ],
        "validationOutcome": {
            "checks": [
                {"code": "STRUCT_ID_PRESENT", "label": "PAN Number", "status": "pass", "message": "Syntax valid: 4th character 'P' indicates Individual citizen."},
                {"code": "CONS_NAME_TOKENS", "label": "Holder Name", "status": "pass", "message": "VIKRAM ADITYA SINGHANIA"}
            ],
            "passed": 2, "warnings": 0, "failed": 0, "isValid": True,
            "extractedFields": {"name": "VIKRAM ADITYA SINGHANIA", "dob": "10/05/1982", "gender": "M", "expiry": "N/A"}
        }
    },
    {
        "id": "DOC-2026-DEMO-04",
        "docType": "Passport",
        "subjectMaskedId": "P9****76",
        "riskScore": 75,
        "ocrConfidence": 91,
        "tamperingDetected": False,
        "qrStatus": "VERIFIED",
        "status": "HIGH RISK",
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S IST"),
        "processedByNode": "IDSHIELD-FORENSIC-NODE-01",
        "processingTimeSeconds": 0.29,
        "layoutIntegrity": 92,
        "imageIntegrity": 88,
        "faceConsistency": 31,
        "faceDetected": True,
        "faceQuality": 90,
        "qrDecodedData": "ICAO_9303_VALIDATED",
        "qrExpectedData": "MINISTRY_OF_EXTERNAL_AFFAIRS_ICAO9303_SIGNATURE",
        "aiExplanation": [
            "BIOMETRIC MISMATCH: Presenter facial geometry diverges significantly from document photograph (31% similarity).",
            "Impersonation attack vector flagged for secondary biometric review."
        ],
        "riskBreakdown": [
            {"signal": "Biometric Facial Divergence", "weight": 45, "impact": "negative", "description": "SFace cosine distance exceeds statutory threshold for individual identity."},
            {"signal": "ICAO 9303 MRZ Band Verified", "weight": -15, "impact": "positive", "description": "Machine readable optical band layout validated."},
            {"signal": "Sanctions & Watchlist Clear", "weight": -5, "impact": "positive", "description": "Zero active red notices matched."}
        ],
        "evidenceRegions": [
            {"id": "EV-FACE-0", "label": "Biometric Discrepancy", "confidence": 95, "x": 62.0, "y": 25.0, "width": 28.0, "height": 48.0, "type": "layout_shift", "explanation": "Facial landmark correlation with presented selfie failed."}
        ],
        "validationOutcome": {
            "checks": [
                {"code": "STRUCT_ID_PRESENT", "label": "Passport Number", "status": "pass", "message": "Passport number extracted."},
                {"code": "CONS_NAME_TOKENS", "label": "Holder Name", "status": "pass", "message": "Farid Hossain"}
            ],
            "passed": 2, "warnings": 0, "failed": 0, "isValid": True,
            "extractedFields": {"name": "Farid Hossain", "dob": "09/09/1988", "gender": "M", "expiry": "01/01/2030"}
        }
    },
    {
        "id": "DOC-2026-DEMO-05",
        "docType": "Driving Licence",
        "subjectMaskedId": "DL01****8765",
        "riskScore": 58,
        "ocrConfidence": 89,
        "tamperingDetected": False,
        "qrStatus": "VERIFIED",
        "status": "SUSPICIOUS",
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S IST"),
        "processedByNode": "IDSHIELD-FORENSIC-NODE-01",
        "processingTimeSeconds": 0.27,
        "layoutIntegrity": 90,
        "imageIntegrity": 91,
        "faceConsistency": 92,
        "faceDetected": True,
        "faceQuality": 92,
        "qrDecodedData": "STATE_TRANSPORT_SMART_RECORD",
        "qrExpectedData": "STATE_TRANSPORT_AUTHORITY_SMART_RECORD",
        "aiExplanation": [
            "STATUTORY LIFECYCLE VIOLATION: Credential expired 227 days ago.",
            "Vehicle transit permissions suspended; secondary verification required."
        ],
        "riskBreakdown": [
            {"signal": "Credential Expired", "weight": 35, "impact": "negative", "description": "Document expired 227 days ago. Unlawful for border clearance."},
            {"signal": "Biometric Portrait Confirmed", "weight": -10, "impact": "positive", "description": "Facial portrait matches template quadrant."}
        ],
        "evidenceRegions": [
            {"id": "EV-EXP", "label": "Expired Validity Window", "confidence": 99, "x": 36.0, "y": 50.0, "width": 45.0, "height": 18.0, "type": "layout_shift", "explanation": "Validity ended on 18/01/2026."}
        ],
        "validationOutcome": {
            "checks": [
                {"code": "STRUCT_ID_PRESENT", "label": "DL Number", "status": "pass", "message": "Alphanumeric format valid."},
                {"code": "EXP_EXPIRED", "label": "Document Expiration Status", "status": "fail", "message": "Credential expired 227 days ago"}
            ],
            "passed": 1, "warnings": 0, "failed": 1, "isValid": False,
            "extractedFields": {"name": "Anil Suresh Patel", "dob": "15/04/1979", "gender": "M", "expiry": "18/01/2026"}
        }
    }
]

def seed_database():
    print("[*] Generating synthetic physical card specimens and audit hashes...")
    for s in DEMO_SCENARIOS:
        img_filename = f"{s['id']}_preview.jpg"
        is_tampered = s["tamperingDetected"]
        holder_name = s["validationOutcome"]["extractedFields"]["name"]
        
        img_url = create_synthetic_id_card(
            filename=img_filename,
            doc_type=s["docType"],
            name=holder_name,
            masked_id=s["subjectMaskedId"],
            is_tampered=is_tampered
        )
        s["imageUrl"] = img_url

        save_document(s)
        record_audit_event(
            event_type="DOCUMENT_INSPECTION_COMPLETED",
            event_data={
                "doc_id": s["id"],
                "doc_type": s["docType"],
                "risk_score": s["riskScore"],
                "status": s["status"],
                "tampering": s["tamperingDetected"]
            },
            case_id=s["id"]
        )
        print(f"  [+] Seeded & Rendered: {s['id']} [{s['docType']}] -> {img_url}")

    print("[✓] All 5 forensic scenarios generated with full image specimens and SHA-256 audit seals.")

if __name__ == "__main__":
    seed_database()