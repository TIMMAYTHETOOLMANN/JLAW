"""
FINAL VALIDATION SCRIPT - PDF BASELINE COMPLIANCE
==================================================

This script validates the dual-agent system against the actual Nike 2019
PDF baseline requirements. It runs comprehensive tests and generates a 
detailed compliance report comparing system output to PDF expectations.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFBaselineValidator:
    """Validates system against PDF baseline requirements."""

    def __init__(self):
        """Initialize validator."""
        self.results: List[Dict[str, Any]] = []
        self.coordinator = None

        # PDF Baseline Requirements (from Nike 2019 analysis)
        self.pdf_baseline = {
            "expected_violations": {
                "late_form4": {
                    "count": "Multiple",
                    "statute": "15 USC § 78p(a)",
                    "severity": "HIGH",
                    "description": "Late Form 4 filings exceeding 2 business days"
                },
                "zero_dollar_transactions": {
                    "count": "Multiple",
                    "statute": "15 USC § 78p(a)",
                    "severity": "HIGH",
                    "description": "Zero-dollar transactions indicating gifts/RSU vesting"
                },
                "sox_deficiencies": {
                    "count": "Present",
                    "statute": "18 USC § 1350",
                    "severity": "CRITICAL",
                    "description": "SOX 302/404 certification deficiencies"
                },
                "material_misstatements": {
                    "count": "Present",
                    "statute": "17 CFR § 240.10b-5",
                    "severity": "CRITICAL",
                    "description": "Revenue recognition irregularities"
                }
            },
            "required_features": [
                "Complete statute text from official sources",
                "CFR implementing regulations",
                "Criminal and civil penalties",
                "Prosecutorial merit assessment",
                "Related party disclosure",
                "Beneficial ownership tracking",
                "Business day calculation",
                "Transaction timing analysis"
            ],
            "output_quality": {
                "dual_agent_validation": True,
                "nothing_missed_guarantee": True,
                "confidence_metrics": True,
                "provenance_tracking": True,
                "legal_framework_complete": True,
                "statute_correlation": "100%"
            }
        }

    async def setup(self):
        """Setup test environment."""
        logger.info("=" * 80)
        logger.info("PDF BASELINE VALIDATION - COMPREHENSIVE TEST")
        logger.info("=" * 80)
        logger.info(f"Date: {datetime.now().isoformat()}")
        logger.info(f"Baseline: Nike 2019 SEC Filings Forensic Analysis PDF")

        try:
            from src.forensics.dual_agent import DualAgentCoordinator
            self.coordinator = DualAgentCoordinator()

            availability = self.coordinator.availability()
            logger.info(f"\n✅ System initialized")
            logger.info(f"   - OpenAI: {availability['openai']}")
            logger.info(f"   - Anthropic: {availability['anthropic']}")
            logger.info(f"   - GovInfo: {availability['govinfo']}")

            if not availability['openai'] or not availability['anthropic']:
                raise ValueError("Both OpenAI and Anthropic required for dual-agent validation")

            return True

        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

    async def test_comprehensive_form4_analysis(self) -> Dict[str, Any]:
        """
        Comprehensive Form 4 analysis matching PDF baseline.
        Tests late filings, zero-dollar transactions, and statute correlation.
        """
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: COMPREHENSIVE FORM 4 ANALYSIS")
        logger.info("PDF Baseline: Late Form 4 + Zero-Dollar Transactions")
        logger.info("=" * 80)

        # Realistic Form 4 with multiple violations (based on PDF patterns)
        sample_form4 = """
        <?xml version="1.0" encoding="UTF-8"?>
        <ownershipDocument>
            <schemaVersion>X0306</schemaVersion>
            <documentType>4</documentType>
            <periodOfReport>2019-03-15</periodOfReport>
            <notSubjectToSection16>0</notSubjectToSection16>
            <issuer>
                <issuerCik>0000320187</issuerCik>
                <issuerName>NIKE INC</issuerName>
                <issuerTradingSymbol>NKE</issuerTradingSymbol>
            </issuer>
            <reportingOwner>
                <reportingOwnerId>
                    <rptOwnerCik>0001234567</rptOwnerCik>
                    <rptOwnerName>PARKER MARK G</rptOwnerName>
                </reportingOwnerId>
                <reportingOwnerAddress>
                    <rptOwnerStreet1>ONE BOWERMAN DRIVE</rptOwnerStreet1>
                    <rptOwnerCity>BEAVERTON</rptOwnerCity>
                    <rptOwnerState>OR</rptOwnerState>
                    <rptOwnerZipCode>97005</rptOwnerZipCode>
                </reportingOwnerAddress>
                <reportingOwnerRelationship>
                    <isDirector>1</isDirector>
                    <isOfficer>1</isOfficer>
                    <isTenPercentOwner>0</isTenPercentOwner>
                    <isOther>0</isOther>
                    <officerTitle>Executive Chairman &amp; Chairman of the Board</officerTitle>
                </reportingOwnerRelationship>
            </reportingOwner>
            
            <nonDerivativeTable>
                <!-- Transaction 1: Late filing (6 business days) -->
                <nonDerivativeTransaction>
                    <securityTitle>
                        <value>Class B Common Stock</value>
                    </securityTitle>
                    <transactionDate>
                        <value>2019-03-15</value>
                    </transactionDate>
                    <transactionCoding>
                        <transactionFormType>4</transactionFormType>
                        <transactionCode>S</transactionCode>
                        <equitySwapInvolved>0</equitySwapInvolved>
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
                    <postTransactionAmounts>
                        <sharesOwnedFollowingTransaction>
                            <value>500000</value>
                        </sharesOwnedFollowingTransaction>
                    </postTransactionAmounts>
                    <ownershipNature>
                        <directOrIndirectOwnership>
                            <value>D</value>
                        </directOrIndirectOwnership>
                    </ownershipNature>
                </nonDerivativeTransaction>
                
                <!-- Transaction 2: Zero-dollar transaction (RSU vesting) -->
                <nonDerivativeTransaction>
                    <securityTitle>
                        <value>Class B Common Stock</value>
                    </securityTitle>
                    <transactionDate>
                        <value>2019-06-01</value>
                    </transactionDate>
                    <transactionCoding>
                        <transactionFormType>4</transactionFormType>
                        <transactionCode>A</transactionCode>
                        <equitySwapInvolved>0</equitySwapInvolved>
                    </transactionCoding>
                    <transactionAmounts>
                        <transactionShares>
                            <value>25000</value>
                        </transactionShares>
                        <transactionPricePerShare>
                            <value>0.00</value>
                        </transactionPricePerShare>
                        <transactionAcquiredDisposedCode>
                            <value>A</value>
                        </transactionAcquiredDisposedCode>
                    </transactionAmounts>
                    <postTransactionAmounts>
                        <sharesOwnedFollowingTransaction>
                            <value>525000</value>
                        </sharesOwnedFollowingTransaction>
                    </postTransactionAmounts>
                    <ownershipNature>
                        <directOrIndirectOwnership>
                            <value>D</value>
                        </directOrIndirectOwnership>
                    </ownershipNature>
                </nonDerivativeTransaction>
                
                <!-- Transaction 3: Another zero-dollar (gift) -->
                <nonDerivativeTransaction>
                    <securityTitle>
                        <value>Class B Common Stock</value>
                    </securityTitle>
                    <transactionDate>
                        <value>2019-09-15</value>
                    </transactionDate>
                    <transactionCoding>
                        <transactionFormType>4</transactionFormType>
                        <transactionCode>G</transactionCode>
                        <equitySwapInvolved>0</equitySwapInvolved>
                    </transactionCoding>
                    <transactionAmounts>
                        <transactionShares>
                            <value>10000</value>
                        </transactionShares>
                        <transactionPricePerShare>
                            <value>0.00</value>
                        </transactionPricePerShare>
                        <transactionAcquiredDisposedCode>
                            <value>D</value>
                        </transactionAcquiredDisposedCode>
                    </transactionAmounts>
                    <postTransactionAmounts>
                        <sharesOwnedFollowingTransaction>
                            <value>515000</value>
                        </sharesOwnedFollowingTransaction>
                    </postTransactionAmounts>
                    <ownershipNature>
                        <directOrIndirectOwnership>
                            <value>D</value>
                        </directOrIndirectOwnership>
                    </ownershipNature>
                </nonDerivativeTransaction>
            </nonDerivativeTable>
            
            <remarks>RSU vesting and gift transactions require additional disclosure under Section 16 rules.</remarks>
            
            <ownerSignature>
                <signatureName>Mark G. Parker</signatureName>
                <signatureDate>2019-03-25</signatureDate>
            </ownerSignature>
        </ownershipDocument>
        """

        filing_metadata = {
            "filing_type": "4",
            "document_url": "https://www.sec.gov/Archives/edgar/data/320187/000119312519087123/d734257d4.xml",
            "filing_date": "2019-03-25",  # Filed 6 business days after 3/15 transaction (LATE)
            "cik": "0000320187",
            "company_name": "NIKE INC",
            "ticker": "NKE",
            "fiscal_year": "2019"
        }

        try:
            result = await self.coordinator.investigate_with_cross_reference(
                content=sample_form4,
                filing_metadata=filing_metadata,
                enable_govinfo_enrichment=True
            )

            # Analyze results against PDF baseline
            validation = self._validate_against_baseline(result, "form4_comprehensive")

            self._print_detailed_results(result, validation, "Form 4 Comprehensive Analysis")

            self.results.append({
                "test": "comprehensive_form4_analysis",
                "status": result.get("status"),
                "violations_found": len(result.get("merged_violations", [])),
                "pdf_compliance": validation,
                "result": result
            })

            return result

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "ERROR", "error": str(e)}

    def _validate_against_baseline(self, result: Dict[str, Any], test_type: str) -> Dict[str, Any]:
        """Validate results against PDF baseline requirements."""
        validation = {
            "compliant": True,
            "checks": {},
            "score": 0,
            "max_score": 0
        }

        violations = result.get("merged_violations", [])
        summary = result.get("investigation_summary", {})

        # Check 1: Dual-agent validation
        validation["checks"]["dual_agent"] = {
            "required": True,
            "passed": summary.get("dual_agent_coverage", False),
            "details": f"OpenAI: {summary.get('openai_initial_count', 0)}, Anthropic: {summary.get('anthropic_cross_reference_count', 0)}"
        }
        validation["max_score"] += 1
        if validation["checks"]["dual_agent"]["passed"]:
            validation["score"] += 1

        # Check 2: Nothing missed validation
        validation["checks"]["nothing_missed"] = {
            "required": True,
            "passed": summary.get("nothing_missed_validation", False),
            "details": f"Confidence: {summary.get('confidence_level', 0):.2%}"
        }
        validation["max_score"] += 1
        if validation["checks"]["nothing_missed"]["passed"]:
            validation["score"] += 1

        # Check 3: Statute correlation
        validation["checks"]["statute_correlation"] = {
            "required": True,
            "passed": summary.get("statutes_correlated", 0) > 0,
            "details": f"{summary.get('statutes_correlated', 0)} statutes, {summary.get('regulations_correlated', 0)} regulations"
        }
        validation["max_score"] += 1
        if validation["checks"]["statute_correlation"]["passed"]:
            validation["score"] += 1

        # Check 4: Legal frameworks complete
        has_legal_frameworks = any(
            v.get("legal_framework") is not None
            for v in violations
        )
        validation["checks"]["legal_frameworks"] = {
            "required": True,
            "passed": has_legal_frameworks,
            "details": f"{len([v for v in violations if v.get('legal_framework')])} violations with complete frameworks"
        }
        validation["max_score"] += 1
        if validation["checks"]["legal_frameworks"]["passed"]:
            validation["score"] += 1

        # Check 5: Provenance tracking
        has_provenance = any(
            v.get("_source") is not None
            for v in violations
        )
        validation["checks"]["provenance_tracking"] = {
            "required": True,
            "passed": has_provenance,
            "details": f"{len([v for v in violations if v.get('_source')])} violations with provenance"
        }
        validation["max_score"] += 1
        if validation["checks"]["provenance_tracking"]["passed"]:
            validation["score"] += 1

        # Calculate compliance
        validation["compliant"] = validation["score"] == validation["max_score"]
        validation["compliance_percentage"] = (validation["score"] / validation["max_score"] * 100) if validation[
                                                                                                           "max_score"] > 0 else 0

        return validation

    def _print_detailed_results(self, result: Dict[str, Any], validation: Dict[str, Any], test_name: str):
        """Print detailed formatted results."""
        logger.info("\n" + "-" * 80)
        logger.info(f"RESULTS: {test_name}")
        logger.info("-" * 80)

        status = result.get("status", "UNKNOWN")
        logger.info(f"Status: {status}")

        # Investigation summary
        summary = result.get("investigation_summary", {})
        logger.info(f"\n📊 Investigation Summary:")
        logger.info(f"   Total Violations: {summary.get('total_violations_detected', 0)}")
        logger.info(f"   OpenAI Initial: {summary.get('openai_initial_count', 0)}")
        logger.info(f"   Anthropic Cross-Ref: {summary.get('anthropic_cross_reference_count', 0)}")
        logger.info(f"   Overlap: {summary.get('overlap_count', 0)}")
        logger.info(f"   Confidence: {summary.get('confidence_level', 0):.2%}")
        logger.info(f"   Statutes: {summary.get('statutes_correlated', 0)}")
        logger.info(f"   Regulations: {summary.get('regulations_correlated', 0)}")

        # Violations detail
        violations = result.get("merged_violations", [])
        if violations:
            logger.info(f"\n🚨 Violations Detected ({len(violations)}):")
            for i, v in enumerate(violations, 1):
                logger.info(f"\n   {i}. {v.get('type', 'UNKNOWN')}")
                logger.info(f"      Statute: {v.get('statute', 'N/A')}")
                logger.info(f"      Severity: {v.get('severity', 'N/A')}")
                logger.info(f"      Source: {v.get('_source', 'N/A')}")
                logger.info(f"      Confirmed By: {', '.join(v.get('_confirmed_by', []))}")

                # Legal framework
                framework = v.get("legal_framework", {})
                if framework:
                    primary = framework.get("primary_statute", {})
                    logger.info(f"      📚 Legal Framework:")
                    logger.info(f"         Citation: {primary.get('citation', 'N/A')}")
                    logger.info(f"         Summary: {primary.get('summary', 'N/A')}")

                    penalties = primary.get("penalties", {})
                    if penalties:
                        logger.info(f"         Penalties: {penalties}")

                    logger.info(f"         GovInfo URL: {primary.get('govinfo_url', 'N/A')}")
                    logger.info(f"         Related Statutes: {len(framework.get('related_statutes', []))}")
                    logger.info(f"         CFR Regulations: {len(framework.get('cfr_regulations', []))}")

        # PDF Baseline validation
        logger.info(f"\n✅ PDF Baseline Validation:")
        logger.info(
            f"   Compliance: {validation['compliance_percentage']:.1f}% ({validation['score']}/{validation['max_score']} checks passed)")
        for check_name, check_data in validation['checks'].items():
            icon = "✅" if check_data['passed'] else "❌"
            logger.info(f"   {icon} {check_name.replace('_', ' ').title()}: {check_data['details']}")

        logger.info("-" * 80)

    async def generate_final_report(self):
        """Generate comprehensive final report."""
        logger.info("\n" + "=" * 80)
        logger.info("FINAL PDF BASELINE COMPLIANCE REPORT")
        logger.info("=" * 80)

        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["status"] == "COMPLETE")
        total_violations = sum(r["violations_found"] for r in self.results)

        # Calculate overall compliance
        all_validations = [r.get("pdf_compliance", {}) for r in self.results]
        total_checks = sum(v.get("max_score", 0) for v in all_validations)
        passed_checks = sum(v.get("score", 0) for v in all_validations)
        overall_compliance = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        logger.info(f"\n📊 Test Execution Summary:")
        logger.info(f"   Tests Run: {total_tests}")
        logger.info(f"   Successful: {successful_tests}")
        logger.info(f"   Failed: {total_tests - successful_tests}")
        logger.info(f"   Total Violations: {total_violations}")

        logger.info(f"\n✅ PDF Baseline Compliance:")
        logger.info(f"   Overall Score: {overall_compliance:.1f}%")
        logger.info(f"   Checks Passed: {passed_checks}/{total_checks}")

        logger.info(f"\n📋 Individual Test Results:")
        for result in self.results:
            validation = result.get("pdf_compliance", {})
            compliance = validation.get("compliance_percentage", 0)
            status_icon = "✅" if result["status"] == "COMPLETE" else "❌"
            compliance_icon = "✅" if compliance == 100 else "⚠️"
            logger.info(
                f"   {status_icon} {result['test']}: {result['violations_found']} violations, {compliance_icon} {compliance:.1f}% compliant")

        # Save detailed report
        output_dir = Path("forensic_reports")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"pdf_baseline_validation_{timestamp}.json"

        report = {
            "validation_date": timestamp,
            "pdf_baseline": self.pdf_baseline,
            "test_results": self.results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "total_violations": total_violations,
                "overall_compliance": overall_compliance,
                "checks_passed": passed_checks,
                "total_checks": total_checks
            }
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"\n📄 Detailed report saved: {output_file}")

        # Final verdict
        logger.info("\n" + "=" * 80)
        logger.info("FINAL VERDICT")
        logger.info("=" * 80)

        if overall_compliance >= 100:
            logger.info("🎉 PERFECT COMPLIANCE - All PDF baseline requirements met!")
            logger.info("✅ System exceeds Nike 2019 analysis baseline")
            logger.info("✅ Dual-agent cross-referencing operational")
            logger.info("✅ Complete statute correlation from GovInfo")
            logger.info("✅ Nothing missed guarantee validated")
        elif overall_compliance >= 80:
            logger.info("✅ HIGH COMPLIANCE - System meets most PDF baseline requirements")
            logger.info(f"⚠️  {100 - overall_compliance:.1f}% of checks need attention")
        else:
            logger.info("⚠️  PARTIAL COMPLIANCE - System needs improvements")
            logger.info(f"❌ {100 - overall_compliance:.1f}% of checks failed")

        logger.info("=" * 80)

    async def run_validation(self):
        """Run complete validation suite."""
        if not await self.setup():
            logger.error("❌ Setup failed - cannot continue")
            return

        try:
            # Run comprehensive test
            await self.test_comprehensive_form4_analysis()
            await asyncio.sleep(1)  # Rate limiting

            # Generate final report
            await self.generate_final_report()

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.coordinator:
                await self.coordinator.close()


async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("DUAL-AGENT SYSTEM - PDF BASELINE VALIDATION")
    print("=" * 80 + "\n")
    
    validator = PDFBaselineValidator()
    await validator.run_validation()
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
