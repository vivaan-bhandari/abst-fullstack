#!/usr/bin/env python3
"""
Script to run Django development server with SSL/HTTPS support.
This script will automatically generate SSL certificates if they don't exist.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_ssl_certificates():
    """Check if SSL certificates exist, generate them if they don't."""
    certs_dir = Path("ssl_certs")
    cert_file = certs_dir / "certificate.crt"
    key_file = certs_dir / "private.key"
    
    if not cert_file.exists() or not key_file.exists():
        print("🔑 SSL certificates not found. Generating them...")
        try:
            subprocess.run([sys.executable, "generate_ssl_certs.py"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to generate SSL certificates")
            return False
    else:
        print("✅ SSL certificates found")
    
    return True

def run_django_ssl():
    """Run Django with SSL support."""
    if not check_ssl_certificates():
        return False
    
    cert_file = "ssl_certs/certificate.crt"
    key_file = "ssl_certs/private.key"
    
    print("🚀 Starting Django with SSL/HTTPS...")
    print(f"🔒 Certificate: {cert_file}")
    print(f"🔑 Private Key: {key_file}")
    print("🌐 Server will be available at: https://127.0.0.1:8000/")
    print("\n⚠️  Note: This is a self-signed certificate.")
    print("   Your browser will show a security warning - this is normal.")
    print("   Click 'Advanced' and 'Proceed to localhost' to continue.")
    print("\n" + "="*60)
    
    try:
        # Run Django with SSL
        subprocess.run([
            sys.executable, "manage.py", "runserver_plus",
            "--cert-file", cert_file,
            "--key-file", key_file,
            "--addrport", "127.0.0.1:8000"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Django server stopped")
    except Exception as e:
        print(f"❌ Error running Django: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔐 Django SSL Server Runner")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Error: manage.py not found in current directory")
        print("   Please run this script from the backend directory")
        sys.exit(1)
    
    # Check if django-extensions is installed
    try:
        import django_extensions
    except ImportError:
        print("❌ django-extensions is not installed")
        print("   Installing required packages...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages")
            sys.exit(1)
    
    run_django_ssl()
