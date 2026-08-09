import json
import os
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any

BLOCKCHAIN_FILE = os.path.join(os.path.dirname(__file__), "..", "blockchain.json")

def _ensure_storage_path() -> str:
    """Ensure the JSON storage file exists."""
    if not os.path.exists(BLOCKCHAIN_FILE):
        with open(BLOCKCHAIN_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    return BLOCKCHAIN_FILE

def _hash_value(value: str) -> str:
    """Helper to return a SHA-256 hash of a string value to preserve privacy."""
    if value is None:
        return ""
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

def get_chain() -> List[Dict[str, Any]]:
    """Return the entire blockchain from storage."""
    _ensure_storage_path()
    try:
        with open(BLOCKCHAIN_FILE, "r", encoding="utf-8") as f:
            chain = json.load(f)
            return chain if isinstance(chain, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def _save_chain(chain: List[Dict[str, Any]]):
    """Save the blockchain to storage."""
    with open(BLOCKCHAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(chain, f, indent=4)

def get_latest_block() -> Dict[str, Any]:
    """Return the most recent block in the chain."""
    chain = get_chain()
    return chain[-1] if chain else None

def hash_block(block: Dict[str, Any]) -> str:
    """Calculate the SHA-256 hash of a block's contents (excluding the hash itself)."""
    # Create a copy so we don't modify the original
    block_copy = block.copy()
    if 'hash' in block_copy:
        del block_copy['hash']
    
    # Sort keys to ensure consistent hashing
    block_string = json.dumps(block_copy, sort_keys=True).encode('utf-8')
    return hashlib.sha256(block_string).hexdigest()

def proof_of_work(block: Dict[str, Any], difficulty: int = 2) -> Dict[str, Any]:
    """Perform a simple proof of work (requires leading zeros)."""
    block['nonce'] = 0
    prefix = '0' * difficulty
    
    while True:
        computed_hash = hash_block(block)
        if computed_hash.startswith(prefix):
            block['hash'] = computed_hash
            return block
        block['nonce'] += 1

def create_genesis_block() -> None:
    """Create the initial block if the chain is empty."""
    chain = get_chain()
    if len(chain) > 0:
        return  # Chain already initialized
        
    genesis_block = {
        "index": 0,
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "GENESIS",
        "record_type": "system",
        "record_hash": _hash_value("genesis_record"),
        "actor_hash": _hash_value("system"),
        "patient_hash": _hash_value("system"),
        "previous_hash": "0",
        "nonce": 0
    }
    
    mined_block = proof_of_work(genesis_block)
    chain.append(mined_block)
    _save_chain(chain)

def log_event(event_type: str, record_type: str, record_id: Any, actor_id: str, patient_id: str) -> Dict[str, Any]:
    """
    Log an event to the blockchain, using immutable hashes for privacy.
    
    Supported event types:
    - MEDICAL_REPORT_UPLOAD
    - PRESCRIPTION_CREATED
    - PRESCRIPTION_UPDATED
    - CONSENT_GRANTED
    - CONSENT_REVOKED
    - RECORD_VIEWED
    - TREATMENT_STATUS_UPDATED
    - DOCTOR_LICENSE_VERIFIED
    """
    create_genesis_block()
    chain = get_chain()
    latest_block = chain[-1]
    
    new_block = {
        "index": len(chain),
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "record_type": record_type,
        "record_hash": _hash_value(str(record_id)),
        "actor_hash": _hash_value(str(actor_id)),
        "patient_hash": _hash_value(str(patient_id)),
        "previous_hash": latest_block["hash"],
        "nonce": 0
    }
    
    mined_block = proof_of_work(new_block)
    chain.append(mined_block)
    _save_chain(chain)
    
    return mined_block

def verify_chain() -> bool:
    """Verify the integrity of the blockchain."""
    chain = get_chain()
    if not chain:
        return True # Empty chain is technically valid
        
    for i in range(1, len(chain)):
        current = chain[i]
        previous = chain[i-1]
        
        # Check if the previous hash matches
        if current['previous_hash'] != previous.get('hash'):
            print(f"Blockchain integrity compromised at block {i}: Invalid previous_hash.")
            return False
            
        # Check if the current block's hash is valid
        current_hash = current.get('hash')
        recomputed_hash = hash_block(current)
        
        if current_hash != recomputed_hash:
            print(f"Blockchain integrity compromised at block {i}: Invalid hash computation.")
            return False
            
        # Check proof of work
        if not current_hash.startswith('00'):
            print(f"Blockchain integrity compromised at block {i}: Invalid proof of work.")
            return False
            
    return True
