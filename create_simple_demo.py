#!/usr/bin/env python3
"""
Create a SUPER SIMPLE demo for Roddy - no Docker, no complexity!
"""

import os
import shutil
from pathlib import Path

def create_simple_demo():
    """Create a simple demo that just works"""
    print("🚀 Creating SUPER SIMPLE demo for Roddy...")
    
    # Create package directory
    package_dir = Path("roddy_simple_demo")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy backend
    print("📁 Copying backend...")
    shutil.copytree("backend", package_dir / "backend")
    
    # Copy frontend build (already built)
    print("📁 Copying React build...")
    shutil.copytree("frontend/build", package_dir / "frontend_build")
    
    # Copy database
    print("💾 Copying database...")
    if os.path.exists("backend/db.sqlite3"):
        shutil.copy2("backend/db.sqlite3", package_dir / "backend" / "db.sqlite3")
        print("✅ Database copied!")
    
    # Create a simple launcher script
    launcher = '''#!/usr/bin/env python3
import os
import subprocess
import sys
import webbrowser
import time

def main():
    print("🚀 Starting ABST App...")
    print("This will start everything automatically!")
    print()
    
    # Check if Python is available
    try:
        subprocess.run([sys.executable, "--version"], check=True, capture_output=True)
    except Exception:
        print("❌ Python not found! Please install Python from python.org")
        input("Press Enter to exit...")
        return
    
    # Install packages
    print("Installing packages...")
    os.chdir('backend')
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"], check=True)
        print("✅ Packages installed!")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
        return
    
    # Setup database
    print("Setting up database...")
    subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
    
    # Start Django with regular HTTP (simpler for demo)
    print("Starting Django server...")
    print("🌐 Your app will be available at: http://localhost:8000")
    print("🔐 Login with: admin / admin123")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Open browser after a few seconds
    def open_browser():
        time.sleep(3)
        webbrowser.open('http://localhost:8000')
        print("🌐 If browser doesn't open automatically, go to: http://localhost:8000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start Django with regular HTTP (no SSL complications)
    subprocess.run([sys.executable, "manage.py", "runserver", "8000"])

if __name__ == "__main__":
    main()
'''
    
    with open(package_dir / "start_app.py", "w") as f:
        f.write(launcher)
    
    # Create Windows launcher
    windows_launcher = """@echo off
title ABST App Launcher
color 0A

echo.
echo ========================================
echo    ABST App Launcher - SUPER SIMPLE!
echo ========================================
echo.
echo This will start your ABST app automatically!
echo.
echo What happens:
echo - Installs required packages
echo - Sets up database
echo - Starts the server
echo - Opens your browser
echo.
echo Press any key to start...
pause >nul

echo.
echo Starting app...
cd /d "%~dp0"
python start_app.py

echo.
echo App stopped.
pause
"""
    
    with open(package_dir / "START_APP.bat", "w") as f:
        f.write(windows_launcher)
    
    # Create Mac launcher
    mac_launcher = """#!/bin/bash

echo ""
echo "========================================"
echo "   ABST App Launcher - SUPER SIMPLE!"
echo "========================================"
echo ""
echo "This will start your ABST app automatically!"
echo ""
echo "What happens:"
echo "- Installs required packages"
echo "- Sets up database"
echo "- Starts the server"
echo "- Opens your browser"
echo ""
read -p "Press Enter to start..."

echo ""
echo "Starting app..."
cd "$(dirname "$0")"
python3 start_app.py

echo ""
echo "App stopped."
read -p "Press Enter to exit..."
"""
    
    with open(package_dir / "START_APP.command", "w") as f:
        f.write(mac_launcher)
    
    # Make executable
    os.chmod(package_dir / "START_APP.command", 0o755)
    
    # Create simple README
    readme = """# ABST App - SUPER SIMPLE!

## 🎯 How to Run (Just Double-Click!)

### Windows:
1. **Double-click** `START_APP.bat`
2. **Press any key** when prompted
3. **That's it!** Browser opens automatically

### Mac:
1. **Double-click** `START_APP.command`
2. **Press Enter** when prompted
3. **That's it!** Browser opens automatically

## 🚀 What Happens:
- ✅ Python packages get installed automatically
- ✅ Database gets set up
- ✅ Server starts on http://localhost:8000
- ✅ Browser opens automatically
- ✅ **ZERO technical knowledge required!**

## 🌐 Simple Setup:
- Uses regular HTTP (no SSL complications)
- Works with all browsers
- No certificate trust issues!

## 📱 What You'll See:
- **EXACTLY the same data** as the development environment
- **All your real facilities, residents, ADLs, and scheduling data**
- **Complete working application**

## 🔐 Login:
- **Username**: admin
- **Password**: admin123

## 🛑 To Stop:
- Press Ctrl+C in the terminal window

---
**This is the EXACT same app with EXACT same data!**
"""
    
    with open(package_dir / "README.txt", "w") as f:
        f.write(readme)
    
    # Create zip
    print("📁 Creating zip file...")
    shutil.make_archive("abst_simple_demo_for_roddy", "zip", package_dir)
    
    # Clean up
    shutil.rmtree(package_dir)
    
    print("✅ SIMPLE demo created: abst_simple_demo_for_roddy.zip")
    print("📁 Send this to Roddy")
    print("📖 He just needs to:")
    print("   1. Extract the zip file")
    print("   2. Double-click START_APP.bat (Windows) or START_APP.command (Mac)")
    print("   3. Press Enter when prompted")
    print("   4. That's it! Browser opens automatically!")
    print("")
    print("🎯 SUPER SIMPLE - no Docker, no complexity!")
    print("🚀 Just Python and your exact data!")

if __name__ == "__main__":
    create_simple_demo()
