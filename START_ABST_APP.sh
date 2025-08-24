#!/bin/bash

echo ""
echo "========================================"
echo "   ABST Application Launcher"
echo "========================================"
echo ""
echo "This will automatically set up and run your ABST application!"
echo ""
echo "INCLUDES YOUR EXACT DATA:"
echo "- All your real facilities"
echo "- All your real residents"
echo "- All your real ADLs"
echo "- All your real scheduling data"
echo "- All your real staff assignments"
echo "- All your real shift templates"
echo ""
echo "What happens automatically:"
echo "- Builds Docker image with your exact data"
echo "- Starts the application"
echo "- Opens your browser automatically"
echo ""
read -p "Press Enter to continue..."

echo ""
echo "Building Docker image (this may take 5-10 minutes first time)..."
echo "Checking for Dockerfile..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# Check if Dockerfile exists in the script directory
if [ ! -f "$SCRIPT_DIR/Dockerfile_exact_data" ]; then
    echo "❌ Dockerfile_exact_data not found in: $SCRIPT_DIR"
    echo "Please make sure you extracted the zip file completely."
    echo "You should see Dockerfile_exact_data in the same folder as this .sh file."
    echo ""
    echo "Files in current directory:"
    ls -la
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ Dockerfile found, building image..."
cd "$SCRIPT_DIR"
docker build -f Dockerfile_exact_data -t abst-exact-data .

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error building Docker image!"
    echo "Please make sure Docker is running and try again."
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "✅ Docker image built successfully!"
echo "Starting application..."
docker run -p 8000:8000 abst-exact-data

echo ""
echo "Application stopped."
read -p "Press Enter to exit..."
