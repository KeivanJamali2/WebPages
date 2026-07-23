# 🎯 Hami Scraper

A beautiful, minimal desktop application for automated web data extraction. Built with PyQt5 and featuring an Apple-inspired user interface.

![Version](https://img.shields.io/badge/version-3.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### Date Range Scraper
- 📅 **Date Range Filtering**: Extract data within specific Jalali (Shamsi) date ranges
- 📊 **Automatic Pagination**: Handles multi-page results
- 🧹 **Outdate Tolerance**: Intelligently stops when reaching old messages

### Reference Code Search (NEW! 🆕)
- 🔍 **Reference Code Search**: Search and extract by specific reference codes
- 📝 **Batch Code Processing**: Process multiple codes in one session
- 📊 **Separate Output**: Reference code results in dedicated output folder

### General Features
- 🎨 **Beautiful UI**: Clean, minimal Apple-inspired design
- 🔐 **Secure Login**: Safely handle credentials with password masking
- 📊 **Real-time Progress**: Live logging with detailed progress indicators
- 💾 **Configuration Save/Load**: Persistent settings between sessions
- 🧵 **Non-blocking**: All operations run in background threads
- 🌐 **Selenium-powered**: Robust web scraping with browser automation
- 🎯 **Batch Processing**: Scrape multiple Hami entries sequentially

## 🚀 Quick Start

### For End Users (Using Executable)

1. Download `HamiScraper.exe`
2. Download ChromeDriver from [here](https://chromedriver.chromium.org/)
3. Run `HamiScraper.exe`
4. Configure your login and paths
5. Choose tool:
   - **Date Range Scraper**: Enter dates and click "▶️ Start Scraping"
   - **Reference Code Search**: Paste codes and click "🔍 Start Reference Code Search"
6. Monitor progress in real-time log

### For Developers

1. **Clone the repository**
```bash
cd Application
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

## 🔨 Building Executable

### Windows (RECOMMENDED for end-users)
**[See Complete Windows Build Guide →](WINDOWS_BUILD_GUIDE.md)**

Quick summary:
```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build_windows.spec
```
Result: `dist/HamiScraper.exe`

### macOS/Linux
```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build_windows.spec
```

### Manual Build
```bash
pyinstaller build_windows.spec
```

The executable will be created in the `dist/` folder.

## 📋 Configuration

The application saves configuration in `config.json`:

```json
{
    "login_url": "https://mail.iau.ac.ir",
    "username": "your@email.com",
    "start_date": "1404/07/01",
    "end_date": "1404/08/01",
    "i_value": 105001,
    "name_value": "حامی 001 واحد یزد",
    "chrome_path": "/path/to/chromedriver",
    "output_dir": "./output"
}
```

**Note**: Password is never saved for security reasons.

## 🎨 UI Components

- **Login Credentials Card**: URL, username, and password inputs
- **Date Range Card**: Start and end date pickers
- **Scraper Settings Card**: Configuration for scraping parameters
- **Paths Card**: ChromeDriver and output directory selection
- **Progress Card**: Real-time logging and progress tracking

### ✨ Auto-Save Feature

The application automatically saves your configuration:
- ✅ When you finish editing any field (on blur)
- ✅ When you browse and select a file/folder
- ✅ When you start scraping
- ✅ Configuration is automatically loaded on next startup

**Note**: Passwords are never saved for security reasons.

## 📦 Dependencies

- **PyQt5**: GUI framework
- **Selenium**: Web automation
- **BeautifulSoup4**: HTML parsing
- **jdatetime**: Persian calendar support

## 🗂️ Project Structure

```
Application/
├── app.py                      # Main GUI application
├── scraper.py                  # Scraper logic and HamiScraper class
├── requirements.txt            # Python dependencies
├── HamiScraper.spec           # PyInstaller build configuration
├── build.bat                   # Windows build script
├── build.sh                    # Linux/Mac build script
├── BUILD_INSTRUCTIONS.md       # Detailed build guide
├── README.md                   # This file
└── config.json                # User configuration (created at runtime)
```

## 🔧 Customization

### Changing Colors

Edit the stylesheet in `app.py`:

```python
# Primary button color
background-color: #007AFF;  # Change to your color

# Window background
background-color: #F5F5F7;  # Change to your color
```

### Adding New Fields

1. Add input widget in `create_*_card()` method
2. Update `get_config()` to include new field
3. Update `save_config()` and `load_config()` methods
4. Update `HamiScraper` class if needed

## 🐛 Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

### ChromeDriver errors
- Download correct ChromeDriver version matching your Chrome browser
- Ensure ChromeDriver is executable (`chmod +x chromedriver` on Linux/Mac)

### Build fails
- Install PyInstaller: `pip install pyinstaller`
- Try cleaning build files: `rm -rf build dist`
- Check for missing dependencies in `hiddenimports`

### UI looks wrong
- Install system fonts (SF Pro Display or Segoe UI)
- Check Qt platform plugins are installed

## 🔒 Security Considerations

- Passwords are stored in memory only during runtime
- Consider using system keyring for production
- Config file does not save passwords
- Implement encryption for sensitive data in production

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- Design inspired by Apple's Human Interface Guidelines
- Built with PyQt5
- Powered by Selenium WebDriver

---

Made with ❤️ and Python
