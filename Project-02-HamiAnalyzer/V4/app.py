"""
HamiAnalyzer Web Application
Main Flask application file
"""
# Set matplotlib to non-interactive backend BEFORE importing analyzer
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web server

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
import zipfile
import shutil
from pathlib import Path
import logging
from datetime import datetime
from functools import wraps
import json
from io import BytesIO
import pandas as pd

# Import local modules
import config
from cleaner import StoreData, RawDataReader, DuplicateDetector, strip_excel_formula, LegacyCSVMigrator
from analyzer import SQLiteAnalyzer
from database import HamiDatabase, get_database
from template_transformer import transform_raw_template

# Initialize database
db = get_database(config.DATABASE_FOLDER / 'hami.db')

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# User management functions
def load_users():
    """Load users from users.txt file"""
    users = {}
    try:
        if config.USERS_FILE.exists():
            with open(config.USERS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',')
                        if len(parts) >= 3:
                            username, password, phone = parts[0].strip(), parts[1].strip(), parts[2].strip()
                            users[username] = {'password': password, 'phone': phone}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
    return users

def verify_user(username, password):
    """Verify user credentials"""
    users = load_users()
    if username in users:
        return users[username]['password'] == password
    return False

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_user(username, password):
            session['username'] = username
            logger.info(f"User {username} logged in successfully")
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'Unknown')
    session.pop('username', None)
    logger.info(f"User {username} logged out")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    # Get statistics
    stats = get_database_stats()
    return render_template('dashboard.html', stats=stats, username=session['username'])

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload ZIP file with raw data"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Get date_source from form
                date_source = request.form.get('date_source', 'first')
                if date_source not in ['first', 'last']:
                    date_source = 'first'
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = config.UPLOAD_FOLDER / filename
                file.save(filepath)
                
                # Extract the ZIP file
                extract_folder = config.UPLOAD_FOLDER / filename.replace('.zip', '')
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)
                
                logger.info(f"File uploaded and extracted: {filename} by {session['username']}")
                flash(f'File "{filename}" uploaded successfully!', 'success')
                
                # Store the extract folder path and date_source for processing
                session['last_upload'] = str(extract_folder)
                session['date_source'] = date_source
                
                return redirect(url_for('process_data'))
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                flash(f'Error uploading file: {str(e)}', 'danger')
        else:
            flash('Only ZIP files are allowed', 'danger')
    
    return render_template('upload.html')

@app.route('/process_data', methods=['GET', 'POST'])
@login_required
def process_data():
    """Process uploaded data using cleaner.py"""
    if request.method == 'POST':
        try:
            extract_folder = session.get('last_upload')
            logger.info(f"Processing data from folder: {extract_folder}")
            
            if not extract_folder:
                flash('No uploaded data found. Please upload a file first.', 'warning')
                return redirect(url_for('upload'))
            
            extract_folder = Path(extract_folder)
            if not extract_folder.exists():
                flash('Upload folder not found.', 'danger')
                return redirect(url_for('upload'))
            
            # Get date_source from session (set during upload)
            date_source = session.get('date_source', 'first')
            if date_source not in ['first', 'last']:
                date_source = 'first'
            
            logger.info(f"Using date_source: {date_source}")
            
            # Get i_values from form
            i_values_str = request.form.get('i_values', '')
            if i_values_str:
                i_values = [int(i.strip()) for i in i_values_str.split(',') if i.strip().isdigit()]
                logger.info(f"Using manually specified i_values: {i_values}")
            else:
                # Auto-detect i values from files
                i_values = auto_detect_i_values(extract_folder)
                logger.info(f"Auto-detected i_values: {i_values}")
            
            if not i_values:
                flash('No valid data files found in the uploaded folder.', 'warning')
                return redirect(url_for('upload'))
            
            logger.info(f"Starting data processing for {len(i_values)} hami IDs...")
            
            # Process data using cleaner with SQLite database
            store_data = StoreData(
                base_output_path=config.DATABASE_FOLDER,
                base_input_path=extract_folder,
                date_source=date_source,
                db=db
            )
            result = store_data.fit(i_values=i_values)
            
            replaced_count = result.get('replaced', 0)
            logger.info(f"Data processed: {result['processed']} new, {replaced_count} replaced, {result['skipped']} skipped by {session['username']}")
            
            # Clean up: Delete the extracted folder (keep the ZIP file)
            try:
                if extract_folder.exists() and extract_folder.is_dir():
                    shutil.rmtree(extract_folder)
                    logger.info(f"Cleaned up extracted folder: {extract_folder}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up extracted folder {extract_folder}: {cleanup_error}")
            
            if replaced_count > 0:
                flash(f'Data processed: {result["processed"]} new requests added, {replaced_count} existing requests replaced!', 'success')
            else:
                flash(f'Data processed: {result["processed"]} new requests added!', 'success')
            
            # Check for duplicates in SQLite
            detector = DuplicateDetector(config.DATABASE_FOLDER, date_source, db=db)
            summary = detector.get_duplicate_summary()
            
            if summary['total_duplicate_groups'] > 0:
                # Store duplicate info in session and redirect to duplicates page
                session['duplicates_summary'] = {
                    'total_duplicate_groups': summary['total_duplicate_groups'],
                    'total_duplicates': summary['total_duplicates'],
                    'date_source': date_source
                }
                logger.info(f"Found {summary['total_duplicate_groups']} duplicate groups with {summary['total_duplicates']} total duplicates")
                flash(f'Found {summary["total_duplicate_groups"]} duplicate groups! Please resolve them.', 'warning')
                return redirect(url_for('duplicates_page', date_source=date_source))
            
            return redirect(url_for('manage_database'))
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            flash(f'Error processing data: {str(e)}', 'danger')
    
    return render_template('process_data.html')

@app.route('/manage_database')
@login_required
def manage_database():
    """Database management page"""
    stats = get_database_stats()
    return render_template('manage_database.html', stats=stats)

@app.route('/clear_database', methods=['POST'])
@login_required
def clear_database():
    """Clear all data from database"""
    global db
    try:
        # Use the global database instance to clear data
        db.clear_database()
        
        # Reinitialize the database to ensure schema is intact
        db = get_database(config.DATABASE_FOLDER / 'hami.db')
        
        logger.info(f"Database cleared by {session['username']}")
        flash('Database cleared successfully!', 'success')
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        flash(f'Error clearing database: {str(e)}', 'danger')
    
    return redirect(url_for('manage_database'))

