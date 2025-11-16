/**
 * JARVIS:LAW Forensic Dashboard - Main Script
 * Handles all interactive functionality for the web-based interface
 */

// Initialize document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Set default dates
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    document.getElementById('startDate').valueAsDate = oneYearAgo;
    document.getElementById('endDate').valueAsDate = today;
    
    // Document type info mapping
    const docInfoMap = {
        "4": "Form 4 - Insider Trading (Officer/Director transactions)",
        "10-K": "10-K - Annual Report",
        "10-Q": "10-Q - Quarterly Report",
        "8-K": "8-K - Current Report (Material events)",
        "S-1": "S-1 - IPO Registration",
        "3": "Form 3 - Initial Insider Ownership",
        "5": "Form 5 - Annual Insider Trading Statement",
        "13D": "Schedule 13D - Beneficial Ownership (5%+)",
        "13F": "13F - Institutional Holdings",
        "DEF 14A": "DEF 14A - Proxy Statement"
    };
    
    // Update document type info
    const docTypeSelect = document.getElementById('docTypeSelect');
    const docTypeInfo = document.getElementById('docTypeInfo');
    
    docTypeSelect.addEventListener('change', function() {
        docTypeInfo.textContent = docInfoMap[this.value] || '';
    });
    
    // Tab switching functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Show corresponding content
            const tabId = btn.id.replace('TabBtn', 'Tab');
            document.getElementById(tabId).classList.add('active');
            
            // Refresh feather icons
            feather.replace();
        });
    });
    
    // Search button functionality
    document.getElementById('searchBtn').addEventListener('click', function() {
        const companyInput = document.getElementById('companyInput').value.trim();
        if (!companyInput) {
            alert('Please enter a company name or ticker symbol.');
            return;
        }
        
        // Simulate API call
        simulateCompanySearch(companyInput);
    });
    
    // Start analysis button
    document.getElementById('startAnalysisBtn').addEventListener('click', function() {
        const cik = document.getElementById('cikDisplay').textContent;
        if (cik === 'Not selected') {
            alert('Please search and select a company first.');
            return;
        }
        
        startAnalysis();
    });
    
    // Stop analysis button
    document.getElementById('stopAnalysisBtn').addEventListener('click', function() {
        stopAnalysis();
    });
    
    // Export outputs button
    document.getElementById('exportOutputsBtn').addEventListener('click', function() {
        alert('Export functionality would open file dialog in a full implementation.\n\nIn production, this would:\n- Open the output folder\n- Display generated files\n- Allow download/export options');
    });
    
    // Clear log button
    document.getElementById('clearLogBtn').addEventListener('click', function() {
        const logContainer = document.getElementById('logContainer');
        logContainer.innerHTML = '<div class="text-blue-400">[LOG] Analysis log cleared</div>';
    });
    
    // Open folder button
    document.getElementById('openFolderBtn').addEventListener('click', function() {
        alert('File explorer would open in a full implementation.\n\nIn production, this would open:\nforensic_output_{session_id}/ folder');
    });
    
    // Open HTML report button
    document.getElementById('openHtmlReportBtn').addEventListener('click', function() {
        alert('HTML report would open in browser in a full implementation.\n\nIn production, this would open:\nforensic_report_{session_id}.html');
    });
    
    // Initialize charts
    initializeCharts();
});

// Simulate company search
function simulateCompanySearch(query) {
    const logContainer = document.getElementById('logContainer');
    
    // Add log entry
    addLogEntry(`[SEARCH] Looking up company: ${query}`, 'blue-400');
    
    // Simulate API delay
    setTimeout(() => {
        // Mock response data
        const mockCompanies = {
            'AAPL': { cik: '0000320193', name: 'Apple Inc.', ticker: 'AAPL' },
            'TSLA': { cik: '0001318605', name: 'Tesla, Inc.', ticker: 'TSLA' },
            'MSFT': { cik: '0000789019', name: 'Microsoft Corporation', ticker: 'MSFT' },
            'AMZN': { cik: '0001018724', name: 'Amazon.com, Inc.', ticker: 'AMZN' },
            'GOOGL': { cik: '0001652044', name: 'Alphabet Inc.', ticker: 'GOOGL' }
        };
        
        const upperQuery = query.toUpperCase();
        const mockData = mockCompanies[upperQuery] || {
            cik: '0001234567',
            name: query.includes('AAPL') ? 'Apple Inc.' : `${query} Corporation`,
            ticker: query.match(/^[A-Z]+$/i) ? query.toUpperCase() : 'N/A'
        };
        
        // Update UI
        document.getElementById('cikDisplay').innerHTML = `
            <span class="text-amber-400">${mockData.cik}</span>
            <span class="ml-2">|</span>
            <span class="ml-2">${mockData.name}</span>
        `;
        
        addLogEntry(`[SUCCESS] Found: ${mockData.name} (CIK: ${mockData.cik})`, 'green-400');
    }, 800);
}

