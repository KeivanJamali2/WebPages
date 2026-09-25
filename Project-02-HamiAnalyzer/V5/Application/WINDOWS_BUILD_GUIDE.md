# 🪟 Building Windows Executable (.exe) - Complete Guide

This guide explains how to build the **HamiScraper Windows executable** on a Windows machine.

---

## 📋 Prerequisites

Before you start, make sure your Windows machine has:

1. **Python 3.8 or higher**
2. **Git** (optional, for version control)
3. **Administrator access** (recommended)

### Step 1: Verify Python Installation

Open **Command Prompt** (Win + R, type `cmd`, press Enter):

```bash
python --version
pip --version
```

You should see version numbers like:
```
Python 3.11.x
pip 24.x.x
```

**If Python is not found:**
- Download from: https://www.python.org/downloads/
- **IMPORTANT:** Check "Add Python to PATH" during installation
- Restart Command Prompt after installation

---

## 🚀 Building Steps

### Step 2: Copy Project Folder to Windows

1. Copy the entire `Application` folder to your Windows machine
2. Example location: `C:\Users\YourUsername\Desktop\Application`

### Step 3: Open Command Prompt in Application Folder

Navigate to your Application folder:

```bash
cd C:\Users\YourUsername\Desktop\Application
```

Or if on a different drive:
```bash
D:
cd D:\Projects\Application
```

Verify you're in the right directory (you should see `app.py`, `scraper.py`, `scraper_by_rf.py`):
```bash
dir
```

### Step 4: Create Virtual Environment (Recommended)

Creating a virtual environment isolates dependencies:

```bash
python -m venv venv
venv\Scripts\activate
```

After activation, you should see `(venv)` at the start of your command prompt.

### Step 5: Install Dependencies

Install all required Python packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages to install:**
- PyQt5 (UI framework)
- selenium (web scraping)
- beautifulsoup4 (HTML parsing)
- jdatetime (Persian calendar)
- pyinstaller (executable builder)

Wait for installation to complete. This may take 2-5 minutes.

### Step 6: Verify Installation

Check that all packages were installed:

```bash
pip list
```

You should see all the packages from `requirements.txt` listed.

### Step 7: Build the Executable

Run PyInstaller with the Windows build specification:

```bash
pyinstaller build_windows.spec
```

**What happens:**
- PyInstaller will analyze your code
- Bundle all dependencies
- Create the executable
- Process may take 2-5 minutes

**Expected output (last few lines):**
```
INFO: Building PKG (CArchive) HamiScraper.pkg completed successfully.
INFO: Building EXE from EXE-00.toc completed successfully.
INFO: Build complete! The results are available in: C:\...\Application\dist
```

### Step 8: Verify the Build

Check the output directory:

```bash
dir dist
```

You should see:
- `HamiScraper.exe` - The standalone executable (typically 100-150 MB)

---

## 🧪 Testing the Executable

### Test 1: Run from Command Prompt

```bash
dist\HamiScraper.exe
```

The application window should open after a few seconds.

**If it doesn't start:**
- Try: `dist\HamiScraper.exe` (with full path if needed)
- Check Windows Defender (may ask for permission)
- See Troubleshooting section below

### Test 2: Run by Double-Clicking

Navigate to `dist` folder in File Explorer:
- Double-click `HamiScraper.exe`
- Application should launch

### Test 3: Test Basic Functionality

Once the app opens:
1. ✅ Fill in login credentials
2. ✅ Set ChromeDriver path
3. ✅ Set output directory
4. ✅ Click "Save Configuration" (should say ✅)
5. ✅ Test Reference Code Search - paste test codes
6. ✅ Click "🔍 Start Reference Code Search" (should NOT error out)

---

## 📦 Distribution

Once `HamiScraper.exe` is built, you can:

### Package for End Users

1. **Create distribution folder:**
   ```bash
   mkdir HamiScraper_Distribution
   ```

2. **Copy the executable:**
   ```bash
   copy dist\HamiScraper.exe HamiScraper_Distribution\
   ```

3. **Copy icon (optional):**
   ```bash
   copy app_logo_icon.ico HamiScraper_Distribution\
   ```

