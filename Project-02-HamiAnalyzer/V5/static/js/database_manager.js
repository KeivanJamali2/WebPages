/**
 * Database Manager JavaScript
 * Handles browsing and searching database files (SQLite version)
 */

// Global state - simplified for SQLite (no date_source/output_type needed)
let currentHami = '';        // Currently selected hami ID
let lastSearchResults = [];  // Store last search results for download all
let lastBrowseFiles = [];    // Store last browse files for download all

// File preview state
let currentPreviewFile = null;
let currentPreviewPage = 1;
let currentPreviewTotalPages = 1;

// Search progress state
let searchProgressInterval = null;
let searchStartTime = null;
let searchEstimatedTime = null;
let searchCurrentProgress = 0;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

/**
 * Search Progress Bar Management
 */
function getDbStats() {
    // Return default stats - the SQLite version doesn't need these from data attributes
    return { hamis: 100, requests: 500, months: 12 };
}

function estimateSearchTime(searchType) {
    // Estimate search time based on search type
    // SQLite searches are generally fast
    const typeMultipliers = {
        'date': 1.0,
        'reference': 0.5,
        'field': 0.8,
        'employee': 1.5
    };
    
    // Base time: 500ms to 3 seconds depending on search type
    return Math.max(500, 2000 * (typeMultipliers[searchType] || 1));
}

function showSearchProgress(searchType) {
    const container = document.getElementById('search-progress-container');
    const resultsContainer = document.getElementById('search-results-container');
    const progressBar = document.getElementById('search-progress-bar');
    const progressPercent = document.getElementById('search-progress-percent');
    const progressStatus = document.getElementById('search-progress-status');
    const progressTime = document.getElementById('search-progress-time');
    const progressDetail = document.getElementById('search-progress-detail');
    const elapsedTime = document.getElementById('search-elapsed-time');
    
    // Reset state
    searchCurrentProgress = 0;
    searchStartTime = Date.now();
    searchEstimatedTime = estimateSearchTime(searchType);
    
    // Show progress container, hide results
    container.style.display = 'block';
    resultsContainer.innerHTML = '';
    
    // Reset progress bar
    progressBar.style.width = '0%';
    progressBar.classList.remove('progress-complete', 'progress-error');
    progressPercent.textContent = '0%';
    progressStatus.textContent = 'Searching database...';
    progressTime.textContent = `Estimated: ${Math.ceil(searchEstimatedTime / 1000)}s`;
    progressDetail.textContent = 'Initializing search...';
    elapsedTime.textContent = 'Elapsed: 0s';
    
    // Disable search buttons
    setSearchButtonsDisabled(true);
    
    // Start progress animation
    startProgressAnimation(searchType);
}

function startProgressAnimation(searchType) {
    // Clear any existing interval
    if (searchProgressInterval) {
        clearInterval(searchProgressInterval);
    }
    
    const phases = getSearchPhases(searchType);
    let currentPhaseIndex = 0;
    let phaseProgress = 0;
    
    searchProgressInterval = setInterval(() => {
        const elapsed = Date.now() - searchStartTime;
        const estimatedProgress = Math.min(95, (elapsed / searchEstimatedTime) * 100);
        
        // Smooth progress: use estimated progress with some randomization for realism
        // Progress should slow down as it approaches 90% (waiting for actual response)
        let targetProgress;
        if (estimatedProgress < 70) {
            targetProgress = estimatedProgress + (Math.random() * 2 - 1);
        } else if (estimatedProgress < 85) {
            // Slow down progress as we approach estimated time
            targetProgress = 70 + ((estimatedProgress - 70) * 0.5);
        } else {
            // Very slow progress after 85%
            targetProgress = Math.min(searchCurrentProgress + 0.1, 92);
        }
        
        searchCurrentProgress = Math.max(searchCurrentProgress, targetProgress);
        searchCurrentProgress = Math.min(searchCurrentProgress, 95); // Never exceed 95% until complete
        
        // Update UI
        updateProgressUI(searchCurrentProgress, elapsed, phases, currentPhaseIndex);
        
        // Move to next phase based on progress
        if (phases.length > 0) {
            const phaseThreshold = (currentPhaseIndex + 1) * (90 / phases.length);
            if (searchCurrentProgress >= phaseThreshold && currentPhaseIndex < phases.length - 1) {
                currentPhaseIndex++;
            }
        }
        
    }, 100); // Update every 100ms for smooth animation
}

function getSearchPhases(searchType) {
    const stats = getDbStats();
    
    switch (searchType) {
        case 'date':
            return [
                'Loading date indices...',
                `Scanning ${stats.months} time period(s)...`,
                'Parsing date fields...',
                'Filtering results...'
            ];
        case 'reference':
            return [
                'Building search index...',
                `Scanning ${stats.hamis} hami file(s)...`,
                'Matching reference codes...',
                'Compiling results...'
            ];
        case 'field':
            return [
                'Initializing field search...',
                `Scanning ${stats.hamis} hami file(s)...`,
                'Processing text patterns...',
                'Filtering matches...'
            ];
        case 'employee':
            return [
                'Building name index...',
                `Scanning ${stats.months} time period(s)...`,
                `Searching ${stats.requests} combined file(s)...`,
                'Matching employee names...',
                'Aggregating results...'
            ];
        default:
            return ['Searching...', 'Processing...'];
    }
}

function updateProgressUI(progress, elapsed, phases, currentPhaseIndex) {
    const progressBar = document.getElementById('search-progress-bar');
    const progressPercent = document.getElementById('search-progress-percent');
    const progressDetail = document.getElementById('search-progress-detail');
    const elapsedTime = document.getElementById('search-elapsed-time');
    const progressTime = document.getElementById('search-progress-time');
    
    // Update progress bar
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', Math.round(progress));
    progressPercent.textContent = `${Math.round(progress)}%`;
    
    // Update elapsed time
    const elapsedSeconds = Math.floor(elapsed / 1000);
    elapsedTime.textContent = `Elapsed: ${elapsedSeconds}s`;
    
    // Update estimated remaining time
    if (progress > 5) {
        const estimatedRemaining = Math.max(0, Math.ceil((elapsed / progress) * (100 - progress) / 1000));
        if (estimatedRemaining > 0) {
            progressTime.textContent = `Remaining: ~${estimatedRemaining}s`;
        } else {
            progressTime.textContent = 'Almost done...';
        }
    }
    
    // Update detail text with current phase
    if (phases.length > 0 && currentPhaseIndex < phases.length) {
        progressDetail.textContent = phases[currentPhaseIndex];
    }
}

function completeSearchProgress(success = true, resultCount = 0) {
    // Stop the animation
    if (searchProgressInterval) {
        clearInterval(searchProgressInterval);
        searchProgressInterval = null;
    }
    
    const progressBar = document.getElementById('search-progress-bar');
    const progressPercent = document.getElementById('search-progress-percent');
    const progressStatus = document.getElementById('search-progress-status');
    const progressDetail = document.getElementById('search-progress-detail');
    const progressTime = document.getElementById('search-progress-time');
    const elapsedTime = document.getElementById('search-elapsed-time');
    
    // Calculate final elapsed time
    const elapsed = Date.now() - searchStartTime;
    const elapsedSeconds = (elapsed / 1000).toFixed(1);
    
    if (success) {
        // Complete the progress bar
        progressBar.style.width = '100%';
        progressBar.classList.add('progress-complete');
        progressPercent.textContent = '100%';
        progressStatus.innerHTML = '<i class="bi bi-check-circle"></i> Search complete!';
        progressDetail.textContent = `Found ${resultCount} result(s)`;
        progressTime.textContent = `Completed in ${elapsedSeconds}s`;
        elapsedTime.textContent = '';
        
        // Hide progress bar after a delay
        setTimeout(() => {
            document.getElementById('search-progress-container').style.display = 'none';
        }, 2000);
    } else {
        progressBar.classList.add('progress-error');
        progressStatus.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Search failed';
        progressTime.textContent = `Failed after ${elapsedSeconds}s`;
    }
    
    // Re-enable search buttons
    setSearchButtonsDisabled(false);
}

function hideSearchProgress() {
    if (searchProgressInterval) {
        clearInterval(searchProgressInterval);
        searchProgressInterval = null;
    }
    document.getElementById('search-progress-container').style.display = 'none';
    setSearchButtonsDisabled(false);
}

function setSearchButtonsDisabled(disabled) {
    // Disable/enable all search buttons
    const searchButtons = document.querySelectorAll('#search button[onclick^="search"]');
    searchButtons.forEach(btn => {
        btn.disabled = disabled;
        if (disabled) {
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Searching...';
        } else {
            btn.innerHTML = '<i class="bi bi-search"></i> Search';
        }
    });
}

function initializeEventListeners() {
    // Browse tab - Hami selector
    const browseHami = document.getElementById('browse-month');
    
    if (browseHami) {
        browseHami.addEventListener('change', function() {
            if (this.value) {
                loadFiles(this.value);
            } else {
                document.getElementById('files-container').innerHTML = `
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle"></i> Select a Hami to view requests.
                    </div>
                `;
            }
        });
    }
    
    // Search type toggle
    const searchTypeRadios = document.querySelectorAll('input[name="search-type"]');
    searchTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            toggleSearchForm(this.value);
        });
    });
    
    // Load hamis when browse tab is shown
    const browseTab = document.getElementById('browse-tab');
    if (browseTab) {
        browseTab.addEventListener('shown.bs.tab', function() {
            loadMonths();
        });
    }

    // "By Field" search - city/source are discrete values, swap the input control
    const fieldNameSelect = document.getElementById('search-field-name');
    if (fieldNameSelect) {
        fieldNameSelect.addEventListener('change', function() {
            toggleFieldSearchValueInput(this.value);
        });
    }
}

function toggleFieldSearchValueInput(fieldName) {
    const textInput = document.getElementById('search-field-value');
    const sourceSelect = document.getElementById('search-field-value-source');
    const hint = document.getElementById('search-field-value-hint');

    if (fieldName === 'source') {
        textInput.style.display = 'none';
        sourceSelect.style.display = '';
        hint.textContent = 'Exact match on how the record was added to the database.';
    } else if (fieldName === 'city') {
        textInput.style.display = '';
        sourceSelect.style.display = 'none';
        textInput.value = '';
        hint.textContent = 'Exact match; pick from the suggested list of known cities.';
    } else {
        textInput.style.display = '';
        sourceSelect.style.display = 'none';
        hint.textContent = 'Use partial text for text fields (e.g., part of name)';
    }
}

function toggleSearchForm(searchType) {
    const dateForm = document.getElementById('date-search-form');
    const referenceForm = document.getElementById('reference-search-form');
    const fieldForm = document.getElementById('field-search-form');
    const employeeForm = document.getElementById('employee-search-form');
    
    // Hide all forms first
    dateForm.style.display = 'none';
    referenceForm.style.display = 'none';
    fieldForm.style.display = 'none';
    employeeForm.style.display = 'none';
    
    // Show the selected form
    if (searchType === 'date') {
        dateForm.style.display = 'block';
    } else if (searchType === 'reference') {
        referenceForm.style.display = 'block';
    } else if (searchType === 'field') {
        fieldForm.style.display = 'block';
    } else if (searchType === 'employee') {
        employeeForm.style.display = 'block';
    }
}

