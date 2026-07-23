from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session, send_file, jsonify
import os
import sys
import logging
import jdatetime
from werkzeug.utils import secure_filename
from functools import wraps

# Import refactored models
from models.processors.generic_processor import GenericProcessor
from models.processors.ppk_processor import PPKProcessor
from models.processors.csdp_processor import CSDPProcessor
from models.processors.distance_processor import DistanceProcessor
from models.processors.distance2_processor import Distance2Processor
from culvert.processors.culvert_processor import CulvertProcessor
from models.auth.auth_manager import AuthManager
from models.analytics.statistics_manager import StatisticsManager
from models.utils.file_manager import FileManager

# Backward compatibility
Generic_DataLoader = GenericProcessor
PPK_Processing_Result_DataLoader = PPKProcessor
CSDP_DataLoader = CSDPProcessor
Delete_Distance_From_Centerline = DistanceProcessor
Dataloader_Distance = Distance2Processor

import pandas as pd
from datetime import datetime

# r'/home/Keivan01/mysite/Files/send_to_others'
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging for production (Gunicorn)
if not app.debug:
    # Log to stderr (captured by Gunicorn/systemd)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    
    # Also log to file for detailed debugging
    log_dir = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)

# Log startup
app.logger.info('Flask application starting up...')

app.config['UPLOAD_FOLDER_SEND'] = os.path.join(BASE_DIR, 'Files', 'send_to_others')
app.config['UPLOAD_FOLDER_RECEIVED'] = os.path.join(BASE_DIR, 'Files', 'received_from_others')
app.config['UPLOAD_FOLDER_SHARE'] = os.path.join(BASE_DIR, 'Files', 'share')
app.config['RESULT_DIR'] = os.path.join(BASE_DIR, 'Files', 'result')
app.config['APP_FOLDER'] = os.path.join(BASE_DIR, 'Files', 'apps')
app.config['STATISTIC'] = os.path.join(BASE_DIR, 'Files', 'statistic')
app.secret_key = 'supersecretkey'

# Initialize managers
auth_manager = AuthManager(os.path.join(BASE_DIR, 'data', 'users.csv'))
stats_manager = StatisticsManager(app.config['STATISTIC'])
file_manager = FileManager(BASE_DIR)

# Tool configuration with icons and descriptions
TOOL_CONFIG = {
    'connect': {'name': 'tool_connect', 'icon': '🔌', 'url': 'connect', 'description': 'tool_connect_desc'},
    'share': {'name': 'tool_share', 'icon': '📁', 'url': 'share_files', 'description': 'tool_share_desc'},
    'generic': {'name': 'tool_generic', 'icon': '📊', 'url': 'generic_processing', 'description': 'tool_generic_desc'},
    'ppk': {'name': 'tool_ppk', 'icon': '📡', 'url': 'PPK_processing', 'description': 'tool_ppk_desc'},
    'csdp': {'name': 'tool_csdp', 'icon': '🗺️', 'url': 'CSDP_processing', 'description': 'tool_csdp_desc'},
    'delete_distance': {'name': 'tool_delete_distance', 'icon': '📏', 'url': 'delete_empty_processing', 'description': 'tool_delete_distance_desc'},
    'distance2': {'name': 'tool_distance2', 'icon': '📐', 'url': 'distance2_processing', 'description': 'tool_distance2_desc'},
    'culvert': {'name': 'tool_culvert', 'icon': '🌉', 'url': 'culvert_processing', 'description': 'tool_culvert_desc'}
}

# Helper function to check if user is logged in
def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this tool', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check tool access
def check_tool_access(tool_key):
    """Check if the logged-in user has access to a specific tool"""
    if 'user_email' not in session:
        return False
    
    allowed_tools = session.get('allowed_tools', [])
    # If no tools specified, user has access to all
    if not allowed_tools:
        return True
    
    return tool_key in allowed_tools

# Initialize old statistics tracking (will be deprecated in favor of StatisticsManager)
ITEMS_LIST = ['Connect to Me', 'Share Files', 'Generic Processing', 'PPK Processing', 'CSDP Processing', 'Image Processing',
         'Delete Empty Processing', 'Distance2 Processing', 'Culvert Processing', 'Chat-GPT']

