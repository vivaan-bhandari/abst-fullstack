#!/usr/bin/env python3
"""
Package the Docker-based demo for Roddy with exact data - FINAL VERSION
"""

import os
import shutil
import subprocess
from pathlib import Path

def package_for_roddy():
    """Create a package with Docker files for Roddy"""
    print("🚀 Creating FINAL Docker package for Roddy with EXACT data...")
    
    # Create package directory
    package_dir = Path("roddy_docker_demo_final")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy both backend and frontend
    print("📁 Copying backend files...")
    shutil.copytree("backend", package_dir / "backend")
    
    print("📁 Building React app locally first...")
    # Build React app locally to avoid Docker dependency issues
    os.chdir("frontend")
    
    # Check if build directory exists, if not build it
    if not os.path.exists("build"):
        print("Building React app...")
        try:
            subprocess.run(["npm", "run", "build"], check=True)
            print("✅ React app built successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build React app: {e}")
            print("Please run 'npm run build' in the frontend directory first")
            return
    else:
        print("✅ Using existing React build")
    
    os.chdir("..")
    
    print("📁 Copying frontend build files...")
    shutil.copytree("frontend/build", package_dir / "frontend" / "build")
    
    # Copy the exact database with all your real data
    print("💾 Copying your exact database with all real data...")
    if os.path.exists("backend/db.sqlite3"):
        shutil.copy2("backend/db.sqlite3", package_dir / "backend" / "db.sqlite3")
        print("✅ Database copied successfully!")
    else:
        print("⚠️  Warning: No database found")
    
    # Copy Docker files
    print("🐳 Copying Docker files...")
    shutil.copy2("Dockerfile_exact_data", package_dir / "Dockerfile_exact_data")
    shutil.copy2("START_ABST_APP.bat", package_dir / "START_ABST_APP.bat")
    shutil.copy2("START_ABST_APP.sh", package_dir / "START_ABST_APP.sh")
    shutil.copy2("START_ABST_APP.command", package_dir / "START_ABST_APP.command")
    
    # Create a comprehensive README
    readme = """# ABST Application - EXACT DATA Demo (FINAL VERSION)

## 🎯 What You'll See
**EXACTLY the same data as the development environment:**
- **All 5 real facilities** with real names and details
- **All 136 real residents** with real information  
- **All 22 real ADL questions**
- **All 2,992 real ADLs** with real data
- **All real scheduling data** and functionality
- **All real staff assignments** and shift templates
- **Complete working application** with both frontend and backend

## 🚀 How to Run (Super Simple!)

### Prerequisites:
1. **Install Docker Desktop** from [docker.com](https://docker.com)
2. **Start Docker Desktop** (make sure it's running)

### Windows Users:
1. **Double-click** `START_ABST_APP.bat`
2. **Press any key** when prompted
3. **Wait** for Docker to build and start (5-10 minutes first time)
4. **That's it!** Your browser will open automatically

### Mac Users:
1. **Double-click** `START_ABST_APP.command` (this opens in Terminal automatically!)
2. **Press Enter** when prompted
3. **Wait** for Docker to build and start (5-10 minutes first time)
4. **That's it!** Your browser will open automatically

### Linux Users:
1. **Double-click** `START_ABST_APP.sh`
2. **Press Enter** when prompted
3. **Wait** for Docker to build and start (5-10 minutes first time)
4. **That's it!** Your browser will open automatically

## 🔧 What Happens Automatically:
- ✅ Docker builds an image with your exact code and data
- ✅ **Your exact database gets included** (with all real data!)
- ✅ Django backend server starts
- ✅ React frontend gets built and served
- ✅ Everything runs in an isolated container
- ✅ **Zero technical knowledge required!**

## 📱 Application Details:
- **URL**: http://localhost:8000
- **Backend**: Django API with your exact database
- **Frontend**: React app built from your exact code
- **Database**: SQLite with all your real data
- **Port**: 8000 (make sure this port is free)

## 🔐 Login Credentials:
- **Username**: admin
- **Password**: admin123
- **Or**: Use any existing user accounts from your database

## 🛑 To Stop the App:
- Simply close the terminal/command prompt window
- Or press Ctrl+C in the terminal
- Docker will automatically clean up

## 🔧 Troubleshooting:
- **If Docker says "not found"**: Make sure Docker Desktop is installed and running
- **If port 8000 is busy**: Close any other applications using port 8000
- **If build fails**: Make sure you have a stable internet connection for downloading packages
- **If nothing happens**: Make sure you double-clicked the right file for your OS
- **If "Dockerfile_exact_data not found"**: The script will now show you exactly where it's looking and what files are present
- **If you get permission errors**: Make sure Docker Desktop is running and you have permission to run Docker commands

## 💡 Pro Tips:
- **First time setup** takes 5-10 minutes as Docker downloads and builds everything
- **Subsequent runs** will be much faster (just starts the container)
- **This is NOT sample data** - it's the exact real data from development!
- **All functionality working** exactly as in the development environment
- **Completely isolated** - won't interfere with anything else on your computer

## 🌐 What's Running:
- **Backend**: Django API server on port 8000
- **Frontend**: React app served by Django
- **Database**: Your exact SQLite database with all real data
- **Container**: Everything runs in Docker for consistency

## 📁 Files Included:
- `Dockerfile_exact_data` - Docker configuration
- `START_ABST_APP.bat` - Windows launcher
- `START_ABST_APP.command` - Mac launcher (opens Terminal automatically!)
- `START_ABST_APP.sh` - Linux launcher
- **Your exact backend code** with all models, views, and APIs
- **Your exact frontend code** with all React components
- **Your exact database** with all real data

---
**This is the EXACT same application with EXACT same data that we're developing!**

**Roddy will see:**
- ✅ Same facilities (Brighton, Murray Highland, etc.)
- ✅ Same residents (all 136 with real names and details)
- ✅ Same ADLs (all 2,992 with real assessment data)
- ✅ Same scheduling data and staff assignments
- ✅ Same shift templates and configurations
- ✅ Same user accounts and permissions
- ✅ **Identical functionality** to what you're using daily

## 🚨 IMPORTANT: This is the FINAL VERSION
This version includes improved error handling and directory detection to ensure the Dockerfile is found correctly, regardless of where the script is run from.
"""
    
    with open(package_dir / "README_For_Roddy.md", "w") as f:
        f.write(readme)
    
    # Create a simple icon/launcher file
    icon_file = """# ABST Application Launcher - EXACT DATA (FINAL VERSION)
# Double-click this file to start the application
# 
# Windows users: Use START_ABST_APP.bat
# Mac users: Use START_ABST_APP.command (opens in Terminal automatically!)
# Linux users: Use START_ABST_APP.sh
#
# Prerequisites: Install Docker Desktop from docker.com
# 
# No technical knowledge required!
# Just double-click and press Enter when prompted!
# 
# The app will set up everything automatically and open in your browser!
# 
# INCLUDES YOUR EXACT DATA - NOT SAMPLE DATA!
# 
# 🚨 This is the FINAL VERSION with improved error handling!
# 🔧 Now properly detects the script directory and finds all files!
"""
    
    with open(package_dir / "START_HERE.txt", "w") as f:
        f.write(icon_file)
    
    # Create zip file
    print("📁 Creating zip file...")
    shutil.make_archive("abst_docker_exact_data_for_roddy_FINAL", "zip", package_dir)
    
    # Clean up
    shutil.rmtree(package_dir)
    
    print("✅ FINAL Docker package created: abst_docker_exact_data_for_roddy_FINAL.zip")
    print("📁 Send this file to Roddy")
    print("📖 He needs to:")
    print("   1. Install Docker Desktop from docker.com")
    print("   2. Extract the zip file")
    print("   3. Double-click START_ABST_APP.bat (Windows) or START_ABST_APP.command (Mac) or START_ABST_APP.sh (Linux)")
    print("   4. Press Enter when prompted")
    print("   5. Wait for Docker to build and start (5-10 minutes first time)")
    print("   6. Browser opens automatically with EXACT same data you have!")
    print("")
    print("🎯 ZERO technical knowledge required after Docker installation!")
    print("🚀 Includes both Django backend AND React frontend!")
    print("💾 Uses your EXACT database with all real data!")
    print("🐳 Everything runs in Docker for consistency!")
    print("🔧 FINAL: Now properly handles directory issues and file detection!")

if __name__ == "__main__":
    package_for_roddy()
