/**
 * PMO Website - Main JavaScript
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    initLanguageToggle();
    initNotifications();
    initFormSections();
    initDynamicTables();
    initModals();
    initAlerts();
});

/**
 * Language Toggle
 */
function initLanguageToggle() {
    const langBtns = document.querySelectorAll('.lang-btn');
    
    langBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const lang = this.dataset.lang;
            setLanguage(lang);
        });
    });
}

function setLanguage(lang) {
    // Send request to server to change language
    fetch('/set-language/' + lang, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload page to apply language change
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error changing language:', error);
    });
}

/**
 * Notifications
 */
function initNotifications() {
    const notificationBtn = document.querySelector('.notification-badge');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    
    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationDropdown.classList.toggle('show');
        });
        
        // Close on outside click
        document.addEventListener('click', function() {
            notificationDropdown.classList.remove('show');
        });
        
        notificationDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
}

function markNotificationRead(notificationId) {
    fetch('/notifications/mark-read/' + notificationId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (item) {
                item.classList.remove('unread');
            }
            updateNotificationCount();
        }
    });
}

function updateNotificationCount() {
    fetch('/notifications/count')
    .then(response => response.json())
    .then(data => {
        const countEl = document.querySelector('.notification-count');
        if (countEl) {
            if (data.count > 0) {
                countEl.textContent = data.count;
                countEl.style.display = 'flex';
            } else {
                countEl.style.display = 'none';
            }
        }
    });
}

/**
 * Form Sections (Collapsible)
 */
function initFormSections() {
    const sectionHeaders = document.querySelectorAll('.form-section-header');
    
    sectionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const section = this.closest('.form-section');
            section.classList.toggle('collapsed');
            
            const icon = this.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = section.classList.contains('collapsed') ? '▶' : '▼';
            }
        });
    });
}

/**
 * Dynamic Tables (Add/Remove Rows)
 */
function initDynamicTables() {
    // Add row buttons
    document.querySelectorAll('.add-row-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tableId = this.dataset.table;
            addTableRow(tableId);
        });
    });
    
    // Remove row buttons (delegate)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-row-btn') || e.target.closest('.remove-row-btn')) {
            const btn = e.target.classList.contains('remove-row-btn') ? e.target : e.target.closest('.remove-row-btn');
            const row = btn.closest('tr');
            if (row) {
                row.remove();
                updateRowNumbers(btn.closest('table'));
            }
        }
    });
}

function addTableRow(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const template = table.querySelector('.row-template');
    
    if (template) {
        const newRow = template.cloneNode(true);
        newRow.classList.remove('row-template', 'd-none');
        newRow.style.display = '';
        
        // Update input names with row index
        const rowIndex = tbody.querySelectorAll('tr:not(.row-template)').length;
        newRow.querySelectorAll('input, select, textarea').forEach(input => {
            const name = input.getAttribute('data-name');
            if (name) {
                input.name = name.replace('INDEX', rowIndex);
            }
        });
        
        tbody.appendChild(newRow);
        updateRowNumbers(table);
        
        // Initialize searchable selects in the new row
        if (typeof initSearchableSelectsInRow === 'function') {
            initSearchableSelectsInRow(newRow);
        }
    }
}

function updateRowNumbers(table) {
    const rows = table.querySelectorAll('tbody tr:not(.row-template)');
    rows.forEach((row, index) => {
        const numCell = row.querySelector('.row-number');
        if (numCell) {
            numCell.textContent = index + 1;
        }
    });
}

/**
 * Modal Functions
 */
function initModals() {
    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });
    
    // Close modal on close button click
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal-overlay');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal-overlay.show');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

/**
 * Alert Auto-dismiss
 */
function initAlerts() {
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    alerts.forEach(alert => {
        const timeout = parseInt(alert.dataset.autoDismiss) || 5000;
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, timeout);
    });
}

/**
 * Form Validation
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    // Clear previous errors
    form.querySelectorAll('.form-error').forEach(el => el.remove());
    form.querySelectorAll('.form-control.error').forEach(el => el.classList.remove('error'));
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
            
            const error = document.createElement('div');
            error.className = 'form-error';
            error.textContent = translations.field_required || 'This field is required';
            field.parentNode.appendChild(error);
        }
    });
    
    return isValid;
}

/**
 * AJAX Form Submit
 */
function submitFormAjax(formId, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    if (!validateForm(formId)) {
        return;
    }
    
    const formData = new FormData(form);
    const submitBtn = form.querySelector('[type="submit"]');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = translations.submitting || 'Submitting...';
    }
    
    fetch(form.action, {
        method: form.method || 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (successCallback) {
                successCallback(data);
            } else {
                showAlert('success', data.message || translations.success || 'Success!');
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            }
        } else {
            showAlert('danger', data.message || translations.error || 'An error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', translations.error || 'An error occurred');
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = translations.submit || 'Submit';
        }
    });
}

/**
 * Show Alert
 */
function showAlert(type, message) {
    const container = document.querySelector('.alert-container') || document.querySelector('.main-container');
    if (!container) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.setAttribute('data-auto-dismiss', '5000');
    alert.innerHTML = `
        <span>${message}</span>
        <button type="button" class="alert-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.insertBefore(alert, container.firstChild);
    
    // Auto dismiss
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

/**
 * Confirm Dialog
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Format Date
 */
function formatDate(dateString, locale) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString(locale || 'en-US', options);
}

/**
 * Export Table to Excel (Client-side helper)
 */
function exportTableToExcel(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Redirect to server-side export
    window.location.href = `/export/table/${tableId}?filename=${filename}`;
}

/**
 * Chart Helpers
 */
function updateChart(chartInstance, newData, newLabels) {
    if (!chartInstance) return;
    
    if (newLabels) {
        chartInstance.data.labels = newLabels;
    }
    
    if (newData) {
        chartInstance.data.datasets.forEach((dataset, index) => {
            if (newData[index]) {
                dataset.data = newData[index];
            }
        });
    }
    
    chartInstance.update();
}

// Global translations object (will be populated by server)
var translations = window.translations || {};