// Start analysis simulation
function startAnalysis() {
    const startBtn = document.getElementById('startAnalysisBtn');
    const stopBtn = document.getElementById('stopAnalysisBtn');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    
    // Disable start button, enable stop button
    startBtn.disabled = true;
    startBtn.classList.add('bg-zinc-700', 'hover:bg-zinc-700');
    startBtn.classList.remove('bg-amber-600', 'hover:bg-amber-700');
    
    stopBtn.disabled = false;
    stopBtn.classList.add('bg-red-600', 'hover:bg-red-700', 'text-white');
    stopBtn.classList.remove('bg-zinc-700', 'hover:bg-zinc-600', 'text-zinc-300');
    
    // Reset progress
    let progress = 0;
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    progressText.textContent = 'Initializing analysis...';
    
    addLogEntry('='.repeat(80), 'text-amber-400');
    addLogEntry('[ANALYSIS] Starting Complete Forensic Analysis', 'text-amber-400 font-bold');
    addLogEntry('='.repeat(80), 'text-amber-400');
    
    // Simulate analysis steps
    const analysisSteps = [
        {text: 'Fetching filings from SEC.gov...', percent: 20, log: '[STEP 1] Fetching SEC filings...'},
        {text: 'Analyzing filings...', percent: 50, log: '[STEP 2] Running forensic analysis modules...'},
        {text: 'Running Batch Pattern Intelligence...', percent: 75, log: '[STEP 3] Executing batch pattern detection...'},
        {text: 'Generating forensic outputs...', percent: 90, log: '[STEP 4] Creating comprehensive reports...'},
        {text: 'Analysis complete!', percent: 100, log: '[STEP 5] Finalizing outputs...'}
    ];
    
    let stepIndex = 0;
    
    const analysisInterval = setInterval(() => {
        if (stepIndex >= analysisSteps.length) {
            clearInterval(analysisInterval);
            
            // Re-enable start button, disable stop button
            startBtn.disabled = false;
            startBtn.classList.remove('bg-zinc-700', 'hover:bg-zinc-700');
            startBtn.classList.add('bg-amber-600', 'hover:bg-amber-700');
            
            stopBtn.disabled = true;
            stopBtn.classList.remove('bg-red-600', 'hover:bg-red-700', 'text-white');
            stopBtn.classList.add('bg-zinc-700', 'hover:bg-zinc-600', 'text-zinc-300');
            
            // Update summary
            updateSummary();
            
            // Update files list
            updateFilesList();
            
            // Update charts
            updateCharts();
            
            addLogEntry('='.repeat(80), 'text-amber-400');
            addLogEntry('[COMPLETE] Forensic analysis finished successfully', 'text-green-400 font-bold');
            addLogEntry('='.repeat(80), 'text-amber-400');
            
            // Switch to summary tab
            document.getElementById('summaryTabBtn').click();
            
            return;
        }
        
        const step = analysisSteps[stepIndex];
        progress = step.percent;
        progressBar.style.width = `${progress}%`;
        progressPercent.textContent = `${progress}%`;
        progressText.textContent = step.text;
        
        addLogEntry(`[PROGRESS] ${step.log}`, 'text-blue-400');
        
        // Add some detailed log entries
        if (stepIndex === 1) {
            addLogEntry('  [INFO] Analyzing 12 filings', 'text-zinc-400');
            addLogEntry('  [FRAUD] Zero-dollar transaction detected', 'text-yellow-400');
            addLogEntry('  [RISK] Overall risk score: 0.65', 'text-yellow-400');
        } else if (stepIndex === 2) {
            addLogEntry('  [BPI] Batch pattern analysis complete', 'text-zinc-400');
            addLogEntry('  [BPI] 3 fraud indicators identified', 'text-yellow-400');
        }
        
        stepIndex++;
    }, 1500);
}

