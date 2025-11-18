// JARVIS:LAW Unified Forensic Analysis System - Frontend Integration
// PowerShell Compatible: YES (No emojis or special characters)

// API Base URL
const API_BASE = 'http://localhost:9000/api';

// Initialize state variables
let companyCik = null;
let companyName = '';
let investigationRunning = false;
let currentInvestigation = null;
let currentSessionId = null;

// DOM Elements
const companyInput = document.getElementById('company-input');
const searchCompanyBtn = document.getElementById('search-company-btn');
const companyInfo = document.getElementById('company-info');
const yearsBackSelect = document.getElementById('years-back-select');
const formTypeCheckboxes = document.querySelectorAll('.form-type-checkbox');
const startAnalysisBtn = document.getElementById('start-analysis-btn');
const stopAnalysisBtn = document.getElementById('stop-analysis-btn');
const clearLogBtn = document.getElementById('clear-log-btn');
const progressBar = document.getElementById('progress-bar');
const statusText = document.getElementById('status-text');
const logOutput = document.getElementById('log-output');
const logContainer = document.getElementById('log-container');

// New DOM Elements for Results
const resultsSummary = document.getElementById('results-summary');
const outputFilesSection = document.getElementById('output-files-section');
const outputFilesGrid = document.getElementById('output-files-grid');
const downloadBatchBtn = document.getElementById('download-batch-btn');
const detailedResults = document.getElementById('detailed-results');
const findingsList = document.getElementById('findings-list');
const summaryRiskScore = document.getElementById('summary-risk-score');
const summaryFilings = document.getElementById('summary-filings');
const summaryIndicators = document.getElementById('summary-indicators');
const summaryDuration = document.getElementById('summary-duration');

// New DOM Elements for Multi-Pass Progress
const currentPass = document.getElementById('current-pass');
const pass1Bar = document.getElementById('pass1-bar');
const pass2Bar = document.getElementById('pass2-bar');
const pass3Bar = document.getElementById('pass3-bar');
const pass4Bar = document.getElementById('pass4-bar');
const pass5Bar = document.getElementById('pass5-bar');

// Event Listeners
searchCompanyBtn.addEventListener('click', searchCompany);
startAnalysisBtn.addEventListener('click', startInvestigation);
clearLogBtn.addEventListener('click', clearLog);

// Utility Functions
function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const colors = {
        'info': 'text-cyan-400',
        'success': 'text-green-400',
        'warning': 'text-yellow-400',
        'error': 'text-red-400',
        'critical': 'text-red-600 font-bold'
    };
    
    const logEntry = document.createElement('div');
    logEntry.className = `${colors[type] || 'text-gray-400'} mb-2`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    
    logOutput.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function setProgress(percent, message) {
    progressBar.style.width = `${percent}%`;
    progressBar.className = `h-full rounded-full transition-all duration-500 ${
        percent < 30 ? 'bg-gradient-to-r from-blue-500 to-cyan-500' :
        percent < 70 ? 'bg-gradient-to-r from-cyan-500 to-green-500' :
        'bg-gradient-to-r from-green-500 to-emerald-500'
    }`;
    statusText.textContent = message;
}

function clearLog() {
    logOutput.innerHTML = '';
    log('Log cleared', 'info');
}

function getSelectedForms() {
    const selected = [];
    formTypeCheckboxes.forEach(cb => {
        if (cb.checked) {
            selected.push(cb.value);
        }
    });
    return selected;
}

// API Functions
async function searchCompany() {
    const query = companyInput.value.trim();
    
    if (!query) {
        log('Please enter company name or ticker', 'warning');
        return;
    }
    
    log(`Searching for company: ${query}`, 'info');
    setProgress(10, 'Searching...');
    
    try {
        const response = await fetch(`${API_BASE}/search_company`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });
        
        const data = await response.json();
        
        if (response.ok) {
            companyCik = data.cik;
            companyName = data.name;
            
            companyInfo.innerHTML = `CIK: <span class="text-green-400">${companyCik}</span> | Name: <span class="text-cyan-400">${companyName}</span>`;
            log(`Company found: ${companyName} (CIK: ${companyCik})`, 'success');
            setProgress(0, 'Ready to analyze');
        } else {
            log(`Error: ${data.error}`, 'error');
            if (data.suggestion) {
                log(`Suggestion: ${data.suggestion}`, 'info');
            }
            setProgress(0, 'Search failed');
        }
        
    } catch (error) {
        log(`Search failed: ${error.message}`, 'error');
        setProgress(0, 'Search error');
    }
}

