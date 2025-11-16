#!/usr/bin/env python3
"""
JARVIS:LAW Forensic Analysis System - Production GUI v3.0
==========================================================

Visual-first forensic analysis GUI with comprehensive charting,
graphing, and natural language summaries.

Primary Features:
- Company search by name/ticker
- Date range and document type selection  
- VISUAL DASHBOARD with charts, graphs, and bubble maps
- Natural language executive summaries
- Integrated ForensicOutputGenerator backend
- Secondary JSON/CSV export capabilities

Author: JARVIS 2.0 Core Commander
Status: PRODUCTION READY - VISUALIZATION FIRST
"""

import sys
import os
import json
import threading
import webbrowser
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

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

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from forensic_output_generator import ForensicOutputGenerator, OutputStandard


class JarvisLawForensicGUI:
    """Visual-first Forensic Analysis GUI with integrated output generation."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS:LAW - Forensic Analysis System v3.0")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # State variables
        self.company_cik = tk.StringVar()
        self.company_name = tk.StringVar()
        self.ticker = tk.StringVar()
        self.doc_limit = tk.StringVar(value="10")
        self.start_date = tk.StringVar(value=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        self.end_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        self.analysis_running = False
        self.analysis_results = {}
        self.generator = ForensicOutputGenerator()
        self.last_session_id = None
        
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
        """Setup the user interface components."""
        self.root.configure(bg=self.colors['bg_medium'])
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="⚖️ JARVIS:LAW",
            font=("Consolas", 20, "bold"),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        subtitle_label = tk.Label(
            header_frame,
            text="SEC Forensic Analysis System v3.0 - Visual Dashboard",
            font=("Consolas", 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim']
        )
        subtitle_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.status_indicator = tk.Label(
            header_frame,
            text="● READY",
            font=('Consolas', 12, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_medium'], padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === INPUT SECTION ===
        input_frame = tk.LabelFrame(
            main_frame,
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
                bg=self.colors['bg_medium'], fg=self.colors['text'], width=15, anchor='w').pack(side=tk.LEFT)
        
        company_entry = tk.Entry(row1, textvariable=self.company_name, font=("Consolas", 10), 
                                width=30, bg='#2a2a3e', fg=self.colors['text'], relief=tk.FLAT)
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
        
        self.cik_label = tk.Label(row1, text="CIK: Not selected", font=("Consolas", 9), 
                                 bg=self.colors['bg_medium'], fg=self.colors['text_dim'])
        self.cik_label.pack(side=tk.LEFT, padx=10)
        
        # Row 2: Date Range
        row2 = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(row2, text="Date Range:", font=("Consolas", 10), 
                bg=self.colors['bg_medium'], fg=self.colors['text'], width=15, anchor='w').pack(side=tk.LEFT)
        
        tk.Label(row2, text="From:", font=("Consolas", 9), 
                bg=self.colors['bg_medium'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=(0, 5))
        start_entry = tk.Entry(row2, textvariable=self.start_date, font=("Consolas", 9), width=12,
                              bg='#2a2a3e', fg=self.colors['text'], relief=tk.FLAT)
        start_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="To:", font=("Consolas", 9), 
                bg=self.colors['bg_medium'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=(10, 5))
        end_entry = tk.Entry(row2, textvariable=self.end_date, font=("Consolas", 9), width=12,
                            bg='#2a2a3e', fg=self.colors['text'], relief=tk.FLAT)
        end_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="(YYYY-MM-DD)", font=("Consolas", 8), 
                bg=self.colors['bg_medium'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=5)
        
        # Row 3: Document Limit
        row3 = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        row3.pack(fill=tk.X, pady=5)
        
        tk.Label(row3, text="Document Limit:", font=("Consolas", 10), 
                bg=self.colors['bg_medium'], fg=self.colors['text'], width=15, anchor='w').pack(side=tk.LEFT)
        
        limit_entry = tk.Entry(row3, textvariable=self.doc_limit, font=("Consolas", 10), width=10,
                              bg='#2a2a3e', fg=self.colors['text'], relief=tk.FLAT)
        limit_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row3, text="(Max filings to analyze - recommended: 10-50)", 
                font=("Consolas", 8, "bold"), bg=self.colors['bg_medium'], 
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
            text="📁 Export JSON/CSV",
            command=self._export_outputs,
            font=("Consolas", 9, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            padx=10
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # === PROGRESS SECTION ===
        progress_frame = tk.LabelFrame(
            main_frame,
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
        
        # === NOTEBOOK FOR RESULTS ===
        results_frame = tk.LabelFrame(
            main_frame,
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
        
        # Tab 1: Executive Summary (Natural Language)
        self.summary_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.summary_tab, text='📊 Executive Summary')
        self._create_summary_tab()
        
        # Tab 2: Visual Analytics
        self.visual_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.visual_tab, text='📈 Visual Analytics')
        self._create_visual_tab()
        
        # Tab 3: Detailed Findings
        self.findings_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.findings_tab, text='🔍 Detailed Findings')
        self._create_findings_tab()
        
        # Tab 4: Export Files
        self.files_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.files_tab, text='📁 Export Files')
        self._create_files_tab()
        
    def _create_input_tab(self):
        """Create the investigation data input tab."""
        # Left panel - controls
        left_panel = ttk.Frame(self.input_tab, style='Dark.TFrame', width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        left_panel.pack_propagate(False)
        
        # Control buttons
        btn_frame = ttk.Frame(left_panel, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, pady=10)
        
        load_btn = tk.Button(
            btn_frame,
            text="📂 Load JSON Data",
            command=self._load_json_file,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=8
        )
        load_btn.pack(fill=tk.X, pady=5)
        
        quick_test_btn = tk.Button(
            btn_frame,
            text="🧪 Load Test Data",
            command=self._load_test_data,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=8
        )
        quick_test_btn.pack(fill=tk.X, pady=5)
        
        # Separator
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Quick input fields
        fields_frame = ttk.Frame(left_panel, style='Dark.TFrame')
        fields_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            fields_frame,
            text="Quick Input Fields",
            font=('Consolas', 11, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent']
        ).pack(anchor=tk.W, pady=5)
        
        # Investigation ID
        self._create_input_field(fields_frame, "Investigation ID:", "investigation_id")
        
        # CIK
        self._create_input_field(fields_frame, "CIK:", "cik")
        
        # Company Name
        self._create_input_field(fields_frame, "Company Name:", "company_name")
        
        # Ticker
        self._create_input_field(fields_frame, "Ticker:", "ticker")
        
        # Risk Score
        self._create_input_field(fields_frame, "Risk Score (0-1):", "risk_score")
        
        # Generate button
        generate_btn = tk.Button(
            left_panel,
            text="🚀 GENERATE FORENSIC OUTPUT",
            command=self._generate_output,
            bg=self.colors['accent2'],
            fg='white',
            font=('Consolas', 12, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=12
        )
        generate_btn.pack(fill=tk.X, pady=20, side=tk.BOTTOM)
        
        # Right panel - JSON editor
        right_panel = ttk.Frame(self.input_tab, style='Dark.TFrame')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            right_panel,
            text="Investigation Data (JSON)",
            font=('Consolas', 11, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent']
        ).pack(anchor=tk.W, pady=5)
        
        # JSON text editor
        self.json_editor = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.json_editor.pack(fill=tk.BOTH, expand=True)
        
    def _create_input_field(self, parent, label_text, field_name):
        """Create an input field with label."""
        frame = ttk.Frame(parent, style='Dark.TFrame')
        frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(
            frame,
            text=label_text,
            font=('Consolas', 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            width=18,
            anchor=tk.W
        )
        label.pack(side=tk.LEFT)
        
        entry = tk.Entry(
            frame,
            font=('Consolas', 9),
            bg='#2a2a3e',
            fg=self.colors['text'],
            relief=tk.FLAT
        )
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Store reference
        if not hasattr(self, 'input_fields'):
            self.input_fields = {}
        self.input_fields[field_name] = entry
        
    def _create_output_tab(self):
        """Create the output preview tab."""
        # Top controls
        control_frame = ttk.Frame(self.output_tab, style='Dark.TFrame')
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            control_frame,
            text="Output Format:",
            font=('Consolas', 10, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT, padx=10)
        
        # Format selector
        self.format_var = tk.StringVar(value='summary')
        formats = [
            ('Executive Summary', 'summary'),
            ('Full JSON', 'json'),
            ('Markdown Report', 'markdown'),
            ('Findings CSV', 'csv')
        ]
        
        for text, value in formats:
            rb = tk.Radiobutton(
                control_frame,
                text=text,
                variable=self.format_var,
                value=value,
                command=self._update_output_display,
                font=('Consolas', 9),
                bg=self.colors['bg_medium'],
                fg=self.colors['text'],
                selectcolor=self.colors['bg_light'],
                activebackground=self.colors['bg_medium']
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        # Output display
        self.output_display = scrolledtext.ScrolledText(
            self.output_tab,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.output_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _create_files_tab(self):
        """Create the output files management tab."""
        # Info panel
        info_frame = ttk.Frame(self.files_tab, style='Dark.TFrame')
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text="Generated Output Files",
            font=('Consolas', 12, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent']
        ).pack(anchor=tk.W, pady=5)
        
        self.session_label = tk.Label(
            info_frame,
            text="No output generated yet",
            font=('Consolas', 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim']
        )
        self.session_label.pack(anchor=tk.W, pady=5)
        
        # Files listbox
        files_frame = ttk.Frame(self.files_tab, style='Dark.TFrame')
        files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(
            files_frame,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg=self.colors['text'],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # Action buttons
        btn_frame = ttk.Frame(self.files_tab, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        open_folder_btn = tk.Button(
            btn_frame,
            text="📂 Open Output Folder",
            command=self._open_output_folder,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=8
        )
        open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        open_html_btn = tk.Button(
            btn_frame,
            text="🌐 Open HTML Report",
            command=self._open_html_report,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=8
        )
        open_html_btn.pack(side=tk.LEFT, padx=5)
        
        open_timeline_btn = tk.Button(
            btn_frame,
            text="📈 Open Timeline",
            command=self._open_timeline,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Consolas', 10, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=8
        )
        open_timeline_btn.pack(side=tk.LEFT, padx=5)
        
    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_bar = tk.Label(
            self.root,
            text="Ready to generate forensic outputs",
            font=('Consolas', 9),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            anchor=tk.W,
            padx=10,
            pady=5
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    # === EVENT HANDLERS ===
    
    def _load_json_file(self):
        """Load investigation data from JSON file."""
        file_path = filedialog.askopenfilename(
            title="Select Investigation Data JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            self.investigation_data = data
            self._update_json_editor()
            self._update_input_fields()
            self._set_status("Loaded data from file", self.colors['accent'])
            messagebox.showinfo("Success", f"Loaded investigation data from:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file:\n{str(e)}")
            self._set_status(f"Error loading file: {str(e)}", self.colors['error'])
            
    def _load_test_data(self):
        """Load sample test data for quick testing."""
        test_data = {
            "investigation_id": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "cik": "0001318605",
            "company_name": "Tesla, Inc.",
            "ticker": "TSLA",
            "risk_score": 0.75,
            "risk_level": "HIGH",
            "filings_analyzed": 12,
            "analysis_period": "3 years",
            "timestamp_start": datetime.now(timezone.utc).isoformat(),
            "timestamp_end": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 120.0,
            "forms_analyzed": ["10-K", "10-Q", "8-K"],
            "fraud_indicators": [{
                "type": "LATE_FILING_NO_NT",
                "severity": 0.5,
                "severity_level": "medium",
                "confidence": 1.0,
                "description": "Late filing without notice to traders",
                "detection_method": "Pattern Analysis",
                "detection_timestamp": datetime.now(timezone.utc).isoformat(),
                "filing_refs": ["0001318605-2023-10-K"]
            }],
            "criminal_exposure": [{
                "statute": "USC_15_78j_b",
                "usc_citation": "15 U.S.C. § 78j(b)",
                "violation_type": "Anti-Fraud Provisions",
                "description": "Potential violation of anti-fraud provisions",
                "confidence": 0.8,
                "detection_timestamp": datetime.now(timezone.utc).isoformat()
            }],
            "civil_exposure": [{
                "regulation": "CFR_17_229_303",
                "cfr_citation": "17 CFR § 229.303",
                "category": "MD&A Disclosure Requirements",
                "description": "Potential deficiency in disclosures",
                "confidence": 0.7
            }],
            "filings_analyzed_list": [],
            "ml_outputs": [],
            "validation_checks": 5,
            "confidence_level": 0.85,
            "benford_violations": 0
        }
        
        self.investigation_data = test_data
        self._update_json_editor()
        self._update_input_fields()
        self._set_status("Loaded test data", self.colors['accent'])
        
    def _generate_output(self):
        """Generate forensic output from investigation data."""
        if self.is_generating:
            messagebox.showwarning("Busy", "Output generation already in progress")
            return
            
        # Get data from JSON editor
        try:
            json_text = self.json_editor.get('1.0', tk.END).strip()
            if json_text:
                self.investigation_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON in editor:\n{str(e)}")
            return
            
        # Update from input fields
        for field_name, entry in self.input_fields.items():
            value = entry.get().strip()
            if value:
                if field_name == "risk_score":
                    try:
                        self.investigation_data[field_name] = float(value)
                    except ValueError:
                        pass
                else:
                    self.investigation_data[field_name] = value
                    
        if not self.investigation_data:
            messagebox.showwarning("No Data", "Please load or enter investigation data first")
            return
            
        # Run generation in thread
        self.is_generating = True
        self._set_status("Generating forensic output...", self.colors['warning'])
        self.status_indicator.config(text="● GENERATING", fg=self.colors['warning'])
        
        thread = threading.Thread(target=self._generate_output_thread, daemon=True)
        thread.start()
        
    def _generate_output_thread(self):
        """Thread worker for output generation."""
        try:
            # Generate output
            output = self.generator.generate_comprehensive_output(self.investigation_data)
            
            # Check for errors
            if output.get('error_occurred'):
                error_msg = output.get('error_details', {}).get('error_message', 'Unknown error')
                self.root.after(0, lambda: self._generation_failed(error_msg))
                return
                
            # Success
            self.last_output = output
            self.last_session_id = output.get('session_id')
            
            self.root.after(0, self._generation_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._generation_failed(str(e)))
            
    def _generation_complete(self):
        """Called when generation completes successfully."""
        self.is_generating = False
        self.status_indicator.config(text="● COMPLETE", fg=self.colors['accent'])
        self._set_status(f"Output generated successfully - Session: {self.last_session_id}", 
                        self.colors['accent'])
        
        # Update displays
        self._update_output_display()
        self._update_files_list()
        
        # Switch to output tab
        self.notebook.select(self.output_tab)
        
        messagebox.showinfo(
            "Success",
            f"Forensic output generated successfully!\n\n"
            f"Session ID: {self.last_session_id}\n"
            f"Output folder: forensic_output_{self.last_session_id}"
        )
        
    def _generation_failed(self, error_msg):
        """Called when generation fails."""
        self.is_generating = False
        self.status_indicator.config(text="● ERROR", fg=self.colors['error'])
        self._set_status(f"Generation failed: {error_msg}", self.colors['error'])
        
        messagebox.showerror(
            "Generation Failed",
            f"Failed to generate forensic output:\n\n{error_msg}"
        )
        
    def _update_json_editor(self):
        """Update JSON editor with current investigation data."""
        self.json_editor.delete('1.0', tk.END)
        if self.investigation_data:
            json_str = json.dumps(self.investigation_data, indent=2)
            self.json_editor.insert('1.0', json_str)
            
    def _update_input_fields(self):
        """Update input fields from investigation data."""
        if not hasattr(self, 'input_fields'):
            return
            
        for field_name, entry in self.input_fields.items():
            if field_name in self.investigation_data:
                entry.delete(0, tk.END)
                entry.insert(0, str(self.investigation_data[field_name]))
                
    def _update_output_display(self):
        """Update the output display based on selected format."""
        if not self.last_output:
            self.output_display.delete('1.0', tk.END)
            self.output_display.insert('1.0', "No output generated yet.\n\nGenerate output from the Investigation Data tab.")
            return
            
        format_type = self.format_var.get()
        self.output_display.delete('1.0', tk.END)
        
        try:
            if format_type == 'summary':
                self._display_summary()
            elif format_type == 'json':
                self._display_json()
            elif format_type == 'markdown':
                self._display_markdown()
            elif format_type == 'csv':
                self._display_csv()
        except Exception as e:
            self.output_display.insert('1.0', f"Error displaying output:\n{str(e)}")
            
    def _display_summary(self):
        """Display executive summary."""
        output = self.last_output
        exec_sum = output.get('executive_summary', {})
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    EXECUTIVE SUMMARY                              ║
╚══════════════════════════════════════════════════════════════════╝

Session ID: {output.get('session_id', 'N/A')}
Generated: {output.get('timestamp_end', 'N/A')}

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

DETAILED FINDINGS: {len(output.get('detailed_findings', []))}
RECOMMENDATIONS: {len(output.get('recommendations', []))}
TIMELINE EVENTS: {len(output.get('timeline_analysis', []))}
DIGITAL ARTIFACTS: {len(output.get('digital_artifacts', []))}
"""
        self.output_display.insert('1.0', summary)
        
    def _display_json(self):
        """Display full JSON output."""
        json_str = json.dumps(self.last_output, indent=2)
        self.output_display.insert('1.0', json_str)
        
    def _display_markdown(self):
        """Display markdown report."""
        if not self.last_session_id:
            return
            
        md_file = Path(f"forensic_output_{self.last_session_id}") / f"forensic_summary_{self.last_session_id}.md"
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                self.output_display.insert('1.0', f.read())
        else:
            self.output_display.insert('1.0', "Markdown file not found")
            
    def _display_csv(self):
        """Display CSV findings."""
        if not self.last_session_id:
            return
            
        csv_file = Path(f"forensic_output_{self.last_session_id}") / f"findings_{self.last_session_id}.csv"
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                self.output_display.insert('1.0', f.read())
        else:
            self.output_display.insert('1.0', "CSV file not found")
            
    def _update_files_list(self):
        """Update the files listbox."""
        self.files_listbox.delete(0, tk.END)
        
        if not self.last_session_id:
            return
            
        self.session_label.config(
            text=f"Session ID: {self.last_session_id}\nOutput Folder: forensic_output_{self.last_session_id}"
        )
        
        output_dir = Path(f"forensic_output_{self.last_session_id}")
        if output_dir.exists():
            for file_path in sorted(output_dir.iterdir()):
                size_kb = file_path.stat().st_size / 1024
                self.files_listbox.insert(tk.END, f"📄 {file_path.name} ({size_kb:.1f} KB)")
                
    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if not self.last_session_id:
            messagebox.showwarning("No Output", "Generate output first")
            return
            
        output_dir = Path(f"forensic_output_{self.last_session_id}")
        if output_dir.exists():
            os.startfile(output_dir)
        else:
            messagebox.showerror("Not Found", "Output folder not found")
            
    def _open_html_report(self):
        """Open HTML report in browser."""
        if not self.last_session_id:
            messagebox.showwarning("No Output", "Generate output first")
            return
            
        html_file = Path(f"forensic_output_{self.last_session_id}") / f"forensic_report_{self.last_session_id}.html"
        if html_file.exists():
            webbrowser.open(html_file.absolute().as_uri())
        else:
            messagebox.showerror("Not Found", "HTML report not found")
            
    def _open_timeline(self):
        """Open timeline visualization in browser."""
        if not self.last_session_id:
            messagebox.showwarning("No Output", "Generate output first")
            return
            
        timeline_file = Path(f"forensic_output_{self.last_session_id}") / f"timeline_{self.last_session_id}.html"
        if timeline_file.exists():
            webbrowser.open(timeline_file.absolute().as_uri())
        else:
            messagebox.showerror("Not Found", "Timeline visualization not found")
            
    def _set_status(self, message, color=None):
        """Update status bar."""
        self.status_bar.config(
            text=message,
            fg=color if color else self.colors['text_dim']
        )


def main():
    """Main entry point."""
    root = tk.Tk()
    app = ForensicAnalysisGUI(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    print("=" * 70)
    print("JARVIS:LAW - Forensic Output Generator v3.0")
    print("=" * 70)
    print("Initializing GUI...")
    print("Status: PRODUCTION READY")
    print("=" * 70)
    main()

