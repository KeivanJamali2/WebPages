#!/bin/bash
# Build script for creating Windows executable using PyInstaller

echo "=========================================="
echo "Hami Scraper - Windows Build Script"
echo "=========================================="
echo ""

# Check if pyinstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec 2>/dev/null

# Build the executable using the spec file
echo "Building Windows executable..."
pyinstaller build_windows.spec

# Check if build was successful
if [ -f "dist/HamiScraper.exe" ]; then
    echo ""
    echo "=========================================="
    echo "✅ Build successful!"
    echo "=========================================="
    echo "Executable location: dist/HamiScraper.exe"
    echo ""
    echo "You can now copy the entire 'dist' folder to a Windows machine."
    echo "The application will run standalone without Python installed."
    echo ""
else
    echo ""
    echo "❌ Build failed. Please check the errors above."
    echo ""
    exit 1
fi
