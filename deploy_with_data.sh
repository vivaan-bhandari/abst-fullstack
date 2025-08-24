#!/bin/bash

echo "🚀 Deploying ABST app with local data to Railway..."

# Check if we're in the right directory
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Step 1: Export local data
echo "📦 Step 1: Exporting local data..."
python export_local_data.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to export local data"
    exit 1
fi

# Step 2: Update Railway environment variables
echo "🔧 Step 2: Setting Railway environment variables..."
railway variables set DEBUG=False
railway variables set USE_HTTPS=True
railway variables set ALLOWED_HOSTS="localhost,127.0.0.1,.railway.app,.vercel.app"
railway variables set CORS_ALLOWED_ORIGINS="https://abst-frontend.vercel.app,https://abst-frontend-git-main-vivaan-bhandari.vercel.app,https://*.railway.app,https://*.vercel.app,http://localhost:3000,https://localhost:3000"
railway variables set CSRF_TRUSTED_ORIGINS="https://abst-fullstack-production.up.railway.app,https://abst-frontend.vercel.app,https://abst-frontend-git-main-vivaan-bhandari.vercel.app,https://localhost:3000,http://localhost:3000"

# Step 3: Deploy to Railway
echo "🚀 Step 3: Deploying to Railway..."
railway up

if [ $? -ne 0 ]; then
    echo "❌ Railway deployment failed"
    exit 1
fi

echo "✅ Deployment complete!"
echo "🌐 Your app with local data is now available at: https://abst-fullstack-production.up.railway.app"
echo "📊 All your local data has been imported to Railway"
echo ""
echo "💡 Next steps:"
echo "   1. Test your app on Railway"
echo "   2. Verify all data is present"
echo "   3. Update your frontend config if needed"
