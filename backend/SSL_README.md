# 🔐 Django SSL/HTTPS Setup

This guide explains how to run Django with SSL/HTTPS support for local development.

## 🚀 Quick Start

### Option 1: Use the Shell Script (Recommended)
```bash
# Make sure you're in the backend directory
cd backend

# Run the SSL server
./run_ssl.sh
```

### Option 2: Use Python Script
```bash
# Make sure you're in the backend directory
cd backend

# Run the SSL server
python3 runserver_ssl.py
```

### Option 3: Manual Command
```bash
# Make sure you're in the backend directory
cd backend

# Run Django with SSL
python3 manage.py runserver_plus \
    --cert-file ssl_certs/certificate.crt \
    --key-file ssl_certs/private.key \
    --addrport 127.0.0.1:8000
```

## 🌐 Access Your Application

Once running, your Django application will be available at:
- **HTTPS**: https://127.0.0.1:8000/
- **HTTP**: http://127.0.0.1:8000/ (will redirect to HTTPS if configured)

## ⚠️ Important Notes

### Browser Security Warning
Since these are self-signed certificates, your browser will show a security warning. This is **normal and expected** for development.

**To proceed:**
1. Click "Advanced" or "Show Details"
2. Click "Proceed to localhost (unsafe)" or similar
3. The warning will appear for each new session

### Frontend Configuration
Make sure your frontend is configured to use HTTPS:
```typescript
// frontend/src/config.ts
const config = {
  development: {
    API_BASE_URL: 'https://127.0.0.1:8000',  // Note: HTTPS
  },
  // ... other configs
};
```

## 🔧 SSL Certificate Management

### Automatic Generation
SSL certificates are automatically generated when you first run the SSL server. They're stored in the `ssl_certs/` directory.

### Manual Regeneration
If you need to regenerate certificates:
```bash
python3 generate_ssl_certs.py
```

### Certificate Files
- `ssl_certs/certificate.crt` - SSL certificate
- `ssl_certs/private.key` - Private key
- `ssl_certs/` - Directory containing all SSL files

## 🛠️ Troubleshooting

### Port Already in Use
If port 8000 is already in use:
```bash
# Find processes using port 8000
lsof -ti:8000

# Kill the process
kill -9 <PID>
```

### Certificate Errors
If you encounter certificate errors:
1. Delete the `ssl_certs/` directory
2. Run the SSL server again (certificates will be regenerated)

### Package Issues
If django-extensions is not installed:
```bash
pip install -r requirements.txt
```

## 🔒 Security Notes

- **Development Only**: These self-signed certificates are for development only
- **Not for Production**: Never use self-signed certificates in production
- **Local Network**: Only accessible from your local machine (127.0.0.1)

## 📚 Additional Resources

- [Django Extensions Documentation](https://django-extensions.readthedocs.io/)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Django HTTPS Settings](https://docs.djangoproject.com/en/4.2/topics/security/#ssl-https)

## 🎯 Next Steps

1. Start the SSL server using one of the methods above
2. Update your frontend to use HTTPS URLs
3. Test your application at https://127.0.0.1:8000/
4. Enjoy secure local development! 🔐✨
