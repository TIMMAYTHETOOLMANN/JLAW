#!/usr/bin/env python3
"""
Full System Integration Test Suite
Tests all aspects of JLAW Forensic System from frontend to backend
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("INTEGRATION_TEST")


class IntegrationTestSuite:
    """Comprehensive integration test suite for JLAW Forensic System"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.api_url = f"{backend_url}/api"
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} | {name}")
        if details:
            logger.info(f"         Details: {details}")
        
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    async def test_backend_health(self) -> bool:
        """Test 1: Backend Health Check"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health", timeout=5) as resp:
                    data = await resp.json()
                    
                    checks = [
                        ("Status", data.get("status") == "healthy"),
                        ("Service", data.get("service") == "mcp-forensics-backend"),
                        ("Forensics Available", data.get("forensics_available") is True),
                        ("Investigator Ready", data.get("investigator_ready") is True),
                    ]
                    
                    all_passed = all(check[1] for check in checks)
                    details = ", ".join([f"{k}: {v}" for k, v in checks])
                    
                    self.log_test("Backend Health Check", all_passed, details)
                    return all_passed
                    
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
    
    async def test_api_root(self) -> bool:
        """Test 2: API Root Information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/", timeout=5) as resp:
                    data = await resp.json()
                    
                    has_endpoints = "endpoints" in data
                    has_version = "version" in data
                    
                    passed = has_endpoints and has_version
                    self.log_test("API Root Information", passed, 
                                f"Endpoints: {len(data.get('endpoints', {}))}")
                    return passed
                    
        except Exception as e:
            self.log_test("API Root Information", False, f"Error: {str(e)}")
            return False
    
    async def test_company_search(self) -> Dict[str, Any]:
        """Test 3: Company Search Functionality"""
        try:
            test_queries = ["TSLA", "AAPL", "NKE"]
            results = {}
            
            async with aiohttp.ClientSession() as session:
                for query in test_queries:
                    async with session.post(
                        f"{self.api_url}/search_company",
                        json={"query": query},
                        timeout=5
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            results[query] = data
            
            passed = len(results) == len(test_queries)
            self.log_test("Company Search", passed, 
                        f"Found: {list(results.keys())}")
            
            return results.get("NKE", {})  # Return Nike for next test
            
        except Exception as e:
            self.log_test("Company Search", False, f"Error: {str(e)}")
            return {}
    
    async def test_investigation_workflow(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test 4: Full Investigation Workflow"""
        if not company_data or "cik" not in company_data:
            self.log_test("Investigation Workflow", False, "No company data")
            return {}
        
        try:
            cik = company_data["cik"]
            async with aiohttp.ClientSession() as session:
                # Start investigation
                request_data = {
                    "cik": cik,
                    "years_back": 1,
                    "forms": ["10-K"]
                }
                
                async with session.post(
                    f"{self.api_url}/start_investigation",
                    json=request_data,
                    timeout=30
                ) as resp:
                    data = await resp.json()
                    
                    checks = [
                        ("Status", data.get("status") in ["completed", "running"]),
                        ("Investigation ID", "investigation_id" in data),
                        ("Risk Score", "risk_score" in data),
                        ("Risk Level", "risk_level" in data),
                    ]
                    
                    passed = all(check[1] for check in checks)
                    details = f"ID: {data.get('investigation_id', 'N/A')}, Risk: {data.get('risk_score', 'N/A')}"
                    
                    self.log_test("Investigation Workflow", passed, details)
                    return data
                    
        except Exception as e:
            self.log_test("Investigation Workflow", False, f"Error: {str(e)}")
            return {}
    
    async def test_investigation_status(self) -> bool:
        """Test 5: Investigation Status Check"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/investigation_status", timeout=5) as resp:
                    data = await resp.json()
                    
                    has_status = "running" in data
                    has_results = "has_results" in data
                    
                    passed = has_status and has_results
                    self.log_test("Investigation Status", passed, 
                                f"Running: {data.get('running')}, Has Results: {data.get('has_results')}")
                    return passed
                    
        except Exception as e:
            self.log_test("Investigation Status", False, f"Error: {str(e)}")
            return False
    
    async def test_investigation_results(self) -> Dict[str, Any]:
        """Test 6: Investigation Results Retrieval"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/investigation_results", timeout=5) as resp:
                    if resp.status == 404:
                        self.log_test("Investigation Results", True, "No results yet (expected)")
                        return {}
                    
                    data = await resp.json()
                    
                    has_investigation = "investigation_id" in data
                    has_risk = "risk_score" in data
                    
                    passed = has_investigation or has_risk
                    self.log_test("Investigation Results", passed, 
                                f"Investigation ID present: {has_investigation}")
                    return data
                    
        except Exception as e:
            self.log_test("Investigation Results", False, f"Error: {str(e)}")
            return {}
    
    async def test_database_stats(self) -> bool:
        """Test 7: Database Statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/database_stats", timeout=5) as resp:
                    data = await resp.json()
                    
                    # Database stats should have some structure
                    passed = isinstance(data, dict)
                    self.log_test("Database Statistics", passed, 
                                f"Stats keys: {list(data.keys()) if isinstance(data, dict) else 'None'}")
                    return passed
                    
        except Exception as e:
            self.log_test("Database Statistics", False, f"Error: {str(e)}")
            return False
    
    async def test_high_risk_companies(self) -> bool:
        """Test 8: High Risk Companies Query"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/high_risk_companies?threshold=0.5", timeout=5) as resp:
                    data = await resp.json()
                    
                    has_companies = "companies" in data
                    has_threshold = "threshold" in data
                    
                    passed = has_companies and has_threshold
                    self.log_test("High Risk Companies", passed, 
                                f"Companies found: {len(data.get('companies', []))}")
                    return passed
                    
        except Exception as e:
            self.log_test("High Risk Companies", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_files(self) -> bool:
        """Test 9: Frontend Files Existence"""
        frontend_path = Path("/home/runner/work/JLAW/JLAW/mcp_forensics_frontend")
        
        required_files = [
            "index.html",
            "script.js",
            "style.css",
            "components/header.js",
            "components/footer.js",
        ]
        
        missing = []
        for file in required_files:
            if not (frontend_path / file).exists():
                missing.append(file)
        
        passed = len(missing) == 0
        details = f"Missing: {missing}" if missing else "All files present"
        self.log_test("Frontend Files Existence", passed, details)
        return passed
    
    def test_backend_files(self) -> bool:
        """Test 10: Backend Core Files Existence"""
        backend_path = Path("/home/runner/work/JLAW/JLAW/mcp_forensics_backend")
        
        required_files = [
            "app.py",
            "unified_forensic_system.py",
            "forensic_output_generator.py",
            "simple_forensics.py",
            "requirements.txt",
        ]
        
        missing = []
        for file in required_files:
            if not (backend_path / file).exists():
                missing.append(file)
        
        passed = len(missing) == 0
        details = f"Missing: {missing}" if missing else "All files present"
        self.log_test("Backend Files Existence", passed, details)
        return passed
    
    def test_forensic_modules(self) -> bool:
        """Test 11: Forensic Module Files Existence"""
        modules_path = Path("/home/runner/work/JLAW/JLAW/examples/jarvis_law_sec_auditor")
        
        key_modules = [
            "forensic_core.py",
            "forensic_output_generator.py",
            "forensic_web_server.py",
            "sec_edgar_fraud_detection.py",
            "filing_analyzer.py",
            "form4_xml_parser.py",
            "form4_html_parser.py",
        ]
        
        missing = []
        for module in key_modules:
            if not (modules_path / module).exists():
                missing.append(module)
        
        passed = len(missing) == 0
        details = f"Missing: {missing}" if missing else f"All {len(key_modules)} modules present"
        self.log_test("Forensic Modules Existence", passed, details)
        return passed
    
    def test_api_integration_script(self) -> bool:
        """Test 12: Frontend API Integration Code"""
        script_path = Path("/home/runner/work/JLAW/JLAW/mcp_forensics_frontend/script.js")
        
        try:
            content = script_path.read_text()
            
            checks = [
                ("API Base URL", "API_BASE" in content or "api" in content.lower()),
                ("Search Company", "search_company" in content.lower()),
                ("Start Investigation", "start_investigation" in content.lower()),
                ("Fetch API", "fetch" in content),
                ("Results Display", "results" in content.lower()),
            ]
            
            passed_checks = sum(1 for _, check in checks if check)
            passed = passed_checks >= 4
            
            self.log_test("Frontend API Integration", passed, 
                        f"{passed_checks}/{len(checks)} integration points found")
            return passed
            
        except Exception as e:
            self.log_test("Frontend API Integration", False, f"Error: {str(e)}")
            return False
    
    async def test_cors_configuration(self) -> bool:
        """Test 13: CORS Configuration"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.options(f"{self.backend_url}/health", timeout=5) as resp:
                    # Check for CORS headers
                    has_cors = any('access-control' in h.lower() for h in resp.headers.keys())
                    
                    self.log_test("CORS Configuration", has_cors, 
                                "CORS headers present" if has_cors else "No CORS headers")
                    return has_cors
                    
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("=" * 80)
        logger.info("JLAW FORENSIC SYSTEM - FULL INTEGRATION TEST SUITE")
        logger.info("=" * 80)
        logger.info("")
        
        # Phase 1: Backend API Tests
        logger.info("PHASE 1: BACKEND API TESTS")
        logger.info("-" * 80)
        await self.test_backend_health()
        await self.test_api_root()
        await self.test_cors_configuration()
        
        # Phase 2: Core Functionality Tests
        logger.info("")
        logger.info("PHASE 2: CORE FUNCTIONALITY TESTS")
        logger.info("-" * 80)
        company_data = await self.test_company_search()
        investigation_data = await self.test_investigation_workflow(company_data)
        await self.test_investigation_status()
        await self.test_investigation_results()
        await self.test_database_stats()
        await self.test_high_risk_companies()
        
        # Phase 3: File Structure Tests
        logger.info("")
        logger.info("PHASE 3: FILE STRUCTURE TESTS")
        logger.info("-" * 80)
        self.test_frontend_files()
        self.test_backend_files()
        self.test_forensic_modules()
        self.test_api_integration_script()
        
        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.passed + self.failed}")
        logger.info(f"Passed: {self.passed} ✅")
        logger.info(f"Failed: {self.failed} ❌")
        logger.info(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        logger.info("")
        
        return self.failed == 0


async def main():
    """Main test runner"""
    suite = IntegrationTestSuite()
    
    # Check if backend is running
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result != 0:
            logger.warning("⚠️  Backend not running on port 8000")
            logger.warning("   Starting backend is recommended for full test coverage")
            logger.warning("   Run: cd mcp_forensics_backend && python -m uvicorn app:app")
            logger.info("")
            
            # Run only file structure tests
            logger.info("Running file structure tests only...")
            suite.test_frontend_files()
            suite.test_backend_files()
            suite.test_forensic_modules()
            suite.test_api_integration_script()
            
            logger.info("")
            logger.info(f"Tests Passed: {suite.passed}/{suite.passed + suite.failed}")
            return
            
    except Exception as e:
        logger.error(f"Error checking backend: {e}")
    
    # Run all tests
    all_passed = await suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
