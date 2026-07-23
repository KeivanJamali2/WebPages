/**
 * Searchable Select Component
 * Converts regular select elements into searchable dropdowns
 */

class SearchableSelect {
    constructor(selectElement) {
        this.select = selectElement;
        this.options = Array.from(selectElement.options);
        this.wrapper = null;
        this.display = null;
        this.dropdown = null;
        this.searchInput = null;
        this.optionsList = null;
        this.noResultsEl = null;
        this.isOpen = false;
        this.highlightedIndex = -1;
        
        this.init();
    }
    
    init() {
        // Don't initialize if already wrapped or if select is hidden template
        if (this.select.closest('.searchable-select-wrapper') || 
            this.select.closest('.row-template')) {
            return;
        }
        
        // Store reference on the element for later access
        this.select._searchableSelect = this;
        
        this.createWrapper();
        this.createDisplay();
        this.createDropdown();
        this.bindEvents();
        this.updateDisplay();
    }
    
    createWrapper() {
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'searchable-select-wrapper';
        this.select.parentNode.insertBefore(this.wrapper, this.select);
        this.wrapper.appendChild(this.select);
    }
    
    createDisplay() {
        this.display = document.createElement('div');
        this.display.className = 'searchable-select-display';
        this.display.setAttribute('role', 'combobox');
        this.display.setAttribute('aria-expanded', 'false');
        
        // Create input inside display
        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.placeholder = this.options[0] ? this.options[0].text : (currentLang === 'fa' ? 'انتخاب کنید' : 'Select');
        this.searchInput.setAttribute('autocomplete', 'off');
        this.display.appendChild(this.searchInput);
        
        this.wrapper.insertBefore(this.display, this.select);
    }
    
    createDropdown() {
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'searchable-select-dropdown';
        
        // Options list
        this.optionsList = document.createElement('div');
        this.optionsList.className = 'searchable-select-options';
        this.optionsList.setAttribute('role', 'listbox');
        
        // Populate options
        this.populateOptions();
        
        // No results message
        this.noResultsEl = document.createElement('div');
        this.noResultsEl.className = 'searchable-select-no-results';
        this.noResultsEl.textContent = currentLang === 'fa' ? 'نتیجه‌ای یافت نشد' : 'No results found';
        
        this.dropdown.appendChild(this.optionsList);
        this.dropdown.appendChild(this.noResultsEl);
        this.wrapper.appendChild(this.dropdown);
    }
    
    populateOptions() {
        this.optionsList.innerHTML = '';
        this.options.forEach((option, index) => {
            const optionEl = document.createElement('div');
            optionEl.className = 'searchable-select-option';
            optionEl.textContent = option.text;
            optionEl.dataset.value = option.value;
            optionEl.dataset.index = index;
            optionEl.setAttribute('role', 'option');
            
            if (option.selected && option.value) {
                optionEl.classList.add('selected');
            }
            
            this.optionsList.appendChild(optionEl);
        });
    }
    
