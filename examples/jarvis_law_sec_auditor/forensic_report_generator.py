"""
JARVIS:LAW Black Site Protocol - Human-Interpretable Forensic Report Generator
Converts digital audit trails to formal courtroom-ready documents
"""

from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import json

from forensic_core import ViolationType, StatuteMapper


class ForensicReportGenerator:
    """Generate formal human-readable forensic reports"""
    
    def __init__(self):
        self.report_sections = []
        
    def generate_executive_summary(self, analysis_data: Dict) -> str:
        """Generate executive summary for leadership/enforcement"""
        
        summary = []
        summary.append("="*100)
        summary.append("FORENSIC AUDIT EXECUTIVE SUMMARY")
        summary.append("="*100)
        summary.append(f"\nReport Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        summary.append(f"Analysis Period: {analysis_data.get('period', 'N/A')}")
        summary.append(f"Subject: {analysis_data.get('company', 'N/A')} (CIK: {analysis_data.get('cik', 'N/A')})")
        
        # Key Findings
        summary.append(f"\n{'='*100}")
        summary.append("KEY FINDINGS")
        summary.append(f"{'='*100}")
        
        total_filings = analysis_data.get('total_filings', 0)
        violations = analysis_data.get('total_violations', 0)
        risk_score = analysis_data.get('risk_score', 0)
        
        summary.append(f"\nDocuments Analyzed: {total_filings}")
        summary.append(f"Potential Violations Detected: {violations}")
        summary.append(f"Overall Risk Assessment: {self._risk_level(risk_score)} ({risk_score:.1%})")
        
        # Critical Findings
        if violations > 0:
            summary.append(f"\n⚠️  CRITICAL FINDINGS REQUIRE IMMEDIATE ATTENTION")
            summary.append(f"\nThis forensic analysis has identified {violations} potential violations")
            summary.append(f"of federal securities laws and regulations. Detailed findings follow.")
        else:
            summary.append(f"\n✓ No material violations detected in analyzed filings.")
        
        # Pattern Summary
        patterns = analysis_data.get('patterns_detected', [])
        if patterns:
            summary.append(f"\n{'='*100}")
            summary.append("FRAUD PATTERN ANALYSIS")
            summary.append(f"{'='*100}")
            summary.append(f"\nDetected {len(patterns)} suspicious patterns:")
            
            for i, pattern in enumerate(patterns, 1):
                summary.append(f"\n{i}. {pattern.get('pattern', 'Unknown Pattern')}")
                summary.append(f"   Confidence Level: {pattern.get('confidence', 0):.1%}")
                summary.append(f"   Risk: {self._risk_level(pattern.get('confidence', 0))}")
                
                if pattern.get('recommendation'):
                    summary.append(f"   Recommended Action: {pattern['recommendation']}")
        
        # Legal Exposure
        if analysis_data.get('statute_references'):
            summary.append(f"\n{'='*100}")
            summary.append("LEGAL EXPOSURE ASSESSMENT")
            summary.append(f"{'='*100}")
            
            criminal = [s for s in analysis_data['statute_references'] if s.get('criminal_penalty')]
            civil = [s for s in analysis_data['statute_references'] if s.get('civil_penalty')]
            
            if criminal:
                summary.append(f"\n⚠️  CRIMINAL EXPOSURE: {len(criminal)} potential criminal violations")
                max_penalty = max([self._parse_penalty_years(s.get('criminal_penalty', '')) for s in criminal])
                summary.append(f"   Maximum Criminal Penalty: {max_penalty} years imprisonment")
            
            if civil:
                summary.append(f"\n⚠️  CIVIL EXPOSURE: {len(civil)} potential civil violations")
                summary.append(f"   Potential for: Disgorgement, Penalties, Injunctive Relief")
        
        summary.append(f"\n{'='*100}")
        summary.append("END OF EXECUTIVE SUMMARY")
        summary.append(f"{'='*100}\n")
        
        return '\n'.join(summary)
    
    def generate_detailed_findings(self, analysis_data: Dict) -> str:
        """Generate detailed findings section"""
        
        findings = []
        findings.append("\n" + "="*100)
        findings.append("DETAILED FORENSIC FINDINGS")
        findings.append("="*100)
        
        # Filing-by-Filing Analysis
        filings = analysis_data.get('filings_analyzed', [])
        
        for i, filing in enumerate(filings, 1):
            findings.append(f"\n{'─'*100}")
            findings.append(f"FILING #{i} - FORENSIC ANALYSIS")
            findings.append(f"{'─'*100}")
            
            findings.append(f"\nDocument Identification:")
            findings.append(f"  Accession Number: {filing.get('accession_number', 'N/A')}")
            findings.append(f"  Filing Date: {filing.get('filing_date', 'N/A')}")
            findings.append(f"  Form Type: {filing.get('form_type', 'N/A')}")
            findings.append(f"  Reporting Person: {filing.get('reporting_owner', 'N/A')}")
            
            # Transaction Summary
            transactions = filing.get('transactions', [])
            if transactions:
                findings.append(f"\nTransaction Summary:")
                findings.append(f"  Total Transactions: {len(transactions)}")
                
                # Group by type
                trans_by_code = {}
                for trans in transactions:
                    code = trans.get('transaction_code', 'Unknown')
                    trans_by_code[code] = trans_by_code.get(code, 0) + 1
                
                findings.append(f"  Transaction Breakdown:")
                for code, count in sorted(trans_by_code.items()):
                    code_name = self._get_transaction_code_name(code)
                    findings.append(f"    - Code {code} ({code_name}): {count} transaction(s)")
                
                # Share volumes
                total_shares = sum([self._parse_shares(t.get('shares', '0')) for t in transactions])
                if total_shares > 0:
                    findings.append(f"  Total Share Volume: {total_shares:,} shares")
            
            # Red Flags
            violations = filing.get('violations', [])
            if violations:
                findings.append(f"\n⚠️  VIOLATIONS DETECTED:")
                for v in violations:
                    findings.append(f"\n  Violation: {v.get('type', 'Unknown')}")
                    findings.append(f"    Citation: {v.get('citation', 'N/A')}")
                    findings.append(f"    Reason: {v.get('reason', 'N/A')}")
                    findings.append(f"    Confidence: {v.get('confidence', 0):.1%}")
            else:
                findings.append(f"\n✓ No violations detected in this filing")
        
        findings.append(f"\n{'='*100}")
        findings.append("END OF DETAILED FINDINGS")
        findings.append(f"{'='*100}\n")
        
        return '\n'.join(findings)
    
    def generate_statute_analysis(self, statute_refs: List[Dict]) -> str:
        """Generate comprehensive statute analysis"""
        
        analysis = []
        analysis.append("\n" + "="*100)
        analysis.append("LEGAL STATUTE ANALYSIS")
        analysis.append("="*100)
        
        if not statute_refs:
            analysis.append("\nNo statute violations detected.")
            return '\n'.join(analysis)
        
        # Group by priority
        by_priority = {}
        for statute in statute_refs:
            priority = statute.get('priority', 5)
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(statute)
        
        # Report by priority
        priority_names = {
            1: "CRITICAL - Immediate Action Required",
            2: "HIGH - Requires Prompt Investigation",
            3: "MODERATE - Monitor and Assess",
            4: "LOW - Document and Review",
            5: "INFORMATIONAL"
        }
        
        for priority in sorted(by_priority.keys()):
            statutes = by_priority[priority]
            
            analysis.append(f"\n{'─'*100}")
            analysis.append(f"PRIORITY {priority} - {priority_names.get(priority, 'Unknown')}")
            analysis.append(f"{'─'*100}")
            analysis.append(f"\nTotal Violations: {len(statutes)}")
            
            for i, statute in enumerate(statutes, 1):
                analysis.append(f"\n{i}. {statute.get('citation', 'Unknown Citation')}")
                analysis.append(f"   Violation: {statute.get('violation', 'N/A')}")
                analysis.append(f"   Description: {statute.get('description', 'N/A')}")
                
                if statute.get('criminal_penalty'):
                    analysis.append(f"   ⚖️  Criminal Penalty: {statute['criminal_penalty']}")
                
                if statute.get('civil_penalty'):
                    analysis.append(f"   💰 Civil Penalty: {statute['civil_penalty']}")
                
                if statute.get('reason'):
                    analysis.append(f"   Basis: {statute['reason']}")
                
                analysis.append(f"   Detection Confidence: {statute.get('confidence', 0):.1%}")
        
        analysis.append(f"\n{'='*100}")
        analysis.append("END OF STATUTE ANALYSIS")
        analysis.append(f"{'='*100}\n")
        
        return '\n'.join(analysis)
    
    def generate_recommendations(self, analysis_data: Dict) -> str:
        """Generate actionable recommendations"""
        
        recs = []
        recs.append("\n" + "="*100)
        recs.append("RECOMMENDATIONS & NEXT STEPS")
        recs.append("="*100)
        
        violations = analysis_data.get('total_violations', 0)
        risk_score = analysis_data.get('risk_score', 0)
        
        if violations == 0:
            recs.append("\n✓ No immediate action required based on current analysis.")
            recs.append("\nRecommended Monitoring:")
            recs.append("  1. Continue periodic review of future filings")
            recs.append("  2. Monitor for pattern changes")
            recs.append("  3. Maintain current compliance protocols")
        else:
            recs.append("\n⚠️  IMMEDIATE ACTIONS REQUIRED:")
            
            if risk_score > 0.7:
                recs.append("\n1. CRITICAL - Escalate to Enforcement Division")
                recs.append("   - Initiate formal investigation")
                recs.append("   - Preserve all evidence")
                recs.append("   - Consider emergency relief measures")
            
            if risk_score > 0.4:
                recs.append("\n2. HIGH PRIORITY - Conduct Deep Dive Investigation")
                recs.append("   - Request additional documentation")
                recs.append("   - Interview relevant parties")
                recs.append("   - Analyze historical filing patterns")
            
            recs.append("\n3. STANDARD - Document Evidence Chain")
            recs.append("   - Preserve chain of custody for all findings")
            recs.append("   - Compile supporting documentation")
            recs.append("   - Prepare enforcement recommendation memo")
            
            # Pattern-specific recommendations
            patterns = analysis_data.get('patterns_detected', [])
            if patterns:
                recs.append("\n4. PATTERN-SPECIFIC ACTIONS:")
                for pattern in patterns:
                    if pattern.get('recommendation'):
                        recs.append(f"   - {pattern['pattern']}: {pattern['recommendation']}")
        
        recs.append(f"\n{'='*100}")
        recs.append("END OF RECOMMENDATIONS")
        recs.append(f"{'='*100}\n")
        
        return '\n'.join(recs)
    
    def generate_complete_report(self, analysis_data: Dict, output_path: Path) -> Path:
        """Generate complete human-readable forensic report"""
        
        report = []
        
        # Title Page
        report.append("╔" + "═"*98 + "╗")
        report.append("║" + " "*98 + "║")
        report.append("║" + "FORENSIC AUDIT REPORT".center(98) + "║")
        report.append("║" + "SEC Filing Analysis".center(98) + "║")
        report.append("║" + " "*98 + "║")
        report.append("║" + f"Generated: {datetime.now().strftime('%B %d, %Y')}".center(98) + "║")
        report.append("║" + " "*98 + "║")
        report.append("╚" + "═"*98 + "╝")
        
        # Confidentiality Notice
        report.append("\n" + "="*100)
        report.append("CONFIDENTIAL - ATTORNEY WORK PRODUCT")
        report.append("="*100)
        report.append("\nThis report contains confidential information prepared in anticipation")
        report.append("of litigation and is protected by attorney-client privilege and")
        report.append("attorney work product doctrine. Unauthorized disclosure is prohibited.")
        report.append("="*100)
        
        # Assemble sections
        report.append(self.generate_executive_summary(analysis_data))
        report.append(self.generate_detailed_findings(analysis_data))
        report.append(self.generate_statute_analysis(analysis_data.get('statute_references', [])))
        report.append(self.generate_recommendations(analysis_data))
        
        # Appendices
        report.append("\n" + "="*100)
        report.append("APPENDICES")
        report.append("="*100)
        report.append("\nAppendix A: Raw Data Export (JSON) - See accompanying file")
        report.append("Appendix B: Visual Analytics - See accompanying graphics")
        report.append("Appendix C: Chain of Custody Documentation - See evidence log")
        report.append("Appendix D: Statute Reference Materials - See legal database")
        
        # Footer
        report.append("\n" + "="*100)
        report.append("END OF FORENSIC AUDIT REPORT")
        report.append("="*100)
        report.append(f"\nReport ID: {analysis_data.get('report_id', 'N/A')}")
        report.append(f"Generated By: JARVIS:LAW Black Site Protocol v2.0")
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        
        # Write to file
        report_content = '\n'.join(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_path
    
    # Helper methods
    
    def _risk_level(self, score: float) -> str:
        """Convert risk score to human label"""
        if score >= 0.7:
            return "CRITICAL"
        elif score >= 0.5:
            return "HIGH"
        elif score >= 0.3:
            return "MODERATE"
        elif score >= 0.1:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _parse_penalty_years(self, penalty: str) -> int:
        """Extract maximum years from penalty string"""
        import re
        matches = re.findall(r'(\d+)\s*years?', penalty.lower())
        return max([int(m) for m in matches]) if matches else 0
    
    def _parse_shares(self, shares_str: str) -> int:
        """Parse share count from string"""
        try:
            # Remove commas and convert
            clean = str(shares_str).replace(',', '').strip()
            return int(float(clean))
        except:
            return 0
    
    def _get_transaction_code_name(self, code: str) -> str:
        """Get human-readable name for transaction code"""
        codes = {
            'P': 'Purchase',
            'S': 'Sale',
            'A': 'Award/Grant',
            'D': 'Disposition',
            'F': 'Tax Withholding',
            'I': 'Discretionary',
            'M': 'Option Exercise',
            'X': 'Exercise',
            'G': 'Gift',
            'J': 'Other'
        }
        return codes.get(code, 'Unknown')


# Export
__all__ = ['ForensicReportGenerator']

