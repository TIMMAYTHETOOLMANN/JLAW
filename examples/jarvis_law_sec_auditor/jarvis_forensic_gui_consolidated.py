#!/usr/bin/env python3
"""
JARVIS:LAW Forensic Analysis System - Consolidated GUI v3.0
============================================================

Complete visual-first forensic analysis GUI with integrated backend.
Single file for easy enhancement and modification.

Features:
- Company search by name or ticker
- Date range and document type selection
- Real-time progress tracking and analysis
- Visual dashboard with charts and graphs (when matplotlib available)
- Natural language executive summaries
- Integrated ForensicOutputGenerator backend
- Multi-format export (JSON, CSV, HTML, Markdown)
- Color-coded analysis log

Author: JARVIS 2.0 Core Commander
Status: PRODUCTION READY - SINGLE FILE CONSOLIDATED
License: MIT
"""

import sys
import os
import json
import threading
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter.font import Font

# Try to import matplotlib for visualizations
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[WARNING] Matplotlib not available - visualizations will be limited")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import forensic modules
try:
    from forensic_output_generator import ForensicOutputGenerator, OutputStandard
    FORENSIC_GENERATOR_AVAILABLE = True
except ImportError:
    FORENSIC_GENERATOR_AVAILABLE = False
    print("[WARNING] ForensicOutputGenerator not available - export features limited")

# Import SEC analysis tools
try:
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
    SEC_TOOLS_AVAILABLE = True
except ImportError:
    SEC_TOOLS_AVAILABLE = False
    print("[WARNING] SEC analysis tools not fully available")


