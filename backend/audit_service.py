import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from database import get_connection

GENESIS_HASH = "0" * 64

def compute_event_hash(previous_hash: str, event_type: str, event_data: Dict[str, Any], timestamp_iso: str) -> str:
    """Generates an immutable SHA-256 hash linking the event to the prior ledger block."""
    serialized_data = json.dumps(event_data, sort_keys=True)
    payload = f"{previous_hash}|{event_type}|{serialized_data}|{timestamp_iso}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def record_audit_event(event_type: str, event_data: Dict[str, Any], case_id: Optional[str] = None) -> Dict[str, Any]:
    """Appends a new verified event to the immutable SQLite audit ledger."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT hash FROM audit_logs ORDER BY rowid DESC LIMIT 1")
    last_row = cursor.fetchone()
    previous_hash = last_row["hash"] if last_row else GENESIS_HASH

    now_iso = datetime.utcnow().isoformat() + "Z"
    event_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
    event_hash = compute_event_hash(previous_hash, event_type, event_data, now_iso)

    cursor.execute("""
        INSERT INTO audit_logs (id, case_id, event_type, event_data, previous_hash, hash, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        case_id or event_id,
        event_type,
        json.dumps(event_data),
        previous_hash,
        event_hash,
        now_iso
    ))
    conn.commit()
    conn.close()

    return {
        "audit_id": event_id,
        "hash": event_hash,
        "previous_hash": previous_hash,
        "timestamp": now_iso
    }

def verify_audit_chain() -> Dict[str, Any]:
    """Walks the entire audit ledger from genesis to verify cryptographic continuity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY rowid ASC")
    rows = cursor.fetchall()
    conn.close()

    expected_previous = GENESIS_HASH
    for idx, row in enumerate(rows):
        try:
            data = json.loads(row["event_data"])
        except Exception:
            data = {}

        recomputed = compute_event_hash(
            expected_previous,
            row["event_type"],
            data,
            row["timestamp"]
        )

        if row["previous_hash"] != expected_previous or recomputed != row["hash"]:
            return {
                "valid": False,
                "total_events": len(rows),
                "broken_at": row["id"],
                "message": f"INTEGRITY VIOLATION: Ledger broken at block {row['id']} (index {idx})"
            }
        expected_previous = row["hash"]

    return {
        "valid": True,
        "total_events": len(rows),
        "broken_at": None,
        "message": f"Chain intact: {len(rows)} immutable forensic events cryptographically verified."
    }