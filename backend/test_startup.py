#!/usr/bin/env python
"""
Simple test script to check if Django can start without issues
"""
import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abst.settings')

try:
    # Try to configure Django
    django.setup()
    print("✅ Django setup successful!")
    
    # Try to import basic Django components
    from django.conf import settings
    print(f"✅ Django settings loaded: {settings.DEBUG}")
    
    # Try to check database connection
    from django.db import connection
    connection.ensure_connection()
    print("✅ Database connection successful!")
    
    print("🎉 All tests passed! Django should start normally.")
    
except Exception as e:
    print(f"❌ Django startup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
