# 🗺️ Development Roadmap - Adding New Features to Hami Scraper

## 📋 Application Overview

**Current Application Structure:**
```
Hami Scraper (PyQt5 Desktop Application)
├── GUI Layer (app.py)
│   ├── Main Window
│   ├── Configuration UI Cards
│   ├── ScraperThread (Background Worker)
│   └── Event Handling
├── Core Logic (scraper.py)
│   ├── Web Scraping (Selenium)
│   ├── Data Extraction (BeautifulSoup)
│   └── File I/O
├── Configuration Management
│   ├── config.json (User settings)
│   └── pairs.json (Data mappings)
└── Build System
    ├── build_windows.spec (PyInstaller config)
    └── build.sh (Build automation)
```

---

## 🛠️ Development Phases

### Phase 1: Planning & Design
**Objective:** Define the new feature/tool

#### Tasks:
- [ ] **1.1** Define what the new part does
  - Functionality description
  - User requirements
  - Integration points with existing code
  
- [ ] **1.2** Design the architecture
  - Will it need a new Python module? (e.g., `new_tool.py`)
  - Will it need UI changes?
  - Database/storage requirements?
  - Configuration parameters?
  
- [ ] **1.3** Plan the UI changes (if applicable)
  - New UI Cards/Components
  - Layout modifications
  - Input fields and buttons
  - Integration with existing UI

- [ ] **1.4** Identify dependencies
  - New pip packages needed?
  - Update `requirements.txt`
  - Update `build_windows.spec` (hidden imports)

---

### Phase 2: Development

**Objective:** Implement the new feature

#### 2A. Create New Tool/Module
- [ ] **2A.1** Create new Python file(s)
  - File naming: `new_tool.py` or `modules/feature_name.py`
  - Structure similar to `scraper.py`
  - Include docstrings and type hints
  
- [ ] **2A.2** Implement core functionality
  - Main class and methods
  - Error handling
  - Progress callbacks (if needed)
  
- [ ] **2A.3** Test the module independently
  - Create test cases
  - Verify functionality
  - Check for bugs and edge cases

#### 2B. Update Main Application (app.py)
- [ ] **2B.1** Add imports
  ```python
  from new_tool import NewTool  # Add to imports section
  ```
  
- [ ] **2B.2** Add UI components
  - Create new `QFrame` or card
  - Add input fields (QLineEdit, QPushButton, etc.)
  - Add to main layout
  
- [ ] **2B.3** Create business logic handlers
  - Add methods to handle user interactions
  - Connect signals/slots
  - Implement validation
  
- [ ] **2B.4** Integrate with ScraperThread or create new thread class
  - If background processing needed, create new `QThread` subclass
  - Example:
    ```python
    class NewToolThread(QThread):
        progress = pyqtSignal(str)
        finished = pyqtSignal(bool, str)
        
        def __init__(self, config):
            super().__init__()
            self.config = config
        
        def run(self):
            # Implementation
            pass
    ```
  
- [ ] **2B.5** Update configuration system
  - Add new config fields to `config.json`
  - Update config save/load methods
  - Add UI for config input

#### 2C. Update Configuration Files
- [ ] **2C.1** Update `requirements.txt`
  ```
  # Add new dependencies if needed
  new_package>=version
  ```
  
- [ ] **2C.2** Update `build_windows.spec`
  ```python
  hiddenimports=[
      # Add any new hidden imports
      'module_name',
  ]
  ```
  
- [ ] **2C.3** Update `config.json` template
  ```json
  {
      "existing_field": "value",
      "new_field": "new_value"
  }
  ```

---

### Phase 3: Testing & Debugging

**Objective:** Ensure new feature works correctly

#### Tasks:
- [ ] **3.1** Unit Testing
  - Test individual methods
  - Test error cases
  - Verify data handling
  
- [ ] **3.2** Integration Testing
  - Test interaction with existing components
  - Test UI events
  - Test configuration save/load
  
- [ ] **3.3** UI Testing
  - Test button clicks
  - Test input validation
  - Verify responsive UI (no freezing)
  
- [ ] **3.4** Edge Case Testing
  - Test with invalid inputs
  - Test with large datasets
  - Test with missing files/resources
  
- [ ] **3.5** Performance Testing
  - Measure execution time
  - Check memory usage
  - Monitor thread behavior

---

### Phase 4: Documentation

**Objective:** Document the new feature

