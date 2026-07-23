# PMO Website - Project Roadmap

## Project Overview
A modular, minimal-design PMO (Project Management Office) website for company internal use, featuring user authentication, dynamic forms, and data analytics capabilities.

## Core Requirements

### 1. Authentication System
- **No public registration** - Admin-managed users only
- User data fields: email, national_id, name, phone (+98 format), password (plain text), role
- Login using email or national_id + password
- Password change functionality in settings
- Users loaded from txt file: `data/users.txt`

### 2. Database Architecture
- **Current Implementation**: NetworkX (in-memory graph)
- **Future Migration**: Neo4j database
- **Design Principle**: Abstract database interface for easy swapping
- **Data Storage**:
  - Users, Projects, FormSubmissions as nodes
  - Relationships: User-[SUBMITTED]->FormSubmission-[BELONGS_TO]->Project
  - Form content stored as txt files in `data/submissions/`
  - Graph stores metadata + file paths for mapping

### 3. Forms System
- **Dynamic & Modular**: Add forms by creating new .py files in `forms/` directory
- Each form inherits from `BaseForm` class
- Forms associated with projects
- Submissions stored as txt files with metadata in graph
- Form data exportable for data science analysis

### 4. Role-Based Access Control
- **Current Roles**:
  - `admin` (head): Access to all features + analytics dashboard
  - `employee` (user): Access to forms and personal settings
- **Future**: Extensible role system with custom permissions

### 5. User Interface
- **Design Style**: Minimal, Apple-inspired
- Clean white/light gray palette
- SF Pro fonts (or fallback to system fonts)
- Subtle shadows and rounded corners
- Responsive and intuitive navigation

## Technology Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database (Current)**: NetworkX (graph library)
- **Database (Future)**: Neo4j
- **Session Management**: Flask-Session
- **Environment**: Conda `webpage-python`

### Frontend
- **Templates**: Jinja2 (Flask templating)
- **Styling**: Custom CSS (Apple-inspired minimal design)
- **JavaScript**: Vanilla JS for interactivity
- **Icons**: Optional (Font Awesome or similar)

### Data Storage
- User initialization: `data/users.txt`
- Form submissions: `data/submissions/{project_id}/{form_type}/{timestamp}.txt`
- Backups: `data/backups/`
- Logs: `logs/`

## Project Structure

```
Project-06-PMOWebsite/V0/
│
├── app.py                      # Main Flask application
├── run.py                      # Application runner
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── ROADMAP.md                  # This file
│
├── data/                       # Data storage
│   ├── users.txt              # Initial user data
│   ├── submissions/           # Form submission files
│   └── backups/               # Data backups
│
├── logs/                       # Application logs
│   └── app.log
│
├── database/                   # Database abstraction layer
│   ├── __init__.py
│   ├── base_db.py             # Abstract database interface
│   ├── networkx_db.py         # NetworkX implementation
│   └── neo4j_db.py            # Neo4j implementation (future)
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── user.py                # User model
│   ├── project.py             # Project model
│   └── form_submission.py     # Form submission model
│
├── forms/                      # Dynamic form definitions
│   ├── __init__.py
│   ├── base_form.py           # Abstract base form class
│   ├── form_registry.py       # Form loader and registry
│   ├── project_request.py     # Example form
│   └── status_update.py       # Example form
│
├── routes/                     # Flask blueprints
│   ├── __init__.py
│   ├── auth.py                # Login/logout routes
│   ├── dashboard.py           # Main dashboard
│   ├── forms_routes.py        # Form selection and submission
│   ├── projects.py            # Project management
│   ├── settings.py            # User settings
│   └── admin.py               # Admin dashboard
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── decorators.py          # Route decorators (@require_login, etc.)
│   ├── validators.py          # Data validation
│   ├── file_handler.py        # File operations
│   └── data_export.py         # Export for data science
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── main.css           # Main stylesheet
│   │   └── forms.css          # Form-specific styles
│   ├── js/
│   │   ├── main.js            # Main JavaScript
│   │   └── forms.js           # Form interactivity
│   └── img/                   # Images and icons
│
└── templates/                  # HTML templates
    ├── base.html              # Base template
    ├── auth/
    │   └── login.html         # Login page
    ├── dashboard/
    │   ├── home.html          # User dashboard
    │   └── admin.html         # Admin dashboard
    ├── forms/
    │   ├── list.html          # Available forms
    │   ├── select_project.html # Project selection
    │   └── render_form.html   # Dynamic form renderer
    ├── projects/
    │   ├── list.html          # Project list
    │   └── detail.html        # Project details
    ├── settings/
    │   └── profile.html       # User settings
    └── errors/
        ├── 404.html           # Not found
        └── 500.html           # Server error
```