def initialize_history_version():
    # List all history files
    existing_files = [f for f in os.listdir(app.config['STATISTIC']) if f.startswith('history_V') and f.endswith('.csv')]
    
    # Extract version numbers from filenames
    if existing_files:
        max_version = max(int(f.split('_V')[1].split('.csv')[0]) for f in existing_files)
    else:
        max_version = -1  # If no files exist, start from -1

    return max_version
            
def add_to_history(name, logged_in):
    """Legacy statistics function - will be replaced by StatisticsManager"""
    file = app.config['STATISTIC']+f"/history_V{initialize_history_version()}.csv"
    if logged_in == 0:
        logged_in = "Logged-in Properly"
    elif logged_in == 1:
        logged_in = "Password Incorrect"
    elif logged_in == 2:
        logged_in = "Bad inputs"
    elif logged_in == 3:
        logged_in = name
    try:
        data = pd.read_csv(file, index_col=0)
        if len(data.columns) != len(ITEMS_LIST)+4:
            raise
    except:
        data = pd.DataFrame(0, index=range(1), columns=["Date", "IP Address", "logged-in"]+ITEMS_LIST+["Downloads"])
        file = app.config['STATISTIC']+f"/history_V{initialize_history_version()+1}.csv"
    
    if name == 'Connect to Me':
        r = 1
    elif name == 'Share Files':
        r = 2
    elif name == 'Generic Processing':
        r = 3
    elif name == 'PPK Processing':
        r = 4
    elif name == 'CSDP Processing':
        r = 5
    elif name == 'Image Processing':
        r = 6
    elif name == 'Delete Empty Processing':
        r = 7
    elif name == 'Distance2 Processing':
        r = 8
    elif name == 'Culvert Processing':
        r = 9
    elif name == 'Chat-GPT':
        r = 10
    else:
        r = 11

    new_row = [datetime.now().strftime("%Y/%m/%d | %H:%M:%S"), request.remote_addr, logged_in] + [1 if _ == r else 0 for _ in range(1, len(ITEMS_LIST)+1)] + [1 if r==11 else 0]
    data.loc[len(data)] = new_row
    
    # Convert numeric columns to int before summing
    numeric_cols = data.columns[3:]  # Skip first 3 columns (Date, IP, logged-in)
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
    
    data.iloc[0, 3:] = data.iloc[1:, 3:].sum().values
    data.iloc[0, :3] = len(data) - 1
    data.to_csv(file)