async function loadMonths() {
    // Load list of hami IDs instead of months (SQLite-based)
    try {
        const response = await fetch('/api/browse_database');
        const data = await response.json();
        
        if (data.error) {
            showError('Error loading hamis: ' + data.error);
            return;
        }
        
        const monthSelect = document.getElementById('browse-month');
        monthSelect.innerHTML = '<option value="">-- Select Hami --</option>';
        
        // Display hamis instead of months
        if (data.hamis) {
            data.hamis.forEach(hami => {
                const option = document.createElement('option');
                option.value = hami.hami_id;
                option.textContent = `Hami ${hami.hami_id} (${hami.request_count} requests)`;
                monthSelect.appendChild(option);
            });
        }
        
        // Clear files display
        document.getElementById('files-container').innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> Select a Hami to view requests.
            </div>
        `;
        
    } catch (error) {
        showError('Error loading hamis: ' + error.message);
    }
}

async function loadFiles() {
    // Load requests for selected hami (SQLite-based)
    const hamiId = document.getElementById('browse-month').value;
    if (!hamiId) {
        document.getElementById('files-container').innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> Select a Hami to view requests.
            </div>
        `;
        return;
    }
    
    // Update global state
    currentHami = hamiId;
    
    try {
        const response = await fetch(`/api/browse_database?hami_id=${hamiId}`);
        const data = await response.json();
        
        if (data.error) {
            showError('Error loading files: ' + data.error);
            return;
        }
        
        displayFiles(data.files || [], hamiId);
        
    } catch (error) {
        showError('Error loading files: ' + error.message);
    }
}

