#!/bin/bash

# Django SSL Server Runner Script
echo "🔐 Django SSL Server Runner"
echo "=========================="

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found in current directory"
    echo "   Please run this script from the backend directory"
    exit 1
fi

# Check if Python virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating your virtual environment first"
fi

# Check if SSL certificates exist
if [ ! -f "ssl_certs/certificate.crt" ] || [ ! -f "ssl_certs/private.key" ]; then
    echo "🔑 SSL certificates not found. Generating them..."
    python3 generate_ssl_certs.py
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate SSL certificates"
        exit 1
    fi
fi

# Install required packages if needed
echo "📦 Checking required packages..."
pip install -r requirements.txt

# Run Django with SSL
echo "🚀 Starting Django with SSL/HTTPS..."
echo "🔒 Certificate: ssl_certs/certificate.crt"
echo "🔑 Private Key: ssl_certs/private.key"
echo "🌐 Server will be available at: https://127.0.0.1:8000/"
echo ""
echo "⚠️  Note: This is a self-signed certificate."
echo "   Your browser will show a security warning - this is normal."
echo "   Click 'Advanced' and 'Proceed to localhost' to continue."
echo ""
echo "============================================================"

# Run Django with SSL
python3 manage.py runserver_plus \
    --cert-file ssl_certs/certificate.crt \
    --key-file ssl_certs/private.key \
    --addrport 127.0.0.1:8000
