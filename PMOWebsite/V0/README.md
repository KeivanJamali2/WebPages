# PMO Website

A modular Project Management Office website with user authentication, dynamic forms, and data analytics capabilities.

## 🎯 Features

- **User Authentication**: Secure login system with role-based access control
- **Role Management**: Admin and employee roles with different permissions
- **Dynamic Forms**: Extensible form system - add new forms by creating Python files
- **Project Management**: Track projects and associate forms with them
- **Data Analytics**: Admin dashboard with statistics and visualizations
- **Modular Database**: NetworkX in-memory database with easy migration path to Neo4j
- **Minimal Design**: Clean, Apple-inspired user interface
- **Comprehensive Logging**: Track all system activities

## 📁 Project Structure

```
V0/
├── app.py                  # Main Flask application
├── run.py                  # Application runner script
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
│
├── data/                   # Data storage
│   ├── users.txt          # User credentials (pipe-delimited)
│   ├── projects.txt       # Project information
│   ├── submissions/       # Form submission files
│   └── backups/           # Database backups
│
├── database/              # Database abstraction layer
│   ├── base_db.py        # Abstract database interface
│   ├── networkx_db.py    # NetworkX implementation
│   └── neo4j_db.py       # Neo4j implementation (future)
│
├── models/                # Data models
│   ├── user.py           # User model
│   ├── project.py        # Project model
│   └── form_submission.py # Form submission model
│
├── forms/                 # Dynamic form definitions
│   ├── base_form.py      # Abstract base form
│   ├── form_registry.py  # Form loader
│   └── *.py              # Custom forms
│
├── routes/                # Flask blueprints
│   ├── auth.py           # Authentication routes
│   ├── dashboard.py      # Dashboard routes
│   ├── settings.py       # User settings
│   ├── forms_routes.py   # Form handling (to be added)
│   └── projects.py       # Project management (to be added)
│
├── utils/                 # Utility functions
│   ├── decorators.py     # Route decorators
│   ├── data_loader.py    # Data loading utilities
│   └── validators.py     # Input validation
│
├── static/                # Static assets
│   ├── css/
│   │   └── main.css      # Main stylesheet
│   └── js/
│       └── main.js       # JavaScript functions
│
└── templates/             # HTML templates
    ├── base.html         # Base template
    ├── auth/             # Authentication templates
    ├── dashboard/        # Dashboard templates
    ├── forms/            # Form templates
    ├── projects/         # Project templates
    ├── settings/         # Settings templates
    └── errors/           # Error pages
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Conda (recommended)

### Installation

1. **Activate the conda environment:**
   ```bash
   conda activate webpage-python
   ```

2. **Navigate to the project directory:**
   ```bash
   cd Project-06-PMOWebsite/V0
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

5. **Access the website:**
   Open your browser and go to: `http://127.0.0.1:5000`

### Default Login Credentials

**Admin Account:**
- Email: `admin@company.com`
- Password: `admin123`

**Employee Account:**
- Email: `employee1@company.com`
- Password: `pass123`

## 👤 User Management

### Adding New Users

Edit `data/users.txt` and add a new line:

```
email|national_id|name|phone|password|role
```

**Example:**
```
john@company.com|9876543210|John Smith|+98 918 123 4567|mypassword|employee
```

**Note:** Restart the application after adding users.

### User Roles

- **admin**: Full access to all features including analytics and user management
- **employee**: Access to forms, projects, and personal settings

## 📋 Forms System

### Current Status
The forms system architecture is ready, but form routes and implementations need to be completed. The following components are in place:

- Base form class architecture (planned)
- Form registry system (planned)
- Form submission storage system (planned)
- Integration with projects and users (planned)

### Adding a New Form (Future)