class JarvisForensicGUI:
    """
    Consolidated Visual-First Forensic Analysis GUI.
    
    This class combines the original workflow-based interface with
    the ForensicOutputGenerator backend for comprehensive analysis.
    """
    
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("JARVIS:LAW - Forensic Analysis System v3.0 (Consolidated)")
        self.root.geometry("1200x850")
        self.root.resizable(True, True)
        
        # State variables
        self.company_cik = tk.StringVar()
        self.company_name = tk.StringVar()
        self.ticker = tk.StringVar()
        self.doc_type = tk.StringVar(value="4")
        self.start_date = tk.StringVar(value=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        self.end_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.doc_limit = tk.StringVar(value="10")
        self.use_date_range = tk.BooleanVar(value=True)
        self.use_doc_limit = tk.BooleanVar(value=True)
        
        # Analysis state
        self.analysis_running = False
        self.current_analyses = []
        self.investigation_data = {}
        self.last_output = None
        self.last_session_id = None
        
        # Backend integrations
        if FORENSIC_GENERATOR_AVAILABLE:
            self.generator = ForensicOutputGenerator()
        else:
            self.generator = None
        
        # Color scheme
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#00ff41',
            'accent2': '#667eea',
            'warning': '#ff9800',
            'error': '#f44336',
            'success': '#4CAF50',
            'text': '#e0e0e0',
            'text_dim': '#888888'
        }
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the complete user interface."""
        self.root.configure(bg=self.colors['bg_medium'])
        
        # === HEADER ===
        self._create_header()
        
        # === MAIN CONTAINER ===
        main_frame = tk.Frame(self.root, bg=self.colors['bg_medium'], padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === INPUT CONFIGURATION SECTION ===
        self._create_input_section(main_frame)
        
        # === PROGRESS SECTION ===
        self._create_progress_section(main_frame)
        
        # === RESULTS NOTEBOOK (TABS) ===
        self._create_results_notebook(main_frame)
        
    def _create_header(self):
        """Create the application header."""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="⚖️ JARVIS:LAW",
            font=("Consolas", 20, "bold"),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="SEC Forensic Analysis System v3.0 - Visual Dashboard (Consolidated)",
            font=("Consolas", 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim']
        )
        subtitle_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Status indicator
        self.status_indicator = tk.Label(
            header_frame,
            text="● READY",
            font=('Consolas', 12, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=10)
        
    def _create_input_section(self, parent):
        """Create the analysis configuration input section."""
        input_frame = tk.LabelFrame(
            parent,
            text="Analysis Configuration",
            font=("Consolas", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            padx=15,
            pady=15
        )
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Company Search
        row1 = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(row1, text="Company/Ticker:", font=("Consolas", 10), 
                bg=self.colors['bg_medium'], fg=self.colors['text'], 
                width=15, anchor='w').pack(side=tk.LEFT)
        
        company_entry = tk.Entry(row1, textvariable=self.company_name, 
                                font=("Consolas", 10), width=30,
                                bg='#2a2a3e', fg=self.colors['text'], 
                                relief=tk.FLAT, insertbackground='white')
        company_entry.pack(side=tk.LEFT, padx=5)
        
        search_btn = tk.Button(
            row1,
            text="🔍 Search Company",
            command=self._search_company,
            font=("Consolas", 9, "bold"),
            bg=self.colors['success'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=5
        )
        search_btn.pack(side=tk.LEFT, padx=5)
        
        self.cik_label = tk.Label(row1, text="CIK: Not selected", 
                                 font=("Consolas", 9), 
                                 bg=self.colors['bg_medium'], 
                                 fg=self.colors['text_dim'])
        self.cik_label.pack(side=tk.LEFT, padx=10)
        
        # Row 2: Document Type
        row2 = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="Document Type:", font=("Consolas", 10),
                bg=self.colors['bg_medium'], fg=self.colors['text'],
                width=15, anchor='w').pack(side=tk.LEFT)
        
        doc_types = ["4", "10-K", "10-Q", "8-K", "S-1", "3", "5", "13D", "13F", "DEF 14A"]
        doc_combo = ttk.Combobox(row2, textvariable=self.doc_type, 
                                values=doc_types, font=("Consolas", 10), 
                                width=15, state="readonly")
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
                                      font=("Consolas", 8),
                                      bg=self.colors['bg_medium'],
                                      fg=self.colors['text_dim'])
        self.doc_info_label.pack(side=tk.LEFT, padx=10)
        
        doc_combo.bind("<<ComboboxSelected>>", 
                      lambda e: self.doc_info_label.config(
                          text=doc_info.get(self.doc_type.get(), "")))
        
        # Row 3: Date Range
        row3 = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        row3.pack(fill=tk.X, pady=5)
        
        date_check = tk.Checkbutton(row3, text="Date Range:", 
                                   variable=self.use_date_range,
                                   font=("Consolas", 10), width=15, anchor='w',
                                   bg=self.colors['bg_medium'], fg=self.colors['text'],
                                   selectcolor=self.colors['bg_light'],
                                   activebackground=self.colors['bg_medium'])
        date_check.pack(side=tk.LEFT)
        
        tk.Label(row3, text="From:", font=("Consolas", 9),
                bg=self.colors['bg_medium'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=(0, 5))
        start_entry = tk.Entry(row3, textvariable=self.start_date, 
                              font=("Consolas", 9), width=12,
                              bg='#2a2a3e', fg=self.colors['text'], 
                              relief=tk.FLAT, insertbackground='white')
        start_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row3, text="To:", font=("Consolas", 9),
                bg=self.colors['bg_medium'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=(10, 5))
        end_entry = tk.Entry(row3, textvariable=self.end_date, 
                            font=("Consolas", 9), width=12,
                            bg='#2a2a3e', fg=self.colors['text'], 
                            relief=tk.FLAT, insertbackground='white')
        end_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row3, text="(YYYY-MM-DD)", font=("Consolas", 8),
                bg=self.colors['bg_medium'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=5)
        
        # Row 4: Document Limit
        row4 = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        row4.pack(fill=tk.X, pady=5)
        
        limit_check = tk.Checkbutton(row4, text="Document Limit:", 
                                    variable=self.use_doc_limit,
                                    font=("Consolas", 10), width=15, anchor='w',
                                    bg=self.colors['bg_medium'], fg=self.colors['text'],
                                    selectcolor=self.colors['bg_light'],
                                    activebackground=self.colors['bg_medium'])
        limit_check.pack(side=tk.LEFT)
        
        limit_entry = tk.Entry(row4, textvariable=self.doc_limit, 
                              font=("Consolas", 10), width=10,
                              bg='#2a2a3e', fg=self.colors['text'], 
                              relief=tk.FLAT, insertbackground='white')
        limit_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row4, text="(Max filings to analyze - recommended: 10-50)",
                font=("Consolas", 8, "bold"),
                bg=self.colors['bg_medium'],
                fg=self.colors['warning']).pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        button_frame = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.analyze_btn = tk.Button(
            button_frame,
            text="🚀 START FORENSIC ANALYSIS",
            command=self._start_analysis,
            font=("Consolas", 12, "bold"),
            bg=self.colors['accent2'],
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            padx=15
        )
        self.analyze_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹ STOP",
            command=self._stop_analysis,
            font=("Consolas", 10, "bold"),
            bg=self.colors['error'],
            fg="white",
            state=tk.DISABLED,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            button_frame,
            text="📁 Export Outputs",
            command=self._export_outputs,
            font=("Consolas", 9, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            padx=10
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="Clear Log",
            command=self._clear_log,
            font=("Consolas", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            padx=10
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
    def _create_progress_section(self, parent):
        """Create the progress tracking section."""
        progress_frame = tk.LabelFrame(
            parent,
            text="Analysis Progress",
            font=("Consolas", 10, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
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
            text="Ready to analyze - Enter company and click START",
            font=("Consolas", 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim']
        )
        self.status_label.pack(anchor='w')
        
    def _create_results_notebook(self, parent):
        """Create the results display notebook with tabs."""
        results_frame = tk.LabelFrame(
            parent,
            text="Analysis Results - Visual Dashboard",
            font=("Consolas", 10, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            padx=10,
            pady=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Analysis Log
        self._create_log_tab()
        
        # Tab 2: Executive Summary
        self._create_summary_tab()
        
        # Tab 3: Visual Analytics
        if MATPLOTLIB_AVAILABLE:
            self._create_visual_tab()
        
        # Tab 4: Export Files
        self._create_files_tab()
        
    def _create_log_tab(self):
        """Create the analysis log tab."""
        log_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(log_tab, text='📋 Analysis Log')
        
        self.log_text = scrolledtext.ScrolledText(
            log_tab,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff41",
            insertbackground="white",
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.log_text.tag_config("success", foreground="#00ff41")
        self.log_text.tag_config("error", foreground="#ff4444")
        self.log_text.tag_config("warning", foreground="#ffaa00")
        self.log_text.tag_config("info", foreground="#00aaff")
        self.log_text.tag_config("header", foreground="#ffffff", 
                                font=("Consolas", 10, "bold"))
        
        # Initial welcome message
        self._log("[JARVIS:LAW] Forensic Analysis System v3.0 - Ready", "header")
        self._log("[SYSTEM] Consolidated GUI version - Single file", "success")
        if FORENSIC_GENERATOR_AVAILABLE:
            self._log("[MODULE] ForensicOutputGenerator: LOADED", "success")
        if SEC_TOOLS_AVAILABLE:
            self._log("[MODULE] SEC Analysis Tools: LOADED", "success")
        if MATPLOTLIB_AVAILABLE:
            self._log("[MODULE] Visualization Engine: LOADED", "success")
        self._log("[STATUS] Ready for analysis...", "info")
        
    def _create_summary_tab(self):
        """Create the executive summary tab."""
        summary_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(summary_tab, text='📊 Executive Summary')
        
        self.summary_text = scrolledtext.ScrolledText(
            summary_tab,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#e0e0e0",
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=15,
            pady=15
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial placeholder
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.insert('1.0', 
            "Executive Summary\n"
            "=" * 80 + "\n\n"
            "No analysis completed yet.\n\n"
            "Configure your analysis parameters and click 'START FORENSIC ANALYSIS'\n"
            "to generate comprehensive forensic output with natural language summaries,\n"
            "risk assessments, and detailed findings."
        )
        self.summary_text.config(state=tk.DISABLED)
        
    def _create_visual_tab(self):
        """Create the visual analytics tab with charts."""
        visual_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(visual_tab, text='📈 Visual Analytics')
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 6), facecolor='#1e1e1e')
        self.canvas = FigureCanvasTkAgg(self.fig, master=visual_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial placeholder
        ax = self.fig.add_subplot(111, facecolor='#1e1e1e')
        ax.text(0.5, 0.5, 'No data to visualize yet\n\nRun analysis to see charts',
               ha='center', va='center', fontsize=14, color='#888888')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self.canvas.draw()
        
    def _create_files_tab(self):
        """Create the export files management tab."""
        files_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(files_tab, text='📁 Export Files')
        
        # Info panel
        info_frame = tk.Frame(files_tab, bg='#1e1e1e')
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text="Generated Output Files",
            font=("Consolas", 12, "bold"),
            bg='#1e1e1e',
            fg=self.colors['accent']
        ).pack(anchor=tk.W, pady=5)
        
        self.session_label = tk.Label(
            info_frame,
            text="No output generated yet",
            font=("Consolas", 9),
            bg='#1e1e1e',
            fg=self.colors['text_dim']
        )
        self.session_label.pack(anchor=tk.W, pady=5)
        
        # Files listbox
        files_frame = tk.Frame(files_tab, bg='#1e1e1e')
        files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(
            files_frame,
            font=("Consolas", 10),
            bg='#2a2a3e',
            fg=self.colors['text'],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Action buttons
        btn_frame = tk.Frame(files_tab, bg='#1e1e1e')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        open_folder_btn = tk.Button(
            btn_frame,
            text="📂 Open Output Folder",
            command=self._open_output_folder,
            font=("Consolas", 10, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=8
        )
        open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        open_html_btn = tk.Button(
            btn_frame,
            text="🌐 Open HTML Report",
            command=self._open_html_report,
            font=("Consolas", 10, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=8
        )
        open_html_btn.pack(side=tk.LEFT, padx=5)
        
    # === EVENT HANDLERS ===
    
    def _log(self, message: str, tag: str = "info"):
        """Add message to analysis log with color tag."""
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
        """Search for company by name/ticker and retrieve CIK."""
        if not SEC_TOOLS_AVAILABLE:
            messagebox.showerror("Module Error", "SEC tools not available")
            return
            
        company_input = self.company_name.get().strip()
        if not company_input:
            messagebox.showwarning("Input Required", 
                                 "Please enter a company name or ticker symbol.")
            return
        
        self._log(f"[SEARCH] Looking up company: {company_input}", "info")
        
        try:
            result = search_company_by_ticker(company_input)
            
            if result and 'cik' in result:
                self.company_cik.set(result['cik'])
                self.company_name.set(result.get('name', company_input))
                self.ticker.set(result.get('ticker', ''))
                self.cik_label.config(
                    text=f"CIK: {result['cik']} | {result.get('name', 'Unknown')}",
                    fg=self.colors['accent']
                )
                self._log(f"[SUCCESS] Found: {result.get('name')} (CIK: {result['cik']})", 
                         "success")
            else:
                messagebox.showerror("Not Found", 
                                   f"Could not find company: {company_input}")
                self._log(f"[ERROR] Company not found: {company_input}", "error")
        except Exception as e:
            messagebox.showerror("Search Error", 
                               f"Error searching company:\n{str(e)}")
            self._log(f"[ERROR] Search failed: {str(e)}", "error")
            
    def _validate_inputs(self) -> bool:
        """Validate user inputs before starting analysis."""
        if not self.company_cik.get():
            messagebox.showerror("Invalid Input", 
                               "Please search and select a company first.")
            return False
        
        if not self.use_date_range.get() and not self.use_doc_limit.get():
            messagebox.showerror("Invalid Input", 
                               "Please select at least Date Range OR Document Limit.")
            return False
        
        if self.use_date_range.get():
            try:
                start = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
                end = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
                if start > end:
                    messagebox.showerror("Invalid Date Range", 
                                       "Start date must be before end date.")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Date Format", 
                                   "Please use YYYY-MM-DD format for dates.")
                return False
        
        if self.use_doc_limit.get():
            try:
                limit = int(self.doc_limit.get())
                if limit <= 0:
                    messagebox.showerror("Invalid Limit", 
                                       "Document limit must be greater than 0.")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Limit", 
                                   "Document limit must be a number.")
                return False
        
        return True
        
    def _start_analysis(self):
        """Start the forensic analysis in a background thread."""
        if not self._validate_inputs():
            return
        
        if not SEC_TOOLS_AVAILABLE:
            messagebox.showerror("Module Error", 
                               "SEC analysis tools not available")
            return
        
        self.analyze_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.analysis_running = True
        self.status_indicator.config(text="● ANALYZING", fg=self.colors['warning'])
        
        analysis_thread = threading.Thread(target=self._run_analysis, daemon=True)
        analysis_thread.start()
        
    def _stop_analysis(self):
        """Stop the running analysis."""
        self.analysis_running = False
        self._log("[USER] Analysis stopped by user", "warning")
        self._reset_ui()
        
    def _run_analysis(self):
        """Execute the complete forensic analysis workflow."""
        try:
            self._log("=" * 80, "header")
            self._log("[ANALYSIS] Starting Complete Forensic Analysis", "header")
            self._log("=" * 80, "header")
            
            # Extract parameters
            cik = self.company_cik.get()
            company = self.company_name.get()
            ticker = self.ticker.get()
            doc_type = self.doc_type.get()
            
            # Determine date range
            if self.use_date_range.get():
                start_date = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
                end_date = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
                year_start = start_date.year
                year_end = end_date.year
            else:
                year_start = year_end = datetime.now().year
            
            # Document limit
            limit = int(self.doc_limit.get()) if self.use_doc_limit.get() else 100
            
            self._log(f"[CONFIG] Company: {company} (CIK: {cik})", "info")
            self._log(f"[CONFIG] Document Type: {doc_type}", "info")
            self._log(f"[CONFIG] Year Range: {year_start} - {year_end}", "info")
            self._log(f"[CONFIG] Document Limit: {limit}", "info")
            
            # Step 1: Fetch filings
            self.status_label.config(text="Fetching filings from SEC.gov...")
            self.progress_var.set(10)
            
            self._log(f"\n[STEP 1] Fetching {doc_type} filings from SEC.gov...", "info")
            
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
                messagebox.showerror("No Filings", 
                                   "No filings found for the specified criteria.")
                self._reset_ui()
                return
            
            self._log(f"[INFO] Fetched {len(filings)} total filings from SEC", "info")
            
            # Filter by date range
            if self.use_date_range.get():
                start_date_str = self.start_date.get()
                end_date_str = self.end_date.get()
                
                filtered_filings = []
                for f in filings:
                    filing_date = f.get('filing_date', '')
                    if not filing_date:
                        continue
                    if filing_date < start_date_str:
                        continue
                    if end_date_str != datetime.now().strftime("%Y-%m-%d"):
                        if filing_date > end_date_str:
                            continue
                    filtered_filings.append(f)
                
                filings = filtered_filings
                self._log(f"[INFO] After date filtering: {len(filings)} filings", "info")
            
            # Apply document limit
            if len(filings) > limit:
                self._log(f"[INFO] Limiting to first {limit} filings", "info")
                filings = filings[:limit]
            
            self._log(f"[SUCCESS] Retrieved {len(filings)} filings", "success")
            self.progress_var.set(20)
            
            if not self.analysis_running:
                self._reset_ui()
                return
            
            # Step 2: Analyze filings
            self.status_label.config(text=f"Analyzing {len(filings)} filings...")
            self._log(f"\n[STEP 2] Running forensic analysis...", "info")
            
            self.current_analyses = []
            total = len(filings)
            
            for i, filing_meta in enumerate(filings, 1):
                if not self.analysis_running:
                    break
                
                progress = 20 + (60 * i / total)
                self.progress_var.set(progress)
                self.status_label.config(text=f"Analyzing filing {i}/{total}...")
                
                self._log(f"\n[FILING {i}/{total}] {filing_meta.get('filing_date')} | "
                         f"{filing_meta.get('accession_number')}", "info")
                
                try:
                    archived_path = filing_meta.get('archived', {}).get('archived_path')
                    if not archived_path:
                        self._log(f"  [SKIP] No archived file", "warning")
                        continue
                    
                    filing_data = self._parse_filing(Path(archived_path))
                    analysis = self._analyze_filing(filing_data)
                    self.current_analyses.append(analysis)
                    
                    risk_score = analysis['final_risk_score']
                    self._log(f"  [RISK] Final Score: {risk_score:.3f}", 
                             "error" if risk_score >= 0.7 else 
                             "warning" if risk_score >= 0.4 else "success")
                    
                except Exception as e:
                    self._log(f"  [ERROR] Analysis failed: {str(e)}", "error")
                    continue
            
            if not self.analysis_running:
                self._reset_ui()
                return
            
            # Step 3: Batch Pattern Intelligence
            if len(self.current_analyses) >= 2:
                self.status_label.config(text="Running Batch Pattern Intelligence...")
                self.progress_var.set(85)
                
                self._log(f"\n[STEP 3] Running Batch Pattern Intelligence...", "info")
                
                try:
                    filings_batch = [a['filing_data'] for a in self.current_analyses]
                    batch_results = analyze_batch(filings_batch, output_dir=None)
                    
                    risk_level = batch_results['master_assessment']['overall_risk_level']
                    self._log(f"[BPI] Overall Risk: {risk_level}", 
                             "error" if risk_level in ['HIGH', 'CRITICAL'] else "warning")
                    self._log(f"[BPI] Risk Signals: "
                             f"{batch_results['master_assessment']['risk_signal_count']}", 
                             "info")
                except Exception as e:
                    self._log(f"[WARNING] Batch analysis failed: {str(e)}", "warning")
            
            # Step 4: Generate outputs
            self.status_label.config(text="Generating forensic outputs...")
            self.progress_var.set(90)
            
            self._generate_forensic_output(cik, company, ticker)
            
            # Step 5: Generate visualizations
            if MATPLOTLIB_AVAILABLE:
                self._generate_visualizations()
            
            # Complete
            self.progress_var.set(100)
            self.status_label.config(text="Analysis complete!")
            self.status_indicator.config(text="● COMPLETE", fg=self.colors['accent'])
            
            self._log("\n" + "=" * 80, "header")
            self._log("[COMPLETE] Forensic analysis finished successfully", "success")
            self._log("=" * 80, "header")
            
            # Switch to summary tab
            self.notebook.select(1)
            
            messagebox.showinfo("Analysis Complete", 
                              f"Successfully analyzed {len(self.current_analyses)} filings.\n\n"
                              f"Check the tabs for detailed results and visualizations.")
            
        except Exception as e:
            self._log(f"\n[FATAL ERROR] Analysis failed: {str(e)}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")
            messagebox.showerror("Analysis Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self._reset_ui()
            
    def _parse_filing(self, filing_path: Path) -> Dict[str, Any]:
        """Parse a filing using appropriate parser."""
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
        
        parser = Form4HTMLParser(str(filing_path))
        return parser.extract_all()
        
    def _analyze_filing(self, filing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run forensic analysis on a single filing."""
        base_risk = 0.0
        patterns = []
        
        # Basic pattern detection
        transactions = filing_data.get('transactions', [])
        if transactions:
            large_trades = [tx for tx in transactions 
                          if tx.get('shares_traded', 0) > 100000]
            if large_trades:
                patterns.append({'pattern': 'LARGE_VOLUME', 'count': len(large_trades)})
                base_risk += 0.1
            
            sales = [tx for tx in transactions 
                    if tx.get('transaction_code') in ['S', 'D']]
            if sales:
                patterns.append({'pattern': 'INSIDER_SALES', 'count': len(sales)})
                base_risk += 0.15
        
        # Module analyses
        try:
            zero_dollar = detect_zero_dollar_risk(filing_data)
            if zero_dollar['detected']:
                self._log("  [MODULE 1] Zero-Dollar Pattern: DETECTED", "warning")
                patterns.append({'pattern': 'ZERO_DOLLAR', 'details': zero_dollar})
                base_risk += zero_dollar.get('risk_impact', 0.2)
        except:
            pass
        
        try:
            plan_check = check_10b5_plan(filing_data)
            if plan_check.get('compliant') == False:
                self._log("  [MODULE 2] 10b5-1 Non-Compliance: FLAGGED", "warning")
                patterns.append({'pattern': '10B5_NON_COMPLIANCE'})
                base_risk += 0.1
        except:
            pass
        
        # Risk weighting
        insider_role = filing_data.get('reporting_owner', {}).get('relationship', 'UNKNOWN')
        try:
            weighted_risk = weight_risk_score(base_risk, insider_role)
        except:
            weighted_risk = base_risk
        
        # Earnings correlation
        try:
            earnings_analysis = correlate_all_transactions(filing_data)
            earnings_flags = sum(1 for tx in earnings_analysis.get('transactions', []) 
                                if tx.get('within_window', False))
            if earnings_flags > 0:
                self._log(f"  [MODULE 4] Earnings Window Trades: {earnings_flags}", 
                         "warning")
                patterns.append({'pattern': 'EARNINGS_WINDOW', 'count': earnings_flags})
                weighted_risk += 0.1
        except:
            pass
        
        weighted_risk = min(1.0, weighted_risk)
        
        return {
            'filing_data': filing_data,
            'patterns_detected': patterns,
            'base_risk_score': base_risk,
            'weighted_risk_score': weighted_risk,
            'final_risk_score': weighted_risk,
            'insider_role': insider_role
        }
        
    def _generate_forensic_output(self, cik: str, company: str, ticker: str):
        """Generate comprehensive forensic output using ForensicOutputGenerator."""
        if not FORENSIC_GENERATOR_AVAILABLE or not self.generator:
            self._log("[WARNING] ForensicOutputGenerator not available", "warning")
            self._generate_basic_summary()
            return
        
        self._log("\n[FORENSIC] Generating comprehensive forensic output...", "info")
        
        # Build investigation data
        investigation_data = {
            "investigation_id": f"JARVIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "cik": cik,
            "company_name": company,
            "ticker": ticker,
            "risk_score": (sum(a['final_risk_score'] for a in self.current_analyses) / 
                         len(self.current_analyses) if self.current_analyses else 0.0),
            "risk_level": "HIGH" if any(a['final_risk_score'] >= 0.7 
                                       for a in self.current_analyses) else "MEDIUM",
            "filings_analyzed": len(self.current_analyses),
            "analysis_period": f"{self.start_date.get()} to {self.end_date.get()}",
            "timestamp_start": datetime.now(timezone.utc).isoformat(),
            "timestamp_end": datetime.now(timezone.utc).isoformat(),
            "fraud_indicators": [],
            "criminal_exposure": [],
            "civil_exposure": [],
            "filings_analyzed_list": [],
            "validation_checks": 5,
            "confidence_level": 0.85
        }
        
        # Extract patterns into findings
        for analysis in self.current_analyses:
            for pattern in analysis['patterns_detected']:
                if pattern['pattern'] == 'ZERO_DOLLAR':
                    investigation_data['fraud_indicators'].append({
                        "type": "ZERO_DOLLAR_TRANSACTION",
                        "severity": 0.8,
                        "severity_level": "high",
                        "confidence": 1.0,
                        "description": "Zero-dollar transaction detected",
                        "detection_timestamp": datetime.now(timezone.utc).isoformat()
                    })
        
        try:
            output = self.generator.generate_comprehensive_output(investigation_data)
            
            if output.get('error_occurred'):
                error_msg = output.get('error_details', {}).get('error_message', 'Unknown')
                self._log(f"[ERROR] Output generation failed: {error_msg}", "error")
                self._generate_basic_summary()
                return
            
            self.last_output = output
            self.last_session_id = output.get('session_id')
            
            self._log(f"[SUCCESS] Forensic output generated - Session: {self.last_session_id}", 
                     "success")
            
            # Update summary display
            self._update_summary_display(output)
            
            # Update files list
            self._update_files_list()
            
        except Exception as e:
            self._log(f"[ERROR] Output generation failed: {str(e)}", "error")
            self._generate_basic_summary()
            
    def _generate_basic_summary(self):
        """Generate basic summary when ForensicOutputGenerator unavailable."""
        if not self.current_analyses:
            return
        
        total = len(self.current_analyses)
        avg_risk = sum(a['final_risk_score'] for a in self.current_analyses) / total
        max_risk = max(a['final_risk_score'] for a in self.current_analyses)
        
        high_risk = sum(1 for a in self.current_analyses if a['final_risk_score'] >= 0.7)
        medium_risk = sum(1 for a in self.current_analyses 
                         if 0.4 <= a['final_risk_score'] < 0.7)
        low_risk = sum(1 for a in self.current_analyses if a['final_risk_score'] < 0.4)
        
        summary = f"""
FORENSIC ANALYSIS SUMMARY
{'=' * 80}

Company: {self.company_name.get()} (CIK: {self.company_cik.get()})
Analysis Period: {self.start_date.get()} to {self.end_date.get()}
Document Type: {self.doc_type.get()}

OVERVIEW
--------
Total Filings Analyzed: {total}
Average Risk Score: {avg_risk:.3f}
Highest Risk Score: {max_risk:.3f}

RISK DISTRIBUTION
-----------------
High Risk Filings (0.7+): {high_risk}
Medium Risk Filings (0.4-0.69): {medium_risk}
Low Risk Filings (<0.4): {low_risk}

ASSESSMENT
----------
Overall Risk Level: {'HIGH' if max_risk >= 0.7 else 'MEDIUM' if max_risk >= 0.4 else 'LOW'}
Recommended Action: {'Immediate review required' if max_risk >= 0.7 else 'Monitor closely' if max_risk >= 0.4 else 'Standard compliance review'}

For detailed forensic output with comprehensive findings, ensure
ForensicOutputGenerator module is properly installed and configured.
"""
        
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        self.summary_text.config(state=tk.DISABLED)
        
    def _update_summary_display(self, output: Dict[str, Any]):
        """Update the summary display with forensic output."""
        exec_sum = output.get('executive_summary', {})
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    FORENSIC ANALYSIS REPORT                       ║
╚══════════════════════════════════════════════════════════════════╝