## Development Phases

### Phase 1: Foundation (Tasks 1-6)
- Project structure setup
- Database abstraction layer
- User model and authentication
- Flask application skeleton

### Phase 2: Core Features (Tasks 7-13)
- Login system
- Dashboard
- Role-based access control
- Form architecture
- Form storage system

### Phase 3: Forms & Projects (Tasks 14-16)
- Example forms
- Form selection interface
- Project management

### Phase 4: User Features (Tasks 17-19)
- User settings
- Data export system
- Admin analytics dashboard

### Phase 5: Polish & Documentation (Tasks 20-27)
- UI/UX styling
- JavaScript interactivity
- Comprehensive documentation
- Error handling and logging
- Testing and validation

## Key Design Principles

### 1. Modularity
- Each component is self-contained
- Clear interfaces between layers
- Easy to extend and modify
- AI-friendly code structure

### 2. Simplicity
- Avoid over-engineering
- Keep files under 300 lines when possible
- Clear naming conventions
- Extensive comments and docstrings

### 3. Future-Proof
- Database abstraction for easy migration
- Role system designed for expansion
- Form system allows unlimited additions
- Configuration-driven behavior

### 4. Documentation-First
- Every module has clear documentation
- README for each major component
- Migration guides for database switch
- Form creation tutorial

## Database Migration Strategy (NetworkX → Neo4j)

### Current NetworkX Implementation
```python
# Simple in-memory graph
graph = nx.DiGraph()
graph.add_node(user_id, type='user', **user_data)
graph.add_edge(user_id, submission_id, relation='SUBMITTED')
```

### Future Neo4j Implementation
```python
# Same interface, different backend
session.run("""
    CREATE (u:User {email: $email, ...})
    CREATE (s:Submission {id: $id, ...})
    CREATE (u)-[:SUBMITTED]->(s)
""", email=email, id=submission_id)
```

### Migration Steps
1. Implement `Neo4jDatabase` class with same interface as `NetworkXDatabase`
2. Update `config.py` to switch database backend
3. Run migration script to export NetworkX data and import to Neo4j
4. Test all functionality with new backend

## User Data Format

`data/users.txt` format (pipe-delimited):
```
email|national_id|name|phone|password|role
admin@company.com|1234567890|John Doe|+98 910 151 1983|admin123|admin
user@company.com|0987654321|Jane Smith|+98 912 345 6789|user123|employee
```

## Forms Data Storage

Form submission example: `data/submissions/PRJ001/project_request/2025-10-24_14-30-45.txt`
```
Form: Project Request
Submitted By: user@company.com
Project: PRJ001
Timestamp: 2025-10-24 14:30:45

Field: Project Name
Value: New Website Redesign

Field: Budget
Value: $50,000

Field: Timeline
Value: 3 months
...
```

## Security Considerations

**Note**: Current implementation uses plain text passwords as requested. For production:
- Implement password hashing (bcrypt/argon2)
- Use HTTPS only
- Add CSRF protection
- Implement rate limiting
- Add session timeout
- Enable audit logging

## Next Steps

1. Review and approve this roadmap
2. Set up development environment (conda activate webpage-python)
3. Begin Phase 1 implementation
4. Iterate and test each component
5. Deploy to staging environment
6. Final testing and production deployment

## Questions to Consider

1. Should we add a "Forgot Password" feature for admins to reset user passwords?
2. Do we need file upload capabilities in forms?
3. Should forms support draft/save functionality?
4. Do we want email notifications for form submissions?
5. Should there be form approval workflows?

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Author**: Development Team