@app.route('/')
def index():
    # Get user's allowed tools if logged in
    tools = []
    if session.get('user_email'):
        user_tools = session.get('allowed_tools', [])
        for tool_key, tool_info in TOOL_CONFIG.items():
            if tool_key in user_tools or not user_tools:  # Show all if no restrictions
                tools.append({
                    'name': tool_info['name'],
                    'icon': tool_info['icon'],
                    'url': url_for(tool_info['url']),
                    'description': tool_info.get('description', '')
                })
    else:
        # Show all tools for non-logged in users (they'll need password at tool level)
        for tool_key, tool_info in TOOL_CONFIG.items():
            tools.append({
                'name': tool_info['name'],
                'icon': tool_info['icon'],
                'url': url_for(tool_info['url']),
                'description': tool_info.get('description', '')
            })
    
    return render_template('index.html', tools=tools)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = auth_manager.authenticate_user(email, password)
        if user:
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            session['allowed_tools'] = user['allowed_tools']
            stats_manager.add_to_history('Login', email, user['name'], request.remote_addr)
            flash('Welcome back, {}!'.format(user['name']), 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
            stats_manager.add_to_history('Failed Login', email if email else 'Unknown', 'Unknown', request.remote_addr)
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    email = session.get('user_email', 'Unknown')
    name = session.get('user_name', 'Unknown')
    stats_manager.add_to_history('Logout', email, name, request.remote_addr)
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_email' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 4:
            flash('Password must be at least 4 characters', 'error')
            return redirect(url_for('change_password'))
        
        email = session['user_email']
        if auth_manager.change_password(email, old_password, new_password):
            stats_manager.add_to_history('Password Changed', email, session.get('user_name'), request.remote_addr)
            flash('Password changed successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Current password is incorrect', 'error')
    
    return render_template('auth/change_password.html')

def handle_file_download(folder, filename=None):
    if filename:
        file_path = os.path.join(folder, filename)
        return send_file(file_path, as_attachment=True)
    else:
        files = os.listdir(folder)
        return render_template('download.html', files=files)

@app.route('/download', defaults={'filename': None, 'folder': None})
@app.route('/download/<folder>/<filename>')
def download_file(filename, folder):
    add_to_history(name=filename, logged_in=3)
    return handle_file_download(app.config[folder], filename)

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        if not files or all(file.filename == '' for file in files):
            flash('No selected file')
            return redirect(request.url)
        upload_folder = app.config['UPLOAD_FOLDER_RECEIVED']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
        flash('Files successfully uploaded')
        return redirect(request.url)
    return render_template('index.html')

@app.route('/share', methods=['GET', 'POST'], defaults={'filename': None})
@app.route('/share/<filename>')
@login_required
def share_files(filename):
    # Check tool access
    if not check_tool_access('share'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Handle file upload
        if 'files[]' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        if not files or all(file.filename == '' for file in files):
            flash('No selected file', 'error')
            return redirect(request.url)
        upload_folder = app.config['UPLOAD_FOLDER_SHARE']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        for file in files:
            if file and file.filename != '':
                filename_secure = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename_secure))
        
        # Track activity
        stats_manager.add_to_history(
            'Share Files', 
            session.get('user_email'), 
            session.get('user_name'), 
            request.remote_addr
        )
        add_to_history(name="Share Files", logged_in=0)
        
        flash('Files successfully uploaded', 'success')
        return redirect(url_for('share_files'))

    # Handle file download
    if filename:
        add_to_history(name=filename, logged_in=3)
        return download_file('UPLOAD_FOLDER_SHARE', filename)
    else:
        # Build file list with metadata
        upload_folder = app.config['UPLOAD_FOLDER_SHARE']
        file_list = []
        if os.path.exists(upload_folder):
            for fname in sorted(os.listdir(upload_folder)):
                fpath = os.path.join(upload_folder, fname)
                if os.path.isfile(fpath):
                    stat = os.stat(fpath)
                    size_bytes = stat.st_size
                    # Human-readable size
                    if size_bytes < 1024:
                        size_str = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    else:
                        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    # Upload date in Persian calendar
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    jalali_date = jdatetime.datetime.fromgregorian(datetime=mod_time)
                    date_str = jalali_date.strftime("%Y/%m/%d - %H:%M")
                    # File extension / type
                    _, ext = os.path.splitext(fname)
                    file_type = ext.lstrip('.').upper() if ext else 'FILE'
                    file_list.append({
                        'name': fname,
                        'size': size_str,
                        'date': date_str,
                        'type': file_type,
                    })
        return render_template('share.html', files=file_list)


@app.route('/share/delete', methods=['POST'])
@login_required
def share_delete_file():
    """Delete a shared file after verifying the privilege password."""
    if not check_tool_access('share'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    password = data.get('password', '')
    filenames = data.get('filenames', [])

    if not filenames:
        return jsonify({'success': False, 'message': 'No files specified'}), 400

    # Read privilege password from file
    password_file = os.path.join(BASE_DIR, 'data', 'share_password.txt')
    try:
        with open(password_file, 'r') as f:
            correct_password = f.read().strip()
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'Password file not configured'}), 500

    if password != correct_password:
        return jsonify({'success': False, 'message': 'Incorrect password'}), 403

    upload_folder = app.config['UPLOAD_FOLDER_SHARE']
    deleted = []
    failed = []
    for fname in filenames:
        safe_name = secure_filename(fname)
        fpath = os.path.join(upload_folder, safe_name)
        if os.path.isfile(fpath):
            try:
                os.remove(fpath)
                deleted.append(safe_name)
            except OSError:
                failed.append(safe_name)
        else:
            failed.append(safe_name)

    # Track activity
    stats_manager.add_to_history(
        f'Share Delete ({len(deleted)} files)',
        session.get('user_email'),
        session.get('user_name'),
        request.remote_addr
    )

    return jsonify({
        'success': True,
        'deleted': deleted,
        'failed': failed,
        'message': f'{len(deleted)} file(s) deleted successfully'
    })

    