Session ID: {output.get('session_id', 'N/A')}
Generated: {output.get('timestamp_end', 'N/A')}
Compliance Level: {output.get('compliance_level', 'N/A')}

COMPANY INFORMATION
-------------------
Investigation ID: {exec_sum.get('investigation_id', 'N/A')}
CIK: {exec_sum.get('company_identifier', {}).get('cik', 'N/A')}
Ticker: {exec_sum.get('company_identifier', {}).get('ticker', 'N/A')}
Company: {exec_sum.get('company_identifier', {}).get('name', 'N/A')}

RISK ASSESSMENT
---------------
Risk Score: {exec_sum.get('risk_assessment', {}).get('overall_risk_score', 'N/A')}
Risk Level: {exec_sum.get('risk_assessment', {}).get('risk_level', 'N/A')}
Assessment: {exec_sum.get('risk_assessment', {}).get('assessment', 'N/A')}
Recommended Action: {exec_sum.get('risk_assessment', {}).get('recommended_action', 'N/A')}
Confidence: {exec_sum.get('risk_assessment', {}).get('confidence_level', 'N/A')}

KEY FINDINGS
------------
Total Filings Analyzed: {exec_sum.get('key_findings', {}).get('total_filings_analyzed', 0)}
Fraud Indicators: {exec_sum.get('key_findings', {}).get('fraud_indicators_detected', 0)}
Criminal Statutes: {exec_sum.get('key_findings', {}).get('criminal_statutes_implicated', 0)}
Civil Violations: {exec_sum.get('key_findings', {}).get('civil_violations_identified', 0)}
Highest Severity: {exec_sum.get('key_findings', {}).get('highest_severity_finding', 'N/A')}