4. **Create README.txt:**
   ```
   HamiScraper - Hami Data Extraction Tool
   
   REQUIREMENTS:
   - Windows 10 or later
   - Chrome/Chromium browser installed
   - ChromeDriver: https://chromedriver.chromium.org/
   
   USAGE:
   1. Download ChromeDriver for your Chrome version
   2. Extract ChromeDriver to a known location
   3. Run HamiScraper.exe
   4. Configure ChromeDriver path
   5. Enter your credentials
   6. Start scraping
   
   FEATURES:
   - Date Range Search: Scrape by date range
   - Reference Code Search: Search by specific codes
   
   For help, contact the developer.
   ```

5. **Zip for distribution:**
   - Right-click `HamiScraper_Distribution` → Send to → Compressed (zipped) folder
   - Share the `.zip` file

---

## ⚠️ Troubleshooting

### Error: "python" command not found

**Solution:** Python not in PATH
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Python311\Scripts\pyinstaller.exe build_windows.spec`

### Error: "No module named 'jdatetime'"

**Solution:** Dependencies not installed
```bash
pip install -r requirements.txt
```

### Error: "ExecutableNotFound: could not find path to executable chromedriver"

**Solution:** This is expected at build time. Just ignore it - ChromeDriver path is set at runtime by users.

### Build takes very long or freezes

**Solution:** 
- First build takes longer (5-10 minutes is normal)
- Ensure you have at least 2GB free disk space
- Close other applications
- Try: `pyinstaller build_windows.spec --onefile` (creates single file instead of folder)

### Executable won't start

**Possible causes:**
1. Windows SmartScreen is blocking it
   - Click "More info" → "Run anyway"

2. Missing Visual C++ Redistributable
   - Download: https://support.microsoft.com/en-us/help/2977003/
   - Install and restart

3. Permission issues
   - Right-click → Properties → Security → Unblock → OK

4. Corrupted build
   - Delete `build` and `dist` folders
   - Run build again: `pyinstaller build_windows.spec`

### Executable crashes when running

**Check logs:**
```bash
dist\HamiScraper.exe 2>&1 > error.log
type error.log
```

Send error logs to developer for diagnosis.

---

## 🔧 Advanced Options

### Create Single-File Executable (Smaller Distribution)

Edit `build_windows.spec` and change:
```python
# From:
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name='HamiScraper', ...)

# To:
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name='HamiScraper', onefile=True, ...)
```

Then rebuild:
```bash
pyinstaller build_windows.spec
```

Result: Single `HamiScraper.exe` file (~150MB) instead of folder

### Add Console Window for Debugging

Edit `build_windows.spec` and change:
```python
console=False,  # Change to True to see debug window
```

---

## ✅ Verification Checklist

Before distributing, verify:

- [ ] `HamiScraper.exe` file exists in `dist` folder
- [ ] Executable runs without errors
- [ ] Application window opens
- [ ] Configuration saves correctly
- [ ] Both scraping modes appear in UI:
  - [ ] Date Range Scraper (with date pickers)
  - [ ] Reference Code Search (with text area)
- [ ] Buttons are clickable and don't crash
- [ ] File browser works
- [ ] Can enter test data without errors

---

## 📞 Support

If you encounter issues:

1. **Check troubleshooting section above**
2. **Verify Python installation:**
   ```bash
   python -m pip --version
   ```
3. **Check dependencies:**
   ```bash
   pip list | grep -E "PyQt5|selenium|jdatetime"
   ```
4. **Rebuild from scratch:**
   ```bash
   rmdir /s build dist
   pyinstaller build_windows.spec
   ```
5. **Contact developer** with error messages

---

## 📚 Additional Resources

- **Python Documentation:** https://docs.python.org/3/
- **PyInstaller Documentation:** https://pyinstaller.org/
- **PyQt5 Documentation:** https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **Selenium Documentation:** https://selenium-python.readthedocs.io/

---

## 🎉 What's Next?

Once you have `HamiScraper.exe`:

1. ✅ Test thoroughly
2. ✅ Create user documentation
3. ✅ Package for distribution
4. ✅ Share with team/users
5. ✅ Gather feedback
6. ✅ Update as needed

**Features included in this build:**
- ✅ Date Range Scraper (original)
- ✅ Reference Code Search (new)
- ✅ Batch Processing
- ✅ Configuration Management
- ✅ Real-time Progress Logging
- ✅ Beautiful UI with dark log viewer

---

**Version:** 3.0  
**Built:** April 28, 2026  
**Developer:** Keivan Jamali  
**Website:** https://keivanjamali.com