    bindEvents() {
        // Input focus - open dropdown
        this.searchInput.addEventListener('focus', () => {
            this.open();
        });
        
        // Input click
        this.searchInput.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!this.isOpen) {
                this.open();
            }
        });
        
        // Search input
        this.searchInput.addEventListener('input', () => {
            if (!this.isOpen) {
                this.open();
            }
            this.filter(this.searchInput.value);
        });
        
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
        
        // Option click
        this.optionsList.addEventListener('click', (e) => {
            const option = e.target.closest('.searchable-select-option');
            if (option) {
                this.selectOption(option);
            }
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target) && !this.dropdown.contains(e.target)) {
                this.close();
            }
        });
        
        // Update when original select changes
        this.select.addEventListener('change', () => {
            this.updateDisplay();
            this.updateSelectedOption();
        });
    }
    
    handleKeydown(e) {
        const visibleOptions = this.optionsList.querySelectorAll('.searchable-select-option:not(.hidden)');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.highlightNext(visibleOptions);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.highlightPrev(visibleOptions);
                break;
            case 'Enter':
                e.preventDefault();
                if (this.highlightedIndex >= 0) {
                    const highlighted = this.optionsList.querySelector('.searchable-select-option.highlighted');
                    if (highlighted) {
                        this.selectOption(highlighted);
                    }
                }
                break;
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
        }
    }
    
    highlightNext(visibleOptions) {
        if (visibleOptions.length === 0) return;
        
        this.clearHighlight();
        this.highlightedIndex = Math.min(this.highlightedIndex + 1, visibleOptions.length - 1);
        visibleOptions[this.highlightedIndex].classList.add('highlighted');
        this.scrollToHighlighted();
    }
    
    highlightPrev(visibleOptions) {
        if (visibleOptions.length === 0) return;
        
        this.clearHighlight();
        this.highlightedIndex = Math.max(this.highlightedIndex - 1, 0);
        visibleOptions[this.highlightedIndex].classList.add('highlighted');
        this.scrollToHighlighted();
    }
    
    clearHighlight() {
        this.optionsList.querySelectorAll('.searchable-select-option.highlighted')
            .forEach(el => el.classList.remove('highlighted'));
    }
    
    scrollToHighlighted() {
        const highlighted = this.optionsList.querySelector('.searchable-select-option.highlighted');
        if (highlighted) {
            highlighted.scrollIntoView({ block: 'nearest' });
        }
    }
    
    filter(query) {
        const normalizedQuery = query.toLowerCase().trim();
        let visibleCount = 0;
        
        this.optionsList.querySelectorAll('.searchable-select-option').forEach(option => {
            const text = option.textContent.toLowerCase();
            const matches = text.includes(normalizedQuery);
            
            option.classList.toggle('hidden', !matches);
            if (matches) visibleCount++;
        });
        
        // Show/hide no results message
        this.noResultsEl.classList.toggle('show', visibleCount === 0);
        
        // Reset highlight
        this.highlightedIndex = -1;
        this.clearHighlight();
    }
    
    selectOption(optionEl) {
        const value = optionEl.dataset.value;
        const index = parseInt(optionEl.dataset.index);
        
        // Update original select
        this.select.selectedIndex = index;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        this.select.dispatchEvent(event);
        
        // Update UI
        this.updateDisplay();
        this.updateSelectedOption();
        this.close();
    }
    
    updateDisplay() {
        const selectedOption = this.options[this.select.selectedIndex];
        
        if (selectedOption && selectedOption.value) {
            this.searchInput.value = selectedOption.text;
            this.searchInput.placeholder = this.options[0] ? this.options[0].text : (currentLang === 'fa' ? 'انتخاب کنید' : 'Select');
        } else {
            this.searchInput.value = '';
            this.searchInput.placeholder = this.options[0] ? this.options[0].text : (currentLang === 'fa' ? 'انتخاب کنید' : 'Select');
        }
    }
    
    updateSelectedOption() {
        const selectedValue = this.select.value;
        
        this.optionsList.querySelectorAll('.searchable-select-option').forEach(option => {
            option.classList.toggle('selected', option.dataset.value === selectedValue && selectedValue !== '');
        });
    }
    
    toggle() {
        this.isOpen ? this.close() : this.open();
    }
    
    open() {
        this.isOpen = true;
        this.dropdown.classList.add('show');
        this.display.classList.add('open');
        this.display.setAttribute('aria-expanded', 'true');
        
        // Position the dropdown
        this.positionDropdown();
        
        // Filter based on current input value
        this.filter(this.searchInput.value);
        
        // Select all text for easy replacement
        this.searchInput.select();
        
        // Reposition on scroll
        this.scrollHandler = () => this.positionDropdown();
        window.addEventListener('scroll', this.scrollHandler, true);
    }
    
    positionDropdown() {
        const rect = this.display.getBoundingClientRect();
        const dropdownHeight = 350;
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;
        
        // Determine if dropdown should open above or below
        let top;
        if (spaceBelow >= dropdownHeight || spaceBelow >= spaceAbove) {
            // Open below
            top = rect.bottom + 4;
        } else {
            // Open above
            top = rect.top - dropdownHeight - 4;
        }
        
        this.dropdown.style.top = `${top}px`;
        this.dropdown.style.left = `${rect.left}px`;
        this.dropdown.style.width = `${Math.max(rect.width, 250)}px`;
    }
    
    close() {
        this.isOpen = false;
        this.dropdown.classList.remove('show');
        this.display.classList.remove('open');
        this.display.setAttribute('aria-expanded', 'false');
        this.highlightedIndex = -1;
        this.clearHighlight();
        
        // Remove scroll handler
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler, true);
        }
    }
    
    // Refresh options (useful when select options change dynamically)
    refresh() {
        this.options = Array.from(this.select.options);
        this.populateOptions();
        this.updateDisplay();
    }
    
    // Destroy the component
    destroy() {
        if (this.wrapper && this.wrapper.parentNode) {
            this.wrapper.parentNode.insertBefore(this.select, this.wrapper);
            this.wrapper.remove();
        }
    }
}

/**
 * Initialize searchable selects
 */
function initSearchableSelects() {
    // Target specific selects that need search functionality
    const selectsToEnhance = document.querySelectorAll(
        'select[name="hr_post[]"], ' +
        'select[name="eq_type[]"], ' +
        'select[name="eq_model[]"], ' +
        'select[name="mat_type[]"], ' +
        'select[name="issue_type[]"], ' +
        'select[name="op_type[]"], ' +
        'select[name="project_id"]'
    );
    
    selectsToEnhance.forEach(select => {
        // Skip if in template row or already initialized
        if (select.closest('.row-template') || select.closest('.searchable-select-wrapper')) {
            return;
        }
        new SearchableSelect(select);
    });
}

/**
 * Initialize searchable select for a newly added row
 */
function initSearchableSelectsInRow(row) {
    const selects = row.querySelectorAll(
        'select[name="hr_post[]"], ' +
        'select[name="eq_type[]"], ' +
        'select[name="eq_model[]"], ' +
        'select[name="mat_type[]"], ' +
        'select[name="issue_type[]"], ' +
        'select[name="op_type[]"]'
    );
    
    selects.forEach(select => {
        if (!select.closest('.searchable-select-wrapper')) {
            new SearchableSelect(select);
        }
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initSearchableSelects();
});

// Export for use in other scripts
window.SearchableSelect = SearchableSelect;
window.initSearchableSelects = initSearchableSelects;
window.initSearchableSelectsInRow = initSearchableSelectsInRow;