@app.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    """Run analysis and generate plots"""
    if request.method == 'POST':
        try:
            # Get date range from form (optional)
            import jdatetime
            start_date = None
            end_date = None
            
            start_date_str = request.form.get('start_date', '').strip()
            end_date_str = request.form.get('end_date', '').strip()
            
            try:
                if start_date_str:
                    # Parse Jalali date (YYYY-MM-DD) and set to beginning of day
                    parts = start_date_str.split('-')
                    if len(parts) == 3:
                        start_date = jdatetime.datetime(int(parts[0]), int(parts[1]), int(parts[2]), 0, 0, 0)
                
                if end_date_str:
                    # Parse Jalali date (YYYY-MM-DD) and set to beginning of day (exclusive)
                    parts = end_date_str.split('-')
                    if len(parts) == 3:
                        end_date = jdatetime.datetime(int(parts[0]), int(parts[1]), int(parts[2]), 0, 0, 0)
                
                # Validate date range
                if start_date and end_date and start_date >= end_date:
                    flash('Start date must be before end date.', 'warning')
                    return redirect(url_for('analyze'))
                    
            except (ValueError, IndexError) as e:
                flash(f'Invalid date format. Please use YYYY-MM-DD format (e.g., 1403-01-01).', 'warning')
                return redirect(url_for('analyze'))
            
            # Get selected plots from form
            selected_plots = request.form.getlist('plots')
            
            if not selected_plots:
                flash('Please select at least one analysis to run.', 'warning')
                return redirect(url_for('analyze'))
            
            # Save the analysis configuration for next time
            config.save_analysis_config(start_date_str, end_date_str, selected_plots)
            
            # Clear previous plots and downloads
            clear_folder(config.PLOTS_FOLDER)
            clear_folder(config.DOWNLOADS_FOLDER)
            
            # Initialize optimized SQLite analyzer (no data loading needed!)
            analyzer = SQLiteAnalyzer(
                db=db,
                plot_folder=config.PLOTS_FOLDER,
                csv_folder=config.DOWNLOADS_FOLDER,
                mapping_data_file_path=config.PEOPLE_INDEX_FILE,
                start_date=start_date,
                end_date=end_date
            )
            
            # Define mapping of function names to actual analyzer methods with their parameters
            analysis_functions = {
                'total_requests_per_hami': lambda: analyzer.total_requests_per_hami(plot=True, show_reference=True),
                'message_date_distribution_per_month': lambda: analyzer.message_date_distribution(plot=True, per='month'),
                'message_date_distribution_per_day': lambda: analyzer.message_date_distribution(plot=True, per='day'),
                'request_date_distribution_per_month': lambda: analyzer.message_date_distribution(plot=True, per='month_request'),
                'top_communicators_employee': lambda: analyzer.top_communicators_for_employee(if_plot=True, n=10),
                'top_communicators_student': lambda: analyzer.top_communicators_for_student(if_plot=True, n=10),
                'top_communicators_place': lambda: analyzer.top_communicators_for_place(if_plot=True, n=10),
                # 'communication_network': lambda: analyzer.communication_network(plot=True, min_count=5, top_n=20),
                'total_messages_per_student': lambda: analyzer.total_messages_per_student(plot=True),
                'common_titles': lambda: analyzer.common_titles(n=20, plot_=True),
                'response_time_per_person': lambda: analyzer.response_time_per_person(plot=True),
                'place_by_field': lambda: (analyzer.top_communicators_for_place(if_plot=False, n=10), analyzer.place_filtered(), analyzer.place_filtered_by(by="field", plot=True), analyzer.place_filtered_by_grouped(by="field", plot=True)),
                'place_by_year': lambda: (analyzer.top_communicators_for_place(if_plot=False, n=10), analyzer.place_filtered(), analyzer.place_filtered_by(by="year", plot=True), analyzer.place_filtered_by_grouped(by="year", plot=True)),
                'place_by_edu_level': lambda: (analyzer.top_communicators_for_place(if_plot=False, n=10), analyzer.place_filtered(), analyzer.place_filtered_by(by="educational_level", plot=True), analyzer.place_filtered_by_grouped(by="educational_level", plot=True)),
                'place_by_faculty': lambda: (analyzer.top_communicators_for_place(if_plot=False, n=10), analyzer.place_filtered(), analyzer.place_filtered_by_grouped(by="field", plot=False), analyzer.place_filtered_by_grouped(by="faculty", plot=True)),
            }
            
            # Run selected analyses dynamically
            analyses_run = 0
            for plot_name in selected_plots:
                if plot_name in analysis_functions:
                    try:
                        analysis_functions[plot_name]()
                        analyses_run += 1
                    except Exception as e:
                        logger.error(f"Error running analysis '{plot_name}': {e}")
                        flash(f"Warning: Analysis '{plot_name}' failed: {str(e)}", 'warning')
                else:
                    logger.warning(f"Unknown analysis function: {plot_name}")
                    flash(f"Warning: Unknown analysis '{plot_name}'", 'warning')
            
            # Build success message
            date_range_info = ""
            if start_date or end_date:
                if start_date and end_date:
                    date_range_info = f" (Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
                elif start_date:
                    date_range_info = f" (From: {start_date.strftime('%Y-%m-%d')})"
                elif end_date:
                    date_range_info = f" (Until: {end_date.strftime('%Y-%m-%d')})"
            
            logger.info(f"Analysis completed ({analyses_run} analyses) by {session['username']}{date_range_info}")
            flash(f'Analysis completed successfully! Generated {analyses_run} plot(s).{date_range_info}', 'success')
            
            return redirect(url_for('view_plots'))
        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            flash(f'Error running analysis: {str(e)}', 'danger')
    
    # Load available analyses from configuration file
    available_analyses = config.load_available_analyses()
    # Load saved analysis configuration
    saved_config = config.load_analysis_config()
    return render_template('analyze.html', 
                          available_analyses=available_analyses,
                          saved_config=saved_config)

@app.route('/plots')
@login_required
def view_plots():
    """View generated plots"""
    plots = []
    if config.PLOTS_FOLDER.exists():
        for file in config.PLOTS_FOLDER.glob('*.png'):
            plots.append({
                'name': file.stem.replace('_', ' ').title(),
                'filename': file.name,
                'path': f'/download_plot/{file.name}'
            })
    # Sort plots alphabetically by name
    plots.sort(key=lambda x: x['name'].lower())
    return render_template('plots.html', plots=plots)

@app.route('/plot_image/<filename>')
@login_required
def plot_image(filename):
    """Serve a plot image for viewing in the browser"""
    try:
        file_path = config.PLOTS_FOLDER / filename
        if file_path.exists():
            return send_file(file_path, mimetype='image/png')
        else:
            return "Plot not found", 404
    except Exception as e:
        logger.error(f"Error serving plot image: {e}")
        return f"Error: {str(e)}", 500

@app.route('/download_plot/<filename>')
@login_required
def download_plot(filename):
    """Download a specific plot"""
    try:
        file_path = config.PLOTS_FOLDER / filename
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        else:
            flash('Plot not found', 'danger')
            return redirect(url_for('view_plots'))
    except Exception as e:
        logger.error(f"Error downloading plot: {e}")
        flash(f'Error downloading plot: {str(e)}', 'danger')
        return redirect(url_for('view_plots'))

@app.route('/download_all_plots')
@login_required
def download_all_plots():
    """Download all plots as a ZIP archive"""
    try:
        if not config.PLOTS_FOLDER.exists():
            flash('No plots available', 'warning')
            return redirect(url_for('view_plots'))
        
        plot_files = list(config.PLOTS_FOLDER.glob('*.png'))
        if not plot_files:
            flash('No plots available', 'warning')
            return redirect(url_for('view_plots'))
        
        # Create ZIP file in memory
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for plot_file in plot_files:
                zf.write(plot_file, plot_file.name)
        
        memory_file.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'hami_analysis_plots_{timestamp}.zip'
        
        logger.info(f"User {session['username']} downloaded all plots ({len(plot_files)} files)")
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        logger.error(f"Error creating plots ZIP: {e}")
        flash(f'Error creating ZIP file: {str(e)}', 'danger')
        return redirect(url_for('view_plots'))

@app.route('/downloads')
@login_required
def view_downloads():
    """View and download CSV files"""
    files = []
    if config.DOWNLOADS_FOLDER.exists():
        for file in config.DOWNLOADS_FOLDER.glob('*.csv'):
            files.append({
                'name': file.stem.replace('_', ' ').title(),
                'filename': file.name,
                'size': f"{file.stat().st_size / 1024:.2f} KB",
                'path': f'/download_csv/{file.name}'
            })
    # Sort files alphabetically by name
    files.sort(key=lambda x: x['name'].lower())
    return render_template('downloads.html', files=files)

@app.route('/download_csv/<filename>')
@login_required
def download_csv(filename):
    """Download a specific CSV file"""
    try:
        file_path = config.DOWNLOADS_FOLDER / filename
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        else:
            flash('File not found', 'danger')
            return redirect(url_for('view_downloads'))
    except Exception as e:
        logger.error(f"Error downloading CSV: {e}")
        flash(f'Error downloading CSV: {str(e)}', 'danger')
        return redirect(url_for('view_downloads'))

