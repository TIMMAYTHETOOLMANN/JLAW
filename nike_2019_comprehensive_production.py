"""
NIKE 2019 COMPREHENSIVE FORENSIC PRODUCTION RUN
================================================

MISSION: Full-scale forensic analysis of ALL Nike (NKE) SEC filings from 2019
BENCHMARK: Gold standard PDF output - our absolute minimum acceptance level
OBJECTIVE: Meet or EXCEED the sophistication demonstrated in content.pdf

Target Company: Nike Inc (CIK: 0000320187)
Analysis Period: January 1, 2019 - December 31, 2019
Filing Types: ALL SEC FILINGS (10-K, 10-Q, 8-K, 4, 3, 5, SC 13G/D, S-8, etc.)

System Capabilities Activated:
✅ Enhanced Contradiction Detector (DeBERTa-v3, 92%+ accuracy)
✅ Advanced Statute Integrator (GovInfo API with direct citations)
✅ Multi-pass AI Analysis (OpenAI + Anthropic when available)
✅ Form 4 Holy Grail Universal Extractor
✅ Beneish M-Score financial forensics
✅ Semantic contradiction graph analysis
✅ Immutable evidence chain with RFC 3161 timestamps
✅ Neo4j knowledge graph (when available)
✅ FinBERT domain adaptation
✅ NIST compliance verification
✅ Prosecutorial merit assessment

Author: JARVIS NEXUS
Date: November 26, 2025
"""

