# Automation Website - Refactored Architecture

## Overview
Professional automation website for processing geospatial and engineering data with a modern, modular architecture.

## 🎯 Project Status
**Current Phase:** Backend Refactoring Complete (Phase 1)
- ✅ All business logic moved to `models/` folder
- ✅ New email-based authentication system
- ✅ Modular processor classes
- ✅ Comprehensive file and analytics management
- ⏳ Next: Route refactoring and UI redesign

## 🏗️ Architecture

### New Directory Structure
```
Project-07-AutomationWebsite/
├── app.py                      # Main Flask application (to be refactored)
├── models/                     # NEW: Business logic layer
│   ├── processors/            # Data processing classes
│   │   ├── generic_processor.py       # Generic cross-section processor
│   │   ├── ppk_processor.py           # PPK GPS data processor
│   │   ├── csdp_processor.py          # CSDP profile processor
│   │   └── distance_processor.py      # Distance filtering processor
│   ├── auth/                  # Authentication & authorization
│   │   └── auth_manager.py            # Email-based login system
│   ├── analytics/             # Statistics & tracking
│   │   └── statistics_manager.py      # Activity logging
│   ├── utils/                 # Utility functions
│   │   └── file_manager.py            # File operations
│   └── ai/                    # AI assistant
│       └── assistant_manager.py       # Chat functionality
├── data/                      # User data
│   └── users.csv             # User registry (email, name, allowed_tools)
├── Files/                     # File storage
│   ├── result/               # Processing results
│   ├── share/                # Shared files
│   ├── statistic/            # Usage statistics
│   └── ...
├── templates/                 # HTML templates
├── static/                    # CSS, JS, images
└── README.md                 # This file
```

## 🔐 Authentication System

### Login System
- **Email + Password Authentication**: Simple login system
- **Manual User Registration**: Admin creates users via utility script or CSV
- **Password Change**: Users can change their password after login
- **Tool Access Control**: Each user has specific tool permissions

### User File Format (`data/users.csv`)
```csv
email,name,password,allowed_tools
user@example.com,John Doe,userpass123,"generic,ppk,share,assistant"
```

**Note**: Passwords are stored as plain text in the CSV file for simplicity.

### Available Tools
- `connect` - Connect to admin files
- `share` - Share files with others
- `generic` - Generic cross-section processing
- `ppk` - PPK GPS data processing
- `csdp` - CSDP profile processing
- `image` - Image processing tools
- `delete_distance` - Distance filtering
- `culvert` - Culvert processing
- `assistant` - AI chat assistant

### Adding New Users

**Option 1: Using the Utility Script (Recommended)**
```bash
python create_user.py
```

Follow the interactive prompts to:
1. Enter user email and name
2. Set initial password (min 4 characters)
3. Select allowed tools
4. Confirm user creation

The script also allows you to view all existing users.

**Option 2: Manual CSV Editing**
1. Open `data/users.csv`
2. Add a new line:
   ```csv
   newuser@example.com,New User,password123,"generic,ppk,share"
   ```
3. Save the file - changes take effect on next login

### Changing Passwords

Users can change their password after logging in:
1. Log in to the website
2. Click "Change Password" in the user menu
3. Enter current password
4. Enter new password (min 4 characters)
5. Confirm new password

**Admin Password Reset**: If a user forgets their password, admin can:
1. Edit `data/users.csv` directly
2. Change the password column to a new password
3. Provide the new password to the user

## 📦 Refactored Modules

### 1. Processors (`models/processors/`)

#### GenericProcessor
- **Purpose**: Process cross-section survey data
- **Input**: CSV with Point, Station, Offset, Elevation
- **Output**: Generic format + analysis files
- **Usage**:
  ```python
  from models.processors.generic_processor import GenericProcessor
  
  processor = GenericProcessor("input.csv")
  processor.fit(epsilon=0.25, round_limit=0.75)
  csv, txt, outranges, zeros = processor.save_files("output_dir/")
  ```

#### PPKProcessor
- **Purpose**: Process PPK GPS result files
- **Input**: CSV with GPS coordinates and timestamps
- **Output**: Segmented data files
- **Usage**:
  ```python
  from models.processors.ppk_processor import PPKProcessor
  
  processor = PPKProcessor("ppk_data.csv", minutes_limit=5, height_limit=1.5)
  ppk_file, empty_file, text_files = processor.save_files("output_dir/")
  ```

#### CSDPProcessor
- **Purpose**: Process cross-section design profiles
- **Input**: Three CSV files (main, second, pashneh)
- **Output**: Combined CSDP file
- **Usage**:
  ```python
  from models.processors.csdp_processor import CSDPProcessor
  
  processor = CSDPProcessor("main.csv", "second.csv", "pashneh.csv")
  processor.fit()
  csv_file = processor.save_files("output_dir/")
  ```

#### DistanceProcessor
- **Purpose**: Filter cross-sections by distance from centerline
- **Input**: CSV with cross-section data
- **Output**: Filtered CSV
- **Usage**:
  ```python
  from models.processors.distance_processor import DistanceProcessor
  
  processor = DistanceProcessor("input.csv", left_bound=-10, right_bound=10)
  processor.fit()
  csv_file = processor.save_files("output_dir/")
  ```

### 2. Authentication (`models/auth/`)

