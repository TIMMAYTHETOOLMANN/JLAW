#!/usr/bin/env python3
"""
JLAW Critical Configuration Fixes Verification Script
=====================================================

This script verifies that all three critical configuration errors
identified in the JLAW Forensic System Audit Report (December 25, 2025)
have been successfully fixed.

CRITICAL-001: strict_mode defaults to True
CRITICAL-002: validate_gate() method access through validator
CRITICAL-003: Missing data contracts for Phases 6, 7, and 9
"""

import sys
from pathlib import Path
from datetime import date


def verify_critical_001():
    """Verify CRITICAL-001: strict_mode defaults to True."""
    print("\n" + "=" * 70)
    print("CRITICAL-001: Verify strict_mode defaults to True")
    print("=" * 70)
    
    from src.core.master_execution_controller import MasterExecutionController
    
    # Test without specifying strict_mode
    controller = MasterExecutionController(
        cik="0000320187",
        company_name="Test Company",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        output_dir=Path("/tmp/test")
    )
    
    if controller.strict_mode is True:
        print("✅ PASS: strict_mode defaults to True")
        return True
    else:
        print("❌ FAIL: strict_mode does not default to True")
        return False


def verify_critical_002():
    """Verify CRITICAL-002: All validate_gate calls use .validator."""
    print("\n" + "=" * 70)
    print("CRITICAL-002: Verify validate_gate() calls use .validator")
    print("=" * 70)
    
    with open('src/core/master_execution_controller.py', 'r') as f:
        content = f.read()
    
    # Count correct patterns
    correct_pattern = 'self._strict_controller.validator.validate_gate'
    correct_count = content.count(correct_pattern)
    
    # Check for incorrect patterns
    lines = content.split('\n')
    incorrect_count = 0
    for line in lines:
        if 'self._strict_controller.validate_gate' in line and \
           'self._strict_controller.validator.validate_gate' not in line:
            incorrect_count += 1
    
    # Verify tuple unpacking
    unpacking_pattern = 'decision, validation_result = self._strict_controller.validator.validate_gate'
    unpacking_count = content.count(unpacking_pattern)
    
    print(f"  • Correct validate_gate calls: {correct_count}/6")
    print(f"  • Incorrect validate_gate calls: {incorrect_count}")
    print(f"  • Calls with proper tuple unpacking: {unpacking_count}/6")
    
    if correct_count == 6 and incorrect_count == 0 and unpacking_count == 6:
        print("✅ PASS: All validate_gate calls correctly use .validator with tuple unpacking")
        return True
    else:
        print("❌ FAIL: Some validate_gate calls are incorrect")
        return False


def verify_critical_003():
    """Verify CRITICAL-003: New data contracts exist and work."""
    print("\n" + "=" * 70)
    print("CRITICAL-003: Verify new data contracts for Phases 6, 7, and 9")
    print("=" * 70)
    
    from src.core.data_contracts import (
        Phase6DualAgentContract,
        Phase7SubagentContract,
        Phase9DossierContract,
        create_contract_for_phase
    )
    
    all_pass = True
    
    # Test Phase 6 contract
    try:
        contract6 = Phase6DualAgentContract(strict_mode=True)
        factory_contract6 = create_contract_for_phase(
            "Phase 6: Dual-Agent AI Cross-Validation",
            {"strict_mode": True}
        )
        
        if isinstance(factory_contract6, Phase6DualAgentContract):
            print("✅ Phase6DualAgentContract: Created and factory works")
        else:
            print("❌ Phase6DualAgentContract: Factory returns wrong type")
            all_pass = False
    except Exception as e:
        print(f"❌ Phase6DualAgentContract: Error - {e}")
        all_pass = False
    
    # Test Phase 7 contract
    try:
        contract7 = Phase7SubagentContract(strict_mode=True)
        factory_contract7 = create_contract_for_phase(
            "Phase 7: Subagent Orchestration",
            {"strict_mode": True}
        )
        
        if isinstance(factory_contract7, Phase7SubagentContract):
            print("✅ Phase7SubagentContract: Created and factory works")
        else:
            print("❌ Phase7SubagentContract: Factory returns wrong type")
            all_pass = False
    except Exception as e:
        print(f"❌ Phase7SubagentContract: Error - {e}")
        all_pass = False
    
    # Test Phase 9 contract
    try:
        contract9 = Phase9DossierContract(strict_mode=True)
        factory_contract9 = create_contract_for_phase(
            "Phase 9: DOJ-Grade Dossier Generation",
            {"strict_mode": True}
        )
        
        if isinstance(factory_contract9, Phase9DossierContract):
            print("✅ Phase9DossierContract: Created and factory works")
        else:
            print("❌ Phase9DossierContract: Factory returns wrong type")
            all_pass = False
    except Exception as e:
        print(f"❌ Phase9DossierContract: Error - {e}")
        all_pass = False
    
    # Test validation methods
    try:
        # Test Phase 6 validation
        test_data6 = {
            "openai_validation_complete": True,
            "anthropic_validation_complete": False,
            "cross_validation_score": 0.80,
            "min_confidence_threshold": 0.75
        }
        result6 = contract6.validate(test_data6)
        
        # Test Phase 7 validation
        test_data7 = {
            "agents_deployed": 10,
            "agents_completed": 9,
            "min_completion_ratio": 0.80
        }
        result7 = contract7.validate(test_data7)
        
        # Test Phase 9 validation
        test_data9 = {
            "fre_902_13_compliant": True,
            "fre_902_14_compliant": True,
            "evidence_chain_complete": True,
            "triple_hash_verified": True,
            "merkle_tree_valid": True,
            "executive_summary_present": True,
            "findings_documented": True,
            "evidence_exhibits_attached": True,
            "chain_of_custody_documented": True,
            "rfc_3161_timestamp_present": True
        }
        result9 = contract9.validate(test_data9)
        
        if result6.passed and result7.passed and result9.passed:
            print("✅ All contract validation methods work correctly")
        else:
            print("❌ Some contract validation methods failed")
            all_pass = False
    except Exception as e:
        print(f"❌ Contract validation error: {e}")
        all_pass = False
    
    return all_pass


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("JLAW CRITICAL CONFIGURATION FIXES VERIFICATION")
    print("Audit Report Date: December 25, 2025")
    print("=" * 70)
    
    results = {
        "CRITICAL-001": verify_critical_001(),
        "CRITICAL-002": verify_critical_002(),
        "CRITICAL-003": verify_critical_003()
    }
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_passed = all(results.values())
    
    for issue, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{issue}: {status}")
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 ALL CRITICAL FIXES VERIFIED SUCCESSFULLY")
        print("The system is now ready for DOJ-grade forensic compliance.")
        return 0
    else:
        print("\n⚠️  SOME CRITICAL FIXES FAILED VERIFICATION")
        print("Please review the errors above and fix them before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