function displayFiles(files, hamiId) {
    const container = document.getElementById('files-container');
    
    // Store files for download all functionality
    lastBrowseFiles = files;
    
    if (files.length === 0) {
        lastBrowseFiles = [];
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> No requests found for this Hami.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="alert alert-info mb-0 flex-grow-1 me-3">
                <i class="bi bi-folder2-open"></i> Found <strong>${files.length}</strong> request(s) for <strong>Hami ${hamiId}</strong>
            </div>
            ${exportButtonHtml('files-container', `hami_${hamiId}_requests`)}
        </div>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Number</th>
                        <th>Ref. Code</th>
                        <th>Source</th>
                        <th>City</th>
                        <th>Subject</th>
                        <th>Name</th>
                        <th>First Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    files.forEach(file => {
        // Truncate subject if too long (max 50 chars)
        let displaySubject = file.subject || 'N/A';
        if (displaySubject.length > 50) {
            displaySubject = displaySubject.substring(0, 47) + '...';
        }
        // Make reference code clickable to copy
        let refCodeHtml = file.reference_code
            ? `<code class="ref-code-copy" style="cursor: pointer;" onclick="copyToClipboard('${file.reference_code}', this)" title="Click to copy"><small>${file.reference_code} <i class="bi bi-clipboard"></i></small></code>`
            : '<small>N/A</small>';

        html += `
            <tr>
                <td>${file.number || 'N/A'}</td>
                <td>${refCodeHtml}</td>
                <td>${renderSourceBadge(file.source)}</td>
                <td dir="rtl">${file.city || '-'}</td>
                <td><small title="${file.subject || ''}">${displaySubject}</small></td>
                <td><small>${file.name || 'N/A'}</small></td>
                <td><small>${file.first_date || 'N/A'}</small></td>
                <td>
                    <button class="btn btn-sm btn-info me-1" onclick="previewFileById('${file.hami_id}', '${file.number}')" title="View request">
                        <i class="bi bi-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// New function to preview file by hami_id and number (SQLite-based)
async function previewFileById(hamiId, number) {
    // Store current file info for pagination (SQLite-based)
    currentPreviewFile = { hami_id: hamiId, number: number };
    currentPreviewPage = 1;
    
    // Reset modal state before showing
    document.getElementById('preview-loading').style.display = 'flex';
    document.getElementById('preview-error').style.display = 'none';
    document.getElementById('preview-table-container').style.display = 'none';
    document.getElementById('preview-global-info').style.display = 'none';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('filePreviewModal'));
    modal.show();
    
    // Load first page
    await loadPreviewDataSQLite();
}

/**
 * Load file preview data for current page (SQLite-based)
 */
async function loadPreviewDataSQLite() {
    const { hami_id, number } = currentPreviewFile;
    
    console.log('Loading preview data (SQLite)...', { hami_id, number, page: currentPreviewPage });
    
    // Show loading state
    const loadingEl = document.getElementById('preview-loading');
    const errorEl = document.getElementById('preview-error');
    const tableContainerEl = document.getElementById('preview-table-container');
    const globalInfoEl = document.getElementById('preview-global-info');
    
    loadingEl.style.display = 'flex';
    errorEl.style.display = 'none';
    tableContainerEl.style.display = 'none';
    globalInfoEl.style.display = 'none';
    
    try {
        const url = `/api/preview_file?hami_id=${hami_id}&number=${number}&page=${currentPreviewPage}&per_page=50`;
        
        console.log('Fetching:', url);
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('Response received:', data);
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to load file');
        }
        
        // Update modal title and info
        document.getElementById('preview-filename').textContent = `Hami ${hami_id} - Request ${number}`;
        document.getElementById('preview-file-info').textContent = data.global_info?.reference_code || '';
        
        // Update pagination info
        const pagination = data.pagination;
        currentPreviewTotalPages = pagination.total_pages;
        
        document.getElementById('pagination-info').textContent = 
            `Page ${pagination.page} of ${pagination.total_pages}`;
        document.getElementById('preview-rows-info').textContent = 
            `Showing rows ${pagination.start_row}-${pagination.end_row} of ${pagination.total_rows}`;
        
        // Enable/disable pagination buttons
        document.getElementById('prev-page-btn').disabled = pagination.page <= 1;
        document.getElementById('next-page-btn').disabled = pagination.page >= pagination.total_pages;
        
        // Display global info
        if (data.global_info) {
            displayGlobalInfo(data.global_info);
            globalInfoEl.style.display = 'block';
        } else {
            globalInfoEl.style.display = 'none';
        }
        
        // Render table
        console.log('Rendering table...');
        renderPreviewTable(data);
        
        // Hide loading, show table
        console.log('Hiding loading, showing table');
        loadingEl.style.display = 'none';
        tableContainerEl.style.display = 'block';
        console.log('Preview loaded successfully');
        
    } catch (error) {
        console.error('Error loading preview:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
        document.getElementById('preview-error-message').textContent = error.message;
    }
}

// downloadFile function removed - SQLite uses different approach via previewFileById

async function searchByDate() {
    const startDate = document.getElementById('search-start-date').value.trim();
    const endDate = document.getElementById('search-end-date').value.trim();
    
    // Show progress bar
    showSearchProgress('date');
    
    try {
        let url = '/api/search_by_date?';
        if (startDate) url += `start_date=${startDate}&`;
        if (endDate) url += `end_date=${endDate}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            completeSearchProgress(false);
            showError('Error searching: ' + data.error);
            return;
        }
        
        completeSearchProgress(true, data.results.length);
        displaySearchResults(data.results, 'date');
        
    } catch (error) {
        completeSearchProgress(false);
        showError('Error searching by date: ' + error.message);
    }
}

async function searchByReference() {
    const referenceCode = document.getElementById('search-reference-code').value.trim();
    
    if (!referenceCode) {
        showError('Please enter a reference code');
        return;
    }
    
    // Show progress bar
    showSearchProgress('reference');
    
    try {
        const response = await fetch(
            `/api/search_by_reference?reference_code=${encodeURIComponent(referenceCode)}`
        );
        const data = await response.json();
        
        if (data.error) {
            completeSearchProgress(false);
            showError('Error searching: ' + data.error);
            return;
        }
        
        completeSearchProgress(true, data.results.length);
        displaySearchResults(data.results, 'reference');
        
    } catch (error) {
        completeSearchProgress(false);
        showError('Error searching by reference: ' + error.message);
    }
}

async function searchByField() {
    const fieldName = document.getElementById('search-field-name').value;
    const searchValue = fieldName === 'source'
        ? document.getElementById('search-field-value-source').value
        : document.getElementById('search-field-value').value.trim();

    if (!searchValue) {
        showError('Please enter a search value');
        return;
    }
    
    // Show progress bar
    showSearchProgress('field');
    
    try {
        const response = await fetch(
            `/api/search_by_field?field_name=${fieldName}&search_value=${encodeURIComponent(searchValue)}`
        );
        const data = await response.json();
        
        if (data.error) {
            completeSearchProgress(false);
            showError('Error searching: ' + data.error);
            return;
        }
        
        completeSearchProgress(true, data.results.length);
        displaySearchResults(data.results, 'field');
        
    } catch (error) {
        completeSearchProgress(false);
        showError('Error searching by field: ' + error.message);
    }
}

async function searchByEmployee() {
    const employeeName = document.getElementById('search-employee-name').value.trim();
    
    if (!employeeName) {
        showError('Please enter a person name');
        return;
    }
    
    // Show progress bar
    showSearchProgress('employee');
    
    try {
        const response = await fetch(
            `/api/search_by_employee?employee_name=${encodeURIComponent(employeeName)}`
        );
        const data = await response.json();
        
        if (data.error) {
            completeSearchProgress(false);
            showError('Error searching: ' + data.error);
            return;
        }
        
        completeSearchProgress(true, data.results.length);
        displaySearchResults(data.results, 'employee');
        
    } catch (error) {
        completeSearchProgress(false);
        showError('Error searching by person: ' + error.message);
    }
}

function displaySearchResults(results, searchType) {
    const container = document.getElementById('search-results-container');
    
    // Store results for download all functionality
    lastSearchResults = results;
    
    if (results.length === 0) {
        lastSearchResults = [];
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> No results found.
            </div>
        `;
        return;
    }
    
    // Count unique hami IDs
    const uniqueHamis = new Set(results.map(r => r.hami_id));
    
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="alert alert-success mb-0 flex-grow-1 me-3">
                <i class="bi bi-check-circle"></i> Found ${results.length} result(s) from ${uniqueHamis.size} unique Hami(s)
            </div>
            ${exportButtonHtml('search-results-container', `search_by_${searchType}`)}
        </div>
        <div class="table-responsive">
            <table class="table table-hover table-sm">
                <thead>
                    <tr>
                        <th>Hami ID</th>
                        <th>Number</th>
                        <th>Source</th>
                        <th>City</th>
                        ${searchType === 'date' ? '<th>Date Range</th>' : ''}
                        ${searchType === 'employee' ? '<th>Matched People</th>' : ''}
                        <th>Subject</th>
                        ${searchType === 'field' ? '<th>Major</th><th>Field</th>' : ''}
                        <th>Name</th>
                        <th>Reference</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    results.forEach(result => {
        const sourceBadge = renderSourceBadge(result.source);
        const hamiCell = result.hami_id === 'unknown'
            ? `<code class="text-muted">unknown</code>
               <button class="btn btn-sm btn-link p-0 ms-1" title="Set the real Hami ID"
                       onclick="editHamiId(${result.id}, '${result.hami_id}', this)">
                   <i class="bi bi-pencil-square"></i>
               </button>`
            : `<code>${result.hami_id}</code>`;
        html += `
            <tr>
                <td>${hamiCell}</td>
                <td>${result.number}</td>
                <td>${sourceBadge}</td>
                <td dir="rtl">${result.city || '-'}</td>
        `;
        
        if (searchType === 'date') {
            html += `<td><small>${result.first_date || 'N/A'}<br>to<br>${result.last_date || 'N/A'}</small></td>`;
        }
        
        if (searchType === 'employee') {
            // Display matched employees
            const matchedEmployees = result.matched_employees || [];
            const matchedDisplay = matchedEmployees.length > 0 
                ? matchedEmployees.map(e => `<span class="badge bg-info text-dark">${e}</span>`).join(' ')
                : 'N/A';
            html += `<td>${matchedDisplay}</td>`;
        }
        
        html += `
                <td><small>${result.subject || 'N/A'}</small></td>
        `;
        
        if (searchType === 'field') {
            html += `
                <td><small>${result.major || 'N/A'}</small></td>
                <td><small>${result.field || 'N/A'}</small></td>
            `;
        }
        
        html += `
                <td>${result.name || 'N/A'}</td>
                <td>
                    <code class="ref-code-copy" style="cursor: pointer;" onclick="copyToClipboard('${result.reference_code || ''}', this)" title="Click to copy">
                        <small>${result.reference_code || 'N/A'} <i class="bi bi-clipboard"></i></small>
                    </code>
                </td>
                <td class="text-nowrap">
                    <button class="btn btn-sm btn-info me-1" onclick="previewFileById('${result.hami_id}', '${result.number}')" title="View request">
                        <i class="bi bi-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

function showError(message) {
    const containers = ['files-container', 'search-results-container'];
    const activeContainer = document.querySelector('.tab-pane.active [id$="-container"]');
    
    if (activeContainer) {
        activeContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> ${message}
            </div>
        `;
    } else {
        alert(message);
    }
}

/**
 * Render a small colored badge for a request's data source tag.
 */
function renderSourceBadge(source) {
    const labels = {
        'scraper': ['bg-primary', 'Scraper'],
        'excel': ['bg-success', 'Excel'],
        'both': ['bg-purple', 'Both']
    };
    const [cls, label] = labels[source] || ['bg-secondary', source || '-'];
    const style = cls === 'bg-purple' ? ' style="background-color:#6f42c1;"' : '';
    return `<span class="badge ${cls}"${style}>${label}</span>`;
}

/**
 * Export whatever table is currently rendered inside a container to a CSV file
 * that Excel opens directly. Checkbox and action columns are dropped, and the
 * leading BOM is what stops Excel from mangling the Persian text.
 */
function exportTableToExcel(containerId, filenamePrefix) {
    const table = document.querySelector(`#${containerId} table`);
    if (!table || !table.querySelector('tbody tr')) {
        alert('There is no table to export yet.');
        return;
    }

    const headerCells = Array.from(table.querySelectorAll('thead tr th'));
    const skipped = new Set();
    headerCells.forEach((th, index) => {
        if (th.querySelector('input, button') || /^actions?$/i.test(th.textContent.trim())) {
            skipped.add(index);
        }
    });

    const cellText = cell => (cell.innerText || cell.textContent || '').replace(/\s+/g, ' ').trim();
    const toRow = cells => Array.from(cells)
        .filter((_, index) => !skipped.has(index))
        .map(cell => `"${cellText(cell).replace(/"/g, '""')}"`)
        .join(',');

    const lines = [toRow(headerCells)];
    table.querySelectorAll('tbody tr').forEach(row => lines.push(toRow(row.cells)));

    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
    const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${filenamePrefix}_${stamp}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

function exportButtonHtml(containerId, filenamePrefix) {
    return `<button class="btn btn-sm btn-outline-success text-nowrap"
                    onclick="exportTableToExcel('${containerId}', '${filenamePrefix}')">
                <i class="bi bi-file-earmark-excel"></i> Export to Excel
            </button>`;
}

/**
 * Manually correct the Hami ID on a request (e.g. the 'unknown' sentinel
 * used for tickets that only came from the excel task-list source, which
 * doesn't say which Hami staff member handled them).
 */
async function editHamiId(requestId, currentHamiId, buttonEl) {
    const newHamiId = prompt(`Enter the real Hami ID for this request (currently "${currentHamiId}"):`);
    if (!newHamiId || !newHamiId.trim() || newHamiId.trim() === currentHamiId) {
        return;
    }

    try {
        const response = await fetch('/api/update_request_hami_id', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId, hami_id: newHamiId.trim() })
        });
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to update Hami ID');
        }

        const cell = buttonEl.closest('td');
        cell.innerHTML = `<code>${newHamiId.trim()}</code>`;
    } catch (error) {
        console.error('Error updating hami_id:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Bulk Hami reassignment (Reassign Hami tab).
 *
 * Correcting the excel-only 'unknown' backlog one prompt at a time is not realistic, so
 * this filters requests down, lets the user tick a selection, and moves them together.
 */
let reassignResults = [];

async function loadReassignRequests() {
    const container = document.getElementById('reassign-results-container');
    const params = new URLSearchParams({
        hami_id: document.getElementById('reassign-filter-hami').value.trim(),
        city: document.getElementById('reassign-filter-city').value,
        source: document.getElementById('reassign-filter-source').value,
        start_date: document.getElementById('reassign-filter-start').value.trim(),
        end_date: document.getElementById('reassign-filter-end').value.trim()
    });

    container.innerHTML = `
        <div class="alert alert-info">
            <i class="bi bi-hourglass-split"></i> Loading requests...
        </div>
    `;

    try {
        const response = await fetch(`/api/find_requests?${params}`);
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to load requests');
        }
        reassignResults = data.results;
        renderReassignResults(data);
    } catch (error) {
        console.error('Error loading requests to reassign:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> ${error.message}
            </div>
        `;
        updateReassignSelection();
    }
}

function renderReassignResults(data) {
    const container = document.getElementById('reassign-results-container');

    if (!data.results.length) {
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-info-circle"></i> No requests match these filters.
            </div>
        `;
        updateReassignSelection();
        return;
    }

    const rows = data.results.map(r => `
        <tr>
            <td><input type="checkbox" class="form-check-input reassign-check" value="${r.id}"
                       onchange="updateReassignSelection()"></td>
            <td><code>${r.hami_id}</code></td>
            <td><code class="text-primary" style="cursor:pointer;"
                      onclick="copyToClipboard('${r.reference_code}', this)">${r.reference_code || '-'}</code></td>
            <td>${renderSourceBadge(r.source)}</td>
            <td>${r.city || '-'}</td>
            <td dir="rtl">${r.subject || '-'}</td>
            <td dir="rtl">${r.name || '-'}</td>
            <td>${r.first_date || '-'}</td>
            <td class="text-center">
                <span class="badge ${r.message_count ? 'bg-secondary' : 'bg-light text-dark'}">${r.message_count}</span>
            </td>
        </tr>
    `).join('');

    container.innerHTML = `
        ${data.truncated ? `
        <div class="alert alert-warning">
            <i class="bi bi-exclamation-triangle"></i>
            Showing the first ${data.count} matches only. Narrow the filters to see the rest.
        </div>` : ''}
        <div class="d-flex justify-content-between align-items-center mb-2">
            <p class="text-muted mb-0">${data.count} request(s) found.</p>
            ${exportButtonHtml('reassign-results-container', 'reassign_candidates')}
        </div>
        <div class="table-responsive" style="max-height: 600px; overflow-y: auto;">
            <table class="table table-sm table-striped table-hover">
                <thead class="table-dark position-sticky top-0">
                    <tr>
                        <th style="width: 40px;">
                            <input type="checkbox" class="form-check-input" id="reassign-check-all"
                                   onchange="setAllReassignChecks(this.checked)">
                        </th>
                        <th>Current Hami</th>
                        <th>Ref. Code</th>
                        <th>Source</th>
                        <th>City</th>
                        <th>Subject</th>
                        <th>Name</th>
                        <th>First Date</th>
                        <th class="text-center">Msgs</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
    updateReassignSelection();
}

function setAllReassignChecks(checked) {
    document.querySelectorAll('.reassign-check').forEach(cb => { cb.checked = checked; });
    const headerCheck = document.getElementById('reassign-check-all');
    if (headerCheck) headerCheck.checked = checked;
    updateReassignSelection();
}

function updateReassignSelection() {
    const selected = document.querySelectorAll('.reassign-check:checked').length;
    const total = document.querySelectorAll('.reassign-check').length;
    document.getElementById('reassign-selected-count').textContent = selected;
    document.getElementById('reassign-apply-btn').disabled = selected === 0;
    const headerCheck = document.getElementById('reassign-check-all');
    if (headerCheck) {
        headerCheck.checked = total > 0 && selected === total;
        headerCheck.indeterminate = selected > 0 && selected < total;
    }
}

async function applyBulkHamiReassign() {
    const targetHami = document.getElementById('reassign-target-hami').value.trim();
    const ids = Array.from(document.querySelectorAll('.reassign-check:checked'))
        .map(cb => parseInt(cb.value, 10));

    if (!targetHami) {
        alert('Enter the Hami ID to assign the selected requests to.');
        return;
    }
    if (!ids.length) {
        return;
    }
    if (!confirm(`Reassign ${ids.length} request(s) to Hami "${targetHami}"?\n\n` +
                 `Each one is given a new number under that Hami. This cannot be undone automatically.`)) {
        return;
    }

    const button = document.getElementById('reassign-apply-btn');
    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Applying...';

    try {
        const response = await fetch('/api/bulk_update_request_hami_id', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_ids: ids, hami_id: targetHami })
        });
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to reassign requests');
        }

        let message = `${data.updated} request(s) moved to Hami "${targetHami}".`;
        if (data.already_assigned.length) {
            message += ` ${data.already_assigned.length} already belonged to that Hami.`;
        }
        if (data.missing.length) {
            message += ` ${data.missing.length} no longer exist.`;
        }
        alert(message);
        await loadReassignRequests();
    } catch (error) {
        console.error('Error reassigning requests:', error);
        alert('Error: ' + error.message);
    } finally {
        button.innerHTML = originalHtml;
        updateReassignSelection();
    }
}

/**
 * Add or update the display name shown for a Hami ID (Hami Names tab).
 */
async function editHamiName(hamiId, currentName, buttonEl) {
    const newName = prompt(`Enter the display name for Hami ${hamiId} (currently "${currentName || 'Unknown'}"):`);
    if (!newName || !newName.trim() || newName.trim() === currentName) {
        return;
    }

    try {
        const response = await fetch('/api/hami_names/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hami_id: hamiId, full_name: newName.trim() })
        });
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to update name');
        }

        buttonEl.closest('tr').querySelector('.hami-name-cell').textContent = newName.trim();
    } catch (error) {
        console.error('Error updating hami name:', error);
        alert('Error: ' + error.message);
    }
}

function copyToClipboard(text, element) {
    navigator.clipboard.writeText(text).then(() => {
        // Show feedback
        const originalContent = element.innerHTML;
        element.innerHTML = '<i class="bi bi-check"></i> Copied!';
        element.classList.add('text-success');
        
        setTimeout(() => {
            element.innerHTML = originalContent;
            element.classList.remove('text-success');
        }, 1500);
    }).catch(err => {
        console.error('Failed to copy: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // Show feedback
        const originalContent = element.innerHTML;
        element.innerHTML = '<i class="bi bi-check"></i> Copied!';
        element.classList.add('text-success');
        
        setTimeout(() => {
            element.innerHTML = originalContent;
            element.classList.remove('text-success');
        }, 1500);
    });
}

async function downloadAllResults() {
    if (!lastSearchResults || lastSearchResults.length === 0) {
        showError('No search results to download');
        return;
    }
    
    // Show loading state
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Preparing...';
    
    try {
        const response = await fetch('/api/download_search_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ results: lastSearchResults })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Download failed');
        }
        
        // Get the blob and create download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'search_results.zip';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch) {
                filename = filenameMatch[1].replace(/"/g, '');
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        showError('Error downloading results: ' + error.message);
    } finally {
        // Restore button state
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

async function downloadAllBrowseFiles() {
    if (!lastBrowseFiles || lastBrowseFiles.length === 0) {
        showError('No files to download');
        return;
    }
    
    // Show loading state
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Preparing...';
    
    try {
        const response = await fetch('/api/download_browse_files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                files: lastBrowseFiles,
                hami_id: currentHami
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Download failed');
        }
        
        // Get the blob and create download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'browse_files.zip';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch) {
                filename = filenameMatch[1].replace(/"/g, '');
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        showError('Error downloading files: ' + error.message);
    } finally {
        // Restore button state
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

// =========================================
// File Preview Functions
// =========================================

// previewFile function removed - replaced by previewFileById (SQLite-based)

// loadPreviewData function removed - replaced by loadPreviewDataSQLite (SQLite-based)

/**
 * Display global info from hami file for combined files
 */
function displayGlobalInfo(info) {
    const refCodeEl = document.getElementById('global-reference-code');
    const refCode = info.reference_code || '-';
    refCodeEl.textContent = refCode + (refCode !== '-' ? ' ' : '');
    refCodeEl.dataset.refcode = refCode;
    // Add clipboard icon if there's a reference code
    if (refCode !== '-') {
        refCodeEl.innerHTML = refCode + ' <i class="bi bi-clipboard"></i>';
    }
    document.getElementById('global-subject').textContent = info.subject || '-';
    document.getElementById('global-name').textContent = info.name || '-';
    document.getElementById('global-student-id').textContent = info.student_id || '-';
    document.getElementById('global-major').textContent = info.major || '-';
    document.getElementById('global-field').textContent = info.field || '-';
    document.getElementById('global-national-id').textContent = info.national_id || '-';
}

/**
 * Navigate to prev/next page in preview
 */
function loadPreviewPage(direction) {
    if (direction === 'prev' && currentPreviewPage > 1) {
        currentPreviewPage--;
    } else if (direction === 'next' && currentPreviewPage < currentPreviewTotalPages) {
        currentPreviewPage++;
    } else {
        return; // No navigation needed
    }
    
    // SQLite-based preview
    loadPreviewDataSQLite();
}

/**
 * Render the preview table with data
 */
function renderPreviewTable(data) {
    const thead = document.getElementById('preview-table-head');
    const tbody = document.getElementById('preview-table-body');
    const table = document.querySelector('.file-preview-table');
    
    // Add file type class
    table.classList.remove('combined-file', 'hami-file');
    table.classList.add(data.file_type === 'combined' ? 'combined-file' : 'hami-file');
    
    // Column configurations for styling
    const columnConfig = getColumnConfig(data.file_type);
    
    // Render header
    let headerHtml = '<tr><th class="row-number-cell">#</th>';
    data.columns.forEach(col => {
        const config = columnConfig[col] || {};
        const className = config.headerClass || '';
        const displayName = config.displayName || formatColumnName(col);
        headerHtml += `<th class="${className}">${displayName}</th>`;
    });
    headerHtml += '</tr>';
    thead.innerHTML = headerHtml;
    
    // Render body
    let bodyHtml = '';
    const startRow = data.pagination.start_row;
    
    data.records.forEach((record, index) => {
        bodyHtml += '<tr>';
        bodyHtml += `<td class="row-number-cell">${startRow + index}</td>`;
        
        data.columns.forEach(col => {
            const value = record[col];
            const config = columnConfig[col] || {};
            const cellHtml = formatCellValue(value, col, config);
            bodyHtml += cellHtml;
        });
        
        bodyHtml += '</tr>';
    });
    
    tbody.innerHTML = bodyHtml;
}

/**
 * Get column configuration based on file type
 */
function getColumnConfig(fileType) {
    if (fileType === 'combined') {
        return {
            'date': { headerClass: 'col-date', cellClass: 'date-cell', displayName: 'Date' },
            'message': { headerClass: 'col-message', cellClass: 'message-cell', displayName: 'Message', isLongText: true },
            'from': { headerClass: 'col-from', cellClass: 'name-cell', displayName: 'From', isPersian: true },
            'to': { headerClass: 'col-to', cellClass: 'name-cell', displayName: 'To', isPersian: true },
            'to_email': { headerClass: 'col-email', cellClass: 'code-cell', displayName: 'To Email' },
            'from_id': { headerClass: 'col-id', cellClass: 'code-cell', displayName: 'From ID' },
            'to_id': { headerClass: 'col-id', cellClass: 'code-cell', displayName: 'To ID' },
            'matched': { headerClass: 'col-matched', cellClass: 'bool-cell', displayName: 'Matched', isBoolean: true }
        };
    } else {
        return {
            'number': { headerClass: 'col-number', cellClass: 'row-number-cell', displayName: 'No.' },
            'subject': { headerClass: 'col-subject', cellClass: 'subject-cell', displayName: 'Subject', isPersian: true },
            'reference_code': { headerClass: 'col-reference', cellClass: 'reference-cell', displayName: 'Reference Code' },
            'major': { headerClass: 'col-major', cellClass: 'name-cell', displayName: 'Major', isPersian: true },
            'name': { headerClass: 'col-name', cellClass: 'name-cell', displayName: 'Name', isPersian: true },
            'national_id': { headerClass: 'col-national-id', cellClass: 'code-cell', displayName: 'National ID' },
            'student_id': { headerClass: 'col-student-id', cellClass: 'code-cell', displayName: 'Student ID' },
            'field': { headerClass: 'col-field', cellClass: 'name-cell', displayName: 'Field', isPersian: true }
        };
    }
}

/**
 * Format column name for display
 */
function formatColumnName(colName) {
    return colName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Format cell value based on column configuration
 */
function formatCellValue(value, colName, config) {
    const cellClass = config.cellClass || '';
    
    // Handle null/empty values
    if (value === null || value === undefined || value === '' || value === '<empty>') {
        return `<td class="${cellClass}"><span class="empty-cell">—</span></td>`;
    }
    
    // Convert to string
    let strValue = String(value);
    
    // Handle boolean values
    if (config.isBoolean) {
        const boolClass = strValue.toLowerCase() === 'true' ? 'true' : 'false';
        const displayValue = strValue.toLowerCase() === 'true' ? '✓ Yes' : '✗ No';
        return `<td class="${cellClass} ${boolClass}">${displayValue}</td>`;
    }
    
    // Check if content looks like Persian/Arabic text
    const hasPersian = config.isPersian || containsPersianText(strValue);
    const rtlClass = hasPersian ? 'rtl-text' : '';
    
    // Handle long text (like messages)
    if (config.isLongText || strValue.length > 200) {
        const escapedValue = escapeHtml(strValue);
        const truncated = strValue.length > 300;
        const displayValue = truncated ? escapeHtml(strValue.substring(0, 300)) + '...' : escapedValue;
        
        return `<td class="${cellClass}">
            <div class="cell-content ${rtlClass}" ${truncated ? `title="${escapedValue}"` : ''}>
                ${displayValue.replace(/\n/g, '<br>')}
            </div>
        </td>`;
    }
    
    // Regular cell
    const escapedValue = escapeHtml(strValue);
    return `<td class="${cellClass}">
        <span class="cell-content ${rtlClass}">${escapedValue}</span>
    </td>`;
}

/**
 * Check if text contains Persian/Arabic characters
 */
function containsPersianText(text) {
    // Persian/Arabic Unicode range
    const persianRegex = /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/;
    return persianRegex.test(text);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// ========================================
// Graph View Functionality
// ========================================

// Graph state
let graphNetwork = null;
let graphData = null;
let graphPhysicsEnabled = true;
let currentGraphFile = null;

/**
 * Open graph view for a request (SQLite-based)
 */
function openGraphView(hamiId, number) {
    currentGraphFile = {
        hami_id: hamiId,
        number: number
    };
    
    // Update modal title
    document.getElementById('graph-filename').textContent = `Graph: Hami ${hamiId} - Request ${number}`;
    document.getElementById('graph-stats').textContent = 'Loading...';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('graphViewModal'));
    modal.show();
    
    // Reset UI state
    document.getElementById('graph-loading').style.display = 'flex';
    document.getElementById('graph-error').style.display = 'none';
    document.getElementById('graph-container').innerHTML = '';
    hideGraphInfoPanel();
    
    // Load graph data
    loadGraphData(hamiId, number);
}

/**
 * Load graph data from API (SQLite-based)
 */
async function loadGraphData(hamiId, number) {
    try {
        const params = new URLSearchParams({
            hami_id: hamiId,
            number: number
        });
        
        const response = await fetch(`/api/preview_file_graph?${params}`);
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to load graph data');
        }
        
        graphData = data;
        
        // Update stats
        document.getElementById('graph-stats').textContent = 
            `${data.stats.total_nodes} nodes • ${data.stats.total_edges} messages`;
        
        // Hide loading, render graph
        document.getElementById('graph-loading').style.display = 'none';
        
        if (data.stats.total_nodes === 0) {
            showGraphEmpty();
        } else {
            renderGraph(data);
        }
        
    } catch (error) {
        console.error('Error loading graph:', error);
        document.getElementById('graph-loading').style.display = 'none';
        document.getElementById('graph-error').style.display = 'block';
        document.getElementById('graph-error-message').textContent = error.message;
    }
}

/**
 * Show empty graph message
 */
function showGraphEmpty() {
    const container = document.getElementById('graph-container');
    container.innerHTML = `
        <div class="graph-empty-message">
            <i class="bi bi-diagram-3"></i>
            <h4>No Valid Message Flow</h4>
            <p class="text-muted">
                This file does not contain valid sender/receiver data for visualization.<br>
                (Messages with empty or "Not in workflow" IDs are excluded)
            </p>
        </div>
    `;
}

/**
 * Render the graph using vis.js
 */
function renderGraph(data) {
    const container = document.getElementById('graph-container');
    
    // Prepare nodes
    const nodes = data.nodes.map(node => ({
        id: node.id,
        label: truncateLabel(node.label, 20),
        title: buildNodeTooltip(node),
        shape: 'circle',
        size: Math.min(20 + (node.messages_sent + node.messages_received) * 2, 50),
        color: {
            background: getNodeColor(node),
            border: '#388E3C',
            highlight: {
                background: '#81C784',
                border: '#2E7D32'
            }
        },
        font: {
            face: 'Vazirmatn, Tahoma, sans-serif',
            size: 12,
            color: '#333'
        },
        // Store original data
        originalData: node
    }));
    
    // Prepare edges
    const edges = data.edges.map((edge, index) => ({
        id: `edge-${index}`,
        from: edge.from,
        to: edge.to,
        arrows: 'to',
        color: {
            color: '#2196F3',
            highlight: '#1976D2',
            opacity: 0.7
        },
        width: 2,
        smooth: {
            type: 'curvedCW',
            roundness: 0.2
        },
        // Store original data
        originalData: edge
    }));
    
    // Create vis.js dataset
    const visData = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };
    
    // Graph options
    const options = {
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 150,
                springConstant: 0.08
            },
            stabilization: {
                iterations: 150,
                updateInterval: 25
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true
        },
        nodes: {
            borderWidth: 2,
            shadow: true
        },
        edges: {
            shadow: true
        }
    };
    
    // Create network
    graphNetwork = new vis.Network(container, visData, options);
    
    // Event handlers
    graphNetwork.on('click', function(params) {
        if (params.nodes.length > 0) {
            // Node clicked
            const nodeId = params.nodes[0];
            const nodeData = visData.nodes.get(nodeId);
            showNodeInfo(nodeData.originalData);
        } else if (params.edges.length > 0) {
            // Edge clicked
            const edgeId = params.edges[0];
            const edgeData = visData.edges.get(edgeId);
            showEdgeInfo(edgeData.originalData);
        } else {
            hideGraphInfoPanel();
        }
    });
    
    graphNetwork.on('hoverNode', function(params) {
        container.style.cursor = 'pointer';
    });
    
    graphNetwork.on('blurNode', function(params) {
        container.style.cursor = 'default';
    });
    
    graphNetwork.on('hoverEdge', function(params) {
        container.style.cursor = 'pointer';
    });
    
    graphNetwork.on('blurEdge', function(params) {
        container.style.cursor = 'default';
    });
}

/**
 * Get node color based on activity
 */
function getNodeColor(node) {
    const total = node.messages_sent + node.messages_received;
    if (total > 5) return '#4CAF50';
    if (total > 2) return '#8BC34A';
    return '#C8E6C9';
}

/**
 * Truncate label for display
 */
function truncateLabel(label, maxLength) {
    if (label.length <= maxLength) return label;
    return label.substring(0, maxLength) + '...';
}

/**
 * Build tooltip for node
 */
function buildNodeTooltip(node) {
    return `
        <div style="text-align: right; direction: rtl; font-family: Vazirmatn, Tahoma;">
            <strong>${escapeHtml(node.title)}</strong><br>
            <small>Sent: ${node.messages_sent} | Received: ${node.messages_received}</small>
        </div>
    `;
}

/**
 * Show node info in panel
 */
function showNodeInfo(node) {
    document.getElementById('graph-info-title').innerHTML = '<i class="bi bi-person-circle"></i> Person Details';
    
    let html = `
        <div class="info-label">Name</div>
        <div class="info-value persian-text">${escapeHtml(node.title)}</div>
        
        <div class="info-label">ID</div>
        <div class="info-value"><code style="font-size: 0.75rem;">${escapeHtml(node.id)}</code></div>
        
        <div class="info-label">Messages Sent</div>
        <div class="info-value">${node.messages_sent}</div>
        
        <div class="info-label">Messages Received</div>
        <div class="info-value">${node.messages_received}</div>
    `;
    
    document.getElementById('graph-info-content').innerHTML = html;
    document.getElementById('graph-info-panel').style.display = 'block';
}

/**
 * Show edge info in panel
 */
function showEdgeInfo(edge) {
    document.getElementById('graph-info-title').innerHTML = '<i class="bi bi-envelope"></i> Message Details';
    
    let html = `
        <div class="info-label">Date</div>
        <div class="info-value">${escapeHtml(edge.date || 'N/A')}</div>
        
        <div class="info-label">From</div>
        <div class="info-value persian-text">${escapeHtml(edge.from_name)}</div>
        
        <div class="info-label">To</div>
        <div class="info-value persian-text">${escapeHtml(edge.to_name)}</div>
        
        <div class="info-label">Message</div>
        <div class="message-text">${escapeHtml(edge.message)}</div>
    `;
    
    document.getElementById('graph-info-content').innerHTML = html;
    document.getElementById('graph-info-panel').style.display = 'block';
}

/**
 * Hide the graph info panel
 */
function hideGraphInfoPanel() {
    document.getElementById('graph-info-panel').style.display = 'none';
}

/**
 * Reset graph view to fit all nodes
 */
function resetGraphView() {
    if (graphNetwork) {
        graphNetwork.fit({
            animation: {
                duration: 500,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

/**
 * Toggle graph physics simulation
 */
function toggleGraphPhysics() {
    if (graphNetwork) {
        graphPhysicsEnabled = !graphPhysicsEnabled;
        graphNetwork.setOptions({
            physics: { enabled: graphPhysicsEnabled }
        });
        
        const btnText = document.getElementById('physics-btn-text');
        if (graphPhysicsEnabled) {
            btnText.textContent = 'Pause Physics';
        } else {
            btnText.textContent = 'Resume Physics';
        }
    }
}

// Clean up graph when modal is closed
document.addEventListener('DOMContentLoaded', function() {
    const graphModal = document.getElementById('graphViewModal');
    if (graphModal) {
        graphModal.addEventListener('hidden.bs.modal', function() {
            if (graphNetwork) {
                graphNetwork.destroy();
                graphNetwork = null;
            }
            graphData = null;
            graphPhysicsEnabled = true;
            document.getElementById('physics-btn-text').textContent = 'Pause Physics';
        });
    }
    
    // Load no-workflow requests when that tab is shown
    const noWorkflowTab = document.getElementById('noworkflow-tab');
    if (noWorkflowTab) {
        noWorkflowTab.addEventListener('shown.bs.tab', function() {
            loadNoWorkflowRequests();
        });
    }
});


// ==================== NO WORKFLOW MANAGEMENT ====================

// Sorting state for no workflow table
let noWorkflowSortColumn = 'last_date';
let noWorkflowSortDirection = 'desc';
let noWorkflowData = [];
let noWorkflowChart = null;
let currentChartType = 'hami';

// ==================== NO WORKFLOW CHARTS ====================

/**
 * Switch between different chart views
 */
function switchNoWorkflowChart(type) {
    currentChartType = type;
    
    // Update button states
    document.querySelectorAll('[id^="chart-btn-"]').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`chart-btn-${type}`).classList.add('active');
    
    // Render the selected chart
    renderNoWorkflowChart();
}

/**
 * Render the no workflow chart based on current type
 */
function renderNoWorkflowChart() {
    if (noWorkflowData.length === 0) {
        document.getElementById('no-workflow-chart-legend').innerHTML = 
            '<span class="text-success">No data to display - all requests have workflow!</span>';
        return;
    }
    
    // Destroy existing chart
    if (noWorkflowChart) {
        noWorkflowChart.destroy();
    }
    
    const ctx = document.getElementById('noWorkflowChart').getContext('2d');
    
    switch (currentChartType) {
        case 'hami':
            renderHamiChart(ctx);
            break;
        case 'month':
            renderMonthChart(ctx);
            break;
        case 'timeline':
            renderTimelineChart(ctx);
            break;
    }
}

/**
 * Render chart showing count per Hami ID
 */
function renderHamiChart(ctx) {
    // Aggregate data by Hami ID
    const hamiCounts = {};
    const hamiDateRanges = {};
    
    noWorkflowData.forEach(req => {
        const hamiId = req.hami_id || 'Unknown';
        if (!hamiCounts[hamiId]) {
            hamiCounts[hamiId] = 0;
            hamiDateRanges[hamiId] = { min: req.first_date, max: req.first_date };
        }
        hamiCounts[hamiId]++;
        
        // Track date range
        if (req.first_date < hamiDateRanges[hamiId].min) {
            hamiDateRanges[hamiId].min = req.first_date;
        }
        if (req.first_date > hamiDateRanges[hamiId].max) {
            hamiDateRanges[hamiId].max = req.first_date;
        }
    });
    
    // Sort by count descending
    const sortedHamis = Object.entries(hamiCounts)
        .sort((a, b) => b[1] - a[1]);
    
    const labels = sortedHamis.map(([id, count]) => `Hami ${id}`);
    const data = sortedHamis.map(([id, count]) => count);
    
    // Generate colors
    const colors = generateColors(labels.length);
    
    noWorkflowChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Requests without Workflow',
                data: data,
                backgroundColor: colors.map(c => c + '80'),
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const hamiId = sortedHamis[context.dataIndex][0];
                            const range = hamiDateRanges[hamiId];
                            return `Date range: ${range.min?.split(' ')[0] || '-'} to ${range.max?.split(' ')[0] || '-'}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Requests'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Hami ID'
                    }
                }
            }
        }
    });
    
    // Update legend
    document.getElementById('no-workflow-chart-legend').innerHTML = 
        `Showing ${labels.length} Hami(s) with missing workflow data. Hover over bars for date range.`;
}