#### AuthManager
- **Purpose**: Handle user authentication and authorization
- **Features**:
  - Email + password authentication (plain text)
  - Tool access control
  - Session management
  - Password change functionality
  - Decorators for route protection

**Usage in Routes**:
```python
from models.auth.auth_manager import AuthManager, login_required, tool_access_required

auth_manager = AuthManager("data/users.csv")

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if auth_manager.login_user(email, password):
        return redirect(url_for('index'))
    else:
        flash('Invalid email or password')
        return redirect(url_for('login'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_pass = request.form['old_password']
    new_pass = request.form['new_password']
    success, msg = auth_manager.change_password(
        session['user_email'], 
        old_pass, 
        new_pass
    )
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('settings'))

@app.route('/generic')
@login_required
@tool_access_required('generic')
def generic_processing():
    # Only accessible to logged-in users with 'generic' permission
    pass
```

### 3. Analytics (`models/analytics/`)

#### StatisticsManager
- **Purpose**: Track user activity and generate analytics
- **Features**:
  - Activity logging with timestamps
  - User tracking
  - Tool usage statistics
  - Download tracking

**Usage**:
```python
from models.analytics.statistics_manager import StatisticsManager

stats = StatisticsManager("Files/statistic")

# Log activity
stats.add_to_history(
    tool_name="Generic Processing",
    user_email=session.get('user_email'),
    user_name=session.get('user_name'),
    ip_address=request.remote_addr
)

# Get statistics
summary = stats.get_statistics_summary()
# Returns: {total_activities, unique_users, tool_usage, total_downloads}
```

### 4. File Management (`models/utils/`)

#### FileManager
- **Purpose**: Centralize all file operations
- **Features**:
  - Upload handling
  - Download management
  - File listing
  - Cleanup utilities

**Usage**:
```python
from models.utils.file_manager import FileManager

file_mgr = FileManager(BASE_DIR)

# Save uploaded file
success, path, msg = file_mgr.save_uploaded_file(file, 'result')

# List files
files = file_mgr.get_file_list('share')

# Download file
return file_mgr.download_file('result.csv', 'result')
```

### 5. AI Assistant (`models/ai/`)

#### AssistantManager
- **Purpose**: AI-powered chat assistant
- **Features**:
  - Hugging Face API integration
  - Context management
  - Error handling
  - Multiple model support

**Usage**:
```python
from models.ai.assistant_manager import AssistantManager

assistant = AssistantManager()
result = assistant.send_message("Tell me about Keivan's projects")

if result['success']:
    response = result['response']
else:
    error = result['error']
```

## 🎨 Design System

### Color Palette (Preserved from Original)
```css
--color-white: #f3f5f5;      /* Background */
--color-blue: #cfd8de;        /* Containers */
--color-gray: #929393;        /* Navigation */
--color-box-blue: #4054b2;    /* Accent/Buttons */
--color-black: #17191f;       /* Text */
```

## 🔄 Migration Guide

### For Existing Code Using Old Classes

All old class names are still supported through backward compatibility aliases:

```python
# Old way (still works)
from Generic_DataLoader_V4 import Generic_DataLoader
dataloader = Generic_DataLoader("file.csv")

# New way (recommended)
from models.processors.generic_processor import GenericProcessor
processor = GenericProcessor("file.csv")
```

### Backward Compatibility Matrix
| Old Class | New Class | Module |
|-----------|-----------|---------|
| `Generic_DataLoader` | `GenericProcessor` | `models.processors.generic_processor` |
| `PPK_Processing_Result_DataLoader` | `PPKProcessor` | `models.processors.ppk_processor` |
| `CSDP_DataLoader` | `CSDPProcessor` | `models.processors.csdp_processor` |
| `Delete_Distance_From_Centerline` | `DistanceProcessor` | `models.processors.distance_processor` |

## 📝 Next Steps

### Phase 2: Route Refactoring (In Progress)
- [ ] Create Flask blueprints
- [ ] Separate routes into modules
- [ ] Integrate new auth system
- [ ] Update all routes to use new managers

### Phase 3: UI Modernization (Upcoming)
- [ ] Modern CSS design system
- [ ] Responsive card-based layout
- [ ] Interactive JavaScript features
- [ ] Premium loading states
- [ ] Mobile-first design

### Phase 4: Security & Testing (Upcoming)
- [ ] Environment variables for secrets
- [ ] CSRF protection
- [ ] Input validation
- [ ] Comprehensive testing
- [ ] Performance optimization

## 🚀 Running the Application

### Current Method (Unchanged)
```bash
python app.py
```

### Requirements
```bash
pip install -r requirements.txt
```

**Main Dependencies:**
- Flask 3.0+ (web framework)
- Werkzeug 3.0+ (WSGI utilities - no password hashing needed)
- pandas 2.1+ (data processing)
- numpy 1.26+ (numerical operations)
- scikit-learn 1.3+ (machine learning for clustering)
- requests 2.31+ (HTTP requests for AI assistant)

**Security Note**: This application stores passwords in plain text for simplicity. For production use, consider implementing proper password hashing.

## 📞 Support

For questions or issues:
- Email: me@keivanjamali.com
- Website: https://keivanjamali.com

## 📄 License

This project is proprietary software. All rights reserved.

---

**Version**: 2.0.0-refactored  
**Last Updated**: October 24, 2025  
**Status**: Backend refactoring complete, UI modernization pending
