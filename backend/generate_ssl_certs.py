#!/usr/bin/env python3
"""
Script to generate self-signed SSL certificates for Django development server.
This creates certificates in the current directory.
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_certificates():
    """Generate self-signed SSL certificates for local development."""
    
    # Check if OpenSSL is available
    try:
        subprocess.run(['openssl', 'version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL is not installed or not in PATH")
        print("Please install OpenSSL first:")
        print("  macOS: brew install openssl")
        print("  Ubuntu/Debian: sudo apt-get install openssl")
        print("  Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        return False
    
    # Create certificates directory
    certs_dir = Path("ssl_certs")
    certs_dir.mkdir(exist_ok=True)
    
    # Generate private key
    private_key_path = certs_dir / "private.key"
    print(f"🔑 Generating private key: {private_key_path}")
    
    try:
        subprocess.run([
            'openssl', 'genrsa', '-out', str(private_key_path), '2048'
        ], check=True, capture_output=True)
        print("✅ Private key generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate private key: {e}")
        return False
    
    # Generate certificate signing request (CSR)
    csr_path = certs_dir / "certificate.csr"
    print(f"📝 Generating certificate signing request: {csr_path}")
    
    try:
        subprocess.run([
            'openssl', 'req', '-new', '-key', str(private_key_path),
            '-out', str(csr_path), '-subj', 
            '/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost'
        ], check=True, capture_output=True)
        print("✅ CSR generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate CSR: {e}")
        return False
    
    # Generate self-signed certificate
    cert_path = certs_dir / "certificate.crt"
    print(f"🔒 Generating self-signed certificate: {cert_path}")
    
    try:
        subprocess.run([
            'openssl', 'x509', '-req', '-days', '365',
            '-in', str(csr_path), '-signkey', str(private_key_path),
            '-out', str(cert_path)
        ], check=True, capture_output=True)
        print("✅ Self-signed certificate generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate certificate: {e}")
        return False
    
    # Clean up CSR file
    csr_path.unlink()
    
    print("\n🎉 SSL certificates generated successfully!")
    print(f"📁 Certificates location: {certs_dir.absolute()}")
    print(f"🔑 Private key: {private_key_path}")
    print(f"🔒 Certificate: {cert_path}")
    print("\n⚠️  Note: These are self-signed certificates for development only.")
    print("   Your browser will show a security warning - this is normal.")
    print("   Click 'Advanced' and 'Proceed to localhost' to continue.")
    
    return True

if __name__ == "__main__":
    print("🚀 Django SSL Certificate Generator")
    print("=" * 40)
    
    if generate_ssl_certificates():
        print("\n✅ Ready to run Django with HTTPS!")
        print("   Use: python manage.py runserver_plus --cert-file ssl_certs/certificate.crt --key-file ssl_certs/private.key")
    else:
        print("\n❌ Failed to generate SSL certificates")
        sys.exit(1)