/**
 * Render chart showing count per month
 */
function renderMonthChart(ctx) {
    // Aggregate data by month
    const monthCounts = {};
    
    noWorkflowData.forEach(req => {
        if (req.first_date) {
            // Extract year-month from date (format: 1404-02-10 11:20:00)
            const yearMonth = req.first_date.substring(0, 7); // "1404-02"
            monthCounts[yearMonth] = (monthCounts[yearMonth] || 0) + 1;
        }
    });
    
    // Sort by date
    const sortedMonths = Object.entries(monthCounts)
        .sort((a, b) => a[0].localeCompare(b[0]));
    
    const labels = sortedMonths.map(([month]) => month);
    const data = sortedMonths.map(([, count]) => count);
    
    noWorkflowChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Requests without Workflow',
                data: data,
                backgroundColor: 'rgba(255, 193, 7, 0.6)',
                borderColor: 'rgb(255, 193, 7)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Requests'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month (Persian Year-Month)'
                    }
                }
            }
        }
    });
    
    // Update legend
    document.getElementById('no-workflow-chart-legend').innerHTML = 
        `Showing distribution across ${labels.length} month(s).`;
}

/**
 * Render timeline chart showing Hami activity over time
 */
function renderTimelineChart(ctx) {
    // Group by Hami and month
    const hamiMonthData = {};
    const allMonths = new Set();
    
    noWorkflowData.forEach(req => {
        const hamiId = req.hami_id || 'Unknown';
        if (req.first_date) {
            const yearMonth = req.first_date.substring(0, 7);
            allMonths.add(yearMonth);
            
            if (!hamiMonthData[hamiId]) {
                hamiMonthData[hamiId] = {};
            }
            hamiMonthData[hamiId][yearMonth] = (hamiMonthData[hamiId][yearMonth] || 0) + 1;
        }
    });
    
    // Sort months
    const sortedMonths = Array.from(allMonths).sort();
    
    // Get top Hamis by total count
    const hamiTotals = Object.entries(hamiMonthData)
        .map(([hamiId, months]) => [hamiId, Object.values(months).reduce((a, b) => a + b, 0)])
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10); // Top 10
    
    const colors = generateColors(hamiTotals.length);
    
    const datasets = hamiTotals.map(([hamiId], index) => ({
        label: `Hami ${hamiId}`,
        data: sortedMonths.map(month => hamiMonthData[hamiId]?.[month] || 0),
        backgroundColor: colors[index] + '80',
        borderColor: colors[index],
        borderWidth: 2,
        fill: false,
        tension: 0.1
    }));
    
    noWorkflowChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedMonths,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        font: { size: 10 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: false,
                    title: {
                        display: true,
                        text: 'Requests'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    
    // Update legend
    document.getElementById('no-workflow-chart-legend').innerHTML = 
        `Showing top ${hamiTotals.length} Hami(s) across ${sortedMonths.length} month(s). Each line represents a Hami's missing workflow over time.`;
}

/**
 * Generate distinct colors for charts
 */
function generateColors(count) {
    const baseColors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#7C4DFF', '#00BCD4', '#8BC34A', '#F44336',
        '#3F51B5', '#009688', '#FFC107', '#795548', '#607D8B'
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
}

/**
 * Sort no workflow requests data
 */
function sortNoWorkflowData(column) {
    // Toggle direction if clicking same column
    if (noWorkflowSortColumn === column) {
        noWorkflowSortDirection = noWorkflowSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        noWorkflowSortColumn = column;
        noWorkflowSortDirection = 'asc';
    }
    
    // Sort the data
    noWorkflowData.sort((a, b) => {
        let valA = a[column] || '';
        let valB = b[column] || '';
        
        // Handle numeric columns
        if (column === 'hami_id' || column === 'total_messages') {
            valA = parseInt(valA) || 0;
            valB = parseInt(valB) || 0;
        }
        
        // Compare primary column
        let result = 0;
        if (valA < valB) result = -1;
        else if (valA > valB) result = 1;
        
        // If primary column is equal, sort by date as secondary
        if (result === 0 && column !== 'last_date') {
            const dateA = a['last_date'] || '';
            const dateB = b['last_date'] || '';
            if (dateA < dateB) result = -1;
            else if (dateA > dateB) result = 1;
        }
        
        return noWorkflowSortDirection === 'asc' ? result : -result;
    });
    
    // Re-render the table
    renderNoWorkflowTable();
}

/**
 * Get sort indicator icon
 */
function getSortIcon(column) {
    if (noWorkflowSortColumn !== column) {
        return '<i class="bi bi-arrow-down-up text-muted ms-1"></i>';
    }
    return noWorkflowSortDirection === 'asc' 
        ? '<i class="bi bi-sort-up ms-1"></i>' 
        : '<i class="bi bi-sort-down ms-1"></i>';
}

/**
 * Render the no workflow table
 */
function renderNoWorkflowTable() {
    const container = document.getElementById('no-workflow-list-container');
    
    if (noWorkflowData.length === 0) {
        container.innerHTML = `
            <div class="alert alert-success">
                <i class="bi bi-check-circle"></i> Great! All requests have workflow data.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="d-flex justify-content-end mb-2">
            ${exportButtonHtml('no-workflow-list-container', 'requests_without_workflow')}
        </div>
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th style="cursor: pointer;" onclick="sortNoWorkflowData('hami_id')">
                            Hami ID ${getSortIcon('hami_id')}
                        </th>
                        <th>Reference Code</th>
                        <th>Student Name</th>
                        <th>Subject</th>
                        <th style="cursor: pointer;" onclick="sortNoWorkflowData('total_messages')">
                            Messages ${getSortIcon('total_messages')}
                        </th>
                        <th style="cursor: pointer;" onclick="sortNoWorkflowData('last_date')">
                            Last Date ${getSortIcon('last_date')}
                        </th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const req of noWorkflowData) {
        html += `
            <tr>
                <td><span class="badge bg-secondary">${req.hami_id || '-'}</span></td>
                <td><code class="small">${req.reference_code || '-'}</code></td>
                <td dir="rtl">${req.name || '-'}</td>
                <td dir="rtl" class="text-truncate" style="max-width: 200px;" title="${req.subject || ''}">${req.subject || '-'}</td>
                <td><span class="badge bg-warning text-dark">${req.total_messages}</span></td>
                <td class="small">${req.last_date || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-warning" onclick="openWorkflowEditor(${req.id})">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                </td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Load list of requests with no workflow
 */
async function loadNoWorkflowRequests() {
    const container = document.getElementById('no-workflow-list-container');
    const requestCount = document.getElementById('no-workflow-request-count');
    const messageCount = document.getElementById('no-workflow-message-count');
    
    container.innerHTML = `
        <div class="alert alert-info">
            <i class="bi bi-hourglass-split"></i> Loading requests with no workflow...
        </div>
    `;
    
    try {
        const response = await fetch('/api/no_workflow_requests');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load requests');
        }
        
        // Update statistics
        requestCount.textContent = data.total_requests;
        messageCount.textContent = data.total_messages;
        
        // Store data globally for sorting
        noWorkflowData = data.requests;
        
        // Sort by default column and render table
        sortNoWorkflowData(noWorkflowSortColumn);
        
        // Render the chart
        renderNoWorkflowChart();
        
    } catch (error) {
        console.error('Error loading no workflow requests:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Error: ${error.message}
            </div>
        `;
    }
}

/**
 * Search for a request by reference code for workflow editing
 */
async function searchRequestForWorkflow() {
    const referenceCode = document.getElementById('workflow-search-reference').value.trim();
    
    if (!referenceCode) {
        alert('Please enter a reference code.');
        return;
    }
    
    try {
        const response = await fetch(`/api/search_request_by_reference?reference_code=${encodeURIComponent(referenceCode)}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Search failed');
        }
        
        if (!data.found) {
            alert('No request found with this reference code.');
            return;
        }
        
        // Open the workflow editor with this request
        openWorkflowEditorWithData(data.request, data.messages);
        
    } catch (error) {
        console.error('Error searching request:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Open the workflow editor modal for a specific request
 */
async function openWorkflowEditor(requestId) {
    try {
        const response = await fetch(`/api/no_workflow_request_detail/${requestId}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load request details');
        }
        
        openWorkflowEditorWithData(data.request, data.messages);
        
    } catch (error) {
        console.error('Error opening workflow editor:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Open workflow editor with provided data
 */
function openWorkflowEditorWithData(request, messages) {
    // Reset forms
    resetInteractiveForm();
    
    // Set request info
    document.getElementById('workflow-edit-request-id').value = request.id;
    document.getElementById('workflow-edit-reference').textContent = request.reference_code || '-';
    document.getElementById('workflow-edit-name').textContent = request.name || '-';
    document.getElementById('workflow-edit-subject').textContent = request.subject || '-';
    
    // Build messages table
    const tableBody = document.getElementById('workflow-messages-table');
    let html = '';
    
    messages.forEach((msg, index) => {
        const isNoWorkflow = msg.from_name === 'Not in workflow' && msg.to_name === 'Not in workflow';
        const rowClass = isNoWorkflow ? 'table-warning' : '';
        
        // Truncate message for preview
        const msgPreview = msg.message ? (msg.message.length > 50 ? msg.message.substring(0, 50) + '...' : msg.message) : '-';
        
        html += `
            <tr class="${rowClass}" data-message-id="${msg.id}">
                <td>${index + 1}</td>
                <td class="small">${msg.date || '-'}</td>
                <td dir="rtl" class="small text-truncate" style="max-width: 200px;" title="${msg.message || ''}">${msgPreview}</td>
                <td>
                    <input type="text" class="form-control form-control-sm workflow-from" 
                           value="${msg.from_name || ''}" dir="rtl" placeholder="From name">
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm workflow-to" 
                           value="${msg.to_name || ''}" dir="rtl" placeholder="To name">
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm workflow-email" 
                           value="${msg.to_email || ''}" placeholder="To email">
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // Pre-populate interactive form with existing messages (for convenience)
    // Only for messages without workflow
    const noWorkflowMessages = messages.filter(m => m.from_name === 'Not in workflow' && m.to_name === 'Not in workflow');
    if (noWorkflowMessages.length > 0 && noWorkflowMessages.length <= 20) {  // Limit to avoid too many entries
        noWorkflowMessages.forEach(msg => {
            addWorkflowEntry({
                date: msg.date || '',
                name: '',
                email: ''
            });
        });
    }
    
    // Switch to first tab
    const firstTab = document.querySelector('#manual-edit-tab');
    if (firstTab) {
        bootstrap.Tab.getOrCreateInstance(firstTab).show();
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('workflowEditorModal'));
    modal.show();
}

/**
 * Save workflow changes
 */
async function saveWorkflowChanges() {
    const requestId = document.getElementById('workflow-edit-request-id').value;
    const tableBody = document.getElementById('workflow-messages-table');
    const rows = tableBody.querySelectorAll('tr');
    
    const workflowUpdates = [];
    
    rows.forEach(row => {
        const messageId = row.dataset.messageId;
        const fromName = row.querySelector('.workflow-from').value.trim();
        const toName = row.querySelector('.workflow-to').value.trim();
        const toEmail = row.querySelector('.workflow-email').value.trim();
        
        // Only include rows where we have data
        if (fromName || toName) {
            workflowUpdates.push({
                message_id: parseInt(messageId),
                from_name: fromName || 'Not in workflow',
                to_name: toName || 'Not in workflow',
                to_email: toEmail || 'Not in workflow',
                from_id: '<empty>',
                to_id: '<empty>'
            });
        }
    });
    
    if (workflowUpdates.length === 0) {
        alert('Please enter workflow data for at least one message.');
        return;
    }
    
    try {
        const response = await fetch('/api/update_workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: parseInt(requestId),
                workflow_updates: workflowUpdates
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to save changes');
        }
        
        alert(`Successfully updated ${data.updated_count} messages.`);
        
        // Close modal and refresh list
        bootstrap.Modal.getInstance(document.getElementById('workflowEditorModal')).hide();
        loadNoWorkflowRequests();
        
    } catch (error) {
        console.error('Error saving workflow changes:', error);
        alert('Error: ' + error.message);
    }
}

// ==================== PASTE WORKFLOW FUNCTIONS ====================

let workflowEntryCounter = 0;

/**
 * Parse and preview pasted workflow text
 */
function parseAndPreviewWorkflow() {
    const text = document.getElementById('workflow-paste-text').value.trim();
    const resultDiv = document.getElementById('workflow-preview-result');
    
    if (!text) {
        resultDiv.innerHTML = '<div class="alert alert-warning">Please paste workflow text first.</div>';
        return;
    }
    
    const entries = parseWorkflowText(text);
    
    if (entries.length === 0) {
        resultDiv.innerHTML = '<div class="alert alert-danger">Could not parse any workflow entries. Please check the format.</div>';
        return;
    }
    
    // Build preview table
    let html = `
        <div class="alert alert-success">
            <i class="bi bi-check-circle"></i> Parsed ${entries.length} workflow entries
        </div>
        <div class="table-responsive">
            <table class="table table-sm table-striped">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Parent ID</th>
                        <th>Date</th>
                        <th>Name</th>
                        <th>Email</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const entry of entries) {
        html += `
            <tr>
                <td>${entry.id}</td>
                <td>${entry.parent_id || 'None'}</td>
                <td dir="rtl">${entry.date}</td>
                <td dir="rtl">${entry.name || '-'}</td>
                <td>${entry.email || '-'}</td>
            </tr>
        `;
    }
    
    html += '</tbody></table></div>';
    resultDiv.innerHTML = html;
}

/**
 * Parse workflow text into structured entries (client-side)
 */
function parseWorkflowText(text) {
    const entries = [];
    const blocks = text.split(/-{10,}/);
    
    for (const block of blocks) {
        const trimmed = block.trim();
        if (!trimmed) continue;
        
        const entry = {};
        const lines = trimmed.split('\n');
        
        for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine || !trimmedLine.includes(':')) continue;
            
            const colonIndex = trimmedLine.indexOf(':');
            const key = trimmedLine.substring(0, colonIndex).trim().toLowerCase().replace(' ', '_');
            const value = trimmedLine.substring(colonIndex + 1).trim();
            
            if (key === 'parent_id') {
                entry.parent_id = value.toLowerCase() === 'none' ? null : value;
            } else if (key === 'id') {
                entry.id = value;
            } else if (key === 'date') {
                entry.date = value;
            } else if (key === 'name') {
                entry.name = value;
            } else if (key === 'email') {
                entry.email = value;
            }
        }
        
        if (entry.id && entry.date) {
            entries.push(entry);
        }
    }
    
    return entries;
}

/**
 * Apply pasted workflow to the request
 */
async function applyPastedWorkflow() {
    const requestId = document.getElementById('workflow-edit-request-id').value;
    const text = document.getElementById('workflow-paste-text').value.trim();
    const resultDiv = document.getElementById('workflow-preview-result');
    
    if (!requestId) {
        alert('No request selected.');
        return;
    }
    
    if (!text) {
        alert('Please paste workflow text first.');
        return;
    }
    
    const entries = parseWorkflowText(text);
    
    if (entries.length === 0) {
        alert('Could not parse any workflow entries. Please check the format.');
        return;
    }
    
    if (!confirm(`Are you sure you want to apply ${entries.length} workflow entries to this request?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply_workflow_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: parseInt(requestId),
                workflow_text: text
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to apply workflow');
        }
        
        // Show result
        let resultHtml = `
            <div class="alert alert-success">
                <i class="bi bi-check-circle"></i> <strong>Workflow Applied!</strong><br>
                ${data.updated} messages updated, ${data.created} messages created.
            </div>
        `;
        
        if (data.errors && data.errors.length > 0) {
            resultHtml += `
                <div class="alert alert-warning">
                    <strong>Warnings:</strong>
                    <ul class="mb-0">
                        ${data.errors.map(e => `<li>${e}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        if (data.details && data.details.length > 0) {
            resultHtml += `
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Action</th>
                                <th>Date</th>
                                <th>From</th>
                                <th>To</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            for (const detail of data.details) {
                const badgeClass = detail.action === 'created' ? 'bg-success' : 'bg-primary';
                resultHtml += `
                    <tr>
                        <td><span class="badge ${badgeClass}">${detail.action}</span></td>
                        <td dir="rtl">${detail.date}</td>
                        <td dir="rtl">${detail.from || '-'}</td>
                        <td dir="rtl">${detail.to || '-'}</td>
                    </tr>
                `;
            }
            resultHtml += '</tbody></table></div>';
        }
        
        resultDiv.innerHTML = resultHtml;
        
        // Close modal after a short delay to show results
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('workflowEditorModal'));
            if (modal) modal.hide();
            
            // Refresh no workflow list
            loadNoWorkflowRequests();
        }, 1500);
        
    } catch (error) {
        console.error('Error applying workflow:', error);
        alert('Error: ' + error.message);
    }
}

// ==================== INTERACTIVE FORM FUNCTIONS ====================

// ==================== PERSIAN DATE HELPERS ====================

/**
 * Persian month names
 */
const persianMonths = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
];

/**
 * Persian day names
 */
const persianDays = [
    'شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'
];

/**
 * Convert Jalali date to day of week
 * Algorithm based on the fact that 1 Farvardin 1 was Saturday (شنبه)
 */
function jalaliDayOfWeek(year, month, day) {
    // Calculate total days from epoch (1/1/1)
    // Using a simplified algorithm
    const g = jalaliToGregorian(year, month, day);
    const date = new Date(g.year, g.month - 1, g.day);
    // JavaScript: 0=Sunday, 1=Monday, ..., 6=Saturday
    // Persian: 0=شنبه (Saturday), 1=یکشنبه (Sunday), ...
    const jsDay = date.getDay();
    // Convert: Saturday(6) -> 0, Sunday(0) -> 1, Monday(1) -> 2, ...
    const persianDayIndex = (jsDay + 1) % 7;
    return persianDays[persianDayIndex];
}

/**
 * Convert Jalali to Gregorian (simplified algorithm)
 */
function jalaliToGregorian(jy, jm, jd) {
    jy = parseInt(jy);
    jm = parseInt(jm);
    jd = parseInt(jd);
    
    let gy, gm, gd, days;
    
    jy += 1595;
    days = -355668 + (365 * jy) + (Math.floor(jy / 33) * 8) + Math.floor(((jy % 33) + 3) / 4) + jd;
    days += (jm < 7) ? (jm - 1) * 31 : ((jm - 7) * 30) + 186;
    
    gy = 400 * Math.floor(days / 146097);
    days %= 146097;
    if (days > 36524) {
        gy += 100 * Math.floor(--days / 36524);
        days %= 36524;
        if (days >= 365) days++;
    }
    gy += 4 * Math.floor(days / 1461);
    days %= 1461;
    if (days > 365) {
        gy += Math.floor((days - 1) / 365);
        days = (days - 1) % 365;
    }
    gd = days + 1;
    
    const sal_a = [0, 31, (((gy % 4 === 0) && (gy % 100 !== 0)) || (gy % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    gm = 0;
    while (gm < 13 && gd > sal_a[gm]) {
        gd -= sal_a[gm];
        gm++;
    }
    
    return { year: gy, month: gm, day: gd };
}

/**
 * Update the day of week display for an entry
 */
function updateDayOfWeek(entryId) {
    const entry = document.getElementById(`workflow-entry-${entryId}`);
    if (!entry) return;
    
    const year = entry.querySelector('.entry-year').value;
    const month = entry.querySelector('.entry-month').value;
    const day = entry.querySelector('.entry-day').value;
    const dayDisplay = entry.querySelector('.entry-day-of-week');
    
    if (year && month && day) {
        try {
            const dayName = jalaliDayOfWeek(year, month, day);
            dayDisplay.textContent = dayName;
            dayDisplay.classList.remove('text-muted');
            dayDisplay.classList.add('text-success', 'fw-bold');
        } catch (e) {
            dayDisplay.textContent = '---';
            dayDisplay.classList.add('text-muted');
            dayDisplay.classList.remove('text-success', 'fw-bold');
        }
    } else {
        dayDisplay.textContent = '---';
        dayDisplay.classList.add('text-muted');
        dayDisplay.classList.remove('text-success', 'fw-bold');
    }
}

/**
 * Build Persian date string from components
 */
function buildPersianDateString(year, month, day, hour, minute) {
    const dayName = jalaliDayOfWeek(year, month, day);
    const monthName = persianMonths[parseInt(month) - 1];
    const h = hour.toString().padStart(2, '0');
    const m = minute.toString().padStart(2, '0');
    return `${dayName}، ${day} ${monthName} ${year} ${h}:${m}`;
}

/**
 * Parse Persian date string into components
 * Supports two formats:
 * 1. "دوشنبه، 27 مرداد 1404 18:23" (workflow format)
 * 2. "1404-02-10 11:20:00" (database format)
 */
function parsePersianDateString(dateStr) {
    const result = { year: '', month: '', day: '', hour: '', minute: '' };
    
    if (!dateStr) return result;
    
    try {
        // Check if it's database format: "1404-02-10 11:20:00"
        const dbFormatMatch = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/);
        if (dbFormatMatch) {
            result.year = dbFormatMatch[1];
            result.month = parseInt(dbFormatMatch[2]).toString(); // Remove leading zero
            result.day = parseInt(dbFormatMatch[3]).toString();   // Remove leading zero
            result.hour = dbFormatMatch[4];
            result.minute = dbFormatMatch[5];
            return result;
        }
        
        // Otherwise try workflow format: "دوشنبه، 27 مرداد 1404 18:23"
        const parts = dateStr.split('،');
        if (parts.length < 2) return result;
        
        const rest = parts[1].trim();
        // Split: "27 مرداد 1404 18:23"
        const tokens = rest.split(/\s+/);
        if (tokens.length < 4) return result;
        
        result.day = tokens[0];
        const monthName = tokens[1];
        result.year = tokens[2];
        
        // Find month index
        const monthIndex = persianMonths.indexOf(monthName);
        if (monthIndex >= 0) {
            result.month = (monthIndex + 1).toString();
        }
        
        // Parse time
        if (tokens[3] && tokens[3].includes(':')) {
            const timeParts = tokens[3].split(':');
            result.hour = timeParts[0] || '';
            result.minute = timeParts[1] || '';
        }
    } catch (e) {
        console.error('Error parsing date:', e);
    }
    
    return result;
}

/**
 * Add a new workflow entry to the interactive form
 */
function addWorkflowEntry(prefill = null) {
    workflowEntryCounter++;
    const container = document.getElementById('workflow-entries-container');
    
    // Build parent ID options from existing entries
    let parentOptions = '<option value="None">None (First Entry)</option>';
    for (let i = 1; i < workflowEntryCounter; i++) {
        parentOptions += `<option value="${i}">${i}</option>`;
    }
    
    // Build month options
    let monthOptions = '<option value="">ماه</option>';
    for (let i = 0; i < 12; i++) {
        const selected = prefill?.month == (i + 1) ? 'selected' : '';
        monthOptions += `<option value="${i + 1}" ${selected}>${persianMonths[i]}</option>`;
    }
    
    // Parse prefill date if it's a string
    let prefillData = { year: '', month: '', day: '', hour: '', minute: '', name: '', email: '' };
    if (prefill) {
        if (typeof prefill.date === 'string' && prefill.date) {
            const parsed = parsePersianDateString(prefill.date);
            prefillData = { ...parsed, name: prefill.name || '', email: prefill.email || '' };
        } else {
            prefillData = { ...prefillData, ...prefill };
        }
    }
    
    const entryHtml = `
        <div class="card mb-3 workflow-entry" id="workflow-entry-${workflowEntryCounter}" data-entry-id="${workflowEntryCounter}">
            <div class="card-header bg-light d-flex justify-content-between align-items-center py-2">
                <span class="fw-bold">Entry #${workflowEntryCounter}</span>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeWorkflowEntry(${workflowEntryCounter})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
            <div class="card-body py-2">
                <div class="row g-2 align-items-end">
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Parent</label>
                        <select class="form-select form-select-sm entry-parent-id">
                            ${parentOptions}
                        </select>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">ID</label>
                        <input type="text" class="form-control form-control-sm entry-id bg-light" value="${workflowEntryCounter}" readonly>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Year</label>
                        <input type="number" class="form-control form-control-sm entry-year" 
                            placeholder="1404" min="1300" max="1500" value="${prefillData.year}"
                            onchange="updateDayOfWeek(${workflowEntryCounter})">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small mb-1">Month</label>
                        <select class="form-select form-select-sm entry-month" onchange="updateDayOfWeek(${workflowEntryCounter})">
                            ${monthOptions}
                        </select>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Day</label>
                        <input type="number" class="form-control form-control-sm entry-day" 
                            placeholder="1" min="1" max="31" value="${prefillData.day}"
                            onchange="updateDayOfWeek(${workflowEntryCounter})">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Day Name</label>
                        <div class="form-control form-control-sm bg-light entry-day-of-week text-center text-muted" dir="rtl">---</div>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Hour</label>
                        <input type="number" class="form-control form-control-sm entry-hour" 
                            placeholder="12" min="0" max="23" value="${prefillData.hour}">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Min</label>
                        <input type="number" class="form-control form-control-sm entry-minute" 
                            placeholder="00" min="0" max="59" value="${prefillData.minute}">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small mb-1">Name</label>
                        <input type="text" class="form-control form-control-sm entry-name" dir="rtl" 
                            placeholder="نام شخص" value="${prefillData.name}">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label small mb-1">Email</label>
                        <input type="text" class="form-control form-control-sm entry-email" 
                            placeholder="email@iau.ir" value="${prefillData.email}">
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', entryHtml);
    
    // Update parent options in all entries
    updateParentOptions();
    
    // Update day of week if we have prefill data
    if (prefillData.year && prefillData.month && prefillData.day) {
        updateDayOfWeek(workflowEntryCounter);
    }
}

/**
 * Remove a workflow entry
 */
function removeWorkflowEntry(entryId) {
    const entry = document.getElementById(`workflow-entry-${entryId}`);
    if (entry) {
        entry.remove();
        updateParentOptions();
    }
}

/**
 * Update parent ID options in all entries
 */
function updateParentOptions() {
    const entries = document.querySelectorAll('.workflow-entry');
    const entryIds = Array.from(entries).map(e => e.dataset.entryId);
    
    entries.forEach((entry, index) => {
        const select = entry.querySelector('.entry-parent-id');
        const currentValue = select.value;
        
        // Build options: only IDs that come before this entry
        let options = '<option value="None">None (First Entry)</option>';
        for (let i = 0; i < index; i++) {
            const id = entryIds[i];
            options += `<option value="${id}">${id}</option>`;
        }
        
        select.innerHTML = options;
        
        // Restore selection if still valid
        if (currentValue && select.querySelector(`option[value="${currentValue}"]`)) {
            select.value = currentValue;
        }
    });
}

/**
 * Preview interactive workflow entries
 */
function previewInteractiveWorkflow() {
    const entries = collectInteractiveEntries();
    const previewDiv = document.getElementById('interactive-workflow-preview');
    
    if (entries.length === 0) {
        previewDiv.innerHTML = '<div class="alert alert-warning">Please add at least one workflow entry.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> Preview of ${entries.length} workflow entries
        </div>
        <div class="table-responsive">
            <table class="table table-sm table-striped">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Parent ID</th>
                        <th>Date</th>
                        <th>Name</th>
                        <th>Email</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const entry of entries) {
        html += `
            <tr>
                <td>${entry.id}</td>
                <td>${entry.parent_id || 'None'}</td>
                <td dir="rtl">${entry.date}</td>
                <td dir="rtl">${entry.name || '-'}</td>
                <td>${entry.email || '-'}</td>
            </tr>
        `;
    }
    
    html += '</tbody></table></div>';
    previewDiv.innerHTML = html;
}

/**
 * Collect entries from interactive form
 */
function collectInteractiveEntries() {
    const entries = [];
    const entryElements = document.querySelectorAll('.workflow-entry');
    
    entryElements.forEach(el => {
        const id = el.querySelector('.entry-id').value;
        const parentId = el.querySelector('.entry-parent-id').value;
        const year = el.querySelector('.entry-year').value.trim();
        const month = el.querySelector('.entry-month').value;
        const day = el.querySelector('.entry-day').value.trim();
        const hour = el.querySelector('.entry-hour').value.trim() || '0';
        const minute = el.querySelector('.entry-minute').value.trim() || '0';
        const name = el.querySelector('.entry-name').value.trim();
        const email = el.querySelector('.entry-email').value.trim();
        
        // Only include if we have the date components
        if (year && month && day) {
            const dateStr = buildPersianDateString(year, month, day, hour, minute);
            entries.push({
                id: id,
                parent_id: parentId === 'None' ? null : parentId,
                date: dateStr,
                name: name,
                email: email
            });
        }
    });
    
    return entries;
}

/**
 * Convert interactive entries to workflow text format
 */
function entriesToWorkflowText(entries) {
    let text = '';
    for (const entry of entries) {
        text += `parent_id: ${entry.parent_id || 'None'}\n`;
        text += `id: ${entry.id}\n`;
        text += `date: ${entry.date}\n`;
        text += `name: ${entry.name}\n`;
        text += `email: ${entry.email}\n`;
        text += '--------------------------------------------------\n';
    }
    return text;
}

/**
 * Apply interactive workflow entries to the request
 */
async function applyInteractiveWorkflow() {
    const requestId = document.getElementById('workflow-edit-request-id').value;
    const entries = collectInteractiveEntries();
    const previewDiv = document.getElementById('interactive-workflow-preview');
    
    if (!requestId) {
        alert('No request selected.');
        return;
    }
    
    if (entries.length === 0) {
        alert('Please add at least one workflow entry with a date.');
        return;
    }
    
    if (!confirm(`Are you sure you want to apply ${entries.length} workflow entries to this request?`)) {
        return;
    }
    
    // Convert to workflow text and use the same API
    const workflowText = entriesToWorkflowText(entries);
    
    try {
        const response = await fetch('/api/apply_workflow_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: parseInt(requestId),
                workflow_text: workflowText
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to apply workflow');
        }
        
        // Show result
        let resultHtml = `
            <div class="alert alert-success">
                <i class="bi bi-check-circle"></i> <strong>Workflow Applied!</strong><br>
                ${data.updated} messages updated, ${data.created} messages created.
            </div>
        `;
        
        if (data.errors && data.errors.length > 0) {
            resultHtml += `
                <div class="alert alert-warning">
                    <strong>Warnings:</strong>
                    <ul class="mb-0">
                        ${data.errors.map(e => `<li>${e}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        previewDiv.innerHTML = resultHtml;
        
        // Close modal after a short delay to show results
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('workflowEditorModal'));
            if (modal) modal.hide();
            
            // Refresh no workflow list
            loadNoWorkflowRequests();
        }, 1500);
        
    } catch (error) {
        console.error('Error applying workflow:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Reset the interactive form when opening the modal
 */
function resetInteractiveForm() {
    workflowEntryCounter = 0;
    document.getElementById('workflow-entries-container').innerHTML = '';
    document.getElementById('interactive-workflow-preview').innerHTML = '';
    document.getElementById('workflow-paste-text').value = '';
    document.getElementById('workflow-preview-result').innerHTML = '';
}

/**
 * Clear all workflow data for the current request
 */
async function clearWorkflow() {
    const requestId = document.getElementById('workflow-edit-request-id').value;
    
    if (!requestId) {
        alert('No request selected.');
        return;
    }
    
    if (!confirm('Are you sure you want to clear ALL workflow data for this request?\n\nThis will reset all messages to "Not in workflow" status.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/clear_workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: parseInt(requestId)
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to clear workflow');
        }
        
        alert(`Successfully cleared workflow for ${data.updated_count} messages.`);
        
        // Close modal and refresh list
        const modal = bootstrap.Modal.getInstance(document.getElementById('workflowEditorModal'));
        if (modal) modal.hide();
        
        // Refresh no workflow list
        loadNoWorkflowRequests();
        
    } catch (error) {
        console.error('Error clearing workflow:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * Template Transformation Functions
 * Convert raw/uncleaned template data to standardized workflow format
 */

async function transformAndPreviewTemplate() {
    const rawTemplateText = document.getElementById('raw-template-text').value.trim();
    
    if (!rawTemplateText) {
        alert('Please paste raw template data first');
        return;
    }
    
    try {
        // Show loading state
        const resultDiv = document.getElementById('template-transform-result');
        resultDiv.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Transforming template...</p></div>';
        
        // Call transformation API
        const response = await fetch('/api/transform_raw_template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                raw_template: rawTemplateText
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            // Show errors
            let errorHtml = '<div class="alert alert-danger alert-dismissible fade show" role="alert"><i class="bi bi-exclamation-triangle"></i> <strong>Transformation Failed</strong>';
            if (data.errors && data.errors.length > 0) {
                errorHtml += '<ul class="mt-2 mb-0">';
                data.errors.forEach(error => {
                    errorHtml += `<li>${escapeHtml(error)}</li>`;
                });
                errorHtml += '</ul>';
            }
            errorHtml += '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';
            resultDiv.innerHTML = errorHtml;
            return;
        }
        
        // Show success with preview
        const entries = data.entries || [];
        let previewHtml = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="bi bi-check-circle"></i> <strong>Transformation Successful!</strong>
                <br><small>Found and transformed ${entries.length} entries</small>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
            
            <div class="card mb-3">
                <div class="card-header bg-light">
                    <h6 class="mb-0"><i class="bi bi-eye"></i> Preview (${entries.length} entries)</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm table-striped mb-0">
                            <thead class="table-dark">
                                <tr>
                                    <th style="width: 30px;">ID</th>
                                    <th style="width: 50px;">Parent</th>
                                    <th style="width: 150px;">Date</th>
                                    <th style="width: 150px;">Name</th>
                                    <th>Email</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        entries.forEach(entry => {
            const parentId = entry.parent_id === null ? '-' : entry.parent_id;
            previewHtml += `
                <tr>
                    <td><strong>${entry.id}</strong></td>
                    <td>${parentId}</td>
                    <td><small>${escapeHtml(entry.date)}</small></td>
                    <td><small dir="rtl">${escapeHtml(entry.name)}</small></td>
                    <td><small>${escapeHtml(entry.email)}</small></td>
                </tr>
            `;
        });
        
        previewHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header bg-light">
                    <h6 class="mb-0"><i class="bi bi-code"></i> Formatted Workflow Text</h6>
                </div>
                <div class="card-body">
                    <textarea class="form-control font-monospace" id="transformed-workflow-text" rows="10" readonly dir="auto">${escapeHtml(data.formatted_text)}</textarea>
                </div>
            </div>
        `;
        
        resultDiv.innerHTML = previewHtml;
        
        // Store the formatted text for applying later
        window.transformedWorkflowText = data.formatted_text;
        
    } catch (error) {
        console.error('Error transforming template:', error);
        const resultDiv = document.getElementById('template-transform-result');
        resultDiv.innerHTML = `<div class="alert alert-danger" role="alert"><i class="bi bi-exclamation-triangle"></i> Error: ${escapeHtml(error.message)}</div>`;
    }
}

async function applyTransformedTemplate() {
    if (!window.transformedWorkflowText) {
        alert('Please transform the template first');
        return;
    }
    
    const requestId = document.getElementById('workflow-edit-request-id').value;
    if (!requestId) {
        alert('No request selected');
        return;
    }
    
    // Automatically apply the transformed workflow using the existing function
    document.getElementById('workflow-paste-text').value = window.transformedWorkflowText;
    
    // Switch to the Paste Workflow tab
    const pasteTab = document.getElementById('paste-workflow-tab');
    if (pasteTab) {
        pasteTab.click();
    }
    
    // Apply it with a short delay to allow tab switch
    setTimeout(() => {
        applyPastedWorkflow();
    }, 100);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
