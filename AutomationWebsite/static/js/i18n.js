/**
 * i18n.js - Internationalization (i18n) for Website
 * Supports English and Persian/Farsi languages with RTL/LTR switching
 */

// Global translations object
let translations = {};
let currentLang = 'en';

/**
 * Load translations from JSON file
 */
async function loadTranslations() {
    try {
        const response = await fetch('/static/translations/i18n.json');
        translations = await response.json();
        console.log('Translations loaded successfully');
    } catch (error) {
        console.error('Error loading translations:', error);
    }
}

/**
 * Get translation for a key in current language
 * @param {string} key - Translation key
 * @param {string} fallback - Fallback text if key not found
 * @returns {string} Translated text
 */
function t(key, fallback = key) {
    if (!translations[currentLang]) {
        return fallback;
    }
    return translations[currentLang][key] || fallback;
}

/**
 * Set the active language
 * @param {string} lang - Language code ('en' or 'fa')
 */
function setLanguage(lang) {
    if (!['en', 'fa'].includes(lang)) {
        console.error('Invalid language:', lang);
        return;
    }
    
    currentLang = lang;
    
    // Store preference in localStorage
    localStorage.setItem('preferred_language', lang);
    
    // Update HTML lang attribute
    document.documentElement.lang = lang;
    
    // Handle RTL/LTR
    if (lang === 'fa') {
        document.body.classList.add('rtl');
        document.body.dir = 'rtl';
    } else {
        document.body.classList.remove('rtl');
        document.body.dir = 'ltr';
    }
    
    // Update all elements with data-i18n attribute
    updateTranslations();
    
    // Update language toggle buttons
    updateLanguageButtons();
    
    console.log('Language set to:', lang);
}

/**
 * Update all elements with data-i18n attributes
 */
function updateTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key);
        
        // Check if element has data-i18n-attr for attribute translation
        const attrName = element.getAttribute('data-i18n-attr');
        if (attrName) {
            element.setAttribute(attrName, translation);
        } else {
            // Update text content
            element.textContent = translation;
        }
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.placeholder = t(key);
    });
    
    // Update titles/tooltips
    document.querySelectorAll('[data-i18n-title]').forEach(element => {
        const key = element.getAttribute('data-i18n-title');
        element.title = t(key);
    });
}

/**
 * Update language toggle button states
 */
function updateLanguageButtons() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        const btnLang = btn.getAttribute('data-lang');
        if (btnLang === currentLang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

/**
 * Initialize i18n system
 */
async function initI18n() {
    // Load translations
    await loadTranslations();
    
    // Get saved language preference or detect browser language
    const savedLang = localStorage.getItem('preferred_language');
    const browserLang = navigator.language || navigator.userLanguage;
    
    // Determine initial language
    let initialLang = 'en';
    if (savedLang) {
        initialLang = savedLang;
    } else if (browserLang.startsWith('fa') || browserLang.startsWith('per')) {
        initialLang = 'fa';
    }
    
    // Set language
    setLanguage(initialLang);
    
    // Setup language toggle buttons
    setupLanguageToggles();
}

/**
 * Setup event listeners for language toggle buttons
 */
function setupLanguageToggles() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            setLanguage(lang);
        });
    });
}

/**
 * Create language toggle widget and inject into page
 */
function createLanguageToggle() {
    const toggle = document.createElement('div');
    toggle.className = 'language-toggle';
    toggle.innerHTML = `
        <button class="lang-btn" data-lang="en">English</button>
        <button class="lang-btn" data-lang="fa">فارسی</button>
    `;
    
    // Insert at beginning of body
    if (document.body.firstChild) {
        document.body.insertBefore(toggle, document.body.firstChild);
    } else {
        document.body.appendChild(toggle);
    }
    
    // Setup click handlers
    setupLanguageToggles();
}

/**
 * Get current language
 * @returns {string} Current language code
 */
function getCurrentLanguage() {
    return currentLang;
}

/**
 * Check if current language is RTL
 * @returns {boolean} True if RTL language
 */
function isRTL() {
    return currentLang === 'fa';
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        createLanguageToggle();
        initI18n();
    });
} else {
    createLanguageToggle();
    initI18n();
}

// Export functions for use in other scripts
window.i18n = {
    t,
    setLanguage,
    getCurrentLanguage,
    isRTL,
    loadTranslations,
    updateTranslations
};
