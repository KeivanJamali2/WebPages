# HamiAnalyzer Web Application

A comprehensive web-based data analysis platform for processing and analyzing Hami system data with advanced visualizations and reporting capabilities.

## Features

### 🔐 User Authentication
- Secure login system
- User management via text file
- Session-based authentication
- No public signup (admin-controlled access)

### 📤 Data Upload & Processing
- ZIP file upload support (up to 500 MB)
- Automatic data extraction and organization
- Support for multiple Hami IDs
- Date-based data structuring

### 📊 Advanced Analytics
- Total requests per Hami
- Message date distribution analysis
- Top communicators (employees, students, places)
- Communication network heatmaps
- Response time analysis
- Common titles/subjects analysis
- Student messaging patterns

### 📈 Visualization
- High-quality PNG plots
- Interactive charts
- Persian/Farsi text support
- Reference tables for better understanding
- Full-screen plot viewing
- Downloadable visualizations

### 💾 Data Export
- CSV file exports for all analyses
- Detailed statistical reports
- Excel-compatible formats
- Organized download management

### 🗄️ Database Management
- View database statistics
- Add incremental data
- Complete database reset
- Size monitoring

## Installation

### Prerequisites
- Python 3.8 or higher
- conda (recommended) or pip

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd /mnt/Data1/Python_Projects/WebPages/Project-04-HamiAnalyzer/V3/Website
   ```

2. **Create and activate conda environment:**
   ```bash
   conda create -n webpage-python python=3.10
   conda activate webpage-python
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure users:**
   Edit `users.txt` to add authorized users:
   ```
   username,password,phone_number
   admin,admin123,09123456789
   ```

## Running the Application

### Development Mode
```bash
conda activate webpage-python
python app.py
```

The application will be available at: `http://localhost:5000`

### Production Mode
For production deployment, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Usage Guide

### 1. Login
- Navigate to the login page
- Enter your username and password
- Click "Login"

### 2. Upload Data
1. Click "Upload Data" in the navigation
2. Select a ZIP file containing your raw data
3. Ensure the ZIP contains files in format:
   - `file_i_j.txt` (message data)
   - `workflow_i_j.txt` (workflow data)
4. Click "Upload File"

### 3. Process Data
1. After upload, you'll be redirected to the process page
2. Enter comma-separated Hami IDs (optional, auto-detects if empty)
3. Click "Process Data"
4. Wait for processing to complete

### 4. Run Analysis
1. Navigate to "Analyze" page
2. Click "Run All Analyses"
3. Wait for analysis to complete (2-5 minutes)
4. View results in Plots and Downloads pages

### 5. View Results
- **Plots Page**: View and download visualization images
- **Downloads Page**: Download detailed CSV reports
- **Dashboard**: See summary statistics

### 6. Database Management
- View current database statistics
- Add more data via upload
- Clear entire database (use with caution!)

## File Structure

```
Website/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── cleaner.py            # Data cleaning logic
├── analyzer.py           # Analysis engine
├── Plot_Config.py        # Plot configuration
├── people_index.csv      # People mapping
├── users.txt             # User credentials
├── requirements.txt      # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── main.js      # JavaScript functions
├── templates/
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── dashboard.html   # Dashboard
│   ├── upload.html      # Upload page
│   ├── process_data.html
│   ├── manage_database.html
│   ├── analyze.html
│   ├── plots.html
│   ├── downloads.html
│   ├── help.html
│   ├── 404.html
│   └── 500.html
├── uploads/             # Uploaded files
├── database/            # Processed data
├── plots/              # Generated plots
├── downloads/          # CSV exports
└── logs/              # Application logs
```

## Configuration

Edit `config.py` to customize:
- File size limits
- Date source (first/last)
- Session timeout
- Logging level
- Folder paths

## Security Features

- Session-based authentication
- Secure file upload validation
- CSRF protection ready
- Password-protected access
- No public registration
- Secure file handling

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Text Processing**: Jdatetime, Arabic Reshaper
- **Icons**: Bootstrap Icons

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (responsive design)

## Troubleshooting

### Issue: Cannot upload files
- Check file size (max 500 MB)
- Ensure ZIP format
- Verify file structure matches requirements

### Issue: Analysis fails
- Ensure database has data
- Check logs in `logs/app.log`
- Verify `people_index.csv` exists

### Issue: Plots not showing
- Run analysis first
- Check `plots/` folder permissions
- Clear browser cache

### Issue: Login not working
- Verify user exists in `users.txt`
- Check username/password format
- Ensure no extra spaces

## Adding New Users

1. Open `users.txt`
2. Add a new line with format: `username,password,phone_number`
3. Save the file
4. New user can now log in

Example:
```
admin,admin123,09123456789
user1,pass1234,09121111111
analyst,secure456,09122222222
```

## Maintenance

### Clearing Logs
```bash
rm -rf logs/*.log
```

### Clearing Uploads
```bash
rm -rf uploads/*
```

### Backing Up Database
```bash
tar -czf database_backup_$(date +%Y%m%d).tar.gz database/
```

## Performance Tips

- Clear old uploads periodically
- Run analysis during off-peak hours
- Monitor database size
- Use database filtering when possible

## License

Proprietary - Internal Use Only

## Support

For issues, questions, or feature requests, contact the system administrator.

## Version History

- **v1.0.0** (2024-11) - Initial release
  - User authentication
  - Data upload and processing
  - Comprehensive analytics
  - Visualization engine
  - Database management
  - Help documentation

---

**HamiAnalyzer** - Advanced Data Analysis Platform
