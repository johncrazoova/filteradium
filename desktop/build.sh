#!/bin/bash
# Filteradium Desktop Build Script
# Builds the app for the current platform

echo "🔧 Building Filteradium Desktop..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Detect platform
case "$(uname -s)" in
    Linux*)     PLATFORM="linux";;
    Darwin*)    PLATFORM="mac";;
    CYGWIN*|MINGW*|MSYS*) PLATFORM="win";;
    *)          PLATFORM="unknown"
esac

echo "🖥️  Detected platform: $PLATFORM"

# Build for current platform
case $PLATFORM in
    linux)
        echo "🐧 Building for Linux..."
        npm run build:linux
        echo "✅ Linux build complete!"
        echo "📁 Output: dist/"
        ;;
    mac)
        echo "🍎 Building for macOS..."
        npm run build:mac
        echo "✅ macOS build complete!"
        echo "📁 Output: dist/"
        ;;
    win)
        echo "🪟 Building for Windows..."
        npm run build:win
        echo "✅ Windows build complete!"
        echo "📁 Output: dist/"
        ;;
    *)
        echo "❌ Unsupported platform"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build complete!"
echo "📋 Files in dist/:"
ls -lh dist/ 2>/dev/null || echo "  (check dist/ folder)"
