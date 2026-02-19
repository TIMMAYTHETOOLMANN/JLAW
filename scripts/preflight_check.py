#!/usr/bin/env python3
"""
JLAW Pre-Flight Validation Script

Validates all system components before forensic analysis execution.

Usage:
    python scripts/preflight_check.py
    python scripts/preflight_check.py --verbose
    python scripts/preflight_check.py --json

Exit Codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import after path setup
from config.secure_config import (
    load_dotenv_file,
    get_api_key,
    validate_sec_user_agent
)


@dataclass
class CheckResult:
    """Result of a single validation check."""
    component: str
    status: str  # "pass", "fail", "warn", "skip"
    message: str
    details: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class PreFlightReport:
    """Complete pre-flight validation report."""
    timestamp: str
    passed: bool
    checks: List[CheckResult]
    summary: Dict[str, int]


class PreFlightChecker:
    """Pre-flight validation orchestrator."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[CheckResult] = []
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(levelname)s | %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def add_result(self, result: CheckResult):
        """Add check result."""
        self.results.append(result)
        
        # Log result
        if result.status == "pass":
            self.logger.info(f"✓ {result.component}: {result.message}")
        elif result.status == "fail":
            self.logger.error(f"✗ {result.component}: {result.message}")
        elif result.status == "warn":
            self.logger.warning(f"⚠ {result.component}: {result.message}")
        elif result.status == "skip":
            self.logger.info(f"○ {result.component}: {result.message}")
    
    # ========================================================================
    # Environment Variable Validation
    # ========================================================================
    
    def check_environment_variables(self) -> CheckResult:
        """Validate environment variables."""
        try:
            env_vars = load_dotenv_file()
            
            if not env_vars:
                return CheckResult(
                    component="Environment Variables",
                    status="fail",
                    message=".env file not found or empty",
                    error="Create .env from .env.example"
                )
            
            # Check required variables
            required = [
                'SEC_USER_AGENT',
                'OPENAI_API_KEY',
                'ANTHROPIC_API_KEY',
            ]
            
            missing = []
            for var in required:
                value = get_api_key(var)
                if not value:
                    missing.append(var)
            
            if missing:
                return CheckResult(
                    component="Environment Variables",
                    status="fail",
                    message=f"Missing required variables: {', '.join(missing)}",
                    details={"loaded": len(env_vars), "missing": missing}
                )
            
            return CheckResult(
                component="Environment Variables",
                status="pass",
                message=f"Loaded {len(env_vars)} variables, all required present",
                details={"count": len(env_vars)}
            )
            
        except Exception as e:
            return CheckResult(
                component="Environment Variables",
                status="fail",
                message="Failed to load environment",
                error=str(e)
            )
    
    # ========================================================================
    # SEC EDGAR API Validation
    # ========================================================================
    
    def check_sec_user_agent(self) -> CheckResult:
        """Validate SEC User-Agent configuration."""
        try:
            user_agent = get_api_key('SEC_USER_AGENT')
            
            if not user_agent:
                return CheckResult(
                    component="SEC User-Agent",
                    status="fail",
                    message="SEC_USER_AGENT not configured",
                    error="Set SEC_USER_AGENT in .env file"
                )
            
            is_valid, msg = validate_sec_user_agent(user_agent)
            
            if not is_valid:
                return CheckResult(
                    component="SEC User-Agent",
                    status="fail",
                    message=msg,
                    error="Update SEC_USER_AGENT in .env file"
                )
            
            return CheckResult(
                component="SEC User-Agent",
                status="pass",
                message="Valid SEC User-Agent configured"
            )
            
        except Exception as e:
            return CheckResult(
                component="SEC User-Agent",
                status="fail",
                message="Validation failed",
                error=str(e)
            )
    
    async def check_sec_api_connectivity(self) -> CheckResult:
        """Test SEC EDGAR API connectivity."""
        try:
            from src.integrations.sec_edgar.edgar_client import SECEdgarClient
            
            user_agent = get_api_key('SEC_USER_AGENT')
            if not user_agent:
                return CheckResult(
                    component="SEC API Connectivity",
                    status="skip",
                    message="Skipped (User-Agent not configured)"
                )
            
            async with SECEdgarClient(user_agent=user_agent) as client:
                # Test with simple ticker lookup
                tickers = await client.get_company_tickers()
                
                if tickers and len(tickers) > 0:
                    return CheckResult(
                        component="SEC API Connectivity",
                        status="pass",
                        message="SEC EDGAR API accessible",
                        details={"ticker_count": len(tickers)}
                    )
                else:
                    return CheckResult(
                        component="SEC API Connectivity",
                        status="warn",
                        message="SEC API responded but returned empty data"
                    )
        
        except Exception as e:
            return CheckResult(
                component="SEC API Connectivity",
                status="fail",
                message="Failed to connect to SEC EDGAR API",
                error=str(e)
            )
    
    # ========================================================================
    # API Key Validation
    # ========================================================================
    
    async def check_openai_api(self) -> CheckResult:
        """Validate OpenAI API key."""
        try:
            api_key = get_api_key('OPENAI_API_KEY')
            
            if not api_key:
                return CheckResult(
                    component="OpenAI API",
                    status="fail",
                    message="OPENAI_API_KEY not configured",
                    error="Set OPENAI_API_KEY in .env file"
                )
            
            # Test API key with simple completion
            import aiohttp
            
            async with aiohttp.ClientSession(trust_env=True) as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return CheckResult(
                            component="OpenAI API",
                            status="pass",
                            message="OpenAI API key valid and accessible"
                        )
                    elif response.status == 401:
                        return CheckResult(
                            component="OpenAI API",
                            status="fail",
                            message="OpenAI API key invalid",
                            error="Check OPENAI_API_KEY in .env file"
                        )
                    else:
                        return CheckResult(
                            component="OpenAI API",
                            status="warn",
                            message=f"OpenAI API returned status {response.status}"
                        )
        
        except asyncio.TimeoutError:
            return CheckResult(
                component="OpenAI API",
                status="warn",
                message="OpenAI API timeout (network issue?)"
            )
        except Exception as e:
            return CheckResult(
                component="OpenAI API",
                status="fail",
                message="Failed to validate OpenAI API",
                error=str(e)
            )
    
    async def check_anthropic_api(self) -> CheckResult:
        """Validate Anthropic API key."""
        try:
            api_key = get_api_key('ANTHROPIC_API_KEY')
            
            if not api_key:
                return CheckResult(
                    component="Anthropic API",
                    status="fail",
                    message="ANTHROPIC_API_KEY not configured",
                    error="Set ANTHROPIC_API_KEY in .env file"
                )
            
            # Test API key with simple message
            import aiohttp
            
            async with aiohttp.ClientSession(trust_env=True) as session:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                
                data = {
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                }
                
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return CheckResult(
                            component="Anthropic API",
                            status="pass",
                            message="Anthropic API key valid and accessible"
                        )
                    elif response.status == 401:
                        return CheckResult(
                            component="Anthropic API",
                            status="fail",
                            message="Anthropic API key invalid",
                            error="Check ANTHROPIC_API_KEY in .env file"
                        )
                    else:
                        return CheckResult(
                            component="Anthropic API",
                            status="warn",
                            message=f"Anthropic API returned status {response.status}"
                        )
        
        except asyncio.TimeoutError:
            return CheckResult(
                component="Anthropic API",
                status="warn",
                message="Anthropic API timeout (network issue?)"
            )
        except Exception as e:
            return CheckResult(
                component="Anthropic API",
                status="fail",
                message="Failed to validate Anthropic API",
                error=str(e)
            )
    
    async def check_polygon_api(self) -> CheckResult:
        """Validate Polygon.io API key (optional)."""
        try:
            api_key = get_api_key('POLYGON_API_KEY')
            
            if not api_key:
                return CheckResult(
                    component="Polygon API",
                    status="skip",
                    message="Not configured (optional - Node 15 will be skipped)"
                )
            
            # Test API key
            import aiohttp
            
            async with aiohttp.ClientSession(trust_env=True) as session:
                url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-01/2023-01-02?apiKey={api_key}"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return CheckResult(
                            component="Polygon API",
                            status="pass",
                            message="Polygon API key valid (Node 15 enabled)"
                        )
                    elif response.status == 401:
                        return CheckResult(
                            component="Polygon API",
                            status="warn",
                            message="Polygon API key invalid (Node 15 will be skipped)",
                            error="Check POLYGON_API_KEY in .env file"
                        )
                    else:
                        return CheckResult(
                            component="Polygon API",
                            status="warn",
                            message=f"Polygon API returned status {response.status}"
                        )
        
        except asyncio.TimeoutError:
            return CheckResult(
                component="Polygon API",
                status="warn",
                message="Polygon API timeout (Node 15 may fail)"
            )
        except Exception as e:
            return CheckResult(
                component="Polygon API",
                status="warn",
                message="Failed to validate Polygon API",
                error=str(e)
            )
    
    # ========================================================================
    # Database Connectivity
    # ========================================================================
    
    async def check_neo4j(self) -> CheckResult:
        """Test Neo4j connectivity (optional)."""
        try:
            uri = get_api_key('NEO4J_URI')
            
            if not uri:
                return CheckResult(
                    component="Neo4j",
                    status="skip",
                    message="Not configured (optional - Node 11 will be skipped)"
                )
            
            from neo4j import AsyncGraphDatabase
            
            user = get_api_key('NEO4J_USER') or 'neo4j'
            password = get_api_key('NEO4J_PASSWORD')
            
            if not password:
                return CheckResult(
                    component="Neo4j",
                    status="warn",
                    message="NEO4J_PASSWORD not set (Node 11 will be skipped)"
                )
            
            driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
            
            try:
                await driver.verify_connectivity()
                return CheckResult(
                    component="Neo4j",
                    status="pass",
                    message="Neo4j connected (Node 11 enabled)"
                )
            finally:
                await driver.close()
        
        except Exception as e:
            return CheckResult(
                component="Neo4j",
                status="warn",
                message="Neo4j connection failed (Node 11 will be skipped)",
                error=str(e)
            )
    
    async def check_redis(self) -> CheckResult:
        """Test Redis connectivity (optional)."""
        try:
            uri = get_api_key('REDIS_URI')
            
            if not uri:
                return CheckResult(
                    component="Redis",
                    status="skip",
                    message="Not configured (optional - caching disabled)"
                )
            
            import redis.asyncio as redis
            
            client = redis.from_url(uri)
            
            try:
                await client.ping()
                return CheckResult(
                    component="Redis",
                    status="pass",
                    message="Redis connected (caching enabled)"
                )
            finally:
                await client.close()
        
        except Exception as e:
            return CheckResult(
                component="Redis",
                status="warn",
                message="Redis connection failed (caching disabled)",
                error=str(e)
            )
    
    async def check_timescaledb(self) -> CheckResult:
        """Test TimescaleDB connectivity (optional)."""
        try:
            uri = get_api_key('TIMESCALEDB_URI')
            
            if not uri:
                return CheckResult(
                    component="TimescaleDB",
                    status="skip",
                    message="Not configured (optional - time-series disabled)"
                )
            
            import asyncpg
            
            try:
                conn = await asyncpg.connect(uri, timeout=5)
                await conn.execute('SELECT 1')
                await conn.close()
                
                return CheckResult(
                    component="TimescaleDB",
                    status="pass",
                    message="TimescaleDB connected (time-series enabled)"
                )
            except Exception as e:
                return CheckResult(
                    component="TimescaleDB",
                    status="warn",
                    message="TimescaleDB connection failed",
                    error=str(e)
                )
        
        except ImportError:
            return CheckResult(
                component="TimescaleDB",
                status="skip",
                message="asyncpg not installed (optional)"
            )
        except Exception as e:
            return CheckResult(
                component="TimescaleDB",
                status="warn",
                message="TimescaleDB check failed",
                error=str(e)
            )
    
    # ========================================================================
    # RFC 3161 TSA Validation
    # ========================================================================
    
    async def check_rfc3161_tsa(self) -> CheckResult:
        """Test RFC 3161 Timestamp Authority accessibility."""
        try:
            from src.core.evidence_chain.rfc3161_client import RFC3161Client
            
            tsa_url = get_api_key('RFC3161_TIMESTAMP_URL') or 'https://freetsa.org/tsr'
            
            if tsa_url == 'local':
                return CheckResult(
                    component="RFC 3161 TSA",
                    status="warn",
                    message="Using local timestamps (NOT court-admissible)",
                    error="Set RFC3161_TIMESTAMP_URL to network TSA for court-admissible evidence"
                )
            
            client = RFC3161Client(tsa_url=tsa_url)
            
            # Test with simple data
            test_data = b"JLAW pre-flight check"
            
            try:
                timestamp_token = await client.timestamp_data(test_data)
                
                if timestamp_token:
                    return CheckResult(
                        component="RFC 3161 TSA",
                        status="pass",
                        message=f"TSA accessible: {tsa_url}",
                        details={"tsa_url": tsa_url}
                    )
                else:
                    return CheckResult(
                        component="RFC 3161 TSA",
                        status="fail",
                        message="TSA returned no timestamp token",
                        error="Check RFC3161_TIMESTAMP_URL in .env"
                    )
            except Exception as e:
                return CheckResult(
                    component="RFC 3161 TSA",
                    status="fail",
                    message=f"TSA request failed: {tsa_url}",
                    error=str(e)
                )
        
        except ImportError:
            return CheckResult(
                component="RFC 3161 TSA",
                status="fail",
                message="RFC 3161 client not available",
                error="Install rfc3161ng: pip install rfc3161ng"
            )
        except Exception as e:
            return CheckResult(
                component="RFC 3161 TSA",
                status="fail",
                message="RFC 3161 check failed",
                error=str(e)
            )
    
    # ========================================================================
    # ML Model Cache
    # ========================================================================
    
    def check_ml_model_cache(self) -> CheckResult:
        """Check ML model cache availability."""
        try:
            from src.ml.model_registry import ModelRegistry
            
            registry = ModelRegistry()
            cache_dir = registry.get_cache_dir()
            
            if not cache_dir.exists():
                return CheckResult(
                    component="ML Model Cache",
                    status="warn",
                    message="Model cache directory does not exist",
                    error="Run: python jlaw_cli.py --download-models"
                )
            
            # Check cached models
            cached_models = []
            missing_models = []
            
            for model_name in registry.MODELS.keys():
                if registry.is_model_cached(model_name):
                    cached_models.append(model_name)
                else:
                    missing_models.append(model_name)
            
            if len(cached_models) == len(registry.MODELS):
                return CheckResult(
                    component="ML Model Cache",
                    status="pass",
                    message=f"All {len(cached_models)} models cached",
                    details={"cached": len(cached_models)}
                )
            elif len(cached_models) > 0:
                return CheckResult(
                    component="ML Model Cache",
                    status="warn",
                    message=f"{len(cached_models)}/{len(registry.MODELS)} models cached",
                    details={
                        "cached": cached_models,
                        "missing": missing_models
                    },
                    error="Run: python jlaw_cli.py --download-models"
                )
            else:
                return CheckResult(
                    component="ML Model Cache",
                    status="warn",
                    message="No models cached",
                    error="Run: python jlaw_cli.py --download-models"
                )
        
        except ImportError:
            return CheckResult(
                component="ML Model Cache",
                status="skip",
                message="Model registry not implemented yet"
            )
        except Exception as e:
            return CheckResult(
                component="ML Model Cache",
                status="warn",
                message="Failed to check ML model cache",
                error=str(e)
            )
    
    # ========================================================================
    # Main Execution
    # ========================================================================
    
    async def run_all_checks(self) -> PreFlightReport:
        """Run all pre-flight checks."""
        self.logger.info("=" * 70)
        self.logger.info("JLAW PRE-FLIGHT VALIDATION")
        self.logger.info("=" * 70)
        self.logger.info("")
        
        # Environment validation
        self.logger.info("ENVIRONMENT VALIDATION")
        self.logger.info("-" * 70)
        self.add_result(self.check_environment_variables())
        self.add_result(self.check_sec_user_agent())
        self.logger.info("")
        
        # SEC API
        self.logger.info("SEC EDGAR API")
        self.logger.info("-" * 70)
        self.add_result(await self.check_sec_api_connectivity())
        self.logger.info("")
        
        # AI Provider APIs
        self.logger.info("AI PROVIDER APIS")
        self.logger.info("-" * 70)
        self.add_result(await self.check_openai_api())
        self.add_result(await self.check_anthropic_api())
        self.add_result(await self.check_polygon_api())
        self.logger.info("")
        
        # Database connectivity
        self.logger.info("DATABASE CONNECTIVITY")
        self.logger.info("-" * 70)
        self.add_result(await self.check_neo4j())
        self.add_result(await self.check_redis())
        self.add_result(await self.check_timescaledb())
        self.logger.info("")
        
        # Evidence chain
        self.logger.info("EVIDENCE CHAIN")
        self.logger.info("-" * 70)
        self.add_result(await self.check_rfc3161_tsa())
        self.logger.info("")
        
        # ML models
        self.logger.info("ML MODELS")
        self.logger.info("-" * 70)
        self.add_result(self.check_ml_model_cache())
        self.logger.info("")
        
        # Generate summary
        summary = {
            "pass": sum(1 for r in self.results if r.status == "pass"),
            "fail": sum(1 for r in self.results if r.status == "fail"),
            "warn": sum(1 for r in self.results if r.status == "warn"),
            "skip": sum(1 for r in self.results if r.status == "skip"),
        }
        
        passed = summary["fail"] == 0
        
        # Print summary
        self.logger.info("=" * 70)
        self.logger.info("SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"PASS: {summary['pass']}")
        self.logger.info(f"FAIL: {summary['fail']}")
        self.logger.info(f"WARN: {summary['warn']}")
        self.logger.info(f"SKIP: {summary['skip']}")
        self.logger.info("")
        
        if passed:
            self.logger.info("✓ ALL CHECKS PASSED - READY FOR FORENSIC ANALYSIS")
        else:
            self.logger.error("✗ SOME CHECKS FAILED - FIX ERRORS BEFORE RUNNING ANALYSIS")
        
        self.logger.info("=" * 70)
        
        return PreFlightReport(
            timestamp=datetime.now().isoformat(),
            passed=passed,
            checks=self.results,
            summary=summary
        )


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JLAW Pre-Flight Validation"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save report to file'
    )
    
    args = parser.parse_args()
    
    # Run checks
    checker = PreFlightChecker(verbose=args.verbose)
    report = await checker.run_all_checks()
    
    # Output JSON if requested
    if args.json:
        report_dict = asdict(report)
        print(json.dumps(report_dict, indent=2))
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        
        print(f"\nReport saved to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