1. Create a new file in `forms/` directory:
   ```python
   # forms/my_custom_form.py
   from forms.base_form import BaseForm
   
   class MyCustomForm(BaseForm):
       form_name = "My Custom Form"
       form_id = "my_custom_form"
       
       def get_fields(self):
           return [
               {'name': 'field1', 'type': 'text', 'label': 'Field 1', 'required': True},
               {'name': 'field2', 'type': 'textarea', 'label': 'Field 2'},
           ]
       
       def validate(self, data):
           # Custom validation logic
           return True, []
   ```

2. The form will be automatically discovered and added to the forms list.

## 🗄️ Database

### Current Implementation: NetworkX

The system currently uses NetworkX for in-memory graph storage. This is suitable for development and small deployments.

**Structure:**
- **Nodes**: Users, Projects, FormSubmissions
- **Edges**: User → Submission, Submission → Project

### Migrating to Neo4j

When you're ready to migrate to Neo4j:

1. **Update configuration** in `config.py`:
   ```python
   DATABASE_TYPE = 'neo4j'
   NEO4J_URI = 'bolt://localhost:7687'
   NEO4J_USER = 'neo4j'
   NEO4J_PASSWORD = 'your_password'
   ```

2. **Implement Neo4j database class** in `database/neo4j_db.py` following the same interface as `NetworkXDatabase`

3. **Update app initialization** in `app.py` to use Neo4j

4. **Export and import data** using the export/import utilities

## 🎨 Customization

### Styling

Edit `static/css/main.css` to customize the appearance. The CSS uses CSS variables for easy theming:

```css
:root {
    --color-primary: #007AFF;     /* Main brand color */
    --color-bg: #FFFFFF;          /* Background color */
    --color-text: #1D1D1F;        /* Text color */
    /* ... more variables */
}
```

### Adding New Routes

1. Create a new blueprint in `routes/`:
   ```python
   from flask import Blueprint
   
   my_bp = Blueprint('my_feature', __name__, url_prefix='/my-feature')
   
   @my_bp.route('/')
   def index():
       return render_template('my_feature/index.html')
   ```

2. Register the blueprint in `app.py`:
   ```python
   from routes.my_feature import my_bp
   app.register_blueprint(my_bp)
   ```

## 📊 Analytics

The admin dashboard provides:
- Total users, projects, and submissions
- Database statistics
- Recent activity
- User list with roles

**Future additions:**
- Charts and graphs
- Export capabilities
- Advanced filtering

## 🔒 Security Notes

**Current Implementation:**
- Plain text passwords (as requested)
- Session-based authentication
- Role-based access control

**For Production:**
- Implement password hashing (bcrypt/argon2)
- Use HTTPS only
- Add CSRF protection
- Implement rate limiting
- Add audit logging
- Use environment variables for secrets

## 📝 Logging

Logs are stored in `logs/app.log` and include:
- Application startup/shutdown
- User authentication attempts
- Database operations
- Errors and exceptions

## 🧪 Testing

To test the application:

1. **Start the server:**
   ```bash
   python run.py
   ```

2. **Test user login:**
   - Navigate to `http://127.0.0.1:5000`
   - Login with test credentials

3. **Test role access:**
   - Admin account can access admin dashboard
   - Employee account restricted to user features

## 🛠️ Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions/classes
- Keep files under 300 lines when possible
- Use meaningful variable names

### Adding Features

The codebase is designed to be AI-friendly and modular:
- Each component is self-contained
- Clear interfaces between layers
- Comprehensive documentation
- Consistent naming conventions

## 📦 Dependencies

Core dependencies (see `requirements.txt`):
- Flask 3.0.0 - Web framework
- NetworkX 3.2.1 - Graph database
- python-dotenv 1.0.0 - Environment management
- Werkzeug 3.0.1 - WSGI utilities

## 🤝 Contributing

When adding features:
1. Follow the existing code structure
2. Add documentation to code
3. Update this README if needed
4. Test thoroughly before committing

## 📄 License

Internal company use only.

## 📞 Support

For questions or issues, contact the system administrator.

---

**Version:** 1.0  
**Last Updated:** 2025-10-24  
**Status:** Initial Release - Core Features Implemented