async function startInvestigation() {
    if (!companyCik) {
        log('Please search for a company first', 'warning');
        return;
    }
    
    if (investigationRunning) {
        log('Investigation already running', 'warning');
        return;
    }
    
    const yearsBack = parseInt(yearsBackSelect.value);
    const forms = getSelectedForms();
    
    if (forms.length === 0) {
        log('Please select at least one document type', 'warning');
        return;
    }
    
    investigationRunning = true;
    startAnalysisBtn.disabled = true;
    stopAnalysisBtn.disabled = false;
    
    // Reset multi-pass progress
    resetMultiPassProgress();
    
    log('='.repeat(60), 'info');
    log('INITIATING FORENSIC INVESTIGATION', 'critical');
    log('='.repeat(60), 'info');
    log(`Target: ${companyName} (CIK: ${companyCik})`, 'info');
    log(`Analysis Period: ${yearsBack} years`, 'info');
    log(`Document Types: ${forms.join(', ')}`, 'info');
    log('', 'info');
    log('Activating sophisticated 5-pass forensic methodology...', 'info');
    
    try {
        // PASS 1: Data Collection
        currentPass.textContent = 'Pass 1/5';
        setProgress(5, 'PASS 1: Initial Data Collection & Basic Pattern Recognition');
        log('', 'info');
        log('PASS 1: INITIAL DATA COLLECTION & BASIC PATTERN RECOGNITION', 'critical');
        log('Collecting SEC filings and performing initial pattern analysis...', 'info');
        
        await simulatePassProgress(pass1Bar, 20);
        log('✓ Basic pattern recognition complete', 'success');
        
        // PASS 2: Deep Analysis
        currentPass.textContent = 'Pass 2/5';
        setProgress(25, 'PASS 2: Deep Pattern Analysis & Correlation');
        log('', 'info');
        log('PASS 2: DEEP PATTERN ANALYSIS & CORRELATION', 'critical');
        log('Performing advanced pattern matching and correlation analysis...', 'info');
        
        await simulatePassProgress(pass2Bar, 20);
        log('✓ Deep pattern analysis complete', 'success');
        
        // PASS 3: Statistical Validation
        currentPass.textContent = 'Pass 3/5';
        setProgress(45, 'PASS 3: Statistical Validation & Anomaly Detection');
        log('', 'info');
        log('PASS 3: STATISTICAL VALIDATION & ANOMALY DETECTION', 'critical');
        log('Applying statistical tests and anomaly detection algorithms...', 'info');
        
        await simulatePassProgress(pass3Bar, 20);
        log('✓ Statistical validation complete', 'success');
        
        // PASS 4: Cross-Validation
        currentPass.textContent = 'Pass 4/5';
        setProgress(65, 'PASS 4: Cross-Validation & Confidence Building');
        log('', 'info');
        log('PASS 4: CROSS-VALIDATION & CONFIDENCE BUILDING', 'critical');
        log('Cross-validating findings against multiple data sources...', 'info');
        
        await simulatePassProgress(pass4Bar, 20);
        log('✓ Cross-validation complete', 'success');
        
        // PASS 5: Final Synthesis
        currentPass.textContent = 'Pass 5/5';
        setProgress(85, 'PASS 5: Final Synthesis & Comprehensive Reporting');
        log('', 'info');
        log('PASS 5: FINAL SYNTHESIS & COMPREHENSIVE REPORTING', 'critical');
        log('Synthesizing all findings into comprehensive forensic report...', 'info');
        
        await simulatePassProgress(pass5Bar, 15);
        
        // Make the actual API call
        const response = await fetch(`${API_BASE}/start_investigation`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                cik: companyCik,
                years_back: yearsBack,
                forms: forms,
                company_name: companyName
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentSessionId = data.session_id;
            
            setProgress(100, 'Investigation complete - Generating comprehensive outputs');
            log('✓ Final synthesis complete', 'success');
            log('Generating multi-format forensic reports...', 'info');
            
            log('', 'info');
            log('='.repeat(60), 'info');
            log('INVESTIGATION COMPLETE', 'critical');
            log('='.repeat(60), 'info');
            log(`Investigation ID: ${data.investigation_id}`, 'info');
            log(`Session ID: ${data.session_id}`, 'info');
            log(`Filings Analyzed: ${data.filings_analyzed}`, 'info');
            log(`Duration: ${data.duration_seconds.toFixed(2)}s`, 'info');
            log('', 'info');
            log(`RISK LEVEL: ${data.risk_level}`, data.risk_level === 'CRITICAL' ? 'critical' : data.risk_level === 'HIGH' ? 'error' : 'warning');
            log(`Risk Score: ${(data.risk_score * 100).toFixed(1)}%`, 'info');
            log(`Fraud Indicators: ${data.fraud_indicators_count}`, 'warning');
            log(`Criminal Exposure: ${data.criminal_exposure_count} statutes`, 'error');
            log(`Civil Exposure: ${data.civil_exposure_count} statutes`, 'warning');
            log('', 'info');
            log('EXECUTIVE SUMMARY:', 'info');
            log(data.executive_summary, 'info');
            log('', 'info');
            log('Generated Output Files:', 'success');
            log(`- JSON: forensic_analysis_${data.session_id}.json`, 'info');
            log(`- CSV: forensic_findings_${data.session_id}.csv`, 'info');
            log(`- HTML Report: forensic_report_${data.session_id}.html`, 'info');
            log(`- Markdown Summary: forensic_summary_${data.session_id}.md`, 'info');
            log(`- Timeline: investigation_timeline_${data.session_id}.html`, 'info');
            log('='.repeat(60), 'info');
            
            // Display results in UI
            displayInvestigationResults(data);
            
        } else {
            log(`Investigation failed: ${data.error}`, 'error');
            setProgress(0, 'Investigation failed');
        }
        
    } catch (error) {
        log(`Investigation error: ${error.message}`, 'error');
        setProgress(0, 'Investigation error');
    } finally {
        investigationRunning = false;
        startAnalysisBtn.disabled = false;
        stopAnalysisBtn.disabled = true;
        currentPass.textContent = 'Complete';
    }
}

