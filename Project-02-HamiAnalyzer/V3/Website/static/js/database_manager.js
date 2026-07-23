/**
 * Database Manager JavaScript
 * Handles browsing and searching database files
 */

// Global state
let currentDateSource = 'first';
let currentOutputType = '';
let currentMonth = '';
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
    // Get database stats from data attributes on search tab
    const searchTab = document.getElementById('search');
    if (!searchTab) return { hamis: 0, requests: 0, months: 0 };
    
    const dateSource = document.getElementById('search-date-source')?.value || 'first';
    
    return {
        hamis: parseInt(searchTab.dataset[`${dateSource}Hamis`]) || 0,
        requests: parseInt(searchTab.dataset[`${dateSource}Requests`]) || 0,
        months: parseInt(searchTab.dataset[`${dateSource}Months`]) || 0
    };
}

function estimateSearchTime(searchType) {
    // Estimate search time based on database size and search type
    // Base times in milliseconds
    const stats = getDbStats();
    const totalFiles = stats.hamis + stats.requests;
    
    // Base time multipliers for different search types
    const typeMultipliers = {
        'date': 1.5,      // Date search scans combined files (slower)
        'reference': 0.8, // Reference search is relatively fast
        'field': 1.0,     // Field search scans hami files
        'employee': 2.0   // Employee search scans combined files more thoroughly
    };
    
    // Calculate estimated time
    // Base: ~50ms per file scanned, with minimum of 1 second
    const baseTime = Math.max(1000, totalFiles * 15 * (typeMultipliers[searchType] || 1));
    
    // Add overhead for months (more folders to scan)
    const monthOverhead = stats.months * 200;
    
    // Cap at reasonable maximum (60 seconds)
    return Math.min(baseTime + monthOverhead, 60000);
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
    // Browse tab event listeners
    const browseDateSource = document.getElementById('browse-date-source');
    const browseOutputType = document.getElementById('browse-output-type');
    const browseMonth = document.getElementById('browse-month');
    
    if (browseDateSource) {
        browseDateSource.addEventListener('change', function() {
            currentDateSource = this.value;
            loadMonths();
        });
    }
    
    if (browseOutputType) {
        browseOutputType.addEventListener('change', function() {
            currentOutputType = this.value;
            if (currentMonth && currentOutputType) {
                loadFiles();
            }
        });
    }
    
    if (browseMonth) {
        browseMonth.addEventListener('change', function() {
            currentMonth = this.value;
            if (currentMonth && currentOutputType) {
                loadFiles();
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
    
    // Load months when browse tab is shown
    const browseTab = document.getElementById('browse-tab');
    if (browseTab) {
        browseTab.addEventListener('shown.bs.tab', function() {
            loadMonths();
        });
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
    try {
        const response = await fetch(`/api/browse_database?date_source=${currentDateSource}`);
        const data = await response.json();
        
        if (data.error) {
            showError('Error loading months: ' + data.error);
            return;
        }
        
        const monthSelect = document.getElementById('browse-month');
        monthSelect.innerHTML = '<option value="">-- Select Month --</option>';
        
        data.months.forEach(month => {
            const option = document.createElement('option');
            option.value = month;
            option.textContent = month;
            monthSelect.appendChild(option);
        });
        
        // Clear files display
        document.getElementById('files-container').innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> Select an output type and month to view files.
            </div>
        `;
        
    } catch (error) {
        showError('Error loading months: ' + error.message);
    }
}

async function loadFiles() {
    try {
        const response = await fetch(
            `/api/browse_database?date_source=${currentDateSource}&output_type=${currentOutputType}&month=${currentMonth}`
        );
        const data = await response.json();
        
        if (data.error) {
            showError('Error loading files: ' + data.error);
            return;
        }
        
        displayFiles(data.files);
        
    } catch (error) {
        showError('Error loading files: ' + error.message);
    }
}

function displayFiles(files) {
    const container = document.getElementById('files-container');
    
    // Store files for download all functionality
    lastBrowseFiles = files;
    
    if (files.length === 0) {
        lastBrowseFiles = [];
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> No files found in this location.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="alert alert-info mb-0 flex-grow-1 me-3">
                <i class="bi bi-folder2-open"></i> Found <strong>${files.length}</strong> file(s) in <strong>${currentMonth}</strong>
            </div>
            <button class="btn btn-success" onclick="downloadAllBrowseFiles()" title="Download all files as ZIP">
                <i class="bi bi-download"></i> Download All (${files.length} files)
            </button>
        </div>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Filename</th>
                        ${currentOutputType === 'combined_output' ? '<th>Hami ID</th><th>Number</th><th>Ref. Code</th><th>Subject</th>' : '<th>Hami ID</th>'}
                        <th>Size</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    files.forEach(file => {
        html += `
            <tr>
                <td><code>${file.filename}</code></td>
        `;
        
        if (currentOutputType === 'combined_output') {
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
                <td>${file.hami_id || 'N/A'}</td>
                <td>${file.number || 'N/A'}</td>
                <td>${refCodeHtml}</td>
                <td><small title="${file.subject || ''}">${displaySubject}</small></td>
            `;
        } else {
            html += `<td>${file.hami_id || 'N/A'}</td>`;
        }
        
        // Build action buttons
        let actionButtons = `
            <button class="btn btn-sm btn-info me-1" onclick="previewFile('${file.date_source}', '${file.month}', '${file.output_type}', '${file.filename}')" title="View file contents">
                <i class="bi bi-eye"></i> View
            </button>`;
        
        // Add Graph button for combined_output files
        if (currentOutputType === 'combined_output') {
            actionButtons += `
            <button class="btn btn-sm btn-graph-view me-1" onclick="openGraphView('${file.date_source}', '${file.month}', '${file.filename}')" title="View message flow graph">
                <i class="bi bi-diagram-3"></i> Graph
            </button>`;
        }
        
        actionButtons += `
            <button class="btn btn-sm btn-primary" onclick="downloadFile('${file.date_source}', '${file.month}', '${file.output_type}', '${file.filename}')" title="Download file">
                <i class="bi bi-download"></i> Download
            </button>`;
        
        html += `
                <td>${file.size}</td>
                <td>
                    ${actionButtons}
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

function downloadFile(dateSource, month, outputType, filename) {
    const url = `/database/download/${dateSource}/${month}/${outputType}/${filename}`;
    window.location.href = url;
}

async function searchByDate() {
    const dateSource = document.getElementById('search-date-source').value;
    const startDate = document.getElementById('search-start-date').value.trim();
    const endDate = document.getElementById('search-end-date').value.trim();
    
    // Show progress bar
    showSearchProgress('date');
    
    try {
        let url = `/api/search_by_date?date_source=${dateSource}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        
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
    const dateSource = document.getElementById('search-date-source').value;
    const referenceCode = document.getElementById('search-reference-code').value.trim();
    
    if (!referenceCode) {
        showError('Please enter a reference code');
        return;
    }
    
    // Show progress bar
    showSearchProgress('reference');
    
    try {
        const response = await fetch(
            `/api/search_by_reference?date_source=${dateSource}&reference_code=${encodeURIComponent(referenceCode)}`
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
    const dateSource = document.getElementById('search-date-source').value;
    const fieldName = document.getElementById('search-field-name').value;
    const searchValue = document.getElementById('search-field-value').value.trim();
    
    if (!searchValue) {
        showError('Please enter a search value');
        return;
    }
    
    // Show progress bar
    showSearchProgress('field');
    
    try {
        const response = await fetch(
            `/api/search_by_field?date_source=${dateSource}&field_name=${fieldName}&search_value=${encodeURIComponent(searchValue)}`
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
    const dateSource = document.getElementById('search-date-source').value;
    const employeeName = document.getElementById('search-employee-name').value.trim();
    
    if (!employeeName) {
        showError('Please enter a person name');
        return;
    }
    
    // Show progress bar
    showSearchProgress('employee');
    
    try {
        const response = await fetch(
            `/api/search_by_employee?date_source=${dateSource}&employee_name=${encodeURIComponent(employeeName)}`
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
    
    // Count unique hami files
    const uniqueHamis = new Set(results.map(r => `${r.date_source}/${r.month}/${r.hami_id}`));
    
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="alert alert-success mb-0 flex-grow-1 me-3">
                <i class="bi bi-check-circle"></i> Found ${results.length} result(s)
            </div>
            <button class="btn btn-success" onclick="downloadAllResults()" title="Download all combined files and unique hami files">
                <i class="bi bi-download"></i> Download All (${results.length} combined + ${uniqueHamis.size} hami)
            </button>
        </div>
        <div class="table-responsive">
            <table class="table table-hover table-sm">
                <thead>
                    <tr>
                        <th>Hami ID</th>
                        <th>Number</th>
                        <th>Month</th>
                        ${searchType === 'date' ? '<th>Date Range</th>' : ''}
                        ${searchType === 'employee' ? '<th>Matched People</th><th>Match Type</th>' : ''}}
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
        html += `
            <tr>
                <td><code>${result.hami_id}</code></td>
                <td>${result.number}</td>
                <td>${result.month}</td>
        `;
        
        if (searchType === 'date') {
            html += `<td><small>${result.first_date}<br>to<br>${result.last_date}</small></td>`;
        }
        
        if (searchType === 'employee') {
            // Display matched employees
            const matchedEmployees = result.matched_employees || [];
            const matchedDisplay = matchedEmployees.length > 0 
                ? matchedEmployees.map(e => `<span class="badge bg-info text-dark">${e}</span>`).join(' ')
                : 'N/A';
            html += `<td>${matchedDisplay}</td>`;
            
            // Display match type with colored badge
            let matchTypeBadge = '';
            if (result.match_type === 'both') {
                matchTypeBadge = '<span class="badge bg-success">From & To</span>';
            } else if (result.match_type === 'from') {
                matchTypeBadge = '<span class="badge bg-primary">Sender</span>';
            } else {
                matchTypeBadge = '<span class="badge bg-secondary">Receiver</span>';
            }
            html += `<td>${matchTypeBadge}</td>`;
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
        `;
        
        // Show View, Graph, and Download buttons for Combined files
        if ((searchType === 'reference' || searchType === 'field' || searchType === 'employee') && result.combined_exists) {
            html += `
                    <button class="btn btn-sm btn-info me-1" onclick="previewFile('${result.date_source}', '${result.month}', 'combined_output', '${result.combined_filename}')" title="View combined file">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-graph-view me-1" onclick="openGraphView('${result.date_source}', '${result.month}', '${result.combined_filename}')" title="View message flow graph">
                        <i class="bi bi-diagram-3"></i>
                    </button>
                    <button class="btn btn-sm btn-primary me-1" onclick="downloadFile('${result.date_source}', '${result.month}', 'combined_output', '${result.combined_filename}')" title="Download combined file">
                        <i class="bi bi-download"></i> Combined
                    </button>
            `;
        } else if (searchType === 'date') {
            html += `
                    <button class="btn btn-sm btn-info me-1" onclick="previewFile('${result.date_source}', '${result.month}', 'combined_output', '${result.filename}')" title="View file">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-graph-view me-1" onclick="openGraphView('${result.date_source}', '${result.month}', '${result.filename}')" title="View message flow graph">
                        <i class="bi bi-diagram-3"></i>
                    </button>
                    <button class="btn btn-sm btn-primary me-1" onclick="downloadFile('${result.date_source}', '${result.month}', 'combined_output', '${result.filename}')" title="Download file">
                        <i class="bi bi-download"></i>
                    </button>
            `;
        }
        
        // View and Download buttons for Hami files
        html += `
                    <button class="btn btn-sm btn-outline-info me-1" onclick="previewFile('${result.date_source}', '${result.month}', 'hami_output', 'hami_${result.hami_id}.csv')" title="View hami file">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="downloadFile('${result.date_source}', '${result.month}', 'hami_output', 'hami_${result.hami_id}.csv')" title="Download hami file">
                        <i class="bi bi-download"></i> Hami
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
                date_source: currentDateSource,
                month: currentMonth,
                output_type: currentOutputType
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

/**
 * Open file preview modal and load file content
 */
async function previewFile(dateSource, month, outputType, filename) {
    // Store current file info for pagination
    currentPreviewFile = { dateSource, month, outputType, filename };
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
    await loadPreviewData();
}

/**
 * Load file preview data for current page
 */
async function loadPreviewData() {
    const { dateSource, month, outputType, filename } = currentPreviewFile;
    
    console.log('Loading preview data...', { dateSource, month, outputType, filename, page: currentPreviewPage });
    
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
        const url = `/api/preview_file?date_source=${dateSource}&month=${month}&output_type=${outputType}&filename=${encodeURIComponent(filename)}&page=${currentPreviewPage}&per_page=50`;
        
        console.log('Fetching:', url);
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('Response received:', data);
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to load file');
        }
        
        // Update modal title and info
        document.getElementById('preview-filename').textContent = data.filename;
        document.getElementById('preview-file-info').textContent = `${data.date_source} / ${data.month}`;
        
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
        
        // Display global info for combined files
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
        loadPreviewData();
    } else if (direction === 'next' && currentPreviewPage < currentPreviewTotalPages) {
        currentPreviewPage++;
        loadPreviewData();
    }
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
 * Open graph view for a combined file
 */
function openGraphView(dateSource, month, filename) {
    currentGraphFile = {
        dateSource: dateSource,
        month: month,
        filename: filename
    };
    
    // Update modal title
    document.getElementById('graph-filename').textContent = 'Graph: ' + filename;
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
    loadGraphData(dateSource, month, filename);
}

/**
 * Load graph data from API
 */
async function loadGraphData(dateSource, month, filename) {
    try {
        const params = new URLSearchParams({
            date_source: dateSource,
            month: month,
            filename: filename
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
});
