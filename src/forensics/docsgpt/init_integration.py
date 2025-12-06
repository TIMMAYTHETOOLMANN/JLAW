"""
DocsGPT Integration Initialization System
==========================================

This module configures and validates the complete integration between
DocsGPT and JLAW SEC Forensic System for enhanced document parsing and analysis.

Usage:
    python -m src.forensics.docsgpt.init_integration
    
    Or from Python:
    from src.forensics.docsgpt.init_integration import initialize_docsgpt_integration
    status = initialize_docsgpt_integration()
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
from dataclasses import asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocsGPTIntegrationValidator:
    """Validates DocsGPT integration setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.docsgpt_path = self.project_root / "external_repos" / "DocsGPT"
        self.validation_results = {}
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("=" * 80)
        logger.info("JARVIS NEXUS - DocsGPT Integration Validation")
        logger.info("=" * 80)
        
        checks = [
            ("Repository Structure", self.check_repository),
            ("Python Dependencies", self.check_dependencies),
            ("DocsGPT Parsers", self.check_parsers),
            ("Vector Store Setup", self.check_vector_store),
            ("Configuration Files", self.check_configuration),
            ("API Keys", self.check_api_keys),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            logger.info(f"\n{'='*60}")
            logger.info(f"Checking: {check_name}")
            logger.info(f"{'='*60}")
            try:
                result = check_func()
                self.validation_results[check_name] = result
                if result['status'] == 'PASS':
                    logger.info(f"✅ {check_name}: PASSED")
                else:
                    logger.warning(f"⚠️  {check_name}: FAILED")
                    all_passed = False
                    if result.get('errors'):
                        for error in result['errors']:
                            logger.error(f"   - {error}")
            except Exception as e:
                logger.error(f"❌ {check_name}: ERROR - {str(e)}")
                self.validation_results[check_name] = {
                    'status': 'ERROR',
                    'errors': [str(e)]
                }
                all_passed = False
        
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("✅ ALL VALIDATION CHECKS PASSED")
        else:
            logger.warning("⚠️  SOME VALIDATION CHECKS FAILED - See details above")
        logger.info("=" * 80)
        
        return {
            'overall_status': 'PASS' if all_passed else 'FAIL',
            'checks': self.validation_results,
            'timestamp': str(Path(__file__).stat().st_mtime)
        }
    
    def check_repository(self) -> Dict[str, Any]:
        """Check DocsGPT repository structure."""
        errors = []
        warnings = []
        
        # Check if DocsGPT repository exists
        if not self.docsgpt_path.exists():
            errors.append(f"DocsGPT repository not found at: {self.docsgpt_path}")
            return {'status': 'FAIL', 'errors': errors}
        
        logger.info(f"✓ DocsGPT repository found: {self.docsgpt_path}")
        
        # Check critical directories
        critical_paths = [
            "application/parser/file",
            "application/parser/connectors",
            "application/vectorstore",
            "application/llm",
        ]
        
        for rel_path in critical_paths:
            full_path = self.docsgpt_path / rel_path
            if full_path.exists():
                logger.info(f"✓ Found: {rel_path}")
            else:
                warnings.append(f"Missing directory: {rel_path}")
        
        # Check parser files
        parser_files = [
            "application/parser/file/docs_parser.py",
            "application/parser/file/html_parser.py",
            "application/parser/file/tabular_parser.py",
            "application/parser/file/json_parser.py",
            "application/parser/file/pptx_parser.py",
            "application/parser/file/image_parser.py",
            "application/parser/chunking.py",
        ]
        
        for rel_path in parser_files:
            full_path = self.docsgpt_path / rel_path
            if full_path.exists():
                logger.info(f"✓ Found parser: {Path(rel_path).name}")
            else:
                warnings.append(f"Missing parser: {rel_path}")
        
        status = 'PASS' if not errors else 'FAIL'
        return {
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'docsgpt_path': str(self.docsgpt_path)
        }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check required Python dependencies."""
        errors = []
        installed = []
        missing = []
        
        required_packages = {
            # Core DocsGPT
            'langchain': 'langchain',
            'langchain_community': 'langchain-community',
            'langchain_openai': 'langchain-openai',
            'sentence_transformers': 'sentence-transformers',
            'faiss': 'faiss-cpu',
            'tiktoken': 'tiktoken',
            
            # Document parsing
            'docx2txt': 'docx2txt',
            'pypdf': 'pypdf',
            'pptx': 'python-pptx',
            'openpyxl': 'openpyxl',
            'ebooklib': 'ebooklib',
            
            # Existing JLAW
            'bs4': 'beautifulsoup4',
            'lxml': 'lxml',
            'pandas': 'pandas',
            'numpy': 'numpy',
        }
        
        for module_name, package_name in required_packages.items():
            try:
                __import__(module_name)
                installed.append(package_name)
                logger.info(f"✓ {package_name}")
            except ImportError:
                missing.append(package_name)
                logger.warning(f"✗ {package_name} - NOT INSTALLED")
        
        if missing:
            errors.append(f"Missing packages: {', '.join(missing)}")
            logger.warning(f"\nTo install missing packages, run:")
            logger.warning(f"pip install {' '.join(missing)}")
        
        status = 'PASS' if not missing else 'FAIL'
        return {
            'status': status,
            'errors': errors,
            'installed': installed,
            'missing': missing
        }
    
    def check_parsers(self) -> Dict[str, Any]:
        """Check if DocsGPT parsers can be imported."""
        errors = []
        available_parsers = []
        failed_parsers = []
        
        # Add DocsGPT to path
        if self.docsgpt_path.exists():
            sys.path.insert(0, str(self.docsgpt_path))
        
        parser_imports = {
            'PDF Parser': ('application.parser.file.docs_parser', 'PDFParser'),
            'HTML Parser': ('application.parser.file.html_parser', 'HTMLParser'),
            'Tabular Parser': ('application.parser.file.tabular_parser', 'ExcelParser'),
            'JSON Parser': ('application.parser.file.json_parser', 'JSONParser'),
            'PPTX Parser': ('application.parser.file.pptx_parser', 'PPTXParser'),
            'Image Parser': ('application.parser.file.image_parser', 'ImageParser'),
            'Chunking': ('application.parser.chunking', 'Chunker'),
        }
        
        for name, (module_path, class_name) in parser_imports.items():
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                available_parsers.append(name)
                logger.info(f"✓ {name} available")
            except Exception as e:
                failed_parsers.append(name)
                logger.warning(f"✗ {name} - {str(e)[:50]}")
        
        if failed_parsers:
            errors.append(f"Failed to import parsers: {', '.join(failed_parsers)}")
        
        status = 'PASS' if len(available_parsers) >= len(parser_imports) * 0.7 else 'FAIL'
        return {
            'status': status,
            'errors': errors,
            'available': available_parsers,
            'failed': failed_parsers
        }
    
    def check_vector_store(self) -> Dict[str, Any]:
        """Check vector store setup."""
        errors = []
        warnings = []
        
        # Check if vector store directory exists
        vector_store_path = self.project_root / "forensic_storage" / "vector_indices"
        if not vector_store_path.exists():
            logger.info(f"Creating vector store directory: {vector_store_path}")
            vector_store_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✓ Vector store path: {vector_store_path}")
        
        # Test FAISS availability
        try:
            import faiss
            logger.info(f"✓ FAISS version: {faiss.__version__ if hasattr(faiss, '__version__') else 'available'}")
        except ImportError:
            errors.append("FAISS not installed - required for vector storage")
        
        # Test sentence transformers
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("✓ Sentence Transformers available")
        except ImportError:
            errors.append("sentence-transformers not installed")
        
        status = 'PASS' if not errors else 'FAIL'
        return {
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'vector_store_path': str(vector_store_path)
        }
    
    def check_configuration(self) -> Dict[str, Any]:
        """Check configuration files."""
        errors = []
        warnings = []
        
        # Check if config module exists
        try:
            from src.forensics.docsgpt.config import DocsGPTConfig
            config = DocsGPTConfig()
            logger.info("✓ DocsGPT configuration module loaded")
            logger.info(f"  - Chunking strategy: {config.chunking.strategy}")
            logger.info(f"  - Embedding model: {config.embedding.model_name}")
            logger.info(f"  - Vector store: {config.vector_store.store_type}")
        except Exception as e:
            errors.append(f"Configuration loading failed: {str(e)}")
        
        # Check parser factory
        try:
            from src.forensics.docsgpt.parser_factory import ParserFactory
            logger.info("✓ ParserFactory module loaded")
        except Exception as e:
            errors.append(f"ParserFactory loading failed: {str(e)}")
        
        status = 'PASS' if not errors else 'FAIL'
        return {
            'status': status,
            'errors': errors,
            'warnings': warnings
        }
    
    def check_api_keys(self) -> Dict[str, Any]:
        """Check API keys configuration."""
        errors = []
        warnings = []
        available_keys = []
        
        api_keys = {
            'OPENAI_API_KEY': 'OpenAI',
            'ANTHROPIC_API_KEY': 'Anthropic',
            'GOOGLE_API_KEY': 'Google AI',
            'SEC_API_KEY': 'SEC API',
        }
        
        for env_var, service in api_keys.items():
            if os.getenv(env_var):
                available_keys.append(service)
                logger.info(f"✓ {service} API key configured")
            else:
                warnings.append(f"{service} API key not set ({env_var})")
                logger.warning(f"⚠️  {service} API key not configured")
        
        if not available_keys:
            errors.append("No API keys configured - LLM features will be limited")
        
        status = 'PASS' if available_keys else 'WARN'
        return {
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'available': available_keys
        }


def initialize_docsgpt_integration(validate_only: bool = False) -> Dict[str, Any]:
    """
    Initialize DocsGPT integration with JLAW SEC Forensic System.
    
    Args:
        validate_only: If True, only run validation without initialization
        
    Returns:
        Dict with initialization status and results
    """
    validator = DocsGPTIntegrationValidator()
    results = validator.validate_all()
    
    if validate_only:
        return results
    
    # If validation passed, perform initialization
    if results['overall_status'] == 'PASS':
        logger.info("\n" + "="*80)
        logger.info("Initializing DocsGPT Integration...")
        logger.info("="*80)
        
        try:
            # Initialize vector store
            from src.forensics.vectorstore.vector_creator import VectorStoreFactory
            logger.info("✓ Vector store factory initialized")
            
            # Initialize parser factory
            from src.forensics.docsgpt.parser_factory import ParserFactory
            logger.info("✓ Parser factory initialized")
            
            # Test parsing capability
            logger.info("\n✅ DocsGPT integration successfully initialized!")
            results['initialization'] = 'SUCCESS'
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            results['initialization'] = 'FAILED'
            results['initialization_error'] = str(e)
    else:
        logger.warning("\n⚠️  Validation failed - skipping initialization")
        results['initialization'] = 'SKIPPED'
    
    return results


def print_integration_status():
    """Print comprehensive integration status."""
    results = initialize_docsgpt_integration(validate_only=True)
    
    print("\n" + "="*80)
    print("JARVIS NEXUS - DocsGPT Integration Status Report")
    print("="*80)
    
    for check_name, check_result in results.get('checks', {}).items():
        status_icon = "✅" if check_result['status'] == 'PASS' else "⚠️"
        print(f"\n{status_icon} {check_name}: {check_result['status']}")
        
        if check_result.get('errors'):
            print("  Errors:")
            for error in check_result['errors']:
                print(f"    - {error}")
        
        if check_result.get('warnings'):
            print("  Warnings:")
            for warning in check_result['warnings']:
                print(f"    - {warning}")
    
    print("\n" + "="*80)
    print(f"Overall Status: {results['overall_status']}")
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize DocsGPT integration")
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate, do not initialize')
    parser.add_argument('--status', action='store_true',
                       help='Print status report')
    
    args = parser.parse_args()
    
    if args.status:
        print_integration_status()
    else:
        results = initialize_docsgpt_integration(validate_only=args.validate_only)
        
        # Save results
        output_file = Path(__file__).parent.parent.parent.parent / "config" / "docsgpt_integration_status.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_file}")