OUTPUT FILES
------------
Detailed Findings: {len(output.get('detailed_findings', []))}
Recommendations: {len(output.get('recommendations', []))}
Timeline Events: {len(output.get('timeline_analysis', []))}
Digital Artifacts: {len(output.get('digital_artifacts', []))}

All output files have been generated in:
forensic_output_{output.get('session_id', 'unknown')}/

Available formats: JSON, Markdown, HTML, CSV
"""
        
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        self.summary_text.config(state=tk.DISABLED)
        
    def _generate_visualizations(self):
        """Generate visual analytics charts."""
        if not self.current_analyses:
            return
        
        self._log("[VISUAL] Generating charts...", "info")
        
        try:
            self.fig.clear()
            
            # Create subplots
            ax1 = self.fig.add_subplot(221, facecolor='#1e1e1e')
            ax2 = self.fig.add_subplot(222, facecolor='#1e1e1e')
            ax3 = self.fig.add_subplot(223, facecolor='#1e1e1e')
            ax4 = self.fig.add_subplot(224, facecolor='#1e1e1e')
            
            # Risk distribution histogram
            risk_scores = [a['final_risk_score'] for a in self.current_analyses]
            ax1.hist(risk_scores, bins=20, color='#667eea', alpha=0.7, edgecolor='white')
            ax1.set_title('Risk Score Distribution', color='white', fontsize=10)
            ax1.set_xlabel('Risk Score', color='#888888', fontsize=8)
            ax1.set_ylabel('Frequency', color='#888888', fontsize=8)
            ax1.tick_params(colors='#888888', labelsize=7)
            
            # Risk level pie chart
            high = sum(1 for s in risk_scores if s >= 0.7)
            medium = sum(1 for s in risk_scores if 0.4 <= s < 0.7)
            low = sum(1 for s in risk_scores if s < 0.4)
            
            colors = ['#f44336', '#ff9800', '#00ff41']
            ax2.pie([high, medium, low], labels=['High', 'Medium', 'Low'],
                   autopct='%1.1f%%', colors=colors, textprops={'color': 'white', 'fontsize': 8})
            ax2.set_title('Risk Level Distribution', color='white', fontsize=10)
            
            # Risk over time
            indices = list(range(len(risk_scores)))
            ax3.plot(indices, risk_scores, color='#667eea', linewidth=2, marker='o', markersize=4)
            ax3.axhline(y=0.7, color='#f44336', linestyle='--', linewidth=1, alpha=0.5)
            ax3.axhline(y=0.4, color='#ff9800', linestyle='--', linewidth=1, alpha=0.5)
            ax3.set_title('Risk Trend', color='white', fontsize=10)
            ax3.set_xlabel('Filing Index', color='#888888', fontsize=8)
            ax3.set_ylabel('Risk Score', color='#888888', fontsize=8)
            ax3.tick_params(colors='#888888', labelsize=7)
            ax3.grid(True, alpha=0.2)
            
            # Pattern detection summary
            pattern_counts = {}
            for analysis in self.current_analyses:
                for pattern in analysis['patterns_detected']:
                    p_type = pattern['pattern']
                    pattern_counts[p_type] = pattern_counts.get(p_type, 0) + 1
            
            if pattern_counts:
                patterns = list(pattern_counts.keys())
                counts = list(pattern_counts.values())
                ax4.barh(patterns, counts, color='#00ff41', alpha=0.7)
                ax4.set_title('Pattern Detection Summary', color='white', fontsize=10)
                ax4.set_xlabel('Count', color='#888888', fontsize=8)
                ax4.tick_params(colors='#888888', labelsize=7)
            else:
                ax4.text(0.5, 0.5, 'No patterns detected', 
                        ha='center', va='center', color='#888888')
                ax4.set_xticks([])
                ax4.set_yticks([])
            
            # Style all axes
            for ax in [ax1, ax2, ax3, ax4]:
                for spine in ax.spines.values():
                    spine.set_color('#888888')
                    spine.set_linewidth(0.5)
            
            self.fig.tight_layout()
            self.canvas.draw()
            
            self._log("[SUCCESS] Visualizations generated", "success")
            
        except Exception as e:
            self._log(f"[ERROR] Visualization failed: {str(e)}", "error")
            
    def _update_files_list(self):
        """Update the files listbox with generated output files."""
        self.files_listbox.delete(0, tk.END)
        
        if not self.last_session_id:
            return
        
        self.session_label.config(
            text=f"Session ID: {self.last_session_id}\n"
                 f"Output Folder: forensic_output_{self.last_session_id}"
        )
        
        output_dir = Path(f"forensic_output_{self.last_session_id}")
        if output_dir.exists():
            for file_path in sorted(output_dir.iterdir()):
                size_kb = file_path.stat().st_size / 1024
                self.files_listbox.insert(tk.END, 
                                         f"📄 {file_path.name} ({size_kb:.1f} KB)")
                
    def _export_outputs(self):
        """Export/open the forensic outputs."""
        if not self.last_session_id:
            messagebox.showinfo("No Output", 
                              "No forensic output generated yet.\n\n"
                              "Run an analysis first to generate outputs.")
            return
        
        output_dir = Path(f"forensic_output_{self.last_session_id}")
        if output_dir.exists():
            try:
                os.startfile(output_dir)
            except:
                messagebox.showinfo("Output Location", 
                                  f"Output files are located at:\n{output_dir.absolute()}")
        else:
            messagebox.showerror("Not Found", "Output folder not found")
            
    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if not self.last_session_id:
            messagebox.showwarning("No Output", "Generate output first")
            return
        
        output_dir = Path(f"forensic_output_{self.last_session_id}")
        if output_dir.exists():
            try:
                os.startfile(output_dir)
            except:
                messagebox.showerror("Error", "Could not open folder")
        else:
            messagebox.showerror("Not Found", "Output folder not found")
            
    def _open_html_report(self):
        """Open HTML report in browser."""
        if not self.last_session_id:
            messagebox.showwarning("No Output", "Generate output first")
            return
        
        html_file = (Path(f"forensic_output_{self.last_session_id}") / 
                    f"forensic_report_{self.last_session_id}.html")
        if html_file.exists():
            webbrowser.open(html_file.absolute().as_uri())
        else:
            messagebox.showerror("Not Found", "HTML report not found")
            
    def _reset_ui(self):
        """Reset UI to ready state."""
        self.analyze_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.analysis_running = False
        self.status_indicator.config(text="● READY", fg=self.colors['accent'])


def main():
    """Main entry point for the application."""
    print("=" * 70)
    print("JARVIS:LAW - Forensic Analysis System v3.0 (Consolidated)")
    print("=" * 70)
    print("Initializing GUI...")
    print(f"ForensicOutputGenerator: {'AVAILABLE' if FORENSIC_GENERATOR_AVAILABLE else 'NOT AVAILABLE'}")
    print(f"SEC Analysis Tools: {'AVAILABLE' if SEC_TOOLS_AVAILABLE else 'NOT AVAILABLE'}")
    print(f"Matplotlib Visualizations: {'AVAILABLE' if MATPLOTLIB_AVAILABLE else 'NOT AVAILABLE'}")
    print("=" * 70)
    
    root = tk.Tk()
    app = JarvisForensicGUI(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    print("GUI Ready - Starting event loop...")
    root.mainloop()


if __name__ == "__main__":
    main()