@app.route('/download_all_csv')
@login_required
def download_all_csv():
    """Download all CSV files as a ZIP archive"""
    try:
        if not config.DOWNLOADS_FOLDER.exists():
            flash('No CSV files available', 'warning')
            return redirect(url_for('view_downloads'))
        
        csv_files = list(config.DOWNLOADS_FOLDER.glob('*.csv'))
        if not csv_files:
            flash('No CSV files available', 'warning')
            return redirect(url_for('view_downloads'))
        
        # Create ZIP file in memory
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for csv_file in csv_files:
                zf.write(csv_file, csv_file.name)
        
        memory_file.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'hami_analysis_csv_{timestamp}.zip'
        
        logger.info(f"User {session['username']} downloaded all CSV files ({len(csv_files)} files)")
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        logger.error(f"Error creating CSV ZIP: {e}")
        flash(f'Error creating ZIP file: {str(e)}', 'danger')
        return redirect(url_for('view_downloads'))

@app.route('/help')
@login_required
def help_page():
    """Help and documentation page"""
    return render_template('help.html')

@app.route('/duplicates')
@login_required
def duplicates_page():
    """Deduplication management page"""
    date_source = request.args.get('date_source', None)
    
    # If no date_source specified, check for duplicates in SQLite
    if date_source is None:
        try:
            # Check SQLite database for duplicates
            detector = DuplicateDetector(config.DATABASE_FOLDER, 'first', db=db)
            summary = detector.get_duplicate_summary()
            
            logger.info(f"Duplicate check - SQLite database: {summary['total_duplicate_groups']} groups")
            
            if summary['total_duplicate_groups'] == 0:
                flash('No duplicates found in the database.', 'info')
                return redirect(url_for('manage_database'))
            
            # Show duplicates page directly
            return render_template('duplicates.html', summary=summary, date_source='sqlite')
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}", exc_info=True)
            flash(f'Error checking duplicates: {str(e)}', 'danger')
            return redirect(url_for('manage_database'))
    
    try:
        detector = DuplicateDetector(config.DATABASE_FOLDER, date_source, db=db)
        summary = detector.get_duplicate_summary()
        
        # Debug logging
        logger.info(f"Duplicates page loaded: {summary['total_duplicate_groups']} groups, {summary['total_duplicates']} records")
        
        return render_template('duplicates.html', summary=summary, date_source=date_source)
    except Exception as e:
        logger.error(f"Error loading duplicates page: {e}", exc_info=True)
        flash(f'Error loading duplicates: {str(e)}', 'danger')
        return redirect(url_for('manage_database'))

# Database navigation and search API routes
@app.route('/api/browse_database', methods=['GET'])
@login_required
def api_browse_database():
    """Browse database - returns list of hamis or requests for a hami"""
    try:
        hami_id = request.args.get('hami_id')
        
        # If no hami_id specified, return list of available hamis
        if not hami_id:
            hamis = sqlite_get_all_hamis()
            counts = db.get_requests_count_by_hami()
            hami_list = [{'hami_id': h, 'request_count': counts.get(h, 0)} for h in hamis]
            return jsonify({'hamis': hami_list})
        
        # Return requests for the specified hami
        requests_list = sqlite_get_requests_for_hami(hami_id)
        files = [{
            'hami_id': r['hami_id'],
            'number': str(r['number']),
            'subject': r.get('subject', ''),
            'reference_code': r.get('reference_code', ''),
            'name': r.get('name', ''),
            'first_date': r.get('first_date', ''),
            'last_date': r.get('last_date', ''),
            'request_id': r['id']
        } for r in requests_list]
        return jsonify({'files': files})
        
    except Exception as e:
        logger.error(f"Error in browse_database API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/database/download/<date_source>/<month>/<output_type>/<filename>')
@login_required
def download_database_file(date_source, month, output_type, filename):
    """Download a specific database file"""
    try:
        # Validate parameters
        if date_source not in ['first', 'last']:
            flash('Invalid date source', 'danger')
            return redirect(url_for('manage_database'))
        
        if output_type not in ['combined_output', 'hami_output']:
            flash('Invalid output type', 'danger')
            return redirect(url_for('manage_database'))
        
        # Construct file path
        file_path = config.DATABASE_FOLDER / date_source / month / output_type / filename
        
        if not file_path.exists():
            flash('File not found', 'danger')
            return redirect(url_for('manage_database'))
        
        # Send file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error downloading database file: {e}")
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('manage_database'))