@app.route('/connect', methods=['GET', 'POST'])
@login_required
def connect():
    # Check tool access
    if not check_tool_access('connect'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    # Track activity
    stats_manager.add_to_history(
        'Connect to Me', 
        session.get('user_email'), 
        session.get('user_name'), 
        request.remote_addr
    )
    add_to_history(name="Connect to Me", logged_in=0)
    
    return redirect(url_for('connect_page'))

@app.route('/connect_page')
@login_required
def connect_page():
    return render_template('connect_page.html')
    
@app.route('/results', defaults={'filename': None})
@app.route('/results/<filename>')
def results(filename):
    if filename:
        return download_file(filename, 'RESULT_DIR')
    else:
        files = session.get('files', [])
        return render_template('result.html', files=files)


@app.route('/PPK_results')
@login_required
def PPK_results():
    """Display PPK processing results with two tabs - files and sorted data view"""
    import json
    
    files = session.get('files', [])
    excel_file = session.get('ppk_excel_file', None)
    num_parts = session.get('ppk_num_parts', 0)
    
    # Load sorted data from JSON file
    sorted_data = []
    sorted_data_file = session.get('ppk_sorted_data_file', None)
    if sorted_data_file:
        json_path = os.path.join(app.config['RESULT_DIR'], sorted_data_file)
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    sorted_data = json.load(f)
            except Exception as e:
                app.logger.error(f"Error loading sorted data: {e}")
    
    return render_template('PPK_results.html', 
                           files=files, 
                           excel_file=excel_file,
                           sorted_data=sorted_data,
                           num_parts=num_parts)


@app.route('/generic_processing', methods=['GET', 'POST'])
@login_required
def generic_processing():
    # Check tool access
    if not check_tool_access('generic'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    def process(file, epsilon, roun_lim):
        dataloader = GenericProcessor(file_path=file)
        dataloader.fit(epsilon=epsilon, round_limit=roun_lim)
        csv_file, txt_file, out_ranges_file, zeros_file = dataloader.save_files(app.config['RESULT_DIR'])
        return csv_file, txt_file, out_ranges_file, zeros_file
    
    if request.method == 'POST':
        file = request.files['file']
        epsilon = float(request.form['epsilon'])
        rounding_limit = float(request.form['rounding_limit'])
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['RESULT_DIR'], filename)
            file.save(file_path)
            # Process the file
            try:
                csv_file, txt_file, out_ranges_file, zeros_file = process(file_path, epsilon, rounding_limit)
                result_files = [os.path.basename(csv_file), os.path.basename(txt_file), os.path.basename(out_ranges_file), os.path.basename(zeros_file)]
                session['files'] = result_files
                
                # Track activity
                stats_manager.add_to_history(
                    'Generic Processing', 
                    session.get('user_email'), 
                    session.get('user_name'), 
                    request.remote_addr
                )
                add_to_history(name='Generic Processing', logged_in=0)
                
                result_url = url_for('results')
                return jsonify({'status': 'success', 'result_url': result_url})
            except Exception as e:
                add_to_history(name='Generic Processing', logged_in=2)
                return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'}), 400
    
    return render_template('generic_process.html')

@app.route('/PPK_processing', methods=['GET', 'POST'])
@login_required
def PPK_processing():
    # Check tool access
    if not check_tool_access('ppk'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    def process(file, time_threshold, elevation_threshold, start_num):
        # If elevation_threshold is 0, pass None to use std deviation method
        elev_thresh = elevation_threshold if elevation_threshold > 0 else None
        dataloader = PPKProcessor(
            file_path=file, 
            time_threshold=time_threshold, 
            elevation_threshold=elev_thresh
        )
        PPK_file, removed_file, text_files, excel_file = dataloader.save_files(app.config['RESULT_DIR'], start_num=start_num)
        sorted_data = dataloader.get_sorted_data_json()
        return PPK_file, removed_file, text_files, excel_file, sorted_data
    
    if request.method == 'POST':
        file = request.files['file']
        time_threshold = float(request.form['time_threshold'])
        elevation_threshold = float(request.form.get('elevation_threshold', 0))
        start_num = int(request.form.get('start_num', 1))
        
        if file and time_threshold:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['RESULT_DIR'], filename)
            file.save(file_path)
            # Process the file
            try:
                PPK_file, removed_file, text_files, excel_file, sorted_data = process(file_path, time_threshold, elevation_threshold, start_num)
                text_files = [os.path.basename(filee) for filee in text_files]
                excel_basename = os.path.basename(excel_file) if excel_file else None
                result_files = [os.path.basename(PPK_file), os.path.basename(removed_file)] + text_files
                
                # Store file references in session (NOT the actual data)
                session['files'] = result_files
                session['ppk_excel_file'] = excel_basename
                
                # Save sorted data to a JSON file instead of session
                import json
                base_name_without_ext = os.path.splitext(filename)[0]
                sorted_data_file = os.path.join(app.config['RESULT_DIR'], f"PPK_{base_name_without_ext}_sorted_data.json")
                with open(sorted_data_file, 'w') as f:
                    json.dump(sorted_data, f)
                session['ppk_sorted_data_file'] = os.path.basename(sorted_data_file)
                session['ppk_num_parts'] = max(row['group_id'] for row in sorted_data) if sorted_data else 0
                
                # Track activity
                stats_manager.add_to_history(
                    'PPK Processing', 
                    session.get('user_email'), 
                    session.get('user_name'), 
                    request.remote_addr
                )
                add_to_history(name='PPK Processing', logged_in=0)
                
                result_url = url_for('PPK_results')
                return jsonify({'status': 'success', 'result_url': result_url})
            except Exception as e:
                add_to_history(name='PPK Processing', logged_in=2)
                return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'}), 400
    
    return render_template('PPK_process.html')

@app.route('/CSDP_processing', methods=['GET', 'POST'])
@login_required
def CSDP_processing():
    # Check tool access
    if not check_tool_access('csdp'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    def process(file1, file2, file3):
        dataloader = CSDPProcessor(file1, file2, file3)
        dataloader.fit()
        CSDP_file = dataloader.save_files(app.config['RESULT_DIR'])
        return CSDP_file
    
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']
        if file1 and file2 and file3:
            filename1 = secure_filename(file1.filename)
            file_path1 = os.path.join(app.config['RESULT_DIR'], filename1)
            file1.save(file_path1)
            filename2 = secure_filename(file2.filename)
            file_path2 = os.path.join(app.config['RESULT_DIR'], filename2)
            file2.save(file_path2)
            filename3 = secure_filename(file3.filename)
            file_path3 = os.path.join(app.config['RESULT_DIR'], filename3)
            file3.save(file_path3)
            # Process the file
            try:
                CSDP_file = process(file_path1, file_path2, file_path3)
                result_files = [os.path.basename(CSDP_file)]
                session['files'] = result_files
                
                # Track activity
                stats_manager.add_to_history(
                    'CSDP Processing', 
                    session.get('user_email'), 
                    session.get('user_name'), 
                    request.remote_addr
                )
                add_to_history(name='CSDP Processing', logged_in=0)
                
                result_url = url_for('results')
                return jsonify({'status': 'success', 'result_url': result_url})
            except Exception as e:
                add_to_history(name='CSDP Processing', logged_in=2)
                return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'}), 400
    
    return render_template('CSDP_process.html')



@app.route('/delete_empty_processing', methods=['GET', 'POST'])
@login_required
def delete_empty_processing():
    # Check tool access
    if not check_tool_access('delete_distance'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    def process(file, left_bound, right_bound):
        dataloader = DistanceProcessor(file, left_bound=left_bound, right_bound=right_bound)
        dataloader.fit()
        csv_file = dataloader.save_files(app.config['RESULT_DIR'])
        return csv_file
    
    if request.method == 'POST':
        file = request.files['file']
        left = float(request.form['left'])
        right = float(request.form['right'])
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['RESULT_DIR'], filename)
            file.save(file_path)
            # Process the file
            try:
                csv_file = process(file_path, left, right)
                result_files = [os.path.basename(csv_file)]
                session['files'] = result_files
                
                # Track activity
                stats_manager.add_to_history(
                    'Delete Empty Processing', 
                    session.get('user_email'), 
                    session.get('user_name'), 
                    request.remote_addr
                )
                add_to_history(name='Delete Empty Processing', logged_in=0)
                
                result_url = url_for('results')
                return jsonify({'status': 'success', 'result_url': result_url})
            except Exception as e:
                add_to_history(name='Delete Empty Processing', logged_in=2)
                return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'}), 400
    
    return render_template('delete_empty_process.html')


@app.route('/distance2_processing', methods=['GET', 'POST'])
@login_required
def distance2_processing():
    # Check tool access
    if not check_tool_access('distance2'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    def process(file, columns_spec):
        dataloader = Distance2Processor(file)
        dataloader.fit(cols=columns_spec)
        csv_file = dataloader.save_files(app.config['RESULT_DIR'])
        return csv_file
    
    if request.method == 'POST':
        file = request.files['file']
        columns_spec = request.form['columns']
        
        if file and columns_spec:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['RESULT_DIR'], filename)
            file.save(file_path)
            # Process the file
            try:
                app.logger.info(f"Processing distance2 file: {file_path}, columns: {columns_spec}")
                csv_file = process(file_path, columns_spec)
                app.logger.info(f"Distance2 processing completed: {csv_file}")
                result_files = [os.path.basename(csv_file)]
                session['files'] = result_files
                
                # Track activity
                stats_manager.add_to_history(
                    'Distance2 Processing', 
                    session.get('user_email'), 
                    session.get('user_name'), 
                    request.remote_addr
                )
                add_to_history(name='Distance2 Processing', logged_in=0)
                
                result_url = url_for('results')
                return jsonify({'status': 'success', 'result_url': result_url})
            except Exception as e:
                import traceback
                app.logger.error(f"Distance2 Processing Error: {str(e)}")
                app.logger.error(traceback.format_exc())
                add_to_history(name='Distance2 Processing', logged_in=2)
                return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'}), 400
    
    return render_template('distance2_process.html')


@app.route('/culvert_processing', methods=['GET'])
@login_required
def culvert_processing():
    """Display culvert design form"""
    # Check tool access
    if not check_tool_access('culvert'):
        flash('You do not have access to this tool', 'error')
        return redirect(url_for('index'))
    
    return render_template('culvert_process.html')


@app.route('/process_culvert', methods=['POST'])
@login_required
def process_culvert():
    """Process culvert design request"""
    # Check tool access
    if not check_tool_access('culvert'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Initialize processor
        processor = CulvertProcessor()
        
        # Process the request
        result = processor.process(form_data)
        
        # Handle both success and warning statuses (DXF is generated in both cases)
        if result['status'] in ['success', 'warning']:
            # Track activity with Persian date
            import jdatetime
            now = jdatetime.datetime.now()
            persian_date = now.strftime('%Y/%m/%d | %H:%M:%S')
            
            stats_manager.add_to_history(
                'Culvert Processing',
                session.get('user_email'),
                session.get('user_name'),
                request.remote_addr
            )
            add_to_history(name='Culvert Processing', logged_in=0 if result['status'] == 'success' else 1)
            
            # Add download URL
            result['download_url'] = url_for('download_culvert_file', 
                                             filename=result['filename'])
            
            # Log with Persian date
            status_text = "generated" if result['status'] == 'success' else "generated with warnings"
            app.logger.info(f"[{persian_date}] Culvert design {status_text}: {result['filename']} by {session.get('user_name')}")
            
        return jsonify(result)
        
    except Exception as e:
        add_to_history(name='Culvert Processing', logged_in=2)
        app.logger.error(f"Culvert processing error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Processing error: {str(e)}'
        }), 500


@app.route('/download_culvert/<filename>')
@login_required
def download_culvert_file(filename):
    """Download generated culvert DXF file"""
    culvert_results_dir = os.path.join(BASE_DIR, 'culvert', 'results')
    return send_from_directory(culvert_results_dir, filename, as_attachment=True)


# Global error handler to log all exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    """Log all unhandled exceptions"""
    import traceback
    app.logger.error(f"Unhandled Exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@app.errorhandler(500)
def handle_500(e):
    """Log 500 errors"""
    import traceback
    app.logger.error(f"500 Error: {str(e)}")
    app.logger.error(traceback.format_exc())
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
