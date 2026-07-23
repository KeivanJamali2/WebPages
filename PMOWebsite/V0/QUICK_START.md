# PMO Website - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Activate Environment
```bash
conda activate webpage-python
```

### Step 2: Navigate to Project
```bash
cd /mnt/Data1/Python_Projects/Advanced-Python/Project-06-PMOWebsite/V0
```

### Step 3: Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python run.py
```

### Step 5: Access the Website
Open your browser and go to: **http://127.0.0.1:5000**

## 🔑 Login Credentials

### Admin Account
- **Email:** admin@company.com
- **Password:** admin123
- **Access:** Full system access, analytics, user management

### Employee Account
- **Email:** employee1@company.com
- **Password:** pass123
- **Access:** Forms, projects, personal settings

## 📱 Available Features

### ✅ Working Now
- User login/logout
- User dashboard
- Admin dashboard with statistics
- Password change
- User profile viewing
- Navigation system
- Error handling
- Flash messages

### 🚧 To Be Implemented
- Forms creation and submission
- Project management pages
- Data visualizations
- Form-project associations

## 🎯 What You Can Test

1. **Login System**
   - Try logging in with admin credentials
   - Try logging in with employee credentials
   - Try wrong credentials

2. **Navigation**
   - Visit dashboard
   - Visit admin dashboard (admin only)
   - Visit settings page

3. **Settings**
   - Change your password
   - View profile information
   - View submission history (will be empty for now)

4. **Access Control**
   - Try accessing admin dashboard as employee (should be denied)
   - Verify navigation shows appropriate links based on role

## 📁 Project Files Overview

### Main Files
- `app.py` - Main Flask application
- `run.py` - Application runner
- `config.py` - Configuration settings

### Data Files
- `data/users.txt` - User credentials (can be edited)
- `data/projects.txt` - Project list
- `logs/app.log` - Application logs

### Key Directories
- `database/` - Database layer (NetworkX)
- `models/` - Data models
- `routes/` - Flask routes/blueprints
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, images

## 🛠️ Common Tasks

### Add a New User
1. Edit `data/users.txt`
2. Add line: `email|national_id|name|phone|password|role`
3. Restart application

Example:
```
newuser@company.com|1111111111|New User|+98 919 999 9999|pass2025|employee
```

### Add a New Project
1. Edit `data/projects.txt`
2. Add line: `project_id|name|description|status|start_date|end_date`
3. Restart application

Example:
```
PRJ006|New Initiative|Description here|active|2025-10-24|
```

### View Logs
```bash
tail -f logs/app.log
```

### Stop the Server
Press `CTRL+C` in the terminal

## 🐛 Troubleshooting

### Port Already in Use
If port 5000 is busy, edit `run.py` and change the port number:
```python
app.run(port=5001)  # Change to different port
```

### Module Not Found
Make sure you activated the conda environment:
```bash
conda activate webpage-python
```

### Database Not Loading
Check that `data/users.txt` exists and is properly formatted.

### Can't Login
1. Check `data/users.txt` for correct credentials
2. Check `logs/app.log` for error messages
3. Ensure database loaded successfully at startup

## 📚 Learn More

- **Full Documentation:** See `README.md`
- **Architecture:** See `ROADMAP.md`
- **Implementation Status:** See `IMPLEMENTATION_SUMMARY.md`

## 🎨 Customization

### Change Colors
Edit `static/css/main.css` and modify CSS variables:
```css
:root {
    --color-primary: #007AFF;  /* Change this */
}
```

### Modify Navigation
Edit `templates/base.html` navigation section.

### Add New Routes
Create new blueprint in `routes/` directory.

## 📊 What's Next?

The core infrastructure is complete! Next steps:

1. **Implement Forms System**
   - Create BaseForm class
   - Add form routes
   - Build form templates

2. **Add Project Management**
   - Create project routes
   - Build project pages

3. **Enhance Analytics**
   - Add charts to admin dashboard
   - Implement data export

See `IMPLEMENTATION_SUMMARY.md` for detailed next steps.

## 💻 Development Tips

- Keep the server running while developing
- Changes to Python files require restart
- Changes to templates/CSS reload automatically (in debug mode)
- Check `logs/app.log` for debugging

## ✅ Quick Test Checklist

- [ ] Application starts without errors
- [ ] Can login as admin
- [ ] Can login as employee  
- [ ] Dashboard displays correctly
- [ ] Admin dashboard works (admin only)
- [ ] Settings page loads
- [ ] Password change works
- [ ] Logout works
- [ ] Error pages display (try invalid URL)

## 🎉 Success!

If you can login and see the dashboard, the core system is working!

---

**Need Help?** Check the detailed README.md or review the code comments.