@app.route('/api/search_by_date', methods=['GET'])
@login_required
def api_search_by_date():
    """Search combined files by date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Use SQLite-based search
        results = sqlite_search_by_date_range(start_date, end_date)
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        logger.error(f"Error in search_by_date API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_by_reference', methods=['GET'])
@login_required
def api_search_by_reference():
    """Search hami files by reference code"""
    try:
        reference_code = request.args.get('reference_code')
        
        if not reference_code:
            return jsonify({'error': 'reference_code is required'}), 400
        
        # Use SQLite-based search
        results = sqlite_search_by_reference(reference_code)
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        logger.error(f"Error in search_by_reference API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_by_field', methods=['GET'])
@login_required
def api_search_by_field():
    """Search hami files by various fields (subject, name, major, field, student_id, national_id)"""
    try:
        field_name = request.args.get('field_name')
        search_value = request.args.get('search_value')
        
        if not field_name:
            return jsonify({'error': 'field_name is required'}), 400
        
        if not search_value:
            return jsonify({'error': 'search_value is required'}), 400
        
        valid_fields = ['subject', 'name', 'major', 'field', 'student_id', 'national_id']
        if field_name not in valid_fields:
            return jsonify({'error': f'Invalid field_name. Must be one of: {", ".join(valid_fields)}'}), 400
        
        # Use SQLite-based search
        results = sqlite_search_by_field(field_name, search_value)
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        logger.error(f"Error in search_by_field API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_by_employee', methods=['GET'])
@login_required
def api_search_by_employee():
    """Search combined files by person name in 'from' and 'to' columns"""
    try:
        employee_name = request.args.get('employee_name')
        
        if not employee_name:
            return jsonify({'error': 'Person name is required'}), 400
        
        # Use SQLite-based search
        results = sqlite_search_by_employee(employee_name)
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        logger.error(f"Error in search_by_employee API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_search_results', methods=['POST'])
@login_required
def api_download_search_results():
    """Download all search results as a ZIP file.
    
    Expects JSON body with 'results' array containing search result objects.
    Each result should have: date_source, month, hami_id, number, combined_filename (optional)
    
    Creates a ZIP with:
    - All combined files (one per result)
    - Unique hami files (deduplicated by hami_id + month)
    """
    try:
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({'error': 'No results provided'}), 400
        
        results = data['results']
        
        if not results:
            return jsonify({'error': 'Empty results list'}), 400
        
        # Create ZIP file in memory
        memory_file = BytesIO()
        
        # Track unique hami files to avoid duplicates
        added_hami_files = set()
        files_added = 0
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for result in results:
                date_source = result.get('date_source', 'first')
                month = result.get('month')
                hami_id = result.get('hami_id')
                number = result.get('number')
                combined_filename = result.get('combined_filename') or result.get('filename')
                
                if not all([month, hami_id]):
                    continue
                
                # Add combined file if it exists
                if combined_filename:
                    combined_path = config.DATABASE_FOLDER / date_source / month / 'combined_output' / combined_filename
                    if combined_path.exists():
                        # Use folder structure in ZIP: combined_output/month/filename
                        arcname = f"combined_output/{month}/{combined_filename}"
                        zf.write(combined_path, arcname)
                        files_added += 1
                
                # Add hami file (only once per unique hami_id + month combination)
                hami_key = f"{date_source}/{month}/{hami_id}"
                if hami_key not in added_hami_files:
                    hami_filename = f"hami_{hami_id}.csv"
                    hami_path = config.DATABASE_FOLDER / date_source / month / 'hami_output' / hami_filename
                    if hami_path.exists():
                        # Use folder structure in ZIP: hami_output/month/filename
                        arcname = f"hami_output/{month}/{hami_filename}"
                        zf.write(hami_path, arcname)
                        added_hami_files.add(hami_key)
                        files_added += 1
        
        if files_added == 0:
            return jsonify({'error': 'No files found to download'}), 404
        
        memory_file.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'search_results_{timestamp}.zip'
        
        logger.info(f"User {session['username']} downloaded search results ({files_added} files, {len(results)} results)")
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        logger.error(f"Error in download_search_results API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_browse_files', methods=['POST'])
@login_required
def api_download_browse_files():
    """Download all files from browse view as a ZIP file.
    
    Expects JSON body with:
    - files: array of file objects with 'filename' property
    - date_source: 'first' or 'last'
    - month: the month folder name
    - output_type: 'combined_output' or 'hami_output'
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        files = data.get('files', [])
        date_source = data.get('date_source', 'first')
        month = data.get('month')
        output_type = data.get('output_type')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        if not month:
            return jsonify({'error': 'Month is required'}), 400
        
        if not output_type:
            return jsonify({'error': 'Output type is required'}), 400
        
        if date_source not in ['first', 'last']:
            return jsonify({'error': 'Invalid date_source'}), 400
        
        if output_type not in ['combined_output', 'hami_output']:
            return jsonify({'error': 'Invalid output_type'}), 400
        
        # Create ZIP file in memory
        memory_file = BytesIO()
        files_added = 0
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_info in files:
                filename = file_info.get('filename')
                if not filename:
                    continue
                
                file_path = config.DATABASE_FOLDER / date_source / month / output_type / filename
                
                if file_path.exists():
                    # Use folder structure in ZIP: output_type/month/filename
                    arcname = f"{output_type}/{month}/{filename}"
                    zf.write(file_path, arcname)
                    files_added += 1
        
        if files_added == 0:
            return jsonify({'error': 'No files found to download'}), 404
        
        memory_file.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'{output_type}_{month}_{timestamp}.zip'
        
        logger.info(f"User {session['username']} downloaded browse files ({files_added} files from {month}/{output_type})")
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        logger.error(f"Error in download_browse_files API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_duplicates', methods=['GET'])
@login_required
def api_check_duplicates():
    """Check for duplicate records by reference code"""
    try:
        detector = DuplicateDetector(config.DATABASE_FOLDER, 'first', db=db)
        summary = detector.get_duplicate_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error in check_duplicates API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_stats', methods=['GET'])
@login_required
def api_search_stats():
    """Get database statistics from SQLite."""
    try:
        stats = db.get_statistics()
        return jsonify({
            'unique_hamis': stats['unique_hamis'],
            'total_requests': stats['total_requests'],
            'total_messages': stats['total_messages'],
            'database_size': db.get_database_size()
        })
        
    except Exception as e:
        logger.error(f"Error in search_stats API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/handle_duplicates', methods=['POST'])
@login_required
def api_handle_duplicates():
    """Handle duplicate records based on user choice"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        action = data.get('action')  # 'keep_older', 'keep_newer', or 'manual'
        records_to_remove = data.get('records_to_remove', [])
        
        if not action:
            return jsonify({'error': 'action is required'}), 400
        
        detector = DuplicateDetector(config.DATABASE_FOLDER, 'first', db=db)
        
        if action == 'keep_older':
            # Get duplicates and keep older ones
            result = detector.keep_older()
            logger.info(f"Kept older duplicates: {result['removed_count']} records removed by {session['username']}")
            return jsonify({
                'success': True,
                'action': 'keep_older',
                'message': f'Removed {result["removed_count"]} newer duplicate records, keeping older ones.'
            })
        
        elif action == 'keep_newer':
            # Get duplicates and keep newer ones
            result = detector.keep_newer()
            logger.info(f"Kept newer duplicates: {result['removed_count']} records removed by {session['username']}")
            return jsonify({
                'success': True,
                'action': 'keep_newer',
                'message': f'Removed {result["removed_count"]} older duplicate records, keeping newer ones.'
            })
        
        elif action == 'manual':
            # Manually remove specified records
            if not records_to_remove:
                return jsonify({'error': 'records_to_remove is required for manual removal'}), 400
            
            result = detector.handle_manual_removal(records_to_remove)
            logger.info(f"Manually removed duplicates: {result['removed_count']} records removed by {session['username']}")
            return jsonify({
                'success': True,
                'action': 'manual',
                'message': f'Removed {result["removed_count"]} selected duplicate records.'
            })
        
        else:
            return jsonify({'error': 'Invalid action. Must be keep_older, keep_newer, or manual'}), 400
        
    except Exception as e:
        logger.error(f"Error in handle_duplicates API: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

# ==================== TEMPLATE TRANSFORMATION API ====================

@app.route('/api/transform_raw_template', methods=['POST'])
@login_required
def api_transform_raw_template():
    """
    Transform raw/uncleaned template data into standardized workflow format.
    
    This is a preprocessing step that converts user-provided raw data
    into the correct format that can then be used with the existing
    parse_workflow_text() and apply_workflow_text() functions.
    
    Request body:
    {
        "raw_template": "raw template text with uncleaned data"
    }
    
    Response:
    {
        "success": bool,
        "formatted_text": "standardized workflow text (ready to paste)",
        "entries": List of parsed entries,
        "errors": List of any parsing errors
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
        
        raw_template = data.get('raw_template', '').strip()
        
        if not raw_template:
            return jsonify({'error': 'raw_template is required', 'success': False}), 400
        
        # Transform the raw template
        result = transform_raw_template(raw_template)
        
        logger.info(f"Transformed template with {len(result.get('entries', []))} entries by {session['username']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error transforming template: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

# ==================== NO WORKFLOW API ROUTES ====================

@app.route('/api/no_workflow_requests', methods=['GET'])
@login_required
def api_no_workflow_requests():
    """Get list of requests with no workflow data."""
    try:
        requests_list = db.get_requests_with_no_workflow()
        count = db.get_no_workflow_count()
        
        return jsonify({
            'success': True,
            'requests': requests_list,
            'total_requests': count['requests'],
            'total_messages': count['messages']
        })
    except Exception as e:
        logger.error(f"Error getting no workflow requests: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/no_workflow_request_detail/<int:request_id>', methods=['GET'])
@login_required
def api_no_workflow_request_detail(request_id):
    """Get detailed information about a request for workflow editing."""
    try:
        detail = db.get_request_messages_detail(request_id)
        if not detail:
            return jsonify({'error': 'Request not found', 'success': False}), 404
        
        return jsonify({
            'success': True,
            'request': detail['request'],
            'messages': detail['messages']
        })
    except Exception as e:
        logger.error(f"Error getting request detail: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/update_workflow', methods=['POST'])
@login_required
def api_update_workflow():
    """Update workflow data for messages in a request."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
        
        request_id = data.get('request_id')
        workflow_updates = data.get('workflow_updates', [])
        
        if not request_id:
            return jsonify({'error': 'request_id is required', 'success': False}), 400
        
        if not workflow_updates:
            return jsonify({'error': 'workflow_updates is required', 'success': False}), 400
        
        # Update each message
        updated_count = db.bulk_update_messages_workflow(request_id, workflow_updates)
        
        logger.info(f"Updated {updated_count} messages workflow for request {request_id} by {session['username']}")
        
        return jsonify({
            'success': True,
            'message': f'Updated workflow for {updated_count} messages.',
            'updated_count': updated_count
        })
    except Exception as e:
        logger.error(f"Error updating workflow: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/apply_workflow_text', methods=['POST'])
@login_required
def api_apply_workflow_text():
    """
    Parse and apply workflow text to a request.
    The workflow text format:
    parent_id: None/1/2/...
    id: 1/2/3/...
    date: Persian date string
    name: sender/receiver name
    email: email address
    --------------------------------------------------
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'success': False}), 400
        
        request_id = data.get('request_id')
        workflow_text = data.get('workflow_text', '')
        
        if not request_id:
            return jsonify({'error': 'request_id is required', 'success': False}), 400
        
        if not workflow_text.strip():
            return jsonify({'error': 'workflow_text is required', 'success': False}), 400
        
        # Parse the workflow text
        entries = parse_workflow_text(workflow_text)
        
        if not entries:
            return jsonify({'error': 'Could not parse workflow text. Please check the format.', 'success': False}), 400
        
        # Apply the workflow
        result = db.apply_workflow_text(request_id, entries)
        
        logger.info(f"Applied workflow text to request {request_id}: {result['updated']} updated, {result['created']} created by {session['username']}")
        
        return jsonify({
            'success': True,
            'message': f"Applied workflow: {result['updated']} messages updated, {result['created']} messages created.",
            'updated': result['updated'],
            'created': result['created'],
            'errors': result['errors'],
            'details': result['details']
        })
    except Exception as e:
        logger.error(f"Error applying workflow text: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


def parse_workflow_text(text: str) -> list:
    """
    Parse workflow text into structured entries.
    
    Format:
    parent_id: None/1/2/...
    id: 1/2/3/...
    date: Persian date string
    name: sender/receiver name
    email: email address
    --------------------------------------------------
    """
    import re
    
    entries = []
    
    # Split by separator
    blocks = re.split(r'-{10,}', text)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        entry = {}
        lines = block.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse key: value format
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                if key == 'parent_id':
                    entry['parent_id'] = value if value.lower() != 'none' else None
                elif key == 'id':
                    entry['id'] = value
                elif key == 'date':
                    entry['date'] = value
                elif key == 'name':
                    entry['name'] = value
                elif key == 'email':
                    entry['email'] = value
        
        # Only add if we have the minimum required fields
        if entry.get('id') and entry.get('date'):
            entries.append(entry)
    
    return entries

@app.route('/api/search_request_by_reference', methods=['GET'])
@login_required
def api_search_request_by_reference():
    """Search for a request by reference code for workflow editing."""
    try:
        reference_code = request.args.get('reference_code', '').strip()
        
        if not reference_code:
            return jsonify({'error': 'reference_code is required', 'success': False}), 400
        
        request_data = db.get_request_by_reference(reference_code)
        
        if not request_data:
            return jsonify({
                'success': True,
                'found': False,
                'message': 'No request found with this reference code.'
            })
        
        # Get messages for this request
        messages = db.get_messages_for_request(request_data['id'])
        
        return jsonify({
            'success': True,
            'found': True,
            'request': request_data,
            'messages': messages
        })
    except Exception as e:
        logger.error(f"Error searching request by reference: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/preview_file', methods=['GET'])
@login_required
def api_preview_file():
    """Preview a database file as JSON for displaying in the browser.
    
    Can use request_id (SQLite) or hami_id + number.
    Returns the file content as JSON with metadata about columns and rows.
    Supports pagination for large files.
    """
    try:
        request_id = request.args.get('request_id', type=int)
        hami_id = request.args.get('hami_id')
        number = request.args.get('number')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get data from SQLite
        if request_id:
            req_data = db.get_request(request_id)
            if not req_data:
                return jsonify({'error': 'Request not found'}), 404
            messages = db.get_messages_for_request(request_id)
        elif hami_id and number:
            req_data = db.get_request_by_hami_number(hami_id, int(number))
            if not req_data:
                return jsonify({'error': 'Request not found'}), 404
            messages = db.get_messages_for_request(req_data['id'])
        else:
            return jsonify({'error': 'request_id or (hami_id and number) are required'}), 400
        
        # Get total rows
        total_rows = len(messages)
        total_pages = (total_rows + per_page - 1) // per_page if total_rows > 0 else 1
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_rows)
        messages_page = messages[start_idx:end_idx]
        
        # Format messages for display
        records = [{
            'date': m.get('date', ''),
            'message': m.get('message', ''),
            'from': m.get('from_name', ''),
            'to': m.get('to_name', ''),
            'to_email': m.get('to_email', ''),
            'from_id': m.get('from_id', ''),
            'to_id': m.get('to_id', ''),
            'matched': m.get('matched', False)
        } for m in messages_page]
        
        # Column info
        columns = ['date', 'message', 'from', 'to', 'to_email', 'from_id', 'to_id', 'matched']
        
        # Build global info from request data
        global_info = {
            'hami_id': req_data.get('hami_id', ''),
            'number': str(req_data.get('number', '')),
            'reference_code': req_data.get('reference_code', ''),
            'subject': req_data.get('subject', ''),
            'name': req_data.get('name', ''),
            'student_id': req_data.get('student_id', ''),
            'national_id': req_data.get('national_id', ''),
            'major': req_data.get('major', ''),
            'field': req_data.get('field', ''),
            'first_date': req_data.get('first_date', ''),
            'last_date': req_data.get('last_date', '')
        }
        
        response_data = {
            'success': True,
            'filename': f"combined_{req_data['hami_id']}_{req_data['number']}.csv",
            'file_type': 'combined',
            'hami_id': req_data['hami_id'],
            'number': str(req_data['number']),
            'columns': columns,
            'records': records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_rows': total_rows,
                'total_pages': total_pages,
                'start_row': start_idx + 1 if total_rows > 0 else 0,
                'end_row': end_idx
            },
            'global_info': global_info
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in preview_file API: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview_file_graph', methods=['GET'])
@login_required
def api_preview_file_graph():
    """Get graph data for combined_output files showing message flow.
    
    Returns nodes (unique senders/receivers) and edges (messages between them).
    """
    try:
        date_source = request.args.get('date_source', 'first')
        month = request.args.get('month')
        filename = request.args.get('filename')
        
        # Validate parameters
        if date_source not in ['first', 'last']:
            return jsonify({'error': 'Invalid date_source'}), 400
        
        if not all([month, filename]):
            return jsonify({'error': 'month and filename are required'}), 400
        
        # Construct file path (only combined_output supported for graph view)
        file_path = config.DATABASE_FOLDER / date_source / month / 'combined_output' / filename
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Clean up Excel formula markers
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].apply(lambda x: strip_excel_formula(x) if pd.notna(x) else x)
        
        # Build graph data
        nodes = {}  # id -> {id, label, type}
        edges = []  # {from, to, message, date}
        
        for _, row in df.iterrows():
            from_id = str(row.get('from_id', '')).strip()
            to_id = str(row.get('to_id', '')).strip()
            from_name = str(row.get('from', '')).strip()
            to_name = str(row.get('to', '')).strip()
            message = str(row.get('message', '')).strip()
            date = str(row.get('date', '')).strip()
            
            # Skip invalid entries
            skip_values = ['<empty>', 'Not in workflow', 'nan', '', 'NaN']
            if from_id in skip_values or to_id in skip_values:
                continue
            
            # Add sender node if not exists
            if from_id not in nodes:
                nodes[from_id] = {
                    'id': from_id,
                    'label': from_name if from_name not in skip_values else from_id[:8],
                    'title': from_name,
                    'messages_sent': 0,
                    'messages_received': 0
                }
            nodes[from_id]['messages_sent'] += 1
            
            # Add receiver node if not exists
            if to_id not in nodes:
                nodes[to_id] = {
                    'id': to_id,
                    'label': to_name if to_name not in skip_values else to_id[:8],
                    'title': to_name,
                    'messages_sent': 0,
                    'messages_received': 0
                }
            nodes[to_id]['messages_received'] += 1
            
            # Add edge
            edges.append({
                'from': from_id,
                'to': to_id,
                'message': message[:200] + '...' if len(message) > 200 else message,
                'date': date,
                'from_name': from_name,
                'to_name': to_name
            })
        
        # Convert nodes dict to list
        nodes_list = list(nodes.values())
        
        return jsonify({
            'success': True,
            'filename': filename,
            'date_source': date_source,
            'month': month,
            'nodes': nodes_list,
            'edges': edges,
            'stats': {
                'total_nodes': len(nodes_list),
                'total_edges': len(edges)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in preview_file_graph API: {e}")
        return jsonify({'error': str(e)}), 500

# Database navigation helper functions
def get_available_months(date_source):
    """Get list of available year-month folders for a date source"""
    months = []
    date_source_folder = config.DATABASE_FOLDER / date_source
    if date_source_folder.exists():
        for folder in sorted(date_source_folder.iterdir()):
            if folder.is_dir():
                months.append(folder.name)
    return months

def get_files_in_month(date_source, month, output_type):
    """Get list of files in a specific month folder"""
    files = []
    folder_path = config.DATABASE_FOLDER / date_source / month / output_type
    
    if not folder_path.exists():
        return files
    
    # Cache for hami data to avoid repeated file reads
    hami_cache = {}
    
    for file in sorted(folder_path.glob('*.csv')):
        file_info = {
            'filename': file.name,
            'size': f"{file.stat().st_size / 1024:.2f} KB",
            'date_source': date_source,
            'month': month,
            'output_type': output_type
        }
        
        # Extract hami_id and number from filename
        if output_type == 'combined_output' and file.name.startswith('combined_'):
            parts = file.stem.split('_')
            if len(parts) == 3:
                file_info['hami_id'] = parts[1]
                file_info['number'] = parts[2]
                
                # Fetch reference_code and subject from corresponding hami file
                hami_info = get_hami_info_for_combined(date_source, month, file_info['hami_id'], file_info['number'], hami_cache)
                file_info['reference_code'] = hami_info.get('reference_code', '')
                file_info['subject'] = hami_info.get('subject', '')
                
        elif output_type == 'hami_output' and file.name.startswith('hami_'):
            parts = file.stem.split('_')
            if len(parts) == 2:
                file_info['hami_id'] = parts[1]
        
        files.append(file_info)
    
    return files


def get_hami_info_for_combined(date_source, month, hami_id, number, hami_cache=None):
    """
    Get reference_code and subject from hami file for a combined file.
    
    Args:
        date_source: 'first' or 'last'
        month: the month folder (e.g., '1404-07')
        hami_id: the hami ID (e.g., '105012')
        number: the request number (e.g., '58')
        hami_cache: optional dictionary to cache hami file data
        
    Returns:
        dict with 'reference_code' and 'subject' keys
    """
    if hami_cache is None:
        hami_cache = {}
    
    cache_key = f"{date_source}_{month}_{hami_id}"
    
    # Check cache first
    if cache_key not in hami_cache:
        hami_file_path = config.DATABASE_FOLDER / date_source / month / 'hami_output' / f'hami_{hami_id}.csv'
        
        if hami_file_path.exists():
            try:
                df = pd.read_csv(hami_file_path)
                # Store entire dataframe in cache
                hami_cache[cache_key] = df
            except Exception as e:
                logger.error(f"Error reading hami file {hami_file_path}: {e}")
                hami_cache[cache_key] = None
        else:
            hami_cache[cache_key] = None
    
    # Get data from cache
    df = hami_cache.get(cache_key)
    
    if df is None:
        return {'reference_code': '', 'subject': ''}
    
    try:
        # Find the row with matching number
        number_int = int(number)
        matching_rows = df[df['number'] == number_int]
        
        if len(matching_rows) > 0:
            row = matching_rows.iloc[0]
            reference_code = str(row.get('reference_code', '')).strip()
            subject = str(row.get('subject', '')).strip()
            
            # Clean up Excel formula markers like ="value"
            reference_code = strip_excel_formula(reference_code)
            subject = strip_excel_formula(subject)
            
            return {'reference_code': reference_code, 'subject': subject}
    except Exception as e:
        logger.error(f"Error finding number {number} in hami {hami_id}: {e}")
    
    return {'reference_code': '', 'subject': ''}


def get_full_hami_info_for_combined(date_source, month, hami_id, number):
    """
    Get all fields from hami file for a combined file (used for preview global info).
    
    Args:
        date_source: 'first' or 'last'
        month: the month folder (e.g., '1404-07')
        hami_id: the hami ID (e.g., '105012')
        number: the request number (e.g., '58')
        
    Returns:
        dict with all hami fields or None if not found
    """
    hami_file_path = config.DATABASE_FOLDER / date_source / month / 'hami_output' / f'hami_{hami_id}.csv'
    
    if not hami_file_path.exists():
        return None
    
    try:
        df = pd.read_csv(hami_file_path)
        
        # Find the row with matching number
        number_int = int(number)
        matching_rows = df[df['number'] == number_int]
        
        if len(matching_rows) == 0:
            return None
        
        row = matching_rows.iloc[0]
        
        # Build result with all fields, cleaning Excel formula markers
        result = {
            'hami_id': hami_id,
            'number': number
        }
        
        # Add all columns from the hami file
        for col in df.columns:
            value = row.get(col, '')
            if pd.isna(value):
                value = ''
            else:
                value = str(value).strip()
                value = strip_excel_formula(value)
            result[col] = value
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting full hami info for {hami_id}/{number}: {e}")
        return None


def parse_combined_file_dates(file_path):
    """Parse dates from a combined file"""
    try:
        import pandas as pd
        import jdatetime
        
        df = pd.read_csv(file_path)
        if 'date' not in df.columns:
            return None, None
        
        # Filter out dummy dates (year 1500)
        valid_dates = []
        for date_str in df['date']:
            if date_str and '1500-01-01' not in date_str:
                try:
                    date_obj = jdatetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    valid_dates.append(date_obj)
                except:
                    pass
        
        if valid_dates:
            return min(valid_dates), max(valid_dates)
        return None, None
    except Exception as e:
        logger.error(f"Error parsing dates from {file_path}: {e}")
        return None, None

def search_hami_by_reference(reference_code, date_source):
    """Search all hami files for a specific reference code"""
    results = []
    date_source_folder = config.DATABASE_FOLDER / date_source
    
    if not date_source_folder.exists():
        return results
    
    import pandas as pd
    
    # Search through all months
    for month_folder in date_source_folder.iterdir():
        if not month_folder.is_dir():
            continue
        
        hami_folder = month_folder / 'hami_output'
        if not hami_folder.exists():
            continue
        
        # Search through all hami files
        for hami_file in hami_folder.glob('hami_*.csv'):
            try:
                df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                if 'reference_code' not in df.columns:
                    continue
                
                # Find matching reference codes (strip Excel formula format for comparison)
                matches = df[df['reference_code'].apply(strip_excel_formula) == strip_excel_formula(reference_code)]
                
                for _, row in matches.iterrows():
                    hami_id = hami_file.stem.replace('hami_', '')
                    number = row['number']
                    
                    # Check if corresponding combined file exists
                    combined_file = month_folder / 'combined_output' / f'combined_{hami_id}_{number}.csv'
                    
                    result = {
                        'hami_id': hami_id,
                        'number': str(number),
                        'month': month_folder.name,
                        'date_source': date_source,
                        'subject': row.get('subject', 'N/A'),
                        'reference_code': strip_excel_formula(row.get('reference_code', 'N/A')),
                        'major': row.get('major', 'N/A'),
                        'name': row.get('name', 'N/A'),
                        'combined_exists': combined_file.exists(),
                        'combined_filename': f'combined_{hami_id}_{number}.csv' if combined_file.exists() else None
                    }
                    results.append(result)
            except Exception as e:
                logger.error(f"Error searching {hami_file}: {e}")
                continue
    
    return results

def search_hami_by_field(field_name, search_value, date_source):
    """Search all hami files by a specific field (subject, name, major, field, student_id, national_id)"""
    results = []
    date_source_folder = config.DATABASE_FOLDER / date_source
    
    if not date_source_folder.exists():
        return results
    
    import pandas as pd
    
    # Validate field name
    valid_fields = ['subject', 'name', 'major', 'field', 'student_id', 'national_id']
    if field_name not in valid_fields:
        return results
    
    # Normalize search value
    search_value_lower = str(search_value).lower().strip()
    
    # Try to convert to int for numeric fields
    search_value_int = None
    if field_name in ['student_id', 'national_id']:
        try:
            search_value_int = int(search_value)
        except (ValueError, TypeError):
            pass
    
    # Search through all months
    for month_folder in date_source_folder.iterdir():
        if not month_folder.is_dir():
            continue
        
        hami_folder = month_folder / 'hami_output'
        if not hami_folder.exists():
            continue
        
        # Search through all hami files
        for hami_file in hami_folder.glob('hami_*.csv'):
            try:
                df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                if field_name not in df.columns:
                    continue
                
                # Find matches (partial match for text fields, exact for numeric)
                matches = pd.DataFrame()
                
                if field_name in ['student_id', 'national_id']:
                    # Handle numeric fields - strip Excel formula format and search
                    df_stripped = df[field_name].apply(strip_excel_formula)
                    if search_value_int is not None:
                        matches = df[df_stripped == str(search_value_int)]
                    if len(matches) == 0:
                        # Also try string comparison in case format differs
                        matches = df[df_stripped.astype(str).str.contains(search_value_lower, na=False, regex=False)]
                else:
                    # Partial/fuzzy match for text fields
                    matches = df[df[field_name].astype(str).str.lower().str.contains(search_value_lower, na=False)]
                
                for _, row in matches.iterrows():
                    hami_id = hami_file.stem.replace('hami_', '')
                    number = row['number']
                    
                    # Check if corresponding combined file exists
                    combined_file = month_folder / 'combined_output' / f'combined_{hami_id}_{number}.csv'
                    
                    result = {
                        'hami_id': hami_id,
                        'number': str(number),
                        'month': month_folder.name,
                        'date_source': date_source,
                        'subject': row.get('subject', 'N/A'),
                        'reference_code': strip_excel_formula(row.get('reference_code', 'N/A')),
                        'major': row.get('major', 'N/A'),
                        'name': row.get('name', 'N/A'),
                        'field': row.get('field', 'N/A'),
                        'student_id': strip_excel_formula(row.get('student_id', 'N/A')),
                        'national_id': strip_excel_formula(row.get('national_id', 'N/A')),
                        'combined_exists': combined_file.exists(),
                        'combined_filename': f'combined_{hami_id}_{number}.csv' if combined_file.exists() else None
                    }
                    results.append(result)
            except Exception as e:
                logger.error(f"Error searching {hami_file}: {e}")
                continue
    
    return results

def search_by_date_range(date_source, start_date, end_date):
    """Search combined files within a date range"""
    results = []
    date_source_folder = config.DATABASE_FOLDER / date_source
    
    if not date_source_folder.exists():
        return results
    
    import pandas as pd
    import jdatetime
    
    # Parse dates
    try:
        if start_date:
            start_dt = jdatetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_dt = None
            
        if end_date:
            end_dt = jdatetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_dt = None
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        return results
    
    # Search through all months
    for month_folder in date_source_folder.iterdir():
        if not month_folder.is_dir():
            continue
        
        combined_folder = month_folder / 'combined_output'
        if not combined_folder.exists():
            continue
        
        # Search through all combined files
        for combined_file in combined_folder.glob('combined_*.csv'):
            try:
                first_date, last_date = parse_combined_file_dates(combined_file)
                
                if first_date is None or last_date is None:
                    continue
                
                # Check if file falls within date range
                include = True
                if start_dt and last_date < start_dt:
                    include = False
                if end_dt and first_date >= end_dt:
                    include = False
                
                if include:
                    parts = combined_file.stem.split('_')
                    if len(parts) == 3:
                        hami_id = parts[1]
                        number = parts[2]
                        
                        # Get additional info from hami file if exists
                        hami_file = month_folder / 'hami_output' / f'hami_{hami_id}.csv'
                        hami_info = {}
                        
                        if hami_file.exists():
                            try:
                                hami_df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                                matching_row = hami_df[hami_df['number'] == int(number)]
                                if len(matching_row) > 0:
                                    hami_info = matching_row.iloc[0].to_dict()
                            except:
                                pass
                        
                        result = {
                            'hami_id': hami_id,
                            'number': number,
                            'month': month_folder.name,
                            'date_source': date_source,
                            'filename': combined_file.name,
                            'first_date': first_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'last_date': last_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'subject': hami_info.get('subject', 'N/A'),
                            'reference_code': strip_excel_formula(hami_info.get('reference_code', 'N/A')),
                            'name': hami_info.get('name', 'N/A'),
                            'size': f"{combined_file.stat().st_size / 1024:.2f} KB"
                        }
                        results.append(result)
            except Exception as e:
                logger.error(f"Error processing {combined_file}: {e}")
                continue
    
    return results

def search_by_employee(employee_name, date_source):
    """Search combined files by person name in 'from' and 'to' columns.
    
    This searches through all combined files looking for the person name
    in either the 'from' or 'to' column, then returns matching combined files
    along with their related hami data.
    
    Args:
        employee_name: The name (or partial name) of the person to search for
        date_source: Either 'first' or 'last'
    
    Returns:
        List of results with combined file info and related hami data
    """
    results = []
    date_source_folder = config.DATABASE_FOLDER / date_source
    
    if not date_source_folder.exists():
        return results
    
    import pandas as pd
    
    # Normalize search value
    search_value_lower = str(employee_name).lower().strip()
    
    if not search_value_lower:
        return results
    
    # Search through all months
    for month_folder in date_source_folder.iterdir():
        if not month_folder.is_dir():
            continue
        
        combined_folder = month_folder / 'combined_output'
        hami_folder = month_folder / 'hami_output'
        
        if not combined_folder.exists():
            continue
        
        # Search through all combined files
        for combined_file in combined_folder.glob('combined_*.csv'):
            try:
                df = pd.read_csv(combined_file)
                
                # Check if 'from' or 'to' columns exist
                has_from = 'from' in df.columns
                has_to = 'to' in df.columns
                
                if not has_from and not has_to:
                    continue
                
                # Search for the employee name in 'from' and 'to' columns
                from_match = False
                to_match = False
                matched_from_values = set()
                matched_to_values = set()
                
                if has_from:
                    from_matches = df[df['from'].astype(str).str.lower().str.contains(search_value_lower, na=False)]
                    if len(from_matches) > 0:
                        from_match = True
                        matched_from_values = set(from_matches['from'].dropna().unique())
                
                if has_to:
                    to_matches = df[df['to'].astype(str).str.lower().str.contains(search_value_lower, na=False)]
                    if len(to_matches) > 0:
                        to_match = True
                        matched_to_values = set(to_matches['to'].dropna().unique())
                
                if not from_match and not to_match:
                    continue
                
                # Extract hami_id and number from filename
                parts = combined_file.stem.split('_')
                if len(parts) != 3:
                    continue
                
                hami_id = parts[1]
                number = parts[2]
                
                # Get related hami data
                hami_info = {}
                hami_file = hami_folder / f'hami_{hami_id}.csv'
                
                if hami_file.exists():
                    try:
                        hami_df = pd.read_csv(hami_file, dtype={'reference_code': str, 'national_id': str, 'student_id': str})
                        matching_row = hami_df[hami_df['number'] == int(number)]
                        if len(matching_row) > 0:
                            hami_info = matching_row.iloc[0].to_dict()
                    except Exception as e:
                        logger.error(f"Error reading hami file {hami_file}: {e}")
                
                # Get date range from combined file
                first_date, last_date = parse_combined_file_dates(combined_file)
                
                # Combine matched values for display
                all_matched_names = matched_from_values | matched_to_values
                
                result = {
                    'hami_id': hami_id,
                    'number': number,
                    'month': month_folder.name,
                    'date_source': date_source,
                    'filename': combined_file.name,
                    'first_date': first_date.strftime('%Y-%m-%d %H:%M:%S') if first_date else 'N/A',
                    'last_date': last_date.strftime('%Y-%m-%d %H:%M:%S') if last_date else 'N/A',
                    # Hami info
                    'subject': hami_info.get('subject', 'N/A'),
                    'reference_code': strip_excel_formula(hami_info.get('reference_code', 'N/A')),
                    'major': hami_info.get('major', 'N/A'),
                    'name': hami_info.get('name', 'N/A'),  # Student name from hami
                    'student_id': strip_excel_formula(hami_info.get('student_id', 'N/A')),
                    'national_id': strip_excel_formula(hami_info.get('national_id', 'N/A')),
                    'field': hami_info.get('field', 'N/A'),
                    # Match info
                    'match_type': 'both' if (from_match and to_match) else ('from' if from_match else 'to'),
                    'matched_from': list(matched_from_values)[:3],  # Limit to first 3 for display
                    'matched_to': list(matched_to_values)[:3],
                    'matched_employees': list(all_matched_names)[:5],  # Combined list for display
                    'combined_exists': True,
                    'combined_filename': combined_file.name,
                    'size': f"{combined_file.stat().st_size / 1024:.2f} KB"
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error searching {combined_file}: {e}")
                continue
    
    return results

# Helper functions
def get_database_stats():
    """Get database statistics using SQLite.
    
    Returns simplified structure for SQLite-only mode:
    stats.hamis, stats.requests, stats.messages, stats.size
    """
    stats = {
        'hamis': 0,
        'requests': 0,
        'messages': 0,
        'size': '0.00 MB',
        'date_range': {},
        'requests_per_hami': {},
        'sqlite_enabled': True
    }
    
    try:
        db_stats = db.get_statistics()
        db_size = db.get_database_size()
        
        # Populate SQLite-based stats
        stats['hamis'] = db_stats['unique_hamis']
        stats['requests'] = db_stats['total_requests']
        stats['messages'] = db_stats['total_messages']
        stats['size'] = db_size
        stats['date_range'] = db_stats.get('date_range', {})
        stats['requests_per_hami'] = db_stats.get('requests_per_hami', {})
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
    
    return stats


# SQLite-based search functions
def sqlite_search_by_reference(reference_code):
    """Search requests by reference code using SQLite"""
    try:
        results = db.search_requests_by_reference(reference_code)
        return [{
            'hami_id': r['hami_id'],
            'number': str(r['number']),
            'subject': r.get('subject', 'N/A'),
            'reference_code': r.get('reference_code', 'N/A'),
            'major': r.get('major', 'N/A'),
            'name': r.get('name', 'N/A'),
            'student_id': r.get('student_id', 'N/A'),
            'national_id': r.get('national_id', 'N/A'),
            'field': r.get('field', 'N/A'),
            'first_date': r.get('first_date', 'N/A'),
            'last_date': r.get('last_date', 'N/A'),
            'request_id': r['id'],
            'combined_exists': True  # SQLite ensures data integrity
        } for r in results]
    except Exception as e:
        logger.error(f"Error in sqlite_search_by_reference: {e}")
        return []


def sqlite_search_by_field(field_name, search_value):
    """Search requests by field using SQLite"""
    try:
        results = db.search_requests_by_field(field_name, search_value)
        return [{
            'hami_id': r['hami_id'],
            'number': str(r['number']),
            'subject': r.get('subject', 'N/A'),
            'reference_code': r.get('reference_code', 'N/A'),
            'major': r.get('major', 'N/A'),
            'name': r.get('name', 'N/A'),
            'student_id': r.get('student_id', 'N/A'),
            'national_id': r.get('national_id', 'N/A'),
            'field': r.get('field', 'N/A'),
            'first_date': r.get('first_date', 'N/A'),
            'last_date': r.get('last_date', 'N/A'),
            'request_id': r['id'],
            'combined_exists': True
        } for r in results]
    except Exception as e:
        logger.error(f"Error in sqlite_search_by_field: {e}")
        return []


def sqlite_search_by_date_range(start_date=None, end_date=None):
    """Search requests by date range using SQLite"""
    try:
        results = db.get_requests_by_date_range(start_date, end_date)
        return [{
            'hami_id': r['hami_id'],
            'number': str(r['number']),
            'subject': r.get('subject', 'N/A'),
            'reference_code': r.get('reference_code', 'N/A'),
            'name': r.get('name', 'N/A'),
            'first_date': r.get('first_date', 'N/A'),
            'last_date': r.get('last_date', 'N/A'),
            'request_id': r['id'],
            'combined_exists': True
        } for r in results]
    except Exception as e:
        logger.error(f"Error in sqlite_search_by_date_range: {e}")
        return []


def sqlite_search_by_employee(employee_name):
    """Search messages by employee name using SQLite"""
    try:
        results = db.search_messages_by_person(employee_name)
        
        # Group by request to avoid duplicates
        request_results = {}
        for r in results:
            request_id = r['request_id']
            if request_id not in request_results:
                request_results[request_id] = {
                    'hami_id': r['hami_id'],
                    'number': str(r['number']),
                    'subject': r.get('subject', 'N/A'),
                    'reference_code': r.get('reference_code', 'N/A'),
                    'name': r.get('student_name', 'N/A'),
                    'request_id': request_id,
                    'combined_exists': True,
                    'matched_employees': set()
                }
            
            if r.get('from_name') and employee_name.lower() in r['from_name'].lower():
                request_results[request_id]['matched_employees'].add(r['from_name'])
            if r.get('to_name') and employee_name.lower() in r['to_name'].lower():
                request_results[request_id]['matched_employees'].add(r['to_name'])
        
        # Convert sets to lists
        for r in request_results.values():
            r['matched_employees'] = list(r['matched_employees'])[:5]
        
        return list(request_results.values())
    except Exception as e:
        logger.error(f"Error in sqlite_search_by_employee: {e}")
        return []


def sqlite_get_all_hamis():
    """Get list of all unique hami IDs"""
    try:
        return db.get_unique_hami_ids()
    except Exception as e:
        logger.error(f"Error getting hami list: {e}")
        return []


def sqlite_get_requests_for_hami(hami_id):
    """Get all requests for a hami ID"""
    try:
        return db.get_requests_by_hami(hami_id)
    except Exception as e:
        logger.error(f"Error getting requests for hami {hami_id}: {e}")
        return []


def sqlite_get_request_details(hami_id, number):
    """Get request details and messages"""
    try:
        request = db.get_request_by_hami_number(hami_id, int(number))
        if not request:
            return None
        
        messages = db.get_messages_for_request(request['id'])
        return {
            'request': request,
            'messages': messages
        }
    except Exception as e:
        logger.error(f"Error getting request details for {hami_id}/{number}: {e}")
        return None


def sqlite_get_request_by_id(request_id):
    """Get request by ID"""
    try:
        return db.get_request(request_id)
    except Exception as e:
        logger.error(f"Error getting request {request_id}: {e}")
        return None


def sqlite_get_messages_for_request(request_id):
    """Get messages for a request ID"""
    try:
        return db.get_messages_for_request(request_id)
    except Exception as e:
        logger.error(f"Error getting messages for request {request_id}: {e}")
        return []

def auto_detect_i_values(folder):
    """Auto-detect i values from uploaded files"""
    i_values = set()
    
    # Search in the folder and all subfolders for file_*.txt
    for file in folder.rglob('file_*.txt'):
        try:
            parts = file.stem.split('_')
            if len(parts) >= 2:
                i_values.add(int(parts[1]))
        except:
            pass
    
    logger.info(f"Auto-detected i_values in {folder}: {sorted(list(i_values))}")
    return sorted(list(i_values))

def clear_folder(folder):
    """Clear all files in a folder"""
    if folder.exists():
        for file in folder.glob('*'):
            if file.is_file():
                file.unlink()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5001)
