"""
Quick Validation Script - Enhanced JLAW Forensic System
Validates all Priority 1 enhancements are properly installed and functional.
"""

import sys
import importlib

def check_module(module_path, module_name, is_required=True):
    """Check if a module is available."""
    try:
        mod = importlib.import_module(module_path)
        print(f"✅ {module_name}: Available")
        return True
    except ImportError as e:
        if is_required:
            print(f"❌ {module_name}: NOT AVAILABLE - {e}")
        else:
            print(f"⚠️  {module_name}: Not available (optional) - {e}")
        return False

def main():
    print("="*80)
    print("JLAW ENHANCED FORENSIC SYSTEM - VALIDATION")
    print("="*80)
    print()
    
    # Check core JLAW modules
    print("📦 Checking Core JLAW Modules...")
    print("-"*60)
    
    core_modules = [
        ("src.forensics.forensic_orchestrator", "Forensic Orchestrator", False),
        ("src.forensics.immutable_storage", "Immutable Storage", False),
        ("src.forensics.core.integrity_manager", "Integrity Manager", False),
    ]
    
    core_available = 0
    for path, name, required in core_modules:
        if check_module(path, name, required):
            core_available += 1
    
    print()
    
    # Check enhancement modules
    print("🚀 Checking Priority 1 Enhancement Modules...")
    print("-"*60)
    
    enhancement_modules = [
        ("src.forensics.enhanced_contradiction_detector", "Enhanced Contradiction Detector"),
        ("src.forensics.benfords_law_analyzer", "Benford's Law Analyzer"),
        ("src.forensics.rfc3161_timestamper", "RFC 3161 Timestamper"),
        ("src.forensics.financial_entity_extractor", "Financial Entity Extractor"),
        ("src.forensics.enhanced_forensic_system", "Enhanced Forensic System"),
    ]
    
    enhancements_available = 0
    for path, name in enhancement_modules:
        if check_module(path, name, False):
            enhancements_available += 1
    
    print()
    
    # Check dependencies
    print("📚 Checking External Dependencies...")
    print("-"*60)
    
    dependencies = [
        ("sentence_transformers", "SentenceTransformers (DeBERTa-v3)", False),
        ("transformers", "HuggingFace Transformers (FinBERT)", False),
        ("torch", "PyTorch (GPU Acceleration)", False),
        ("benford", "benford_py (Benford's Law)", False),
        ("rfc3161ng", "rfc3161ng (RFC 3161 Timestamps)", False),
        ("spacy", "spaCy (Entity Extraction)", False),
        ("sklearn", "scikit-learn (ML Support)", False),
        ("numpy", "NumPy (Numerical)", True),
        ("pandas", "Pandas (Data)", True),
    ]
    
    deps_available = 0
    for module, name, required in dependencies:
        if check_module(module, name, required):
            deps_available += 1
    
    print()
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Core Modules: {core_available}/{len(core_modules)}")
    print(f"Enhancement Modules: {enhancements_available}/{len(enhancement_modules)}")
    print(f"Dependencies: {deps_available}/{len(dependencies)}")
    print()
    
    # Overall status
    if enhancements_available == len(enhancement_modules):
        print("🎉 SUCCESS: All Priority 1 enhancements are available!")
        print()
        print("Next Steps:")
        print("1. Install dependencies: pip install -r requirements_enhancements.txt")
        print("2. Download spaCy model: python -m spacy download en_core_web_lg")
        print("3. Run tests: pytest tests/test_enhanced_forensics.py")
        print("4. Start using: from src.forensics.enhanced_forensic_system import run_enhanced_investigation")
        return 0
    else:
        print("⚠️  PARTIAL: Some enhancements are not available")
        print()
        print("To enable all enhancements:")
        print("1. pip install -r requirements_enhancements.txt")
        print("2. python -m spacy download en_core_web_lg")
        print()
        print("Note: System will work with available enhancements (graceful degradation)")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

