# Building Hami Scraper as Windows Executable

This guide explains how to build the Hami Scraper application as a standalone Windows executable (.exe) file.

## Prerequisites

1. Python 3.8 or higher
2. All dependencies from `requirements.txt` installed
3. PyInstaller installed (`pip install pyinstaller`)

## Build Methods

### Method 1: Using the Build Script (Recommended)

On Linux/Mac:
```bash
chmod +x build.sh
./build.sh
```

On Windows:
```cmd
pyinstaller build_windows.spec
```

### Method 2: Manual Build

Run PyInstaller directly:
```bash
pyinstaller build_windows.spec
```

Or build with default settings:
```bash
pyinstaller --name HamiScraper \
            --onefile \
            --windowed \
            --icon=app_logo_icon.ico \
            --add-data "app_logo_icon.ico:." \
            app.py
```

## Build Output

After successful build, you'll find:
- `dist/HamiScraper.exe` - The standalone executable
- `build/` - Temporary build files (can be deleted)

## Distribution

1. Copy the entire `dist` folder to the target Windows machine
2. The application will run standalone without requiring Python installation
3. Make sure ChromeDriver is installed on the target machine and configured in the app

## Troubleshooting

### Missing DLLs
If you get DLL errors on Windows, install Visual C++ Redistributable:
https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads

### Application doesn't start
- Check that all dependencies are included in the .spec file
- Try running with console mode enabled (set `console=True` in .spec file) to see error messages

### Icon not showing
- Ensure `app_logo_icon.ico` is in the same directory as `app.py`
- The icon must be a valid .ico file

## Using Wine (Alternative Method)

If you want to build on Linux using Wine:

```bash
# Install Wine
sudo apt-get install wine winetricks

# Install Python in Wine
winetricks python38

# Install dependencies in Wine Python
wine pip install -r requirements.txt
wine pip install pyinstaller

# Build
wine pyinstaller build_windows.spec
```

Note: PyInstaller on Linux can create Windows executables without Wine in most cases.

## Application Information

- **Name:** Hami Scraper
- **Version:** 3.0
- **Director:** Keivan Jamali
- **Website:** https://keivanjamali.com
- **Contact:** k1jamali01@gmail.com
- **Icon:** app_logo_icon.ico