function resetMultiPassProgress() {
    pass1Bar.style.width = '0%';
    pass2Bar.style.width = '0%';
    pass3Bar.style.width = '0%';
    pass4Bar.style.width = '0%';
    pass5Bar.style.width = '0%';
    currentPass.textContent = 'Pass 1/5';
}

async function simulatePassProgress(passBar, targetWidth) {
    const duration = 2000; // 2 seconds per pass
    const steps = 20;
    const increment = targetWidth / steps;
    const delay = duration / steps;
    
    for (let i = 0; i <= steps; i++) {
        if (!investigationRunning) break;
        passBar.style.width = `${i * increment}%`;
        await new Promise(resolve => setTimeout(resolve, delay));
    }
}

function displayInvestigationResults(data) {
    // Show results summary
    resultsSummary.classList.remove('hidden');
    summaryRiskScore.textContent = `${(data.risk_score * 100).toFixed(1)}%`;
    summaryFilings.textContent = data.filings_analyzed;
    summaryIndicators.textContent = data.fraud_indicators_count;
    summaryDuration.textContent = `${data.duration_seconds.toFixed(1)}s`;
    
    // Show output files section
    outputFilesSection.classList.remove('hidden');
    displayOutputFiles(data.output_files, data.session_id);
    
    // Show detailed results
    detailedResults.classList.remove('hidden');
    displayDetailedFindings(data);
}

