// HamiAnalyzer JavaScript Functions

// Alerts are now permanent - users can dismiss them manually via the close button
// No auto-dismiss functionality

// Confirm before dangerous actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}

// Format file sizes
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Loading overlay
function showLoading(message) {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-light" role="status" style="width: 4rem; height: 4rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-light mt-3 fs-5">${message || 'Processing...'}</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }).catch(function(err) {
        showToast('Failed to copy', 'danger');
    });
}

// Show toast notification
function showToast(message, type) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { autohide: false });
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Initialize popovers
document.addEventListener('DOMContentLoaded', function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add scroll to top button
document.addEventListener('DOMContentLoaded', function() {
    const scrollBtn = document.createElement('button');
    scrollBtn.id = 'scrollTopBtn';
    scrollBtn.className = 'btn btn-primary position-fixed bottom-0 end-0 m-3 rounded-circle';
    scrollBtn.style.width = '50px';
    scrollBtn.style.height = '50px';
    scrollBtn.style.display = 'none';
    scrollBtn.style.zIndex = '1000';
    scrollBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
    scrollBtn.onclick = scrollToTop;
    document.body.appendChild(scrollBtn);
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            scrollBtn.style.display = 'block';
        } else {
            scrollBtn.style.display = 'none';
        }
    });
});

// Print page
function printPage() {
    window.print();
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        cols.forEach(function(col) {
            csvRow.push(col.innerText);
        });
        csv.push(csvRow.join(','));
    });
    
    const csvString = csv.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    a.click();
}

console.log('HamiAnalyzer JS loaded successfully!');
