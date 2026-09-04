"""
SwasthyaConnect — Local Blockchain Engine
==========================================
Pure Python, SHA-256 chained block system.
No external blockchain libraries required.
Stored entirely inside the existing SQLite database.

Block Structure:
  block_index      → sequential position in chain
  timestamp        → ISO datetime of block creation
  record_type      → event type (MEDICAL_RECORD_ADDED, etc.)
  patient_id       → patient this block belongs to (None for system events)
  payload_hash     → SHA-256 of the actual data being recorded
  previous_hash    → SHA-256 of the prior block (the chain link)
  block_hash       → SHA-256(index + timestamp + record_type + payload_hash + previous_hash + nonce)
  nonce            → lightweight proof-of-work counter (not mining)
  verified         → 1/0 flag (set after local validation)
"""

import hashlib
import json
import sqlite3
import os
import datetime
from typing import Optional, List, Dict, Any

# ── Path resolution ────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_NAME = os.path.join(_BASE_DIR, "data", "swasthya_v1.db")

# ── Block event types ──────────────────────────────────────────────────────────
BLOCK_MEDICAL_RECORD    = "MEDICAL_RECORD_ADDED"
BLOCK_PRESCRIPTION      = "PRESCRIPTION_ADDED"
BLOCK_TREATMENT_UPDATE  = "TREATMENT_UPDATED"
BLOCK_REFERRAL_CREATED  = "REFERRAL_CREATED"
BLOCK_AI_SUMMARY        = "AI_SUMMARY_SAVED"
BLOCK_AUTH_EVENT        = "AUTH_EVENT"
BLOCK_RESOURCE_UPDATED  = "RESOURCE_UPDATED"
BLOCK_APPOINTMENT       = "APPOINTMENT_BOOKED"
BLOCK_GRANT_REQUEST     = "GRANT_REQUEST_CREATED"
BLOCK_GRANT_DISBURSED   = "GOVT_GRANT_DISBURSED"
BLOCK_GENESIS           = "GENESIS"

DIFFICULTY = 2          # number of leading zeros required in block_hash (lightweight)
GENESIS_HASH = "0" * 64  # the anchor for block #0


# ── Core hash functions ────────────────────────────────────────────────────────

def sha256(data: str) -> str:
    """Returns lowercase hex SHA-256 digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_payload_hash(data: Any) -> str:
    """
    Deterministically hashes any Python object (dict, str, int).
    Dicts are sorted before hashing to ensure consistency.
    """
    if isinstance(data, dict):
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    else:
        canonical = str(data)
    return sha256(canonical)


def compute_block_hash(index: int, timestamp: str, record_type: str,
                       payload_hash: str, previous_hash: str, nonce: int) -> str:
    """Computes the final block hash from all header fields."""
    raw = f"{index}|{timestamp}|{record_type}|{payload_hash}|{previous_hash}|{nonce}"
    return sha256(raw)


def mine_block(index: int, timestamp: str, record_type: str,
               payload_hash: str, previous_hash: str) -> tuple[str, int]:
    """
    Lightweight proof-of-work: increment nonce until block_hash
    starts with DIFFICULTY leading zeros. Returns (block_hash, nonce).
    This is intentionally very fast (not real crypto mining).
    """
    nonce = 0
    target = "0" * DIFFICULTY
    while True:
        candidate = compute_block_hash(
            index, timestamp, record_type, payload_hash, previous_hash, nonce
        )
        if candidate.startswith(target):
            return candidate, nonce
        nonce += 1


# ── Database table initialization ─────────────────────────────────────────────

def initialize_blockchain_table():
    """Creates the blockchain_chain table if it does not exist."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_chain (
                block_index     INTEGER PRIMARY KEY,
                timestamp       TEXT NOT NULL,
                record_type     TEXT NOT NULL,
                patient_id      INTEGER,
                actor_id        INTEGER,
                payload_hash    TEXT NOT NULL,
                previous_hash   TEXT NOT NULL,
                block_hash      TEXT NOT NULL UNIQUE,
                nonce           INTEGER NOT NULL DEFAULT 0,
                extra_data      TEXT,
                verified        INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.commit()

        # Create genesis block if chain is empty
        cursor.execute("SELECT COUNT(*) FROM blockchain_chain")
        count = cursor.fetchone()[0]
        if count == 0:
            _create_genesis_block(cursor)
            conn.commit()
            print("[Blockchain] Genesis block created. Chain initialized.")
        else:
            print(f"[Blockchain] Chain loaded. {count} blocks on record.")

        conn.close()
    except Exception as e:
        print(f"[Blockchain] Init error: {e}")


