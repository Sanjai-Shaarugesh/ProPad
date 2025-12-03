#!/bin/bash
# scripts/download-translation-deps.sh
# Download googletrans and dependencies for Flatpak build

set -e

echo "📦 Downloading Translation Dependencies for Flatpak"
echo "══════════════════════════════════════════════════════════════════"
echo ""

# Create directory
mkdir -p python-modules

# Download googletrans and all its dependencies
echo "📥 Downloading  dependencies..."
uv pip download --dest python-modules \
     \
    httpx==0.27.2 \
    httpcore==1.0.7 \
    h2==4.1.0 \
    hpack==4.0.0 \
    hyperframe==6.0.1 \
    anyio \
    2>/dev/null || \
uv pip download --dest python-modules \
    
    httpx \
    httpcore \
    h2 \
    hpack \
    hyperframe \
    anyio

echo ""
echo "✅ Dependencies downloaded!"
echo ""
echo "📝 Files in python-modules/:"
ls -lh python-modules/ | grep -E "(httpx|httpcore|h2|hpack|hyperframe|anyio)" || true
echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "🎯 Next Steps:"
echo "   1. Add the wheel files to your Flatpak manifest"
echo "   2. Or run: just update-flatpak-deps"
echo "   3. Then build: just flatpak-build"
echo "══════════════════════════════════════════════════════════════════"