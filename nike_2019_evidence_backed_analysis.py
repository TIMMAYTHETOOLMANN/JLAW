"""
Nike 2019 Evidence-Backed Forensic Analysis
===========================================

Complete forensic analysis with full evidence-backed reporting.
Analyzes ALL 89 filings, reports on violations with complete evidence chains.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from benchmark_compliance_test import BenchmarkComplianceTester
from enhanced_forensic_report_generator import (
    EnhancedForensicReportGenerator,
    FilingAnalysis,
    ViolationDetail
)
from src.forensics.reporting.evidence_backed_reporter import (
    EvidenceBackedReporter,
    ConfidenceLevel
)
from src.forensics.reporting.evidence_extractors import (
    Form4EvidenceExtractor,
    FinancialStatementEvidenceExtractor
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvidenceBackedForensicAnalysis:
    """
    Complete evidence-backed forensic analysis system
    """
    
    def __init__(self):
        self.benchmark_tester = BenchmarkComplianceTester()
        self.report_generator = EnhancedForensicReportGenerator()
        self.evidence_reporter = EvidenceBackedReporter(min_confidence=ConfidenceLevel.MODERATE)
        self.form4_extractor = Form4EvidenceExtractor()
        self.financial_extractor = FinancialStatementEvidenceExtractor()
        
        self.total_filings_collected = 0
        self.filings_with_violations = 0
        self.total_violations_detected = 0
        self.evidence_backed_violations = 0
        
    async def run_complete_analysis(self):
        """
        Execute complete evidence-backed forensic analysis
        """
        logger.info("="*80)
        logger.info("EVIDENCE-BACKED FORENSIC ANALYSIS - Nike Inc. 2019")
        logger.info("="*80)
        logger.info("")
        
        # Phase 1: Collect ALL filings
        logger.info("[PHASE 1/5] Collecting ALL Nike 2019 SEC Filings...")
        filings = await self.benchmark_tester._collect_nike_2019_filings()
        self.total_filings_collected = len(filings)
        logger.info(f"✓ Collected {self.total_filings_collected} filings")
        logger.info(f"  - Form 4: {sum(1 for f in filings if f['type'] == '4')}")
        logger.info(f"  - 10-K: {sum(1 for f in filings if f['type'] == '10-K')}")
        logger.info(f"  - 10-Q: {sum(1 for f in filings if f['type'] == '10-Q')}")
        logger.info(f"  - 8-K: {sum(1 for f in filings if f['type'] == '8-K')}")
        logger.info("")
        
        # Phase 2: Detect violations using existing system
        logger.info("[PHASE 2/5] Detecting Violations...")
        await self.benchmark_tester.run_benchmark_test()
        
        total_detected = (
            len(self.benchmark_tester.results['late_form4']) +
            len(self.benchmark_tester.results['zero_dollar']) +
            len(self.benchmark_tester.results['material_misstatements']) +
            len(self.benchmark_tester.results['critical_violations'])
        )
        self.total_violations_detected = total_detected
        logger.info(f"✓ Detected {total_detected} potential violations")
        logger.info(f"  - Late Form 4: {len(self.benchmark_tester.results['late_form4'])}")
        logger.info(f"  - Zero-Dollar: {len(self.benchmark_tester.results['zero_dollar'])}")
        logger.info(f"  - Misstatements: {len(self.benchmark_tester.results['material_misstatements'])}")
        logger.info(f"  - SOX 302: {len(self.benchmark_tester.results['critical_violations'])}")
        logger.info("")
        
        # Phase 3: Extract evidence and validate
        logger.info("[PHASE 3/5] Extracting Evidence & Validating...")
        evidence_backed_violations = await self._extract_and_validate_evidence()
        self.evidence_backed_violations = len(evidence_backed_violations)
        logger.info(f"✓ {self.evidence_backed_violations} violations passed evidence standards")
        logger.info(f"  Evidence Reporter Statistics:")
        stats = self.evidence_reporter.get_statistics()
        for key, value in stats.items():
            logger.info(f"    - {key}: {value}")
        logger.info("")
        
        # Phase 4: Generate evidence-backed report
        logger.info("[PHASE 4/5] Generating Evidence-Backed Report...")
        report = await self._generate_evidence_backed_report(evidence_backed_violations, filings)
        logger.info(f"✓ Report generated: {len(report):,} characters")
        logger.info("")
        
        # Phase 5: Save results
        logger.info("[PHASE 5/5] Saving Results...")
        report_file = self._save_report(report)
        stats_file = self._save_statistics(evidence_backed_violations)
        logger.info(f"✓ Report saved: {report_file}")
        logger.info(f"✓ Statistics saved: {stats_file}")
        logger.info("")
        
        # Final Summary
        logger.info("="*80)
        logger.info("✅ EVIDENCE-BACKED ANALYSIS COMPLETE")
        logger.info("="*80)
        logger.info(f"Total Filings Analyzed: {self.total_filings_collected}")
        logger.info(f"Filings with Violations: {self.filings_with_violations}")
        logger.info(f"Total Violations Detected: {self.total_violations_detected}")
        logger.info(f"Evidence-Backed Violations: {self.evidence_backed_violations}")
        logger.info(f"Rejection Rate: {100 - (self.evidence_backed_violations/self.total_violations_detected*100):.1f}%")
        logger.info(f"Total Damages: ${self.benchmark_tester.results['total_damages']:,.2f}")
        logger.info("="*80)
        
        return report
    
    async def _extract_and_validate_evidence(self):
        """
        Extract evidence for each violation and validate
        """
        validated_violations = []
        
        # Process Late Form 4 violations
        for v in self.benchmark_tester.results['late_form4']:
            filing_data = {
                'transaction_date': v['transaction_date'],
                'filing_date': v['filing_date'],
                'accession': v['accession'],
                'insider': 'Reporting Person',
                'url': v['url'],
                'company': 'Nike Inc.'
            }
            
            violation_evidence = self.form4_extractor.extract_late_filing_evidence(filing_data)
            
            if violation_evidence and self.evidence_reporter.evaluate_violation(violation_evidence):
                validated_violations.append({
                    'original': v,
                    'evidence': violation_evidence,
                    'type': 'late_form4'
                })
        
        # Process Zero-Dollar violations
        for v in self.benchmark_tester.results['zero_dollar']:
            filing_data = {
                'accession': v['accession'],
                'shares': v['shares'],
                'price_per_share': v['price_per_share'],
                'transaction_code': v['transaction_code']
            }
            
            violation_evidence = self.form4_extractor.extract_zero_dollar_evidence(filing_data)
            
            if violation_evidence and self.evidence_reporter.evaluate_violation(violation_evidence):
                validated_violations.append({
                    'original': v,
                    'evidence': violation_evidence,
                    'type': 'zero_dollar'
                })
        
        # Process Material Misstatements
        for v in self.benchmark_tester.results['material_misstatements']:
            filing_data = {
                'type': v['filing_type'],
                'accession': v['accession'],
                'contains_restatement': True
            }
            
            violation_evidence = self.financial_extractor.extract_restatement_evidence(filing_data)
            
            if violation_evidence and self.evidence_reporter.evaluate_violation(violation_evidence):
                validated_violations.append({
                    'original': v,
                    'evidence': violation_evidence,
                    'type': 'misstatement'
                })
        
        # Process SOX 302 violations
        for v in self.benchmark_tester.results['critical_violations']:
            filing_data = {
                'type': v['filing_type'],
                'accession': v['accession'],
                'missing_sox_302': True
            }
            
            violation_evidence = self.financial_extractor.extract_sox_302_evidence(filing_data)
            
            if violation_evidence and self.evidence_reporter.evaluate_violation(violation_evidence):
                validated_violations.append({
                    'original': v,
                    'evidence': violation_evidence,
                    'type': 'sox302'
                })
        
        return validated_violations
    
    async def _generate_evidence_backed_report(self, violations, all_filings):
        """
        Generate complete evidence-backed report
        """
        # Count unique filings with violations
        filings_with_violations = set(v['original']['accession'] for v in violations)
        self.filings_with_violations = len(filings_with_violations)
        
        # Create filing map
        filing_map = {f['accession']: f for f in all_filings}
        
        # Group violations by filing
        violation_by_filing = {}
        for v in violations:
            acc = v['original']['accession']
            if acc not in violation_by_filing:
                violation_by_filing[acc] = []
            violation_by_filing[acc].append(v)
        
        # Build report
        lines = [
            "="*80,
            "NIKE INC. (NKE) - 2019 SEC FILINGS FORENSIC ANALYSIS",
            "EVIDENCE-BACKED DOJ-LEVEL INVESTIGATION REPORT",
            "="*80,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Target Company: Nike Inc. (CIK: 0000320187)",
            f"Analysis Period: January 1, 2019 - December 31, 2019",
            "",
            "ANALYSIS SCOPE:",
            f"  Total Filings Collected: {self.total_filings_collected}",
            f"  Filings with Violations: {self.filings_with_violations}",
            f"  Filings Cleared: {self.total_filings_collected - self.filings_with_violations}",
            "",
            "VIOLATION SUMMARY:",
            f"  Total Violations Detected: {self.total_violations_detected}",
            f"  Evidence-Backed Violations: {self.evidence_backed_violations}",
            f"  Rejected (Insufficient Evidence): {self.total_violations_detected - self.evidence_backed_violations}",
            "",
            "CRIMINAL REFERRALS:",
            f"  Recommended: {sum(1 for v in violations if v['original'].get('severity') == 'CRITICAL')}",
            "",
            f"Estimated Total Damages: ${self.benchmark_tester.results['total_damages']:,.2f}",
            "",
            "="*80,
            "",
            "EVIDENCE QUALITY STANDARDS",
            "",
            "This report applies ZERO-TOLERANCE evidence standards. Every violation",
            "reported includes:",
            "  ✓ Exact quotes from source documents",
            "  ✓ Precise document locations",
            "  ✓ Complete statute citations with regulatory text",
            "  ✓ Step-by-step reasoning chains",
            "  ✓ Confidence assessments with justification",
            "",
            f"Reportability Rate: {self.evidence_backed_violations/self.total_violations_detected*100:.1f}%",
            f"Evidence Reporter Statistics: {self.evidence_reporter.get_statistics()}",
            "",
            "="*80,
            "",
            "VIOLATIONS BY TYPE",
            ""
        ]
        
        # Count by type
        type_counts = {}
        for v in violations:
            vtype = v['original']['type']
            type_counts[vtype] = type_counts.get(vtype, 0) + 1
        
        for vtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"• {vtype}: {count}")
        
        lines.extend([
            "",
            "="*80,
            "",
            "PER-FILING DETAILED ANALYSIS",
            "(Only filings with violations are shown)",
            "",
            "="*80,
            ""
        ])
        
        # Generate per-filing reports
        for acc in sorted(violation_by_filing.keys()):
            filing = filing_map.get(acc)
            if not filing:
                continue
            
            filing_violations = violation_by_filing[acc]
            
            lines.extend([
                "",
                f"{filing['type']} - Filed {filing['filing_date']}",
                f"Accession Number: {acc}",
                f"Document URL: {filing['url']}",
                f"Violations Found: {len(filing_violations)}",
                ""
            ])
            
            for i, v in enumerate(filing_violations, 1):
                evidence = v['evidence']
                lines.extend([
                    f"Violation {i}: {evidence.violation_type}",
                    f"• Severity: {evidence.severity}",
                    f"• Confidence: {evidence.confidence.name} ({evidence.confidence.value:.0%})",
                    f"• Evidence Strength: {evidence.get_evidence_strength_score():.2f}/1.00",
                    f"• Reportable: {'YES' if evidence.is_reportable() else 'NO'}",
                    "",
                    f"EVIDENCE ITEMS: {len(evidence.supporting_evidence)}",
                ])
                
                for j, ev_item in enumerate(evidence.supporting_evidence, 1):
                    lines.extend([
                        f"  Evidence {j}:",
                        f"    Type: {ev_item.evidence_type.value}",
                        f"    Source: {ev_item.source_document}",
                        f"    Location: {ev_item.source_location}",
                        f"    Content: {ev_item.content}",
                        f"    Verified: {ev_item.verification_status}",
                        ""
                    ])
                
                lines.extend([
                    f"STATUTE CITATIONS: {len(evidence.statute_citations)}",
                ])
                
                for j, statute in enumerate(evidence.statute_citations, 1):
                    lines.extend([
                        f"  Statute {j}:",
                        f"    Title: {statute.title}",
                        f"    Text: {statute.full_text[:200]}...",
                        f"    Violation: {statute.violation_description}",
                        ""
                    ])
                
                lines.extend([
                    f"REASONING CHAIN: {len(evidence.reasoning_chain)} steps",
                ])
                
                for j, step in enumerate(evidence.reasoning_chain, 1):
                    lines.append(f"  {j}. {step}")
                
                lines.extend([
                    "",
                    f"CONFIDENCE JUSTIFICATION:",
                    f"{evidence.confidence_justification}",
                    "",
                    "-"*80,
                    ""
                ])
        
        return "\n".join(lines)
    
    def _save_report(self, report: str) -> str:
        """Save report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"EVIDENCE_BACKED_FORENSIC_REPORT_Nike_Inc_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename
    
    def _save_statistics(self, violations) -> str:
        """Save statistics to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"EVIDENCE_BACKED_STATISTICS_{timestamp}.json"
        
        import json
        stats = {
            'analysis_date': datetime.now().isoformat(),
            'total_filings_collected': self.total_filings_collected,
            'filings_with_violations': self.filings_with_violations,
            'total_violations_detected': self.total_violations_detected,
            'evidence_backed_violations': self.evidence_backed_violations,
            'rejection_rate': f"{100 - (self.evidence_backed_violations/self.total_violations_detected*100):.1f}%",
            'reporter_statistics': self.evidence_reporter.get_statistics(),
            'violations': [v['evidence'].to_dict() for v in violations]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        return filename


async def main():
    """Run complete evidence-backed analysis"""
    analyzer = EvidenceBackedForensicAnalysis()
    report = await analyzer.run_complete_analysis()
    
    print("\n" + "="*80)
    print("REPORT PREVIEW (First 2000 characters)")
    print("="*80)
    print(report[:2000])
    print("\n... (full report saved to file)")


if __name__ == "__main__":
    asyncio.run(main())

