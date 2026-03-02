# utils.py - helper functions
import hashlib

def hash_pin(pin: str) -> str:
    """Return sha256 hex digest of PIN string."""
    return hashlib.sha256(pin.encode('utf-8')).hexdigest()

def verify_pin(pin: str, pin_hash: str) -> bool:
    return hash_pin(pin) == pin_hash