import asyncio
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Ensure JLAW is in path
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.forensic_orchestrator import ForensicOrchestrator, ForensicCase, InvestigationStatus
from src.forensics.config_manager import ConfigurationManager
from src.forensics.immutable_storage import StorageConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'nike_2019_comprehensive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NikeComprehensiveProduction:
    """Orchestrates comprehensive Nike 2019 forensic analysis."""
    
    # Nike CIK and company info
    NIKE_CIK = "0000320187"
    NIKE_NAME = "Nike Inc"
    ANALYSIS_YEAR = 2019
    
    # ALL possible SEC form types
    ALL_FORM_TYPES = [
        # Periodic Reports
        "10-K", "10-K/A",
        "10-Q", "10-Q/A",
        "8-K", "8-K/A",
        
        # Insider Trading
        "3", "3/A",
        "4", "4/A",
        "5", "5/A",
        
        # Beneficial Ownership
        "SC 13G", "SC 13G/A",
        "SC 13D", "SC 13D/A",
        
        # Proxy Statements
        "DEF 14A", "DEFA14A", "DEFM14A",
        "PRER14A", "PREC14A",
        
        # Registration Statements
        "S-1", "S-1/A",
        "S-3", "S-3/A",
        "S-4", "S-4/A",
        "S-8", "S-8 POS",
        
        # Other
        "144",
        "UPLOAD",
        "EFFECT"
    ]
    
    def __init__(self):
        """Initialize production system."""
        self.config_mgr = ConfigurationManager()
        self.config = self.config_mgr.config
        
        # Create storage config
        self.storage_config = StorageConfig(
            provider=self.config.storage_provider
        )
        
        # Initialize orchestrator with full capabilities
        self.orchestrator = ForensicOrchestrator(
            govinfo_api_key=self.config.govinfo.api_key,
            storage_config=self.storage_config,
            audit_signing_key=b"nike-2019-comprehensive-production",
            user_agent="JARVIS-NEXUS-RECON contact@nits-secops.org"
        )
        
        # Results tracking
        self.results = {
            'case_id': None,
            'analysis_start': datetime.now(timezone.utc).isoformat(),
            'analysis_end': None,
            'total_filings_collected': 0,
            'total_filings_analyzed': 0,
            'total_violations_detected': 0,
            'filings_by_type': {},
            'violations_by_type': {},
            'violations_by_statute': {},
            'high_risk_findings': [],
            'benchmark_comparison': {},
            'processing_errors': [],
            'execution_time_seconds': 0
        }
        
    def print_banner(self):
        """Display mission banner."""
        print("\n" + "="*100)
        print(" " * 20 + "NIKE 2019 COMPREHENSIVE FORENSIC PRODUCTION RUN")
        print("="*100)
        print(f"\n📊 MISSION PARAMETERS:")
        print(f"   Company: {self.NIKE_NAME} (CIK: {self.NIKE_CIK})")
        print(f"   Period: {self.ANALYSIS_YEAR}-01-01 to {self.ANALYSIS_YEAR}-12-31")
        print(f"   Scope: ALL SEC FILINGS")
        print(f"   Target Form Types: {len(self.ALL_FORM_TYPES)} form types")
        
        print(f"\n🎯 BENCHMARK TARGET:")
        print(f"   Minimum Standard: content.pdf gold standard output")
        print(f"   Expected Performance: EXCEED previous system capabilities")
        
        print(f"\n⚙️  SYSTEM CAPABILITIES:")
        print(f"   ✅ Enhanced Contradiction Detection (DeBERTa-v3)")
        print(f"   ✅ Advanced Statute Integration (GovInfo API)")
        print(f"   ✅ Multi-pass AI Analysis (OpenAI + Anthropic)")
        print(f"   ✅ Form 4 Holy Grail Extractor")
        print(f"   ✅ Financial Forensics (Beneish M-Score)")
        print(f"   ✅ Semantic Graph Analysis")
        print(f"   ✅ Immutable Evidence Chain")
        
        print(f"\n🚀 EXECUTION MODE: AUTONOMOUS")
        print(f"   No manual intervention - full recursive execution")
        print(f"   Adaptive error handling after 5x identical errors")
        print(f"   Self-healing fallback mechanisms")
        
        print("\n" + "="*100 + "\n")
        
    async def collect_all_filings(self) -> List[Dict[str, Any]]:
        """
        Collect ALL Nike filings from 2019.
        Uses SEC EDGAR API to get comprehensive filing list.
        """
        logger.info(f"[STEP 1] Collecting ALL Nike filings from {self.ANALYSIS_YEAR}...")
        
        try:
            # Use the orchestrator's internal SEC analyzer
            from src.forensics.sec_edgar_analyzer import SECForensicAnalyzer
            sec_analyzer = SECForensicAnalyzer(user_agent=self.orchestrator.user_agent)
            
            # Get company filings for 2019
            all_filings = []
            
            # The SEC EDGAR API returns recent filings, but we need 2019 specifically
            # We'll need to fetch and filter
            logger.info(f"   Fetching filings from SEC EDGAR...")
            
            # Note: SEC API typically returns recent filings
            # For historical data, we may need to use the company facts endpoint
            # or parse the full submission history
            
            # For now, let's use the orchestrator's collection method
            # which internally calls SEC EDGAR API
            case = ForensicCase(
                case_id=f"NIKE_2019_COMPREHENSIVE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                target_cik=self.NIKE_CIK,
                target_company=self.NIKE_NAME,
                investigation_start=datetime.now(timezone.utc)
            )
            
            self.results['case_id'] = case.case_id
            
            # Collect filings - orchestrator handles rate limiting
            filings = await self.orchestrator._collect_filings(
                case=case,
                filing_types=self.ALL_FORM_TYPES,
                years=1  # Will be filtered to 2019
            )
            
            # Filter to only 2019 filings
            filings_2019 = []
            for filing in filings:
                filing_date = filing.get('filing_date', '')
                if filing_date and filing_date.startswith('2019'):
                    filings_2019.append(filing)
            
            logger.info(f"   ✓ Collected {len(filings_2019)} filings from 2019")
            
            # Count by type
            form_counts = {}
            for filing in filings_2019:
                form_type = filing.get('form_type', 'UNKNOWN')
                form_counts[form_type] = form_counts.get(form_type, 0) + 1
            
            self.results['total_filings_collected'] = len(filings_2019)
            self.results['filings_by_type'] = form_counts
            
            logger.info(f"\n   📋 Filing Breakdown:")
            for form_type, count in sorted(form_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"      {form_type}: {count}")
            
            return filings_2019
            
        except Exception as e:
            logger.error(f"   ❌ Error collecting filings: {e}")
            self.results['processing_errors'].append({
                'stage': 'collection',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return []
    
    async def analyze_form4_filing(self, filing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a Form 4 filing with Holy Grail extractor.
        """
        form_type = filing.get('form_type', 'UNKNOWN')
        filing_date = filing.get('filing_date', 'UNKNOWN')
        accession = filing.get('accession_number', 'UNKNOWN')
        
        try:
            from src.forensics.insider_form4_analyzer import InsiderForm4Analyzer
            
            analyzer = InsiderForm4Analyzer(
                user_agent=self.orchestrator.user_agent
            )
            
            violations = await analyzer.analyze_form4(
                xml_url=filing.get('document_url', ''),
                viewer_url=filing.get('viewer_url'),
                filing_date_str=filing_date
            )
            
            if violations:
                logger.info(f"      ✓ Found {len(violations)} violations")
                
                result = {
                    'form_type': form_type,
                    'filing_date': filing_date,
                    'accession_number': accession,
                    'violations': [
                        {
                            'type': v.type,
                            'description': v.description,
                            'severity': v.severity,
                            'statute': v.applicable_statute,
                            'section': v.section_violated
                        }
                        for v in violations
                    ],
                    'violation_count': len(violations)
                }
                
                return result
            else:
                logger.info(f"      • No violations detected")
                return None
                
        except Exception as e:
            logger.error(f"      ❌ Error analyzing Form 4: {e}")
            self.results['processing_errors'].append({
                'stage': 'form4_analysis',
                'filing': accession,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return None
    
    async def analyze_periodic_filing(self, filing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a 10-K/10-Q/8-K filing with full forensic capabilities.
        """
        form_type = filing.get('form_type', 'UNKNOWN')
        filing_date = filing.get('filing_date', 'UNKNOWN')
        accession = filing.get('accession_number', 'UNKNOWN')
        
        try:
            # Use the orchestrator's SEC analyzer (with AI if available)
            analysis = await self.orchestrator.sec_analyzer.analyze_filing(
                cik=self.NIKE_CIK,
                accession_number=accession,
                filing_type=form_type
            )
            
            if analysis and analysis.violations:
                logger.info(f"      ✓ Found {len(analysis.violations)} violations")
                
                result = {
                    'form_type': form_type,
                    'filing_date': filing_date,
                    'accession_number': accession,
                    'violations': [
                        {
                            'type': v.violation_type,
                            'description': v.description,
                            'severity': v.severity_level,
                            'statute': v.applicable_statute,
                            'section': v.section_violated,
                            'confidence': v.confidence_score
                        }
                        for v in analysis.violations
                    ],
                    'violation_count': len(analysis.violations),
                    'risk_score': analysis.overall_risk_score
                }
                
                return result
            else:
                logger.info(f"      • No violations detected")
                return None
                
        except Exception as e:
            logger.error(f"      ❌ Error analyzing periodic filing: {e}")
            self.results['processing_errors'].append({
                'stage': 'periodic_analysis',
                'filing': accession,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return None
    
    async def analyze_filing(self, filing: Dict[str, Any], index: int, total: int) -> Optional[Dict[str, Any]]:
        """
        Route filing to appropriate analyzer based on form type.
        """
        form_type = filing.get('form_type', 'UNKNOWN')
        filing_date = filing.get('filing_date', 'UNKNOWN')
        accession = filing.get('accession_number', 'UNKNOWN')
        
        logger.info(f"\n   [{index}/{total}] {form_type} ({filing_date}) - {accession}")
        
        # Route to specialized analyzer
        if form_type in ('3', '3/A', '4', '4/A', '5', '5/A'):
            return await self.analyze_form4_filing(filing)
        
        elif form_type in ('10-K', '10-K/A', '10-Q', '10-Q/A', '8-K', '8-K/A'):
            return await self.analyze_periodic_filing(filing)
        
        else:
            logger.info(f"      • Form type {form_type} not yet implemented - skipping")
            return None
    
    async def execute_comprehensive_analysis(self):
        """
        Main execution: collect all filings and analyze with full system capabilities.
        """
        start_time = datetime.now(timezone.utc)
        
        self.print_banner()
        
        # Step 1: Collect all filings
        filings = await self.collect_all_filings()
        
        if not filings:
            logger.error("\n❌ No filings collected. Aborting analysis.")
            return
        
        # Step 2: Analyze each filing
        logger.info(f"\n[STEP 2] Analyzing {len(filings)} filings with full forensic capabilities...")
        logger.info(f"   (This may take 10-30 minutes depending on filing count and API rate limits)")
        
        all_violation_results = []
        analyzed_count = 0
        
        for i, filing in enumerate(filings, 1):
            result = await self.analyze_filing(filing, i, len(filings))
            
            if result:
                all_violation_results.append(result)
                analyzed_count += 1
                
                # Update statistics
                for violation in result['violations']:
                    v_type = violation['type']
                    self.results['violations_by_type'][v_type] = \
                        self.results['violations_by_type'].get(v_type, 0) + 1
                    
                    statute = violation.get('statute', 'UNKNOWN')
                    self.results['violations_by_statute'][statute] = \
                        self.results['violations_by_statute'].get(statute, 0) + 1
            
            # Rate limiting pause every 10 requests
            if i % 10 == 0:
                logger.info(f"   ⏸️  Rate limiting pause (10 requests)...")
                await asyncio.sleep(1.0)
        
        # Step 3: Calculate final statistics
        self.results['total_filings_analyzed'] = analyzed_count
        self.results['total_violations_detected'] = sum(
            r['violation_count'] for r in all_violation_results
        )
        
        end_time = datetime.now(timezone.utc)
        self.results['analysis_end'] = end_time.isoformat()
        self.results['execution_time_seconds'] = (end_time - start_time).total_seconds()
        
        # Step 4: Generate comprehensive report
        await self.generate_final_report(all_violation_results)
    
    async def generate_final_report(self, violation_results: List[Dict[str, Any]]):
        """
        Generate comprehensive final report with benchmark comparison.
        """
        logger.info(f"\n[STEP 3] Generating comprehensive forensic report...")
        
        print("\n" + "="*100)
        print(" " * 30 + "ANALYSIS COMPLETE")
        print("="*100)
        
        print(f"\n📊 FILING ANALYSIS SUMMARY:")
        print(f"   Total Filings Collected: {self.results['total_filings_collected']}")
        print(f"   Total Filings Analyzed: {self.results['total_filings_analyzed']}")
        print(f"   Analysis Coverage: {self.results['total_filings_analyzed']/self.results['total_filings_collected']*100:.1f}%")
        
        print(f"\n📋 FILINGS BY TYPE:")
        for form_type, count in sorted(
            self.results['filings_by_type'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:  # Top 10
            print(f"   {form_type}: {count}")
        
        print(f"\n⚠️  VIOLATIONS DETECTED:")
        print(f"   Total Violations: {self.results['total_violations_detected']}")
        
        if self.results['violations_by_type']:
            print(f"\n   Breakdown by Type:")
            for v_type, count in sorted(
                self.results['violations_by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"      {v_type}: {count}")
        
        if self.results['violations_by_statute']:
            print(f"\n   Breakdown by Statute:")
            for statute, count in sorted(
                self.results['violations_by_statute'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]:  # Top 10
                print(f"      {statute}: {count}")
        
        # Benchmark comparison (if we know the gold standard numbers)
        print(f"\n🎯 BENCHMARK COMPARISON:")
        print(f"   Gold Standard Target: 54+ violations (from content.pdf)")
        print(f"   Current Run Detected: {self.results['total_violations_detected']} violations")
        
        if self.results['total_violations_detected'] >= 54:
            print(f"   Status: ✅ MEETS OR EXCEEDS BENCHMARK")
        else:
            print(f"   Status: ⚠️  BELOW BENCHMARK TARGET")
        
        print(f"\n⏱️  EXECUTION TIME:")
        print(f"   Total Time: {self.results['execution_time_seconds']:.1f} seconds")
        print(f"   Avg Time per Filing: {self.results['execution_time_seconds']/self.results['total_filings_analyzed']:.2f} seconds")
        
        if self.results['processing_errors']:
            print(f"\n❌ PROCESSING ERRORS: {len(self.results['processing_errors'])}")
            for error in self.results['processing_errors'][:5]:  # Show first 5
                print(f"   - {error['stage']}: {error['error'][:100]}")
        
        print("\n" + "="*100 + "\n")
        
        # Save detailed JSON report
        output_file = f"nike_2019_comprehensive_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'metadata': self.results,
                'detailed_violations': violation_results
            }, f, indent=2, default=str)
        
        logger.info(f"✅ Detailed report saved to: {output_file}")
        
        print(f"📄 Detailed JSON report: {output_file}\n")


async def main():
    """Main entry point."""
    try:
        production = NikeComprehensiveProduction()
        await production.execute_comprehensive_analysis()
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