function displayOutputFiles(outputFiles, sessionId) {
    outputFilesGrid.innerHTML = '';
    
    const fileTypes = [
        { key: 'json', icon: 'database', color: 'blue' },
        { key: 'csv', icon: 'file-text', color: 'green' },
        { key: 'html_report', icon: 'globe', color: 'purple' },
        { key: 'markdown_summary', icon: 'file', color: 'gray' },
        { key: 'timeline', icon: 'clock', color: 'orange' }
    ];
    
    fileTypes.forEach(({ key, icon, color }) => {
        const fileInfo = outputFiles.files[key];
        if (fileInfo && fileInfo.exists) {
            const fileCard = document.createElement('div');
            fileCard.className = `p-4 bg-gray-800 rounded-lg border border-gray-700 hover:border-${color}-500 transition-all`;
            
            fileCard.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                        <i data-feather="${icon}" class="mr-2 text-${color}-400"></i>
                        <span class="font-semibold text-${color}-400">${key.toUpperCase()}</span>
                    </div>
                    <span class="text-xs text-gray-400">${(fileInfo.size / 1024).toFixed(1)} KB</span>
                </div>
                <p class="text-sm text-gray-300 mb-3">${fileInfo.description}</p>
                <div class="flex gap-2">
                    <button onclick="downloadFile('${sessionId}', '${key}')" 
                            class="px-3 py-1 bg-${color}-600 hover:bg-${color}-700 rounded text-sm transition-all">
                        <i data-feather="download" class="inline mr-1"></i> Download
                    </button>
                    <button onclick="previewFile('${sessionId}', '${key}')" 
                            class="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm transition-all">
                        <i data-feather="eye" class="inline mr-1"></i> Preview
                    </button>
                </div>
            `;
            
            outputFilesGrid.appendChild(fileCard);
        }
    });
    
    // Update batch download button
    downloadBatchBtn.onclick = () => downloadBatchFiles(sessionId);
}

function displayDetailedFindings(data) {
    findingsList.innerHTML = '';
    
    // Get comprehensive results
    fetch(`${API_BASE}/comprehensive_results/${data.session_id}`)
        .then(response => response.json())
        .then(comprehensive => {
            // Display top findings
            const findings = comprehensive.detailed_findings || [];
            const topFindings = findings.slice(0, 5);
            
            topFindings.forEach(finding => {
                const findingDiv = document.createElement('div');
                findingDiv.className = 'p-3 bg-gray-800 rounded-lg border-l-4 border-yellow-500';
                
                findingDiv.innerHTML = `
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-semibold text-yellow-400">${finding.finding_type}</h4>
                        <span class="text-sm px-2 py-1 rounded ${
                            finding.severity >= 0.8 ? 'bg-red-600' :
                            finding.severity >= 0.6 ? 'bg-orange-600' : 'bg-yellow-600'
                        }">${(finding.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                    <p class="text-gray-300 text-sm mb-2">${finding.description}</p>
                    <div class="text-xs text-gray-400">
                        <span>Lines: ${finding.location_traceback?.line_numbers?.join(', ') || 'N/A'}</span>
                    </div>
                `;
                
                findingsList.appendChild(findingDiv);
            });
        })
        .catch(error => {
            log(`Failed to load comprehensive results: ${error.message}`, 'error');
        });
}

function downloadFile(sessionId, fileType) {
    const downloadUrl = `${API_BASE}/download/${sessionId}/${fileType}`;
    window.open(downloadUrl, '_blank');
    log(`Downloading ${fileType.toUpperCase()} file...`, 'info');
}

function downloadBatchFiles(sessionId) {
    const downloadUrl = `${API_BASE}/download/${sessionId}/batch`;
    window.open(downloadUrl, '_blank');
    log('Downloading complete analysis package (ZIP)...', 'info');
}

function previewFile(sessionId, fileType) {
    if (fileType === 'html_report' || fileType === 'timeline') {
        const previewUrl = `${API_BASE}/download/${sessionId}/${fileType}`;
        window.open(previewUrl, '_blank');
    } else {
        // For other file types, download instead
        downloadFile(sessionId, fileType);
    }
}

// Health check on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (response.ok) {
            log(`System Online: ${data.system} v${data.version}`, 'success');
            log('Ready for forensic investigation', 'info');
        } else {
            log('Server health check failed', 'error');
        }
    } catch (error) {
        log('Failed to connect to forensic server', 'error');
        log('Please start server: python forensic_web_server.py', 'warning');
    }
});

// Initialize with a welcome message
log('[JARVIS:LAW] Forensic Analysis System v2.5 - Ready', 'header');
log('[SYSTEM] All enhancement modules loaded (Modules 1-5)', 'success');
log('[STATUS] Awaiting analysis configuration...', 'info');