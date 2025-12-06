"""
COMPREHENSIVE DUAL-AGENT INVESTIGATION TEST
===========================================

Tests the enhanced dual-agent system against the PDF baseline requirements:
1. OpenAI performs initial violation detection
2. Anthropic cross-references with GovInfo API for complete statute correlation
3. System catches ALL violations shown in the PDF report minimum baseline
4. Nothing is missed through dual-pass validation

PDF Baseline Requirements (Nike 2019 Analysis):
- Late Form 4 filings detection
- Zero-dollar transaction identification
- SOX certification deficiencies
- Revenue recognition irregularities
- Material misstatement detection
- Complete statute correlation with full legal text
- Prosecutorial merit assessment
- Estimated damages calculation
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DualAgentInvestigationTest:
    """Test harness for dual-agent investigation system."""
    
    def __init__(self):
        """Initialize test harness."""
        self.results: List[Dict[str, Any]] = []
        self.coordinator = None
    
    async def setup(self):
        """Setup test environment."""
        logger.info("=" * 80)
        logger.info("DUAL-AGENT INVESTIGATION SYSTEM - COMPREHENSIVE TEST")
        logger.info("=" * 80)
        
        try:
            from src.forensics.dual_agent import DualAgentCoordinator
            self.coordinator = DualAgentCoordinator()
            
            availability = self.coordinator.availability()
            logger.info(f"✅ System initialized")
            logger.info(f"   - OpenAI: {availability['openai']}")
            logger.info(f"   - Anthropic: {availability['anthropic']}")
            logger.info(f"   - GovInfo: {availability['govinfo']}")
            
            if not availability['openai']:
                logger.warning("⚠️ OpenAI not available - set OPENAI_API_KEY")
            if not availability['anthropic']:
                logger.warning("⚠️ Anthropic not available - set ANTHROPIC_API_KEY")
            if not availability['govinfo']:
                logger.warning("⚠️ GovInfo not available - set GOVINFO_API_KEY")
            
            return availability['openai'] and availability['anthropic']
        
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def test_late_form4_detection(self) -> Dict[str, Any]:
        """
        Test detection of late Form 4 filings.
        
        PDF Baseline: Must detect filings >2 business days late
        """
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Late Form 4 Filing Detection")
        logger.info("=" * 80)
        
        # Sample Form 4 with late filing
        sample_form4 = """
        <ownershipDocument>
            <issuer>
                <issuerCik>0000320187</issuerCik>
                <issuerName>NIKE INC</issuerName>
                <issuerTradingSymbol>NKE</issuerTradingSymbol>
            </issuer>
            <reportingOwner>
                <reportingOwnerId>
                    <rptOwnerCik>0001234567</rptOwnerCik>
                    <rptOwnerName>DOE JOHN</rptOwnerName>
                </reportingOwnerId>
                <reportingOwnerRelationship>
                    <isDirector>1</isDirector>
                    <isOfficer>1</isOfficer>
                    <officerTitle>Chief Executive Officer</officerTitle>
                </reportingOwnerRelationship>
            </reportingOwner>
            <nonDerivativeTable>
                <nonDerivativeTransaction>
                    <securityTitle>
                        <value>Class B Common Stock</value>
                    </securityTitle>
                    <transactionDate>
                        <value>2019-03-15</value>
                    </transactionDate>
                    <transactionCoding>
                        <transactionCode>S</transactionCode>
                    </transactionCoding>
                    <transactionAmounts>
                        <transactionShares>
                            <value>50000</value>
                        </transactionShares>
                        <transactionPricePerShare>
                            <value>85.50</value>
                        </transactionPricePerShare>
                        <transactionAcquiredDisposedCode>
                            <value>D</value>
                        </transactionAcquiredDisposedCode>
                    </transactionAmounts>
                </nonDerivativeTransaction>
            </nonDerivativeTable>
        </ownershipDocument>
        """
        
        filing_metadata = {
            "filing_type": "4",
            "document_url": "https://www.sec.gov/Archives/edgar/data/320187/0001234567-19-000123.xml",
            "filing_date": "2019-03-25",  # 6 business days after transaction (LATE)
            "cik": "0000320187",
            "company_name": "NIKE INC",
        }
        
        try:
            result = await self.coordinator.investigate_with_cross_reference(
                content=sample_form4,
                filing_metadata=filing_metadata,
                enable_govinfo_enrichment=True
            )
            
            self._print_investigation_result(result, "Late Form 4 Detection")
            self.results.append({
                "test": "late_form4_detection",
                "status": result.get("status"),
                "violations_found": len(result.get("merged_violations", [])),
                "result": result
            })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def test_zero_dollar_transaction(self) -> Dict[str, Any]:
        """
        Test detection of zero-dollar transactions (gifts, RSU vesting).
        
        PDF Baseline: Must detect and flag zero-price transactions
        """
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Zero-Dollar Transaction Detection")
        logger.info("=" * 80)
        
        sample_form4 = """
        <ownershipDocument>
            <issuer>
                <issuerCik>0000320187</issuerCik>
                <issuerName>NIKE INC</issuerName>
            </issuer>
            <reportingOwner>
                <reportingOwnerId>
                    <rptOwnerName>SMITH JANE</rptOwnerName>
                </reportingOwnerId>
            </reportingOwner>
            <nonDerivativeTable>
                <nonDerivativeTransaction>
                    <securityTitle>
                        <value>Class B Common Stock</value>
                    </securityTitle>
                    <transactionDate>
                        <value>2019-06-01</value>
                    </transactionDate>
                    <transactionCoding>
                        <transactionCode>A</transactionCode>
                    </transactionCoding>
                    <transactionAmounts>
                        <transactionShares>
                            <value>10000</value>
                        </transactionShares>
                        <transactionPricePerShare>
                            <value>0.00</value>
                        </transactionPricePerShare>
                        <transactionAcquiredDisposedCode>
                            <value>A</value>
                        </transactionAcquiredDisposedCode>
                    </transactionAmounts>
                </nonDerivativeTransaction>
            </nonDerivativeTable>
        </ownershipDocument>
        """
        
        filing_metadata = {
            "filing_type": "4",
            "document_url": "https://www.sec.gov/Archives/edgar/data/320187/0001234567-19-000456.xml",
            "filing_date": "2019-06-03",
            "cik": "0000320187",
            "company_name": "NIKE INC",
        }
        
        try:
            result = await self.coordinator.investigate_with_cross_reference(
                content=sample_form4,
                filing_metadata=filing_metadata,
                enable_govinfo_enrichment=True
            )
            
            self._print_investigation_result(result, "Zero-Dollar Transaction Detection")
            self.results.append({
                "test": "zero_dollar_transaction",
                "status": result.get("status"),
                "violations_found": len(result.get("merged_violations", [])),
                "result": result
            })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def test_material_misstatement(self) -> Dict[str, Any]:
        """
        Test detection of material misstatements in 10-K/10-Q filings.
        
        PDF Baseline: Must detect revenue recognition issues and accounting irregularities
        """
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Material Misstatement Detection")
        logger.info("=" * 80)
        
        sample_10k = """
        MANAGEMENT'S DISCUSSION AND ANALYSIS
        
        Revenue Recognition:
        The Company recognized revenue of $39.1 billion for fiscal year 2019, 
        representing a 15% increase year-over-year. This growth was primarily 
        driven by strong performance in our North America segment.
        
        However, subsequent analysis revealed that $500 million in revenue 
        was recognized prematurely due to channel stuffing practices where 
        products were shipped to distributors prior to actual customer orders.
        
        Additionally, the Company failed to properly disclose related party 
        transactions totaling $75 million with entities controlled by executive 
        management.
        
        SOX CERTIFICATIONS:
        The CEO and CFO have certified that internal controls over financial 
        reporting were effective as of May 31, 2019. However, material 
        weaknesses were subsequently identified in the revenue recognition 
        process that were not disclosed in the original certification.
        """
        
        filing_metadata = {
            "filing_type": "10-K",
            "document_url": "https://www.sec.gov/Archives/edgar/data/320187/000032018719000029/nke-20190531.htm",
            "filing_date": "2019-07-25",
            "cik": "0000320187",
            "company_name": "NIKE INC",
        }
        
        try:
            result = await self.coordinator.investigate_with_cross_reference(
                content=sample_10k,
                filing_metadata=filing_metadata,
                enable_govinfo_enrichment=True
            )
            
            self._print_investigation_result(result, "Material Misstatement Detection")
            self.results.append({
                "test": "material_misstatement",
                "status": result.get("status"),
                "violations_found": len(result.get("merged_violations", [])),
                "result": result
            })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def _print_investigation_result(self, result: Dict[str, Any], test_name: str):
        """Print formatted investigation results."""
        logger.info("\n" + "-" * 80)
        logger.info(f"INVESTIGATION RESULTS: {test_name}")
        logger.info("-" * 80)
        
        status = result.get("status", "UNKNOWN")
        logger.info(f"Status: {status}")
        
        summary = result.get("investigation_summary", {})
        logger.info(f"\nSummary:")
        logger.info(f"  Total Violations: {summary.get('total_violations_detected', 0)}")
        logger.info(f"  OpenAI Detected: {summary.get('openai_initial_count', 0)}")
        logger.info(f"  Anthropic Cross-Referenced: {summary.get('anthropic_cross_reference_count', 0)}")
        logger.info(f"  Overlap: {summary.get('overlap_count', 0)}")
        logger.info(f"  Confidence: {summary.get('confidence_level', 0):.2%}")
        logger.info(f"  Statutes Correlated: {summary.get('statutes_correlated', 0)}")
        logger.info(f"  Regulations Correlated: {summary.get('regulations_correlated', 0)}")
        logger.info(f"  Nothing Missed: {summary.get('nothing_missed_validation', False)}")
        
        # Print violations
        violations = result.get("merged_violations", [])
        if violations:
            logger.info(f"\nViolations Detected:")
            for i, v in enumerate(violations, 1):
                logger.info(f"  {i}. {v.get('type', 'UNKNOWN')}")
                logger.info(f"     Statute: {v.get('statute', 'N/A')}")
                logger.info(f"     Severity: {v.get('severity', 'N/A')}")
                logger.info(f"     Source: {v.get('_source', 'N/A')}")
                logger.info(f"     Confirmed By: {v.get('_confirmed_by', [])}")
                
                # Print legal framework if available
                legal_framework = v.get("legal_framework", {})
                if legal_framework:
                    primary_statute = legal_framework.get("primary_statute", {})
                    logger.info(f"     Legal Framework:")
                    logger.info(f"       Primary: {primary_statute.get('citation', 'N/A')}")
                    logger.info(f"       Summary: {primary_statute.get('summary', 'N/A')}")
                    logger.info(f"       Penalties: {primary_statute.get('penalties', {})}")
                    logger.info(f"       GovInfo: {primary_statute.get('govinfo_url', 'N/A')}")
                    
                    related = legal_framework.get("related_statutes", [])
                    if related:
                        logger.info(f"       Related Statutes: {len(related)}")
                    
                    cfr = legal_framework.get("cfr_regulations", [])
                    if cfr:
                        logger.info(f"       CFR Regulations: {len(cfr)}")
        
        logger.info("-" * 80)
    
    async def generate_summary_report(self):
        """Generate final summary report."""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL TEST SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["status"] == "COMPLETE")
        total_violations = sum(r["violations_found"] for r in self.results)
        
        logger.info(f"\nTests Run: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {total_tests - successful_tests}")
        logger.info(f"Total Violations Detected: {total_violations}")
        
        logger.info(f"\nTest Results:")
        for result in self.results:
            status_icon = "✅" if result["status"] == "COMPLETE" else "❌"
            logger.info(f"  {status_icon} {result['test']}: {result['violations_found']} violations")
        
        # Save results to file
        output_dir = Path("forensic_reports")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"dual_agent_test_results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "total_violations": total_violations,
                },
                "tests": self.results,
            }, f, indent=2, default=str)
        
        logger.info(f"\n✅ Results saved to: {output_file}")
        
        logger.info("\n" + "=" * 80)
        logger.info("PDF BASELINE COMPLIANCE CHECK")
        logger.info("=" * 80)
        
        # Check against PDF baseline requirements
        baseline_checks = {
            "Late Form 4 Detection": any(r["test"] == "late_form4_detection" and r["violations_found"] > 0 for r in self.results),
            "Zero-Dollar Transaction Detection": any(r["test"] == "zero_dollar_transaction" and r["violations_found"] > 0 for r in self.results),
            "Material Misstatement Detection": any(r["test"] == "material_misstatement" and r["violations_found"] > 0 for r in self.results),
            "Dual-Agent Cross-Reference": all(r["status"] == "COMPLETE" for r in self.results),
            "GovInfo Statute Correlation": total_violations > 0,
        }
        
        for check, passed in baseline_checks.items():
            icon = "✅" if passed else "❌"
            logger.info(f"{icon} {check}")
        
        all_passed = all(baseline_checks.values())
        if all_passed:
            logger.info("\n🎉 ALL PDF BASELINE REQUIREMENTS MET")
        else:
            logger.info("\n⚠️ Some baseline requirements not met - review configuration")
        
        logger.info("=" * 80)
    
    async def run_all_tests(self):
        """Run all tests."""
        if not await self.setup():
            logger.error("❌ Setup failed - ensure API keys are configured")
            return
        
        try:
            # Run all test cases
            await self.test_late_form4_detection()
            await asyncio.sleep(1)  # Rate limiting
            
            await self.test_zero_dollar_transaction()
            await asyncio.sleep(1)
            
            await self.test_material_misstatement()
            
            # Generate summary
            await self.generate_summary_report()
        
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
        
        finally:
            if self.coordinator:
                await self.coordinator.close()


async def main():
    """Main entry point."""
    test_harness = DualAgentInvestigationTest()
    await test_harness.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

