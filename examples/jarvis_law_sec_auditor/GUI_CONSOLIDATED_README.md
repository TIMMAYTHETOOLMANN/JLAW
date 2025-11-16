# JARVIS:LAW Forensic GUI - Consolidated Version
## Single-File Reference Guide

### File Location
`jarvis_forensic_gui_consolidated.py`

### Overview
This is a **complete, single-file GUI** that consolidates all forensic analysis functionality:
- Original SEC filing workflow (company search, date ranges, document selection)
- ForensicOutputGenerator backend integration
- Visual analytics with matplotlib charts
- Multi-format export (JSON, CSV, HTML, Markdown)
- Natural language executive summaries

### Key Features

#### 1. **Visual-First Interface**
- Analysis log with color-coded messages
- Executive summary in natural language
- Charts and graphs (risk distribution, trend analysis, pattern detection)
- Export files browser

#### 2. **Input Configuration**
- Company/Ticker search with automatic CIK lookup
- Document type selector (Form 4, 10-K, 10-Q, 8-K, etc.)
- Date range selection (from/to dates)
- Document limit control (recommended: 10-50 filings)

#### 3. **Analysis Workflow**
```
1. User enters company name or ticker → Clicks "Search Company"
2. System retrieves CIK automatically
3. User sets date range and document limit
4. Clicks "START FORENSIC ANALYSIS"
5. System:
   - Fetches filings from SEC.gov
   - Runs forensic analysis modules
   - Generates comprehensive output
   - Creates visualizations
   - Exports all formats
```

#### 4. **Output Tabs**
- **Analysis Log**: Real-time color-coded progress and results
- **Executive Summary**: Natural language report with risk assessment
- **Visual Analytics**: Charts showing risk distribution, trends, patterns
- **Export Files**: List of generated files with quick access buttons

### Module Integration

#### Forensic Modules (Automatic)
1. Zero-Dollar Risk Detection
2. 10b5-1 Compliance Check
3. Risk Weighting (by insider role)
4. Earnings Window Correlation
5. Batch Pattern Intelligence

#### Backend Systems
- **ForensicOutputGenerator**: Generates comprehensive forensic output files
- **SEC Crawler**: Fetches filings from SEC EDGAR database
- **Form Parsers**: HTML and XML parser for Form 4 and other filings

### Generated Output Files

For each analysis session, the system creates:
```
forensic_output_{session_id}/
├── forensic_output_{session_id}.json      # Complete data (machine-readable)
├── forensic_summary_{session_id}.md       # Natural language summary
├── forensic_report_{session_id}.html      # Visual HTML report
├── findings_{session_id}.csv              # Detailed findings table
├── timeline_{session_id}.csv              # Timeline of events
├── recommendations_{session_id}.csv       # Action recommendations
└── timeline_{session_id}.html             # Interactive timeline visualization
```

### How to Use

#### Basic Workflow
1. **Launch**: `python jarvis_forensic_gui_consolidated.py`
2. **Search Company**: Enter "Tesla" or "TSLA" → Click "Search Company"
3. **Configure Analysis**:
   - Date Range: Set from/to dates (e.g., 2023-01-01 to 2024-12-31)
   - Document Limit: Set to 10-50 for optimal performance
4. **Run**: Click "START FORENSIC ANALYSIS"
5. **Review**: Check all tabs for results and visualizations
6. **Export**: Click "Export Outputs" or "Open Output Folder"

#### Advanced Options
- **Document Type**: Change from Form 4 to 10-K, 10-Q, etc. for different analysis types
- **Date Range Toggle**: Uncheck to analyze all available filings
- **Document Limit Toggle**: Uncheck to use date range only

### Color Coding in Analysis Log

- **GREEN (success)**: Successful operations, low-risk findings
- **YELLOW (warning)**: Medium-risk findings, non-critical warnings
- **RED (error)**: High-risk findings, critical errors
- **BLUE (info)**: Informational messages, configuration details
- **WHITE (header)**: Section headers, major milestones

### Customization Points

The consolidated file is structured for easy modification:

#### 1. Color Scheme (Line 107-118)
```python
self.colors = {
    'bg_dark': '#1a1a2e',       # Header background
    'bg_medium': '#16213e',     # Main background
    'bg_light': '#0f3460',      # Button background
    'accent': '#00ff41',        # Primary accent (green)
    'accent2': '#667eea',       # Secondary accent (purple)
    'warning': '#ff9800',       # Warning color (orange)
    'error': '#f44336',         # Error color (red)
    'success': '#4CAF50',       # Success color (green)
    'text': '#e0e0e0',          # Primary text
    'text_dim': '#888888'       # Secondary text
}
```

