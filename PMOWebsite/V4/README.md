# PMO Website - Daily Performance Tracking System

A Flask web application for tracking daily employee performance in construction/project management environments.

## Features

- **Three User Roles**:
  - **Boss**: Create projects, view analytics, manage system
  - **Admin**: Review and approve/reject daily forms
  - **Employee**: Submit daily performance forms

- **Daily Form Sections**:
  - Date/Time & General Info
  - Human Resources (staff attendance)
  - Tools & Equipment (usage hours)
  - Construction Operations (progress tracking)
  - Incoming Materials
  - Climate Conditions
  - Project Issues & Problems
  - Safety & Incidents
  - Special Events

- **Bilingual Support**: English and Persian (فارسی) with RTL support

- **Real-time Analytics**: Interactive charts for bosses to analyze project performance

- **Excel Export**: Export forms and data to Excel format

- **Notification System**: Real-time notifications for form submissions and approvals

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd Project-02-PMOWebsite/V1
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure users** in `user.txt`:
   ```
   # username,password,role
   admin,admin123,boss
   manager,manager123,admin
   worker1,worker123,employee
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application** at `http://localhost:5000`

## Project Structure

```
V1/
├── app.py                 # Main application entry
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── user.txt              # User credentials (CSV format)
├── translations.py        # EN/FA translations
│
├── models/               # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── project.py
│   ├── daily_form.py
│   ├── notification.py
│   └── comment.py
│
├── routes/               # Flask blueprints
│   ├── auth.py           # Login/logout
│   ├── main.py           # Dashboard
│   ├── forms.py          # Daily form CRUD
│   ├── projects.py       # Project management
│   ├── analytics.py      # Charts/analytics API
│   ├── notifications.py  # Notification system
│   └── export.py         # Excel export
│
├── utils/                # Helper utilities
│   ├── auth.py           # Auth decorators
│   └── helpers.py        # Date/format helpers
│
├── templates/            # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   ├── auth/
│   ├── forms/
│   ├── projects/
│   ├── analytics/
│   ├── export/
│   └── notifications/
│
├── static/               # Static files
│   ├── css/style.css
│   └── js/main.js
│
├── forms/                # Form configurations
│   └── daily_form_configuration.py
│
├── Projects/             # Project configurations
│   └── project_configuration.py
│
└── data/                 # Database & uploads
    └── pmo.db
```

## User Roles & Permissions

| Feature | Employee | Admin | Boss |
|---------|----------|-------|------|
| Submit daily forms | ✅ | ✅ | ✅ |
| View own forms | ✅ | ✅ | ✅ |
| View all forms | ❌ | ✅ | ✅ |
| Approve/reject forms | ❌ | ✅ | ❌ |
| Create projects | ❌ | ❌ | ✅ |
| View analytics | ❌ | ❌ | ✅ |
| Export to Excel | Own only | All | All |

## Workflow

1. **Employee** fills out daily form → Saves as draft or submits
2. **Admin** reviews pending forms → Approves or rejects with comments
3. If rejected, **Employee** can edit and resubmit
4. **Boss** views analytics and manages projects

## Configuration

### Adding Users

Edit `user.txt` directly (no restart required):
```
username,password,role
```

Roles: `boss`, `admin`, `employee`

### Adding Projects

Edit `Projects/project_configuration.py` to add new projects:
```python
projects = {
    "Project-Code": {
        "name": "Project Name",
        "location": "Location",
        "contract_number": "Contract #",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",  # or "On-Going"
        "budget": 1000000,
        "Owner": "Client Name",
        "manager": "Manager Name"
    }
}
```

### Customizing Form Fields

Edit `forms/daily_form_configuration.py` to customize:
- Human resource positions
- Equipment types
- Material categories
- Form field options

## API Endpoints (Analytics)

- `GET /analytics/api/overview` - Summary statistics
- `GET /analytics/api/forms-by-date` - Forms timeline
- `GET /analytics/api/forms-by-project` - Forms per project
- `GET /analytics/api/forms-by-employee` - Forms per employee
- `GET /analytics/api/equipment-hours` - Equipment usage
- `GET /analytics/api/human-resources` - HR summary
- `GET /analytics/api/safety-incidents` - Safety statistics
- `GET /analytics/api/progress-summary` - Construction progress

All endpoints accept optional query parameters: `from_date`, `to_date`, `project_id`

## Language Switching

Click the EN/فا buttons in the navbar to toggle between English and Persian.
The interface will switch immediately, including RTL text direction for Persian.

## Development

### Debug Mode

Set in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Database Reset

Delete `data/pmo.db` and restart the application to reset the database.

## License

Internal use only.
