import json
import hashlib
import os
from datetime import datetime

def calculate_entry_hash(entry):
    # Sort keys for deterministic hashing
    entry_str = json.dumps(entry, sort_keys=True)
    return hashlib.sha256(entry_str.encode('utf-8')).hexdigest()

def log_transfer(audit_file, log_data):
    try:
        if os.path.exists(audit_file):
            with open(audit_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []
            
        previous_hash = "0" * 64 # Genesis hash
        if logs:
            previous_hash = logs[-1]["current_hash"]
            
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "previous_hash": previous_hash,
            "data": log_data
        }
        
        new_entry["current_hash"] = calculate_entry_hash(new_entry)
        logs.append(new_entry)
        
        with open(audit_file, "w") as f:
            json.dump(logs, f, indent=4)
            
        print(f"Audit log written to {audit_file}. Entry hash: {new_entry['current_hash']}")
        return True
    except Exception as e:
        print(f"Error writing audit log: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    sample_data = {
        "username": "admin",
        "source_database": "source_db",
        "destination_database": "target_db",
        "record_count": 5,
        "hash_before": "abc...",
        "hash_after": "abc...",
        "transfer_status": "PASS"
    }
    log_transfer("audit_log.json", sample_data)