def _create_genesis_block(cursor: sqlite3.Cursor):
    """Inserts the immutable genesis block (block #0)."""
    timestamp = "2026-01-01T00:00:00"
    payload_hash = sha256("SwasthyaConnect::GENESIS::BLOCK")
    block_hash, nonce = mine_block(0, timestamp, BLOCK_GENESIS, payload_hash, GENESIS_HASH)
    cursor.execute("""
        INSERT INTO blockchain_chain
            (block_index, timestamp, record_type, patient_id, actor_id,
             payload_hash, previous_hash, block_hash, nonce, extra_data, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (0, timestamp, BLOCK_GENESIS, None, None,
          payload_hash, GENESIS_HASH, block_hash, nonce,
          "SwasthyaConnect Genesis Block — Chain Anchor", 1))


# ── Core block operations ──────────────────────────────────────────────────────

def get_chain_tip() -> Optional[Dict]:
    """Returns the most recent block (chain tip) as a dict."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM blockchain_chain ORDER BY block_index DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[Blockchain] Error fetching tip: {e}")
        return None


def add_block(record_type: str, data: Any,
              patient_id: Optional[int] = None,
              actor_id: Optional[int] = None,
              extra_data: Optional[str] = None) -> Optional[Dict]:
    """
    Adds a new block to the chain.

    Args:
        record_type:  One of the BLOCK_* constants.
        data:         The actual data being recorded (dict or str).
                      This is hashed — NOT stored raw (privacy preserved).
        patient_id:   Patient this record belongs to.
        actor_id:     User ID of the person performing the action.
        extra_data:   Optional small metadata string (e.g. record title).

    Returns:
        The new block as a dict, or None on failure.
    """
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()

        # Get current chain tip
        cursor.execute(
            "SELECT block_index, block_hash FROM blockchain_chain ORDER BY block_index DESC LIMIT 1"
        )
        tip = cursor.fetchone()
        if tip is None:
            # Chain not initialized
            conn.close()
            initialize_blockchain_table()
            return add_block(record_type, data, patient_id, actor_id, extra_data)

        prev_index, previous_hash = tip
        new_index = prev_index + 1

        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        payload_hash = compute_payload_hash(data)

        # Mine the block hash (very fast at DIFFICULTY=2)
        block_hash, nonce = mine_block(
            new_index, timestamp, record_type, payload_hash, previous_hash
        )

        cursor.execute("""
            INSERT INTO blockchain_chain
                (block_index, timestamp, record_type, patient_id, actor_id,
                 payload_hash, previous_hash, block_hash, nonce, extra_data, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_index, timestamp, record_type, patient_id, actor_id,
              payload_hash, previous_hash, block_hash, nonce, extra_data, 1))

        conn.commit()
        conn.close()

        print(f"[Blockchain] Block #{new_index} added → {record_type} | hash: {block_hash[:16]}...")
        return {
            "block_index": new_index,
            "timestamp": timestamp,
            "record_type": record_type,
            "patient_id": patient_id,
            "actor_id": actor_id,
            "payload_hash": payload_hash,
            "previous_hash": previous_hash,
            "block_hash": block_hash,
            "nonce": nonce,
            "extra_data": extra_data,
            "verified": 1
        }

    except Exception as e:
        print(f"[Blockchain] Error adding block: {e}")
        return None


# ── Chain verification ─────────────────────────────────────────────────────────

def verify_chain() -> tuple[bool, List[str]]:
    """
    Walks the entire blockchain and recomputes every block hash.
    Returns (True, []) if chain is intact.
    Returns (False, [error_messages]) if any block is tampered.
    """
    errors = []
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM blockchain_chain ORDER BY block_index ASC"
        )
        blocks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not blocks:
            errors.append("Chain is empty — no blocks found.")
            return False, errors

        # Verify genesis block
        genesis = blocks[0]
        if genesis["previous_hash"] != GENESIS_HASH:
            errors.append(f"Block #0 (Genesis): Invalid previous_hash. Chain corrupted.")

        for i, block in enumerate(blocks):
            # Recompute block hash
            expected_hash = compute_block_hash(
                block["block_index"],
                block["timestamp"],
                block["record_type"],
                block["payload_hash"],
                block["previous_hash"],
                block["nonce"]
            )
            if expected_hash != block["block_hash"]:
                errors.append(
                    f"Block #{block['block_index']} ({block['record_type']}): "
                    f"Hash mismatch! Expected {expected_hash[:16]}... "
                    f"Got {block['block_hash'][:16]}... TAMPERED."
                )

            # Verify chain link (previous_hash matches prior block)
            if i > 0:
                prev_block = blocks[i - 1]
                if block["previous_hash"] != prev_block["block_hash"]:
                    errors.append(
                        f"Block #{block['block_index']}: Broken chain link! "
                        f"previous_hash does not match Block #{prev_block['block_index']} hash."
                    )

        if errors:
            print(f"[Blockchain] INTEGRITY FAILURE: {len(errors)} error(s) found.")
            return False, errors
        else:
            print(f"[Blockchain] Chain verified OK. {len(blocks)} blocks intact.")
            return True, []

    except Exception as e:
        errors.append(f"Verification error: {str(e)}")
        return False, errors


def verify_patient_chain(patient_id: int) -> tuple[bool, List[str]]:
    """
    Verifies all blocks belonging to a specific patient.
    Does NOT re-verify the full global chain (faster for UI).
    """
    errors = []
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM blockchain_chain WHERE patient_id = ? ORDER BY block_index ASC",
            (patient_id,)
        )
        blocks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not blocks:
            return True, []  # No blocks for patient — not an error

        for block in blocks:
            expected = compute_block_hash(
                block["block_index"], block["timestamp"],
                block["record_type"], block["payload_hash"],
                block["previous_hash"], block["nonce"]
            )
            if expected != block["block_hash"]:
                errors.append(
                    f"Block #{block['block_index']} ({block['record_type']}) "
                    f"at {block['timestamp'][:10]}: INTEGRITY FAILURE"
                )

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Error: {str(e)}"]


# ── Query functions ────────────────────────────────────────────────────────────

def get_patient_blocks(patient_id: int = None, limit: int = 100) -> List[Dict]:
    """Returns all blockchain records for a specific patient. If patient_id is None, returns the full system chain."""
    if patient_id is None:
        return get_full_chain(limit=limit)
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM blockchain_chain
            WHERE patient_id = ?
            ORDER BY block_index DESC
            LIMIT ?
        """, (patient_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Blockchain] Error fetching patient blocks: {e}")
        return []


def get_full_chain(limit: int = 500) -> List[Dict]:
    """Returns the full chain (for government/admin audit view)."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM blockchain_chain ORDER BY block_index DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Blockchain] Error fetching chain: {e}")
        return []


def get_chain_stats() -> Dict:
    """Returns summary statistics about the chain."""
    stats = {
        "total_blocks": 0,
        "event_counts": {},
        "chain_valid": False,
        "last_block_time": None
    }
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM blockchain_chain")
        stats["total_blocks"] = cursor.fetchone()["cnt"]

        cursor.execute("""
            SELECT record_type, COUNT(*) as cnt
            FROM blockchain_chain GROUP BY record_type
        """)
        for row in cursor.fetchall():
            stats["event_counts"][row["record_type"]] = row["cnt"]

        cursor.execute(
            "SELECT timestamp FROM blockchain_chain ORDER BY block_index DESC LIMIT 1"
        )
        last = cursor.fetchone()
        if last:
            stats["last_block_time"] = last["timestamp"]

        conn.close()
        is_valid, _ = verify_chain()
        stats["chain_valid"] = is_valid
    except Exception as e:
        print(f"[Blockchain] Stats error: {e}")
    return stats