// Stop analysis
function stopAnalysis() {
    const startBtn = document.getElementById('startAnalysisBtn');
    const stopBtn = document.getElementById('stopAnalysisBtn');
    const progressText = document.getElementById('progressText');
    
    // Re-enable start button, disable stop button
    startBtn.disabled = false;
    startBtn.classList.remove('bg-zinc-700', 'hover:bg-zinc-700');
    startBtn.classList.add('bg-amber-600', 'hover:bg-amber-700');
    
    stopBtn.disabled = true;
    stopBtn.classList.remove('bg-red-600', 'hover:bg-red-700', 'text-white');
    stopBtn.classList.add('bg-zinc-700', 'hover:bg-zinc-600', 'text-zinc-300');
    
    progressText.textContent = 'Analysis stopped by user';
    addLogEntry('[USER] Analysis stopped by user', 'text-yellow-400');
}

// Add log entry
function addLogEntry(message, classes) {
    const logContainer = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = classes;
    logEntry.innerHTML = `[${timestamp}] ${message}`;
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Update executive summary
function updateSummary() {
    const summaryContent = document.getElementById('summaryContent');
    const now = new Date();
    const sessionId = `JARVIS-${now.getFullYear()}${(now.getMonth()+1).toString().padStart(2,'0')}${now.getDate().toString().padStart(2,'0')}-${now.getHours().toString().padStart(2,'0')}${now.getMinutes().toString().padStart(2,'0')}${now.getSeconds().toString().padStart(2,'0')}`;
    
    summaryContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div class="bg-zinc-800 rounded-lg p-4">
                <h4 class="font-bold text-amber-500 mb-2">INVESTIGATION OVERVIEW</h4>
                <p><strong>Session ID:</strong> ${sessionId}</p>
                <p><strong>Generated:</strong> ${now.toLocaleString()}</p>
                <p><strong>Compliance Level:</strong> MAXIMUM</p>
            </div>
            <div class="bg-zinc-800 rounded-lg p-4">
                <h4 class="font-bold text-amber-500 mb-2">COMPANY INFORMATION</h4>
                <p><strong>Investigation ID:</strong> INV-2025-00147</p>
                <p><strong>CIK:</strong> ${document.getElementById('cikDisplay').textContent.split('|')[0].trim()}</p>
                <p><strong>Company:</strong> ${document.getElementById('cikDisplay').textContent.split('|')[1]?.trim() || 'N/A'}</p>
            </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div class="bg-zinc-800 rounded-lg p-4">
                <h4 class="font-bold text-amber-500 mb-2">RISK ASSESSMENT</h4>
                <p><strong>Risk Score:</strong> 0.65</p>
                <p><strong>Risk Level:</strong> <span class="text-amber-500">MEDIUM</span></p>
                <p><strong>Assessment:</strong> Elevated risk profile identified</p>
                <p><strong>Recommended Action:</strong> Enhanced monitoring</p>
                <p><strong>Confidence:</strong> 85%</p>
            </div>
            <div class="bg-zinc-800 rounded-lg p-4">
                <h4 class="font-bold text-amber-500 mb-2">KEY FINDINGS</h4>
                <p><strong>Total Filings Analyzed:</strong> 12</p>
                <p><strong>Fraud Indicators:</strong> 3</p>
                <p><strong>Criminal Statutes:</strong> 1</p>
                <p><strong>Civil Violations:</strong> 2</p>
                <p><strong>Highest Severity:</strong> <span class="text-amber-500">MEDIUM</span></p>
            </div>
        </div>
        
        <div class="bg-zinc-800 rounded-lg p-4 mb-6">
            <h4 class="font-bold text-amber-500 mb-3">DETAILED FINDINGS</h4>
            <ul class="list-disc pl-5 space-y-2">
                <li><strong>Fraud Indicator (FI-001):</strong> Potential insider trading pattern detected in 3 recent transactions</li>
                <li><strong>Timing Issue (FI-002):</strong> Unusual derivative transactions during earnings blackout period</li>
                <li><strong>Disclosure Deficiency (CV-001):</strong> Incomplete disclosure in Form 4 filing dated ${new Date(Date.now() - 2592000000).toLocaleDateString()}</li>
                <li><strong>Pattern Alert (FI-003):</strong> Multiple trades executed through single brokerage account</li>
            </ul>
        </div>
        
        <div class="bg-zinc-800 rounded-lg p-4">
            <h4 class="font-bold text-amber-500 mb-3">RECOMMENDATIONS</h4>
            <ol class="list-decimal pl-5 space-y-2">
                <li><strong>HIGH Priority:</strong> Conduct detailed review of insider trading activity during blackout periods</li>
                <li><strong>MEDIUM Priority:</strong> Request clarification on incomplete Form 4 disclosures</li>
                <li><strong>MEDIUM Priority:</strong> Monitor for continued pattern of suspicious trading behavior</li>
                <li><strong>LOW Priority:</strong> Standard compliance documentation update</li>
            </ol>
        </div>
    `;
}

// Update files list
function updateFilesList() {
    const sessionInfo = document.getElementById('sessionInfo');
    const filesList = document.getElementById('filesList');
    const now = new Date();
    const sessionId = `JARVIS-${now.getFullYear()}${(now.getMonth()+1).toString().padStart(2,'0')}${now.getDate().toString().padStart(2,'0')}-${now.getHours().toString().padStart(2,'0')}${now.getMinutes().toString().padStart(2,'0')}${now.getSeconds().toString().padStart(2,'0')}`;
    
    sessionInfo.innerHTML = `
        Session ID: ${sessionId}<br>
        Output Folder: forensic_output_${sessionId}
    `;
    
    filesList.innerHTML = `
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 forensic_report_${sessionId}.html</span>
            <span class="text-zinc-500 text-sm">45.2 KB</span>
        </li>
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 forensic_summary_${sessionId}.md</span>
            <span class="text-zinc-500 text-sm">12.7 KB</span>
        </li>
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 forensic_output_${sessionId}.json</span>
            <span class="text-zinc-500 text-sm">87.3 KB</span>
        </li>
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 findings_${sessionId}.csv</span>
            <span class="text-zinc-500 text-sm">8.4 KB</span>
        </li>
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 timeline_${sessionId}.csv</span>
            <span class="text-zinc-500 text-sm">5.4 KB</span>
        </li>
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 timeline_${sessionId}.html</span>
            <span class="text-zinc-500 text-sm">23.1 KB</span>
        </li>
        <li class="flex justify-between items-center p-2 hover:bg-zinc-800 rounded cursor-pointer">
            <span>📄 recommendations_${sessionId}.csv</span>
            <span class="text-zinc-500 text-sm">3.9 KB</span>
        </li>
    `;
}

// Initialize charts (placeholder - would use Chart.js in production)
function initializeCharts() {
    // In a real implementation, you would initialize Chart.js charts here
    // For demonstration, we'll add placeholder text to the canvases
    
    const charts = [
        { id: 'riskDistributionChart', text: 'Risk Distribution Chart\n(Chart.js integration required)' },
        { id: 'riskLevelChart', text: 'Risk Level Breakdown\n(Chart.js integration required)' },
        { id: 'riskTrendChart', text: 'Risk Trend Analysis\n(Chart.js integration required)' }
    ];
    
    charts.forEach(chart => {
        const canvas = document.getElementById(chart.id);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#3f3f46';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#a1a1aa';
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            const lines = chart.text.split('\n');
            lines.forEach((line, index) => {
                ctx.fillText(line, canvas.width / 2, canvas.height / 2 + (index - 0.5) * 20);
            });
        }
    });
}

// Update charts with analysis data
function updateCharts() {
    // In a real implementation, this would update the Chart.js instances with actual data
    // For demonstration, we'll update the placeholder text
    
    const charts = [
        { id: 'riskDistributionChart', text: 'Risk Distribution:\n3 High | 5 Medium | 4 Low' },
        { id: 'riskLevelChart', text: 'Risk Levels:\nHigh: 25% | Medium: 42% | Low: 33%' },
        { id: 'riskTrendChart', text: 'Trend: Rising risk pattern detected' }
    ];
    
    charts.forEach(chart => {
        const canvas = document.getElementById(chart.id);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#18181b';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#fbbf24';
            ctx.font = '16px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            const lines = chart.text.split('\n');
            lines.forEach((line, index) => {
                ctx.fillText(line, canvas.width / 2, canvas.height / 2 + (index - 0.5) * 25);
            });
        }
    });
    
    addLogEntry('[VISUAL] Charts updated with analysis data', 'text-green-400');
}
