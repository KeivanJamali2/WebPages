/* ========================================
   PMO Website - Main JavaScript
   ======================================== */

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            flash.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            
            setTimeout(function() {
                flash.remove();
            }, 300);
        }, 5000);
    });
});

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
        } else {
            input.classList.remove('error');
        }
    });
    
    return isValid;
}

// Confirmation dialog
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Show loading indicator
function showLoading(button) {
    if (button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = 'Loading...';
    }
}

// Hide loading indicator
function hideLoading(button) {
    if (button && button.dataset.originalText) {
        button.disabled = false;
        button.textContent = button.dataset.originalText;
    }
}

console.log('PMO Website JS loaded');
