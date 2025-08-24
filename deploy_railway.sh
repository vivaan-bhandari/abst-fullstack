#!/bin/bash

echo "🚀 Deploying to Railway..."

# Set production environment variables
echo "Setting production environment variables..."

# Update Railway environment variables
railway variables set DEBUG=False
railway variables set USE_HTTPS=True
railway variables set ALLOWED_HOSTS="localhost,127.0.0.1,.railway.app,.vercel.app"
railway variables set CORS_ALLOWED_ORIGINS="https://abst-frontend.vercel.app,https://abst-frontend-git-main-vivaan-bhandari.vercel.app,https://*.railway.app,https://*.vercel.app,http://localhost:3000,https://localhost:3000"
railway variables set CSRF_TRUSTED_ORIGINS="https://abst-fullstack-production.up.railway.app,https://abst-frontend.vercel.app,https://abst-frontend-git-main-vivaan-bhandari.vercel.app,https://localhost:3000,http://localhost:3000"

echo "✅ Environment variables updated"
echo "🔄 Deploying to Railway..."

# Deploy to Railway
railway up

echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: https://abst-fullstack-production.up.railway.app"
