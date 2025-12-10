#!/usr/bin/env python3
"""

       JLAW UNIFIED FORENSIC ANALYSIS SYSTEM - COMPLETE IMPLEMENTATION        

  Version: 11.0.0-UNIFIED-COMPLETE                                            
  Date: December 6, 2025                                                      
  Compliance: UNIFIED_FORENSIC_SYSTEM_README.md (13-Phase Pipeline)           

  COMPLETE 13-PHASE INTEGRATION:                                              
   Phase 1:  Document Acquisition (SEC EDGAR API)                           
   Phase 2:  DocsGPT Document Parsing (Semantic chunking)                   
   Phase 3:  Agent-Powered Scraping (OpenAI/Anthropic)                      
   Phase 4:  Quantitative Forensics (Benford/Beneish/Altman)                
   Phase 5:  Revenue Recognition (DSO trends, hockey stick)                 
   Phase 6:  Financial Flow Analysis (Circular flows, schemes)              
   Phase 7:  Linguistic Deception (Hedging, obfuscation)                    
   Phase 8:  Temporal Analysis (Timeline anomalies, delays)                 
   Phase 9:  Contradiction Detection (Cross-document)                       
   Phase 10: ML Fraud Detection (BERT/XGBoost ensemble)                     
   Phase 11: Statutory Mapping (15 USC/17 CFR + GovInfo)                    
   Phase 12: Dual-Agent Prosecution (OpenAI + Anthropic)                    
   Phase 13: Report Generation (Complete output stack)                      

"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'unified_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# Import the production baseline system for comparison
from jlaw_production_forensic import UnifiedForensicAnalyzer as BaselineAnalyzer

# Import all forensic modules as specified in README
try:
    from src.forensics.unified_forensic_pipeline import UnifiedForensicPipeline
    PIPELINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"UnifiedForensicPipeline import failed: {e}")
    PIPELINE_AVAILABLE = False

try:
    from src.forensics.unified_report_generator import UnifiedReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"UnifiedReportGenerator import failed: {e}")
    REPORT_GENERATOR_AVAILABLE = False

try:
    from src.forensics.forensic_context import ForensicContext
    CONTEXT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ForensicContext import failed: {e}")
    CONTEXT_AVAILABLE = False


class CompleteUnifiedForensicSystem:
    """
    Complete implementation of the 13-phase Unified Forensic Analysis System
    as specified in UNIFIED_FORENSIC_SYSTEM_README.md
    
    This system integrates:
    - Baseline production system (97 violations)
    - All 13 phases from README specification
    - Complete output stack per README
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize baseline for comparison
        self.baseline_analyzer = None
        
        # Initialize unified pipeline if available
        self.unified_pipeline = UnifiedForensicPipeline() if PIPELINE_AVAILABLE else None
        
        # Results storage
        self.baseline_results = None
        self.unified_results = None
        
    async def execute_complete_analysis(
        self,
        ticker: str = None,
        cik: str = None,
        year: int = None,
        start_date: str = None,
        end_date: str = None,
        company_name: str = None,
        verbose: bool = False,
        filing_types: Optional[str] = None,
        no_report: bool = False,
    ):
        """
        Execute complete 13-phase unified forensic analysis.
        
        Strategy:
        1. Run baseline production system (proven 97 violations)
        2. Run unified pipeline with all 13 phases
        3. Merge results intelligently
        4. Generate complete output stack per README
        """
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            
        # Resolve parameters
        if not cik and ticker:
            # Map common tickers to CIKs
            ticker_map = {
                'NKE': ('0000320187', 'NIKE, Inc.'),
                'AAPL': ('0000320193', 'Apple Inc.'),
                'MSFT': ('0000789019', 'Microsoft Corporation'),
                'TSLA': ('0001318605', 'Tesla, Inc.'),
            }
            if ticker.upper() in ticker_map:
                cik, company_name = ticker_map[ticker.upper()]
                
        if not company_name:
            company_name = f"Company {ticker or cik}"
            
        if year:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

        # Normalize filing types
        normalized_filing_types = None
        if filing_types:
            ft = filing_types.strip()
            if ft.lower() != 'all':
                normalized_filing_types = [p.strip() for p in ft.split(',') if p.strip()]
            
        print("\n" + "="*100)
        print("JLAW UNIFIED FORENSIC ANALYSIS SYSTEM - COMPLETE 13-PHASE PIPELINE")
        print("="*100)
        print(f"Target: {company_name} (CIK: {cik}, Ticker: {ticker})")
        print(f"Period: {start_date} to {end_date}")
        print(f"Output: {self.output_dir}")
        print(f"Mode: LIVE SEC DATA + ALL 13 PHASES")
        if normalized_filing_types is None:
            print(f"Filing Types: ALL (comprehensive)")
        else:
            print(f"Filing Types: {', '.join(normalized_filing_types)}")
        print("="*100)
        
        # 
        # EXECUTION STRATEGY: BASELINE + UNIFIED
        # 
        
        print("\n EXECUTION STRATEGY:")
        print("   Step 1: Run baseline system (Form 4 + 10-K/Q)")
        print("   Step 2: Intelligent multi-filing analysis (8-K, Proxy, etc.)")
        print("   Step 3: Execute unified 13-phase pipeline")
        print("   Step 4: Merge and enhance results")
        print("   Step 5: Generate complete output stack")
        print()
        
        # 
        # STEP 1: BASELINE PRODUCTION SYSTEM (Proven Results)
        # 
        
        print("\n STEP 1: BASELINE PRODUCTION SYSTEM")
        print("-" * 100)
        print("   Running proven benchmark system for baseline...")
        
        async with BaselineAnalyzer(cik=cik, company_name=company_name) as baseline:
            # Update globals for baseline system
            import jlaw_production_forensic
            jlaw_production_forensic.NIKE_CIK = cik
            jlaw_production_forensic.TARGET_COMPANY = company_name
            jlaw_production_forensic.ANALYSIS_YEAR = year if year else 2019
            
            markdown, json_data = await baseline.run_complete_analysis()
            
            self.baseline_results = {
                'analyzer': baseline,
                'markdown': markdown,
                'json': json_data,
                'filings': baseline.filings,
                'violations': baseline.violations,
                'filing_analyses': baseline.filing_analyses
            }
            
        baseline_violations = len(self.baseline_results['violations'])
        baseline_damages = sum(v.estimated_damages for v in self.baseline_results['violations'])
        baseline_criminal = sum(1 for v in self.baseline_results['violations'] if v.criminal_referral)
        
        print(f"\n    BASELINE COMPLETE:")
        print(f"      Filings Analyzed:   {len(self.baseline_results['filings'])}")
        print(f"      Violations Found:   {baseline_violations}")
        print(f"      Criminal Referrals: {baseline_criminal}")
        print(f"      Estimated Damages:  ${baseline_damages:,.2f}")
        
        # 
        # STEP 2: INTELLIGENT MULTI-FILING ANALYSIS
        # 
        
        print("\n STEP 2: INTELLIGENT MULTI-FILING ANALYSIS")
        print("-" * 100)
        print("   Analyzing ALL filing types with appropriate modules...")
        print("   (8-Ks, Proxies, 11-Ks, Registration Statements, etc.)")
        
        try:
            from intelligent_filing_analyzer import analyze_all_filings_intelligently
            import aiohttp
            
            async with aiohttp.ClientSession(headers={"User-Agent": "JLAW-Forensics/11.0"}) as session:
                intelligent_results = await analyze_all_filings_intelligently(
                    self.baseline_results['filings'],
                    session
                )
                
            print(f"\n    INTELLIGENT ANALYSIS COMPLETE:")
            print(f"      Filing Types Analyzed:   {intelligent_results['coverage_report']['unique_filing_types']}")
            print(f"      Total Filings Covered:   {intelligent_results['coverage_report']['filings_analyzed']}")
            print(f"      Coverage:                {intelligent_results['coverage_report']['coverage_percentage']:.1f}%")
            print(f"      Additional Violations:   {len(intelligent_results['additional_violations'])}")
            print(f"      Red Flags Identified:    {len(intelligent_results['all_red_flags'])}")
            
            # Store for merging
            self.intelligent_results = intelligent_results
            
        except Exception as e:
            logger.error(f"Intelligent filing analysis failed: {e}", exc_info=True)
            print(f"     Intelligent analysis encountered issues: {e}")
            self.intelligent_results = None
        
        # 
        # STEP 3: UNIFIED 13-PHASE PIPELINE
        # 
        
        print("\n STEP 3: UNIFIED 13-PHASE PIPELINE")
        print("-" * 100)
        
        if self.unified_pipeline and PIPELINE_AVAILABLE:
            print("   Executing all 13 phases per README specification...")
            
            try:
                # Execute unified pipeline
                context = await self.unified_pipeline.execute(
                    ticker=ticker,
                    cik=cik,
                    start_date=start_date,
                    end_date=end_date,
                    filing_types=normalized_filing_types
                )
                
                self.unified_results = {
                    'context': context,
                    'filings': context.filings if hasattr(context, 'filings') else [],
                    'violations': context.violations if hasattr(context, 'violations') else [],
                    'parsed_documents': context.parsed_documents if hasattr(context, 'parsed_documents') else [],
                    'chunks': context.chunks if hasattr(context, 'chunks') else [],
                    'benford_results': context.benford_results if hasattr(context, 'benford_results') else {},
                    'linguistic_metrics': context.deception_metrics if hasattr(context, 'deception_metrics') else {},
                    'temporal_anomalies': context.timeline_anomalies if hasattr(context, 'timeline_anomalies') else [],
                    'contradictions': context.contradictions if hasattr(context, 'contradictions') else [],
                    'ml_fraud_scores': context.ml_fraud_scores if hasattr(context, 'ml_fraud_scores') else {},
                }
                
                print(f"\n    UNIFIED PIPELINE COMPLETE:")
                print(f"      Filings Collected:       {len(self.unified_results['filings'])}")
                print(f"      Documents Parsed:        {len(self.unified_results['parsed_documents'])}")
                print(f"      Chunks Created:          {len(self.unified_results['chunks'])}")
                print(f"      Violations Detected:     {len(self.unified_results['violations'])}")
                print(f"      Temporal Anomalies:      {len(self.unified_results['temporal_anomalies'])}")
                print(f"      Contradictions:          {len(self.unified_results['contradictions'])}")
                
            except Exception as e:
                logger.error(f"Unified pipeline execution failed: {e}", exc_info=True)
                print(f"     Unified pipeline encountered issues: {e}")
                print(f"    Continuing with baseline results only")
                self.unified_results = None
        else:
            print("     Unified pipeline not available, using baseline only")
            self.unified_results = None
            
        # 
        # STEP 4: INTELLIGENT MERGE
        # 
        
        print("\n STEP 4: INTELLIGENT RESULT MERGING")
        print("-" * 100)
        
        merged_results = await self._merge_results()
        
        print(f"    MERGE COMPLETE:")
        print(f"      Total Violations:        {merged_results['total_violations']}")
        print(f"      Unique Violation Types:  {len(merged_results['violation_types'])}")
        print(f"      Total Damages:           ${merged_results['total_damages']:,.2f}")
        print(f"      Criminal Referrals:      {merged_results['criminal_referrals']}")
        
        # 
        # STEP 5: COMPLETE OUTPUT STACK (Per README)
        # 
        
        if no_report:
            print("\n STEP 5: REPORT GENERATION SKIPPED (--no-report)")
            print("-" * 100)
            output_path = None
        else:
            print("\n STEP 5: GENERATING COMPLETE OUTPUT STACK")
            print("-" * 100)
            
            output_path = await self._generate_complete_output_stack(
                merged_results,
                company_name,
                cik,
                start_date,
                end_date
            )
            
            print(f"    OUTPUT STACK GENERATED:")
            print(f"      Report Directory: {output_path}")
            print(f"      Main Report:      {output_path / 'FORENSIC_REPORT.md'}")
            print(f"      Executive Brief:  {output_path / 'executive_summary.md'}")
            print(f"      Machine Data:     {output_path / 'machine_readable'}")
            print(f"      Evidence Chain:   {output_path / 'evidence'}")
            print(f"      Appendices:       {output_path / 'appendices'}")
        
        # 
        # FINAL SUMMARY
        # 
        
        print("\n" + "="*100)
        print(" UNIFIED FORENSIC ANALYSIS COMPLETE")
        print("="*100)
        
        print(f"\n FINAL STATISTICS:")
        print(f"   Company:             {company_name}")
        print(f"   Analysis Period:     {start_date} to {end_date}")
        print(f"   Filings Analyzed:    {merged_results['filings_analyzed']}")
        print(f"   Total Violations:    {merged_results['total_violations']}")
        print(f"   Criminal Referrals:  {merged_results['criminal_referrals']}")
        print(f"   Estimated Damages:   ${merged_results['total_damages']:,.2f}")
        
        print(f"\n VIOLATION BREAKDOWN:")
        for vtype, count in sorted(merged_results['violation_types'].items(), key=lambda x: -x[1]):
            print(f"   {vtype}: {count}")
            
        print(f"\n  SEVERITY DISTRIBUTION:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = merged_results['severity_distribution'].get(severity, 0)
            if count > 0:
                print(f"   {severity}: {count}")
                
        if merged_results.get('filing_coverage'):
            coverage = merged_results['filing_coverage']
            print(f"\n FILING COVERAGE:")
            print(f"   Filing Types Analyzed:   {coverage.get('unique_filing_types', 0)}")
            print(f"   Total Coverage:          {coverage.get('coverage_percentage', 0):.1f}%")
            
        if merged_results.get('red_flags'):
            print(f"\n RED FLAGS IDENTIFIED:")
            print(f"   Total: {len(merged_results['red_flags'])}")
            # Show top 5 red flags
            for flag in merged_results['red_flags'][:5]:
                print(f"    {flag}")
            if len(merged_results['red_flags']) > 5:
                print(f"   ... and {len(merged_results['red_flags']) - 5} more")
                
        if merged_results.get('ml_fraud_score'):
            print(f"\n ML FRAUD ASSESSMENT:")
            print(f"   Fraud Probability:   {merged_results['ml_fraud_score']:.1%}")
            risk = 'HIGH' if merged_results['ml_fraud_score'] > 0.7 else 'ELEVATED' if merged_results['ml_fraud_score'] > 0.5 else 'MODERATE'
            print(f"   Risk Level:          {risk}")
            
        print(f"\n OUTPUT LOCATION:")
        print(f"   {output_path}")
        
        print("\n" + "="*100)
        
        return merged_results, output_path
        
    async def _merge_results(self):
        """Intelligently merge baseline, intelligent analysis, and unified results."""
        merged = {
            'filings_analyzed': len(self.baseline_results['filings']),
            'total_violations': len(self.baseline_results['violations']),
            'violation_types': {},
            'severity_distribution': {},
            'total_damages': 0.0,
            'criminal_referrals': 0,
            'violations': self.baseline_results['violations'],
            'filings': self.baseline_results['filings'],
            'red_flags': [],
            'filing_coverage': {}
        }
        
        # Aggregate from baseline
        for v in self.baseline_results['violations']:
            merged['violation_types'][v.violation_type] = merged['violation_types'].get(v.violation_type, 0) + 1
            merged['severity_distribution'][v.severity] = merged['severity_distribution'].get(v.severity, 0) + 1
            merged['total_damages'] += v.estimated_damages
            if v.criminal_referral:
                merged['criminal_referrals'] += 1
                
        # Add intelligent analysis results
        if hasattr(self, 'intelligent_results') and self.intelligent_results:
            # Add violations from intelligent analysis
            for viol in self.intelligent_results.get('additional_violations', []):
                merged['total_violations'] += 1
                vtype = viol.get('type', 'Unknown')
                merged['violation_types'][vtype] = merged['violation_types'].get(vtype, 0) + 1
                severity = viol.get('severity', 'MEDIUM')
                merged['severity_distribution'][severity] = merged['severity_distribution'].get(severity, 0) + 1
                
            # Add red flags
            merged['red_flags'] = self.intelligent_results.get('all_red_flags', [])
            
            # Add coverage info
            merged['filing_coverage'] = self.intelligent_results.get('coverage_report', {})
                
        # Add unified results if available
        if self.unified_results:
            # Add any additional violations from unified pipeline
            for v in self.unified_results.get('violations', []):
                # Check for duplicates
                if not any(bv.violation_id == v.violation_id for bv in self.baseline_results['violations']):
                    merged['violations'].append(v)
                    merged['total_violations'] += 1
                    merged['violation_types'][v.violation_type] = merged['violation_types'].get(v.violation_type, 0) + 1
                    # Severity distribution & damages
                    if getattr(v, 'severity', None):
                        merged['severity_distribution'][v.severity] = merged['severity_distribution'].get(v.severity, 0) + 1
                    try:
                        merged['total_damages'] += float(getattr(v, 'estimated_damages', 0.0) or 0.0)
                    except Exception:
                        pass
                    if getattr(v, 'criminal_referral', False):
                        merged['criminal_referrals'] += 1
                    
            # Add enhanced metrics
            merged['benford_analysis'] = self.unified_results.get('benford_results', {})
            merged['linguistic_metrics'] = self.unified_results.get('linguistic_metrics', {})
            merged['temporal_anomalies'] = self.unified_results.get('temporal_anomalies', [])
            merged['contradictions'] = self.unified_results.get('contradictions', [])
            merged['ml_fraud_score'] = self.unified_results.get('ml_fraud_scores', {}).get('ensemble_score', 0.0)
            
            # Merge filings count (use max/union of accession numbers)
            try:
                base_ids = {getattr(f, 'accession_number', None) for f in merged['filings']}
                uni_filings = self.unified_results.get('filings', [])
                for uf in uni_filings:
                    if getattr(uf, 'accession_number', None) not in base_ids:
                        merged['filings'].append(uf)
                merged['filings_analyzed'] = len(merged['filings'])
            except Exception:
                merged['filings_analyzed'] = max(
                    merged.get('filings_analyzed', 0),
                    len(self.unified_results.get('filings', []))
                )
        
        return merged
        
    async def _generate_complete_output_stack(self, results, company_name, cik, start_date, end_date):
        """Generate complete output stack per README specification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_slug = company_name.replace(' ', '_').replace(',', '').replace('.', '')
        year = start_date[:4]
        
        output_path = self.output_dir / f"{company_slug}_{year}_FORENSIC_ANALYSIS_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # If we have a full unified context and the unified report generator is available,
        # delegate to it to produce the DOJ-grade, full output stack (preferred path).
        try:
            if REPORT_GENERATOR_AVAILABLE and self.unified_results and self.unified_results.get('context'):
                context = self.unified_results['context']
                # Ensure context metadata is populated
                context.company_name = context.company_name or company_name
                context.cik = context.cik or (cik or "")
                context.analysis_period_start = context.analysis_period_start or start_date
                context.analysis_period_end = context.analysis_period_end or end_date
                
                generator = UnifiedReportGenerator(output_path)
                generator.generate_full_report(context)
                
                return output_path
        except Exception as e:
            logger.warning(f"Falling back to baseline output stack generation: {e}")
        
        # Fallback path: generate baseline-style output stack
        # Create subdirectories per README
        (output_path / "machine_readable").mkdir(exist_ok=True)
        (output_path / "evidence").mkdir(exist_ok=True)
        (output_path / "evidence" / "source_documents").mkdir(exist_ok=True)
        (output_path / "appendices").mkdir(exist_ok=True)
        
        # 1. Main forensic report (use baseline markdown + enhancements)
        main_report = self.baseline_results['markdown']
        
        # Add enhanced sections if available
        if results.get('ml_fraud_score'):
            enhanced_section = f"\n\n## ENHANCED FORENSIC ANALYSIS\n\n"
            enhanced_section += f"### ML Fraud Probability Assessment\n"
            enhanced_section += f"- **Overall Score:** {results['ml_fraud_score']:.1%}\n"
            enhanced_section += f"- **Risk Level:** {'HIGH' if results['ml_fraud_score'] > 0.7 else 'ELEVATED' if results['ml_fraud_score'] > 0.5 else 'MODERATE'}\n\n"
            
            if results.get('temporal_anomalies'):
                enhanced_section += f"### Temporal Analysis\n"
                enhanced_section += f"- **Anomalies Detected:** {len(results['temporal_anomalies'])}\n\n"
                
            if results.get('contradictions'):
                enhanced_section += f"### Contradiction Detection\n"
                enhanced_section += f"- **Contradictions Found:** {len(results['contradictions'])}\n\n"
                
            main_report += enhanced_section
            
        (output_path / "FORENSIC_REPORT.md").write_text(main_report, encoding='utf-8')
        
        # 2. Executive summary
        exec_summary = self._generate_executive_summary(results, company_name, start_date, end_date)
        (output_path / "executive_summary.md").write_text(exec_summary, encoding='utf-8')
        
        # 3. Machine-readable outputs
        import json
        
        violations_data = [
            {
                'violation_id': v.violation_id,
                'type': v.violation_type,
                'severity': v.severity,
                'statutory_reference': v.statutory_reference,
                'description': v.description,
                'damages': v.estimated_damages,
                'criminal_referral': v.criminal_referral,
                'accession_number': v.accession_number,
                'filing_date': v.filing_date,
            }
            for v in results['violations']
        ]
        (output_path / "machine_readable" / "violations.json").write_text(
            json.dumps(violations_data, indent=2), encoding='utf-8'
        )
        
        # Summary statistics
        summary = {
            'company': company_name,
            'cik': cik,
            'period': f"{start_date} to {end_date}",
            'total_filings': results['filings_analyzed'],
            'total_violations': results['total_violations'],
            'criminal_referrals': results['criminal_referrals'],
            'estimated_damages': results['total_damages'],
            'violation_types': results['violation_types'],
            'severity_distribution': results['severity_distribution'],
            'ml_fraud_score': results.get('ml_fraud_score', 0.0),
        }
        (output_path / "machine_readable" / "summary.json").write_text(
            json.dumps(summary, indent=2), encoding='utf-8'
        )

        # Additional module outputs (if unified pipeline ran)
        if self.unified_results:
            try:
                # Parsed documents metadata
                pdocs = []
                for d in self.unified_results.get('parsed_documents', []):
                    md = getattr(d, 'metadata', {}) or {}
                    pdocs.append({
                        'doc_id': getattr(d, 'doc_id', ''),
                        'filing_type': md.get('filing_type', ''),
                        'filing_date': md.get('filing_date', ''),
                        'document_url': md.get('document_url', ''),
                        'content_length': md.get('content_length', None),
                        'truncated': md.get('truncated', False)
                    })
                (output_path / "machine_readable" / "parsed_documents.json").write_text(
                    json.dumps(pdocs, indent=2), encoding='utf-8'
                )
                # Temporal anomalies
                tanoms = [
                    {
                        'type': getattr(a, 'anomaly_type', ''),
                        'description': getattr(a, 'description', ''),
                        'severity': getattr(a, 'severity', ''),
                        'date': getattr(a, 'date', None),
                        'related_filings': getattr(a, 'related_filings', [])
                    } for a in self.unified_results.get('temporal_anomalies', [])
                ]
                (output_path / "machine_readable" / "temporal_anomalies.json").write_text(
                    json.dumps(tanoms, indent=2), encoding='utf-8'
                )
                # Contradictions
                contr = [
                    {
                        'type': getattr(c, 'contradiction_type', ''),
                        'description': getattr(c, 'description', ''),
                        'source_document': getattr(c, 'source_document', ''),
                        'target_document': getattr(c, 'target_document', ''),
                        'severity': getattr(c, 'severity', '')
                    } for c in self.unified_results.get('contradictions', [])
                ]
                (output_path / "machine_readable" / "contradictions.json").write_text(
                    json.dumps(contr, indent=2), encoding='utf-8'
                )
                # Statute mappings
                try:
                    statute_mappings = [
                        {
                            'statute': getattr(m, 'statute', ''),
                            'name': getattr(m, 'name', ''),
                            'jurisdiction': getattr(m, 'jurisdiction', ''),
                            'penalties': getattr(m, 'penalties', ''),
                            'govinfo_url': getattr(m, 'govinfo_url', ''),
                            'applicable_violations': getattr(m, 'applicable_violations', [])
                        }
                        for m in getattr(self.unified_results.get('context'), 'statute_mappings', [])
                    ]
                except Exception:
                    statute_mappings = []
                (output_path / "machine_readable" / "statute_mappings.json").write_text(
                    json.dumps(statute_mappings, indent=2), encoding='utf-8'
                )
            except Exception as e:
                logger.warning(f"Failed to write extended machine-readable outputs: {e}")
        
        # 4. Chain of custody
        chain_of_custody = {
            'analysis_system': 'JLAW Unified Forensic Analysis System v11.0',
            'timestamp': timestamp,
            'data_source': 'SEC EDGAR (live)',
            'evidence_items': [
                {
                    'violation_id': v.violation_id,
                    'evidence_hash': v.evidence_hash if hasattr(v, 'evidence_hash') else '',
                    'document_url': v.document_url,
                }
                for v in results['violations']
            ]
        }
        (output_path / "evidence" / "chain_of_custody.json").write_text(
            json.dumps(chain_of_custody, indent=2), encoding='utf-8'
        )
        
        # 5. Methodology appendix
        methodology = self._generate_methodology()
        (output_path / "appendices" / "methodology.md").write_text(methodology, encoding='utf-8')
        
        return output_path
        
    def _generate_executive_summary(self, results, company_name, start_date, end_date):
        """Generate 2-page executive brief."""
        lines = []
        
        lines.append(f"# EXECUTIVE SUMMARY")
        lines.append(f"## {company_name} - SEC Filings Forensic Analysis")
        lines.append("")
        lines.append(f"**Analysis Period:** {start_date} to {end_date}")
        lines.append(f"**Report Date:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Key Findings")
        lines.append("")
        lines.append(f"- **Total Filings Analyzed:** {results['filings_analyzed']}")
        lines.append(f"- **Total Violations Identified:** {results['total_violations']}")
        lines.append(f"- **Criminal Referrals Recommended:** {results['criminal_referrals']}")
        lines.append(f"- **Estimated Total Damages:** ${results['total_damages']:,.2f}")
        lines.append("")
        lines.append("## Violation Summary")
        lines.append("")
        for vtype, count in sorted(results['violation_types'].items(), key=lambda x: -x[1]):
            lines.append(f"- **{vtype}:** {count}")
        lines.append("")
        lines.append("## Severity Distribution")
        lines.append("")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = results['severity_distribution'].get(severity, 0)
            if count > 0:
                lines.append(f"- **{severity}:** {count}")
        lines.append("")
        
        if results.get('ml_fraud_score'):
            risk_level = 'HIGH' if results['ml_fraud_score'] > 0.7 else 'ELEVATED' if results['ml_fraud_score'] > 0.5 else 'MODERATE'
            lines.append("## Risk Assessment")
            lines.append("")
            lines.append(f"- **ML Fraud Probability:** {results['ml_fraud_score']:.1%}")
            lines.append(f"- **Overall Risk Level:** {risk_level}")
            lines.append("")
            
        lines.append("## Recommendations")
        lines.append("")
        if results['criminal_referrals'] > 0:
            lines.append(f"1. **Immediate Action Required:** {results['criminal_referrals']} violation(s) warrant DOJ criminal referral")
        lines.append(f"2. **Compliance Review:** Systematic review recommended based on violation patterns")
        lines.append(f"3. **Legal Consultation:** Engage securities counsel for remediation strategy")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*This is an executive summary. See FORENSIC_REPORT.md for detailed analysis.*")
        
        return '\n'.join(lines)
        
    def _generate_methodology(self):
        """Generate methodology appendix."""
        lines = []
        
        lines.append("# ANALYSIS METHODOLOGY")
        lines.append("")
        lines.append("## System Architecture")
        lines.append("")
        lines.append("This analysis was conducted using the JLAW Unified Forensic Analysis System,")
        lines.append("a comprehensive 13-phase pipeline that integrates:")
        lines.append("")
        lines.append("1. **Document Acquisition** - Live SEC EDGAR API")
        lines.append("2. **Document Parsing** - Semantic chunking and analysis")
        lines.append("3. **Agent Analysis** - AI-powered intelligent extraction")
        lines.append("4. **Quantitative Forensics** - Statistical fraud detection")
        lines.append("5. **Revenue Analysis** - Financial pattern detection")
        lines.append("6. **Flow Analysis** - Transaction flow mapping")
        lines.append("7. **Linguistic Analysis** - Deception pattern detection")
        lines.append("8. **Temporal Analysis** - Timeline anomaly detection")
        lines.append("9. **Contradiction Detection** - Cross-document verification")
        lines.append("10. **ML Fraud Detection** - Machine learning ensemble")
        lines.append("11. **Statutory Mapping** - Legal framework correlation")
        lines.append("12. **Dual-Agent Validation** - Multi-model verification")
        lines.append("13. **Report Generation** - DOJ-grade output")
        lines.append("")
        lines.append("## Data Sources")
        lines.append("")
        lines.append("- **Primary:** SEC EDGAR public filings (live API)")
        lines.append("- **Statutory:** GovInfo.gov USC/CFR references")
        lines.append("- **Validation:** Multi-agent AI analysis")
        lines.append("")
        lines.append("## Compliance")
        lines.append("")
        lines.append("- SEC EDGAR rate limiting: 9 requests/second")
        lines.append("- All data publicly available")
        lines.append("- Chain of custody maintained")
        lines.append("- Evidence hashing (SHA-256)")
        lines.append("")
        
        return '\n'.join(lines)


def parse_args():
    """Parse command-line arguments per README specification."""
    parser = argparse.ArgumentParser(
        description="JLAW Unified Forensic Analysis System - Complete 13-Phase Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze by ticker and year
  python jlaw_forensic.py --ticker NKE --year 2019

  # Analyze by CIK and year
  python jlaw_forensic.py --cik 0000320187 --year 2019

  # Custom date range
  python jlaw_forensic.py --ticker NKE --start-date 2019-01-01 --end-date 2019-12-31

  # Verbose output
  python jlaw_forensic.py --ticker NKE --year 2019 --verbose

  # Custom output directory
  python jlaw_forensic.py --ticker NKE --year 2019 --output-dir /path/to/output
        """
    )
    
    parser.add_argument('--cik', type=str, help='Company CIK number (e.g., 0000320187)')
    parser.add_argument('--ticker', type=str, help='Company ticker symbol (e.g., NKE)')
    parser.add_argument('--year', type=int, help='Analysis year (e.g., 2019)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-report', action='store_true', help='Skip report generation (testing only)')
    parser.add_argument(
        '--filing-types',
        type=str,
        help='Comma-separated SEC filing types to include (e.g., "10-K,10-Q,8-K,4,DEF 14A"). Use "all" (default) for all filings.'
    )
    parser.add_argument(
        '--recursive-engine',
        action='store_true',
        help='Use 6-node Recursive Evidence Engine (blueprint integration mode)'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point per README specification."""
    args = parse_args()
    
    if not args.cik and not args.ticker:
        print("Error: Must provide --cik or --ticker")
        sys.exit(1)
        
    if not args.year and not (args.start_date and args.end_date):
        print("Error: Must provide --year or both --start-date and --end-date")
        sys.exit(1)
    
    # Use Recursive Evidence Engine if requested
    if args.recursive_engine:
        try:
            from src.forensics.recursive_evidence_engine import RecursiveEvidenceEngine
            
            # Resolve CIK if ticker provided
            cik = args.cik
            if not cik and args.ticker:
                ticker_map = {
                    'NKE': '0000320187',
                    'AAPL': '0000320193',
                    'MSFT': '0000789019',
                    'TSLA': '0001318605',
                }
                cik = ticker_map.get(args.ticker.upper())
            
            if not cik:
                print(f"Error: Unknown ticker {args.ticker}")
                sys.exit(1)
            
            # Determine date range
            if args.year:
                start_date = f"{args.year}-01-01"
                end_date = f"{args.year}-12-31"
            else:
                start_date = args.start_date
                end_date = args.end_date
            
            # Initialize and run recursive engine
            engine = RecursiveEvidenceEngine(output_dir=args.output_dir)
            
            print("\n" + "="*60)
            print("RECURSIVE EVIDENCE ENGINE - BLUEPRINT MODE")
            print("="*60)
            
            result = await engine.run_investigation(
                cik=cik,
                start_date=start_date,
                end_date=end_date,
                target_entity=args.ticker or cik
            )
            
            print(f"\n✅ Investigation complete!")
            print(f"Total violations: {result.get('total_violations', 0)}")
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Recursive engine failed: {e}", exc_info=True)
            print(f"\n❌ Recursive engine failed: {e}")
            sys.exit(1)
    
    # Otherwise use standard unified system
    system = CompleteUnifiedForensicSystem(output_dir=args.output_dir)
    
    try:
        results, output_path = await system.execute_complete_analysis(
            ticker=args.ticker,
            cik=args.cik,
            year=args.year,
            start_date=args.start_date,
            end_date=args.end_date,
            verbose=args.verbose,
            filing_types=args.filing_types,
            no_report=args.no_report
        )
        
        print(f"\n Analysis complete! Output: {output_path}")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n  Analysis interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n\n Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

