"""
Document handling utilities for form attachments.
"""
import os
import zipfile
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'doc', 'docx', 'zip', 'rar'}


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Get the file extension."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def calculate_total_size(files):
    """Calculate total size of uploaded files in bytes."""
    total_size = 0
    for file in files:
        # Save current position
        file.seek(0, 2)  # Seek to end
        total_size += file.tell()
        file.seek(0)  # Reset to beginning
    return total_size


def ensure_documents_folder():
    """Ensure the form documents folder exists."""
    folder = current_app.config.get('FORM_DOCUMENTS_FOLDER', 
                                     os.path.join(current_app.config['BASE_DIR'], 'data', 'form_documents'))
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def get_form_documents_path(project_code, form_date, document_code):
    """
    Generate the path for storing form documents.
    Structure: form_documents/project_code/YYYY/MM/document_code.zip
    """
    base_folder = ensure_documents_folder()
    
    # Create year/month structure
    year = form_date.strftime('%Y')
    month = form_date.strftime('%m')
    
    # Build path
    folder_path = os.path.join(base_folder, project_code, year, month)
    
    # Ensure folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    return folder_path


def save_form_documents(files, project_code, form_date, document_code, event_files=None, existing_path=None):
    """
    Save uploaded documents as a zip file.
    
    Args:
        files: List of FileStorage objects from the form (main documents)
        project_code: The project code for folder organization
        form_date: The form date for folder organization
        document_code: The document code for naming the zip file
        event_files: Dict mapping event index to FileStorage object for event documents
        existing_path: Existing documents path to update (preserves existing files)
        
    Returns:
        str: Relative path to the saved zip file, or existing_path if no new files
    """
    # Filter valid main files
    valid_files = []
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            valid_files.append(file)
    
    # Filter valid event files
    valid_event_files = {}
    if event_files:
        for idx, file in event_files.items():
            if file and file.filename and allowed_file(file.filename):
                valid_event_files[idx] = file
    
    # Check if we have anything new to save
    has_new_files = valid_files or valid_event_files
    
    # If no new files, return existing path (preserve it)
    if not has_new_files:
        return existing_path
    
    # Check total size of new files
    all_new_files = valid_files + list(valid_event_files.values())
    if all_new_files:
        max_size = current_app.config.get('MAX_DOCUMENT_SIZE', 200 * 1024 * 1024)
        total_size = calculate_total_size(all_new_files)
        
        if total_size > max_size:
            raise ValueError(f"Total file size ({total_size / (1024*1024):.1f} MB) exceeds limit ({max_size / (1024*1024):.0f} MB)")
    
    # Get the folder path
    folder_path = get_form_documents_path(project_code, form_date, document_code)
    
    # Create zip filename with timestamp for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"{document_code}_{timestamp}.zip"
    zip_path = os.path.join(folder_path, zip_filename)
    
    # Collect existing files if updating
    existing_files = {}
    if existing_path:
        existing_full_path = get_documents_full_path(existing_path)
        if existing_full_path and os.path.exists(existing_full_path):
            try:
                with zipfile.ZipFile(existing_full_path, 'r') as old_zip:
                    for info in old_zip.infolist():
                        existing_files[info.filename] = old_zip.read(info.filename)
            except Exception:
                pass
    
    # Create the zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add existing files first (that aren't being replaced)
        for filename, content in existing_files.items():
            # Skip if it's an event file being replaced
            if filename.startswith('events/'):
                # Check if this event file is being replaced
                continue_adding = True
                for idx in valid_event_files.keys():
                    if filename.startswith(f'events/event_{idx}_'):
                        continue_adding = False
                        break
                if not continue_adding:
                    continue
            zipf.writestr(filename, content)
        
        # Add new main documents
        for file in valid_files:
            filename = secure_filename(file.filename)
            file_content = file.read()
            zipf.writestr(filename, file_content)
            file.seek(0)
        
        # Add event documents in events/ folder
        for idx, file in valid_event_files.items():
            filename = secure_filename(file.filename)
            # Store as events/event_0_filename.ext
            event_filename = f"events/event_{idx}_{filename}"
            file_content = file.read()
            zipf.writestr(event_filename, file_content)
            file.seek(0)
    
    # Delete old zip if we created a new one
    if existing_path and has_new_files:
        delete_form_documents(existing_path)
    
    # Return relative path from base folder
    base_folder = ensure_documents_folder()
    relative_path = os.path.relpath(zip_path, base_folder)
    
    return relative_path


def get_event_document_filename(documents_path, event_index):
    """
    Get the filename of a document for a specific event from the ZIP.
    
    Args:
        documents_path: Relative path to the zip file
        event_index: The index of the event
        
    Returns:
        str: Filename if found, None otherwise
    """
    full_path = get_documents_full_path(documents_path)
    
    if not full_path or not os.path.exists(full_path):
        return None
    
    try:
        with zipfile.ZipFile(full_path, 'r') as zipf:
            for info in zipf.infolist():
                if info.filename.startswith(f'events/event_{event_index}_'):
                    # Return just the original filename part
                    return info.filename.split(f'event_{event_index}_', 1)[-1]
    except Exception:
        pass
    
    return None


def delete_form_documents(documents_path):
    """
    Delete the documents zip file for a form.
    
    Args:
        documents_path: Relative path to the zip file
    """
    if not documents_path:
        return
    
    base_folder = ensure_documents_folder()
    full_path = os.path.join(base_folder, documents_path)
    
    if os.path.exists(full_path):
        os.remove(full_path)


def get_documents_full_path(documents_path):
    """
    Get the full path to the documents zip file.
    
    Args:
        documents_path: Relative path stored in database
        
    Returns:
        str: Full path to the zip file
    """
    if not documents_path:
        return None
    
    base_folder = ensure_documents_folder()
    return os.path.join(base_folder, documents_path)


def list_documents_in_zip(documents_path):
    """
    List all files in a documents zip file.
    
    Args:
        documents_path: Relative path to the zip file
        
    Returns:
        list: List of dicts with filename and size info
    """
    full_path = get_documents_full_path(documents_path)
    
    if not full_path or not os.path.exists(full_path):
        return []
    
    files_info = []
    try:
        with zipfile.ZipFile(full_path, 'r') as zipf:
            for info in zipf.infolist():
                files_info.append({
                    'filename': info.filename,
                    'size': info.file_size,
                    'compressed_size': info.compress_size,
                    'date_time': datetime(*info.date_time) if info.date_time else None
                })
    except Exception:
        pass
    
    return files_info


def get_zip_file_size(documents_path):
    """
    Get the size of the zip file in bytes.
    
    Args:
        documents_path: Relative path to the zip file
        
    Returns:
        int: Size in bytes, or 0 if file doesn't exist
    """
    full_path = get_documents_full_path(documents_path)
    
    if full_path and os.path.exists(full_path):
        return os.path.getsize(full_path)
    
    return 0


def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