#### Tasks:
- [ ] **4.1** Update README.md
  - Add feature description
  - Add usage instructions
  - Add any new dependencies
  
- [ ] **4.2** Add code documentation
  - Docstrings for all classes/methods
  - Inline comments for complex logic
  - Type hints on functions
  
- [ ] **4.3** Update configuration documentation (if applicable)
  - Document new config fields
  - Provide default values
  - Explain any constraints
  
- [ ] **4.4** Create usage examples
  - Show how to use the feature
  - Include screenshots (if UI change)
  - Document any special requirements

---

### Phase 5: Building the Executable

**Objective:** Create the final .exe file

#### Tasks:
- [ ] **5.1** Clean build environment
  ```bash
  rm -rf build dist *.spec __pycache__ 2>/dev/null
  ```
  
- [ ] **5.2** Verify all dependencies are installed
  ```bash
  pip install -r requirements.txt
  ```
  
- [ ] **5.3** Test application runs correctly
  ```bash
  python app.py
  ```
  
- [ ] **5.4** Update build specification if needed
  - Check `build_windows.spec` for any new hidden imports
  - Add new data files (images, configs, etc.)
  - Verify icon path
  
- [ ] **5.5** Run preliminary build check (optional)
  ```bash
  pyinstaller build_windows.spec --onefile --windowed
  ```
  
- [ ] **5.6** Execute final build
  ```bash
  chmod +x build.sh
  ./build.sh
  ```
  
  Or on Windows:
  ```cmd
  pyinstaller build_windows.spec
  ```
  
- [ ] **5.7** Verify executable
  - Check `dist/HamiScraper.exe` exists
  - Run executable on target system (Windows)
  - Test all features work as expected
  - Verify no console errors appear

---

## 📊 Quick Reference: File Modifications Checklist

| File | Changes | Priority |
|------|---------|----------|
| `app.py` | Add imports, UI components, handlers | High |
| `new_tool.py` | Create new file with core logic | High |
| `requirements.txt` | Add dependencies | High |
| `build_windows.spec` | Add hidden imports, data files | High |
| `config.json` | Add new config fields | Medium |
| `pairs.json` | Update mappings if needed | Medium |
| `README.md` | Document feature | Medium |
| `BUILD_INSTRUCTIONS.md` | Update if build process changed | Low |

---

## 🔄 Development Workflow Timeline

```
Phase 1: Planning & Design
    ↓ (1-2 days)
Phase 2: Development
    ├── 2A: Create New Module (2-5 days)
    ├── 2B: Update UI & Integration (2-5 days)
    └── 2C: Update Config Files (1 day)
    ↓ (Total: 5-11 days)
Phase 3: Testing & Debugging
    ↓ (2-5 days)
Phase 4: Documentation
    ↓ (1-2 days)
Phase 5: Building the Executable
    ↓ (1-2 hours)
✅ COMPLETE - Ready for Distribution
```

---

## 💡 Tips for Success

### Code Organization
- Keep the structure clean and modular
- One responsibility per class/function
- Use descriptive names for variables and methods

### UI Development (PyQt5)
- Build UI incrementally and test
- Use layouts (QVBoxLayout, QHBoxLayout) for responsive design
- Always connect signals and slots properly

### Threading
- Never access UI from worker threads directly
- Use signals/slots for thread-to-UI communication
- Always join threads properly on shutdown

### Configuration Management
- Save config when user changes values
- Load config on startup
- Provide sensible defaults

### Building & Distribution
- Always test the executable on a clean Windows machine
- Include ChromeDriver in distribution if needed
- Create a user guide for end-users

---

## 🚀 Commands Reference

### Development
```bash
# Run application
python app.py

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Check code style
pylint *.py
```

### Building
```bash
# macOS/Linux
chmod +x build.sh
./build.sh

# Windows
pyinstaller build_windows.spec
```

### Troubleshooting
```bash
# Rebuild from scratch
rm -rf build dist __pycache__ .pytest_cache
pyinstaller build_windows.spec

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## 📝 Notes

- **Security**: Never save passwords in config files (already implemented)
- **Performance**: Use threading for long-running operations
- **Testing**: Test with various Chrome versions/drivers
- **Distribution**: Include clear installation instructions for end-users
- **Version**: Update version number in comments when building

---

**Last Updated:** April 28, 2026
**Application Version:** 3.0
**Maintainer:** Keivan Jamali
