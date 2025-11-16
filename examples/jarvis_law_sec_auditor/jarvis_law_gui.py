"""
JARVIS:LAW Forensic Analysis System - Graphical User Interface
===============================================================

Plug-and-play GUI for SEC forensic analysis with all enhancement modules.

Features:
- Company search by name or ticker
- Date range selection
- SEC document type selector (Form 4, 10-K, 10-Q, 8-K, etc.)
- Flexible document limit (date range OR count)
- Real-time progress tracking
- Comprehensive results display
- Batch Pattern Intelligence integration

PowerShell Compatible: YES
"""

import sys
import os
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter.font import Font

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.sec_crawler import fetch_sec_filings_by_cik, search_company_by_ticker
from form4_html_parser import Form4HTMLParser
from form4_xml_parser import Form4XMLParser
from tools import (
    detect_zero_dollar_risk,
    check_10b5_plan,
    weight_risk_score,
    correlate_all_transactions,
    analyze_batch
)


class JarvisLawGUI:
    """Main GUI application for JARVIS:LAW Forensic Analysis System."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS:LAW - SEC Forensic Analysis System v2.5")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # State variables
        self.company_cik = tk.StringVar()
        self.company_name = tk.StringVar()
        self.doc_type = tk.StringVar(value="4")
        self.start_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.end_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.doc_limit = tk.StringVar(value="10")
        self.use_date_range = tk.BooleanVar(value=True)
        self.use_doc_limit = tk.BooleanVar(value=True)
        
        self.analysis_running = False
        self.current_analyses = []
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface components."""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#1a1a2e", height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="JARVIS:LAW",
            font=("Consolas", 20, "bold"),
            bg="#1a1a2e",
            fg="#00ff41"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        subtitle_label = tk.Label(
            header_frame,
            text="SEC Forensic Analysis System - All Modules Operational",
            font=("Consolas", 10),
            bg="#1a1a2e",
            fg="#888888"
        )
        subtitle_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Main container
        main_frame = tk.Frame(self.root, padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === INPUT SECTION ===
        input_frame = tk.LabelFrame(
            main_frame,
            text="Analysis Configuration",
            font=("Consolas", 11, "bold"),
            padx=15,
            pady=15
        )
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Company Input
        row1 = tk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(row1, text="Company:", font=("Consolas", 10), width=15, anchor='w').pack(side=tk.LEFT)
        
        company_entry = tk.Entry(row1, textvariable=self.company_name, font=("Consolas", 10), width=30)
        company_entry.pack(side=tk.LEFT, padx=5)
        
        search_btn = tk.Button(
            row1,
            text="Search Company",
            command=self._search_company,
            font=("Consolas", 9),
            bg="#4CAF50",
            fg="white",
            cursor="hand2"
        )
        search_btn.pack(side=tk.LEFT, padx=5)
        
        self.cik_label = tk.Label(row1, text="CIK: Not selected", font=("Consolas", 9), fg="#666666")
        self.cik_label.pack(side=tk.LEFT, padx=10)
        
        # Row 2: Document Type
        row2 = tk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="Document Type:", font=("Consolas", 10), width=15, anchor='w').pack(side=tk.LEFT)
        
        doc_types = ["4", "10-K", "10-Q", "8-K", "S-1", "3", "5", "13D", "13F", "DEF 14A"]
        doc_combo = ttk.Combobox(row2, textvariable=self.doc_type, values=doc_types, 
                                 font=("Consolas", 10), width=15, state="readonly")
        doc_combo.pack(side=tk.LEFT, padx=5)
        
        doc_info = {
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
        }
        
        self.doc_info_label = tk.Label(row2, text=doc_info.get("4", ""), 
                                       font=("Consolas", 8), fg="#555555")
        self.doc_info_label.pack(side=tk.LEFT, padx=10)
        
        doc_combo.bind("<<ComboboxSelected>>", lambda e: self.doc_info_label.config(
            text=doc_info.get(self.doc_type.get(), "")))
        
        # Row 3: Date Range
        row3 = tk.Frame(input_frame)
        row3.pack(fill=tk.X, pady=5)
        
        date_check = tk.Checkbutton(row3, text="Date Range:", variable=self.use_date_range,
                                   font=("Consolas", 10), width=15, anchor='w')
        date_check.pack(side=tk.LEFT)
        
        tk.Label(row3, text="From:", font=("Consolas", 9)).pack(side=tk.LEFT, padx=(0, 5))
        start_entry = tk.Entry(row3, textvariable=self.start_date, font=("Consolas", 9), width=12)
        start_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row3, text="To (optional):", font=("Consolas", 9)).pack(side=tk.LEFT, padx=(10, 5))
        end_entry = tk.Entry(row3, textvariable=self.end_date, font=("Consolas", 9), width=12)
        end_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row3, text="(YYYY-MM-DD, To defaults to today)", font=("Consolas", 8), fg="#888888").pack(side=tk.LEFT, padx=5)
        
        # Row 4: Document Limit
        row4 = tk.Frame(input_frame)
        row4.pack(fill=tk.X, pady=5)
        
        limit_check = tk.Checkbutton(row4, text="Document Limit:", variable=self.use_doc_limit,
                                    font=("Consolas", 10), width=15, anchor='w')
        limit_check.pack(side=tk.LEFT)
        
        limit_entry = tk.Entry(row4, textvariable=self.doc_limit, font=("Consolas", 10), width=10)
        limit_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row4, text="(PRIMARY - Max filings to analyze)", font=("Consolas", 8, "bold"), fg="#ff8800").pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.analyze_btn = tk.Button(
            button_frame,
            text="START FORENSIC ANALYSIS",
            command=self._start_analysis,
            font=("Consolas", 11, "bold"),
            bg="#007acc",
            fg="white",
            height=2,
            cursor="hand2"
        )
        self.analyze_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(
            button_frame,
            text="STOP",
            command=self._stop_analysis,
            font=("Consolas", 10),
            bg="#dc3545",
            fg="white",
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="Clear Log",
            command=self._clear_log,
            font=("Consolas", 9),
            bg="#6c757d",
            fg="white",
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # === PROGRESS SECTION ===
        progress_frame = tk.LabelFrame(
            main_frame,
            text="Analysis Progress",
            font=("Consolas", 10, "bold"),
            padx=10,
            pady=10
        )
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(
            progress_frame,
            text="Ready to analyze",
            font=("Consolas", 9),
            fg="#666666"
        )
        self.status_label.pack(anchor='w')
        
        # === OUTPUT/LOG SECTION ===
        log_frame = tk.LabelFrame(
            main_frame,
            text="Analysis Log & Results",
            font=("Consolas", 10, "bold"),
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff41",
            insertbackground="white",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.log_text.tag_config("success", foreground="#00ff41")
        self.log_text.tag_config("error", foreground="#ff4444")
        self.log_text.tag_config("warning", foreground="#ffaa00")
        self.log_text.tag_config("info", foreground="#00aaff")
        self.log_text.tag_config("header", foreground="#ffffff", font=("Consolas", 10, "bold"))
        
        # Initial welcome message
        self._log("[JARVIS:LAW] Forensic Analysis System v2.5 - Ready", "header")
        self._log("[SYSTEM] All enhancement modules loaded (Modules 1-5)", "success")
        self._log("[STATUS] Awaiting analysis configuration...", "info")
    
    def _log(self, message: str, tag: str = "info"):
        """Add message to log with optional color tag."""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def _clear_log(self):
        """Clear the analysis log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log("[SYSTEM] Log cleared", "info")
    
    def _search_company(self):
        """Search for company by name/ticker and get CIK."""
        company_input = self.company_name.get().strip()
        if not company_input:
            messagebox.showwarning("Input Required", "Please enter a company name or ticker symbol.")
            return
        
        self._log(f"[SEARCH] Looking up company: {company_input}", "info")
        
        try:
            # Use SEC search function
            result = search_company_by_ticker(company_input)
            
            if result and 'cik' in result:
                self.company_cik.set(result['cik'])
                self.company_name.set(result.get('name', company_input))
                self.cik_label.config(
                    text=f"CIK: {result['cik']} | {result.get('name', 'Unknown')}",
                    fg="#00ff41"
                )
                self._log(f"[SUCCESS] Found: {result.get('name')} (CIK: {result['cik']})", "success")
            else:
                messagebox.showerror("Not Found", f"Could not find company: {company_input}")
                self._log(f"[ERROR] Company not found: {company_input}", "error")
        except Exception as e:
            messagebox.showerror("Search Error", f"Error searching company:\n{str(e)}")
            self._log(f"[ERROR] Search failed: {str(e)}", "error")
    
    def _validate_inputs(self) -> bool:
        """Validate user inputs before starting analysis."""
        # Check CIK
        if not self.company_cik.get():
            messagebox.showerror("Invalid Input", "Please search and select a company first.")
            return False
        
        # Check that at least one constraint is selected
        if not self.use_date_range.get() and not self.use_doc_limit.get():
            messagebox.showerror("Invalid Input", "Please select at least Date Range OR Document Limit.")
            return False
        
        # Validate date range if selected
        if self.use_date_range.get():
            try:
                start = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
                end = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
                if start > end:
                    messagebox.showerror("Invalid Date Range", "Start date must be before end date.")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Date Format", "Please use YYYY-MM-DD format for dates.")
                return False
        
        # Validate document limit if selected
        if self.use_doc_limit.get():
            try:
                limit = int(self.doc_limit.get())
                if limit <= 0:
                    messagebox.showerror("Invalid Limit", "Document limit must be greater than 0.")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Limit", "Document limit must be a number.")
                return False
        
        return True
    
    def _start_analysis(self):
        """Start the forensic analysis in a background thread."""
        if not self._validate_inputs():
            return
        
        # Disable start button, enable stop button
        self.analyze_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.analysis_running = True
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(target=self._run_analysis, daemon=True)
        analysis_thread.start()
    
    def _stop_analysis(self):
        """Stop the running analysis."""
        self.analysis_running = False
        self._log("[USER] Analysis stopped by user", "warning")
        self.analyze_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Analysis stopped")
    
    def _run_analysis(self):
        """Execute the complete forensic analysis workflow."""
        try:
            self._log("=" * 80, "header")
            self._log("[ANALYSIS] Starting Complete Forensic Analysis", "header")
            self._log("=" * 80, "header")
            
            # Extract parameters
            cik = self.company_cik.get()
            company = self.company_name.get()
            doc_type = self.doc_type.get()
            
            # Determine year range
            if self.use_date_range.get():
                start_date = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
                end_date = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
                year_start = start_date.year
                year_end = end_date.year
            else:
                year_start = year_end = datetime.now().year
            
            # Document limit
            if self.use_doc_limit.get():
                limit = int(self.doc_limit.get())
            else:
                limit = 100  # Default max
            
            self._log(f"[CONFIG] Company: {company} (CIK: {cik})", "info")
            self._log(f"[CONFIG] Document Type: {doc_type}", "info")
            self._log(f"[CONFIG] Year Range: {year_start} - {year_end}", "info")
            self._log(f"[CONFIG] Document Limit: {limit}", "info")
            
            # Step 1: Fetch filings from SEC.gov
            self.status_label.config(text="Fetching filings from SEC.gov...")
            self.progress_var.set(10)
            
            self._log(f"\n[STEP 1] Fetching {doc_type} filings from SEC.gov...", "info")
            
            # Fetch with a higher limit to ensure we get enough after date filtering
            fetch_limit = limit * 3 if self.use_date_range.get() else limit
            
            filings = fetch_sec_filings_by_cik(
                cik=cik,
                form_type=doc_type,
                year_start=year_start,
                year_end=year_end,
                limit=fetch_limit
            )
            
            if not filings:
                self._log("[ERROR] No filings retrieved from SEC.gov", "error")
                messagebox.showerror("No Filings", "No filings found for the specified criteria.")
                self._reset_ui()
                return
            
            self._log(f"[INFO] Fetched {len(filings)} total filings from SEC", "info")
            
            # Filter by date range if specified (start date only - end date is optional)
            if self.use_date_range.get():
                start_date_str = self.start_date.get()
                end_date_str = self.end_date.get()
                
                # Apply start date filter
                filtered_filings = []
                for f in filings:
                    filing_date = f.get('filing_date', '')
                    if not filing_date:
                        continue
                    
                    # Check start date
                    if filing_date < start_date_str:
                        continue
                    
                    # Check end date only if it's different from today (meaning user set it)
                    if end_date_str != datetime.now().strftime("%Y-%m-%d"):
                        if filing_date > end_date_str:
                            continue
                    
                    filtered_filings.append(f)
                
                filings = filtered_filings
                self._log(f"[INFO] After date filtering: {len(filings)} filings", "info")
            
            # CRITICAL: Apply document limit AFTER filtering - this is the final constraint
            if len(filings) > limit:
                self._log(f"[INFO] Limiting to first {limit} filings (from {len(filings)} available)", "info")
                filings = filings[:limit]
            
            self._log(f"[SUCCESS] Retrieved {len(filings)} filings", "success")
            self.progress_var.set(20)
            
            if not self.analysis_running:
                self._reset_ui()
                return
            
            # Step 2: Parse and analyze each filing
            self.status_label.config(text=f"Analyzing {len(filings)} filings...")
            self._log(f"\n[STEP 2] Running forensic analysis on {len(filings)} filings...", "info")
            
            self.current_analyses = []
            total = len(filings)
            
            for i, filing_meta in enumerate(filings, 1):
                if not self.analysis_running:
                    break
                
                progress = 20 + (60 * i / total)
                self.progress_var.set(progress)
                self.status_label.config(text=f"Analyzing filing {i}/{total}...")
                
                self._log(f"\n[FILING {i}/{total}] {filing_meta.get('filing_date')} | {filing_meta.get('accession_number')}", "info")
                
                try:
                    # Parse filing
                    archived_path = filing_meta.get('archived', {}).get('archived_path')
                    if not archived_path:
                        self._log(f"  [SKIP] No archived file", "warning")
                        continue
                    
                    filing_data = self._parse_filing(Path(archived_path))
                    
                    # Run forensic analysis
                    analysis = self._analyze_filing(filing_data)
                    self.current_analyses.append(analysis)
                    
                    self._log(f"  [RISK] Final Score: {analysis['final_risk_score']:.3f}", 
                             "error" if analysis['final_risk_score'] >= 0.7 else "warning" if analysis['final_risk_score'] >= 0.4 else "success")
                    
                except Exception as e:
                    self._log(f"  [ERROR] Analysis failed: {str(e)}", "error")
                    continue
            
            if not self.analysis_running:
                self._reset_ui()
                return
            
            # Step 3: Batch Pattern Intelligence (Module 5)
            if len(self.current_analyses) >= 2:
                self.status_label.config(text="Running Batch Pattern Intelligence...")
                self.progress_var.set(85)
                
                self._log(f"\n[STEP 3] Running Module 5: Batch Pattern Intelligence...", "info")
                
                filings_batch = [a['filing_data'] for a in self.current_analyses]
                batch_results = analyze_batch(filings_batch, output_dir=None)
                
                self._log(f"[BPI] Overall Risk: {batch_results['master_assessment']['overall_risk_level']}", 
                         "error" if batch_results['master_assessment']['overall_risk_level'] in ['HIGH', 'CRITICAL'] else "warning")
                self._log(f"[BPI] Risk Signals: {batch_results['master_assessment']['risk_signal_count']}", "info")
                self._log(f"[BPI] Composite Risk: {batch_results['master_assessment']['composite_risk_score']:.3f}", "info")
            
            # Step 4: Generate summary
            self.status_label.config(text="Generating summary...")
            self.progress_var.set(95)
            
            self._generate_summary()
            
            # Complete
            self.progress_var.set(100)
            self.status_label.config(text="Analysis complete!")
            
            self._log("\n" + "=" * 80, "header")
            self._log("[COMPLETE] Forensic analysis finished successfully", "success")
            self._log("=" * 80, "header")
            
            messagebox.showinfo("Analysis Complete", 
                              f"Successfully analyzed {len(self.current_analyses)} filings.\n\n"
                              f"Check the log for detailed results.")
            
        except Exception as e:
            self._log(f"\n[FATAL ERROR] Analysis failed: {str(e)}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")
            messagebox.showerror("Analysis Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self._reset_ui()
    
    def _parse_filing(self, filing_path: Path) -> Dict[str, Any]:
        """Parse a filing using appropriate parser."""
        # Read first few lines to determine file type
        with open(filing_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = f.read(500).lower()
        
        is_html = '<html' in first_lines or '<!doctype html' in first_lines
        is_xml = '<?xml' in first_lines and '<ownershipdocument>' in first_lines
        
        if is_xml and not is_html:
            try:
                parser = Form4XMLParser(str(filing_path))
                return parser.extract_all()
            except:
                pass
        
        # Default to HTML parser
        parser = Form4HTMLParser(str(filing_path))
        return parser.extract_all()
    
    def _analyze_filing(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run forensic analysis on a single filing."""
        base_risk = 0.0
        patterns = []
        
        # Basic pattern detection
        transactions = filing_data.get('transactions', [])
        if transactions:
            large_trades = [tx for tx in transactions if tx.get('shares_traded', 0) > 100000]
            if large_trades:
                patterns.append({'pattern': 'LARGE_VOLUME', 'count': len(large_trades)})
                base_risk += 0.1
            
            sales = [tx for tx in transactions if tx.get('transaction_code') in ['S', 'D']]
            if sales:
                patterns.append({'pattern': 'INSIDER_SALES', 'count': len(sales)})
                base_risk += 0.15
        
        # Module 1: Zero-Dollar Detection
        zero_dollar = detect_zero_dollar_risk(filing_data)
        if zero_dollar['detected']:
            self._log("  [MODULE 1] Zero-Dollar Pattern: DETECTED", "warning")
            patterns.append({'pattern': 'ZERO_DOLLAR', 'details': zero_dollar})
            base_risk += zero_dollar.get('risk_impact', 0.2)
        
        # Module 2: 10b5-1 Compliance
        plan_check = check_10b5_plan(filing_data)
        if plan_check.get('compliant') == False:
            self._log("  [MODULE 2] 10b5-1 Non-Compliance: FLAGGED", "warning")
            patterns.append({'pattern': '10B5_NON_COMPLIANCE'})
            base_risk += 0.1
        
        # Module 3: Risk Weighting
        insider_role = filing_data.get('reporting_owner', {}).get('relationship', 'UNKNOWN')
        weighted_risk = weight_risk_score(base_risk, insider_role)
        
        # Module 4: Earnings Correlation
        earnings_analysis = correlate_all_transactions(filing_data)
        earnings_flags = sum(1 for tx in earnings_analysis.get('transactions', []) 
                            if tx.get('within_window', False))
        if earnings_flags > 0:
            self._log(f"  [MODULE 4] Earnings Window Trades: {earnings_flags}", "warning")
            patterns.append({'pattern': 'EARNINGS_WINDOW', 'count': earnings_flags})
            weighted_risk += 0.1
        
        weighted_risk = min(1.0, weighted_risk)
        
        return {
            'filing_data': filing_data,
            'patterns_detected': patterns,
            'base_risk_score': base_risk,
            'weighted_risk_score': weighted_risk,
            'final_risk_score': weighted_risk,
            'insider_role': insider_role
        }
    
    def _generate_summary(self):
        """Generate and display analysis summary."""
        if not self.current_analyses:
            return
        
        self._log("\n" + "-" * 80, "info")
        self._log("[SUMMARY] Analysis Results", "header")
        self._log("-" * 80, "info")
        
        total = len(self.current_analyses)
        avg_risk = sum(a['final_risk_score'] for a in self.current_analyses) / total
        max_risk = max(a['final_risk_score'] for a in self.current_analyses)
        
        high_risk = sum(1 for a in self.current_analyses if a['final_risk_score'] >= 0.7)
        medium_risk = sum(1 for a in self.current_analyses if 0.4 <= a['final_risk_score'] < 0.7)
        low_risk = sum(1 for a in self.current_analyses if a['final_risk_score'] < 0.4)
        
        self._log(f"Total Filings Analyzed: {total}", "info")
        self._log(f"Average Risk Score: {avg_risk:.3f}", "info")
        self._log(f"Highest Risk Score: {max_risk:.3f}", "error" if max_risk >= 0.7 else "warning")
        self._log(f"", "info")
        self._log(f"High Risk Filings (0.7+): {high_risk}", "error" if high_risk > 0 else "info")
        self._log(f"Medium Risk Filings (0.4-0.69): {medium_risk}", "warning" if medium_risk > 0 else "info")
        self._log(f"Low Risk Filings (<0.4): {low_risk}", "success")
    
    def _reset_ui(self):
        """Reset UI to ready state."""
        self.analyze_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.analysis_running = False


def main():
    """Main entry point for GUI application."""
    root = tk.Tk()
    app = JarvisLawGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
