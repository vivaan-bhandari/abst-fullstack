#!/usr/bin/env python3
"""
Verify all required files are present for the Docker package
"""

import os
from pathlib import Path

def verify_files():
    """Check that all required files exist"""
    print("🔍 Verifying required files for Docker package...")
    
    required_files = [
        "Dockerfile_exact_data",
        "START_ABST_APP.bat",
        "START_ABST_APP.sh", 
        "START_ABST_APP.command",
        "backend/",
        "frontend/",
        "backend/db.sqlite3"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                print(f"✅ Directory: {file_path}")
            else:
                size = os.path.getsize(file_path)
                print(f"✅ File: {file_path} ({size} bytes)")
        else:
            print(f"❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    print()
    
    if missing_files:
        print("❌ Some required files are missing!")
        print("Missing files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("✅ All required files are present!")
        return True

if __name__ == "__main__":
    verify_files()
