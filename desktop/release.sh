#!/bin/bash
# Filteradium - Manual Build & Release Script
# Usage: ./release.sh [version]
# Example: ./release.sh 1.1.0

VERSION=${1:-"1.0.0"}
TAG="v${VERSION}"

echo "🚀 Filteradium Release Script"
echo "=============================="
echo "Version: ${VERSION}"
echo "Tag: ${TAG}"
echo ""

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Git working directory is not clean"
    echo "   Please commit or stash changes first"
    exit 1
fi

# Create git tag
echo "📌 Creating git tag ${TAG}..."
git tag -a ${TAG} -m "Release ${VERSION}"

# Push tag
echo "📤 Pushing tag to GitHub..."
git push origin ${TAG}

echo ""
echo "✅ Tag ${TAG} pushed!"
echo ""
echo "📋 GitHub Actions will now:"
echo "   1. Build Windows portable (.exe)"
echo "   2. Build macOS app"
echo "   3. Build Linux AppImage and .deb"
echo "   4. Create GitHub Release with all files"
echo ""
echo "🔗 Monitor build progress:"
echo "   https://github.com/johncrazoova/filteradium/actions"
echo ""
echo "📦 Release will be available at:"
echo "   https://github.com/johncrazoova/filteradium/releases/tag/${TAG}"
