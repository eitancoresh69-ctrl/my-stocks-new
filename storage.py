# storage.py - Simple storage module (FIXED)
import json
import os
from typing import Any, Optional
from pathlib import Path

STORAGE_DIR = Path(".cache")
STORAGE_DIR.mkdir(exist_ok=True)

def load(key: str) -> Optional[Any]:
    """Load data from storage"""
    try:
        filepath = STORAGE_DIR / f"{key}.json"
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {key}: {e}")
    return None

def save(key: str, data: Any) -> bool:
    """Save data to storage"""
    try:
        filepath = STORAGE_DIR / f"{key}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving {key}: {e}")
        return False

def delete(key: str) -> bool:
    """Delete data from storage"""
    try:
        filepath = STORAGE_DIR / f"{key}.json"
        if filepath.exists():
            os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error deleting {key}: {e}")
        return False

def clear_all() -> bool:
    """Clear all storage"""
    try:
        for file in STORAGE_DIR.glob("*.json"):
            os.remove(file)
        return True
    except Exception as e:
        print(f"Error clearing storage: {e}")
        return False