#### 2. Default Values (Line 64-71)
```python
self.doc_type = tk.StringVar(value="4")  # Default document type
self.start_date = tk.StringVar(value=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
self.end_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
self.doc_limit = tk.StringVar(value="10")  # Default filing limit
```

#### 3. Risk Thresholds (Line 1154-1166)
Adjust risk score thresholds for classification:
- High Risk: >= 0.7
- Medium Risk: 0.4 - 0.69
- Low Risk: < 0.4

#### 4. Visualization Settings (Line 1243-1305)
Customize chart colors, sizes, and styles in `_generate_visualizations()`

### Enhancement Examples

#### Add New Tab
```python
def _create_custom_tab(self):
    custom_tab = tk.Frame(self.notebook, bg='#1e1e1e')
    self.notebook.add(custom_tab, text='🎯 Custom Analysis')
    # Add your custom widgets here
```

#### Add New Analysis Module
```python
def _analyze_filing(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
    # ...existing code...
    
    # Add your custom analysis
    custom_result = your_custom_analysis_function(filing_data)
    if custom_result['flagged']:
        patterns.append({'pattern': 'CUSTOM_PATTERN'})
        base_risk += 0.15
    
    # ...rest of existing code...
```

#### Add Export Format
```python
def _export_custom_format(self):
    if not self.last_output:
        return
    
    # Your custom export logic
    custom_file = Path(f"forensic_output_{self.last_session_id}") / "custom_output.txt"
    with open(custom_file, 'w') as f:
        f.write("Your custom formatted output")
```

### Dependencies

**Required:**
- `tkinter` (built-in with Python)
- `pathlib` (built-in with Python 3.4+)
- `datetime` (built-in)
- `json` (built-in)
- `threading` (built-in)

**Optional (for full features):**
- `matplotlib` - For visual analytics charts
- Local forensic modules:
  - `forensic_output_generator.py`
  - `tools/sec_crawler.py`
  - `form4_html_parser.py`
  - `form4_xml_parser.py`
  - `tools/__init__.py` (analysis modules)

**Graceful Degradation:**
The GUI will work with limited features if optional dependencies are missing.

### Troubleshooting

#### Issue: "Module not available" warnings
**Solution**: Install missing modules or run with limited features

#### Issue: GUI window doesn't appear
**Solution**: Check if tkinter is properly installed:
```bash
python -c "import tkinter; print('Tkinter OK')"
```

#### Issue: Visualizations not showing
**Solution**: Install matplotlib:
```bash
pip install matplotlib
```

#### Issue: Company search fails
**Solution**: Check internet connection and SEC.gov accessibility

### Performance Tips

1. **Document Limit**: Keep between 10-50 for optimal performance
2. **Date Range**: Narrow ranges process faster
3. **Document Type**: Form 4 is fastest, 10-K/10-Q are slower (larger files)
4. **Progress**: Monitor the Analysis Log tab for real-time progress

### Best Practices

1. **Start Small**: Begin with 10 filings to test
2. **Review Logs**: Always check Analysis Log for detailed information
3. **Save Outputs**: Export/backup forensic outputs for records
4. **Incremental Analysis**: Run multiple smaller analyses rather than one massive analysis
5. **Visual Review**: Use Visual Analytics tab to quickly identify patterns

### File Structure

The consolidated file is organized in sections:
- **Lines 1-60**: Imports and setup
- **Lines 61-120**: Class initialization
- **Lines 121-450**: UI creation methods
- **Lines 451-650**: Event handlers
- **Lines 651-950**: Analysis workflow
- **Lines 951-1350**: Output generation and visualization
- **Lines 1351-1450**: Helper methods
- **Lines 1451-1480**: Main entry point

### Quick Reference

| Action | Location | Shortcut |
|--------|----------|----------|
| Search Company | Input Section | Enter + Click Search |
| Start Analysis | Big Blue Button | - |
| Stop Analysis | Red Stop Button | - |
| Clear Log | Clear Log Button | - |
| Export Files | Export Outputs Button | - |
| Open Folder | Files Tab → Open Folder | - |
| View Report | Files Tab → Open HTML | - |

### Version History

- **v3.0 (Consolidated)**: Single-file version with all features integrated
- **v2.5**: Original multi-file version with separate modules
- **v2.0**: Initial visual dashboard with basic analytics
- **v1.0**: Command-line version

### Support

For issues or enhancements, refer to the inline code documentation and comments throughout the file. The code is structured to be self-documenting with clear function names and descriptive comments.

---

**Status**: PRODUCTION READY ✅
**Last Updated**: November 11, 2025
**File Size**: ~50KB (single file)
**Lines of Code**: ~1,480

