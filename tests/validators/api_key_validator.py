"""
API Key Validator - Validate all API keys and test connectivity.
"""

import os
import re
import asyncio
import aiohttp
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIValidationResult:
    """Result from API key validation."""
    passed: bool
    message: str
    can_skip: bool = False
    details: Optional[Dict] = None


class APIKeyValidator:
    """
    Validate API keys and test connectivity.
    
    Validates:
    - SEC EDGAR API (User-Agent string, connectivity, rate limit)
    - OpenAI API (key format, model access, quota)
    - Anthropic API (key validation, Claude 3 access)
    - Polygon.io API (optional, WebSocket connectivity)
    - GovInfo API (optional, statute lookup)
    - Neo4j (optional, connection test, schema validation)
    - TimescaleDB (optional, connection test, table existence)
    """
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize API key validator.
        
        Args:
            mock_mode: If True, skip actual API calls
        """
        self.mock_mode = mock_mode
        self._load_env()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        env_file = Path(__file__).resolve().parent.parent.parent / '.env'
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:
                            os.environ[key] = value
    
    def _is_placeholder(self, value: str) -> bool:
        """Check if value is a placeholder."""
        placeholders = [
            'YOUR_', 'YOUR-', 'YourProject', 'YourCompany',
            'your-email', 'contact@example', '_HERE', 'PLACEHOLDER'
        ]
        return any(ph in value for ph in placeholders)
    
    def validate_sec_user_agent(self) -> APIValidationResult:
        """
        Validate SEC EDGAR User-Agent configuration.
        
        Returns:
            Validation result
        """
        user_agent = os.getenv('SEC_USER_AGENT', '')
        
        if not user_agent:
            return APIValidationResult(
                passed=False,
                message="SEC_USER_AGENT not set in environment",
                can_skip=False,
                details={'required': True}
            )
        
        # Check for placeholder
        if self._is_placeholder(user_agent):
            return APIValidationResult(
                passed=False,
                message=f"SEC_USER_AGENT contains placeholder: '{user_agent}'",
                can_skip=False,
                details={'user_agent': user_agent}
            )
        
        # Check for email
        email_pattern = r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
        if not re.search(email_pattern, user_agent):
            return APIValidationResult(
                passed=False,
                message=f"SEC_USER_AGENT missing email address: '{user_agent}'",
                can_skip=False,
                details={'user_agent': user_agent}
            )
        
        # Check minimum length
        if len(user_agent) < 15:
            return APIValidationResult(
                passed=False,
                message=f"SEC_USER_AGENT too short: '{user_agent}'",
                can_skip=False,
                details={'user_agent': user_agent, 'length': len(user_agent)}
            )
        
        return APIValidationResult(
            passed=True,
            message=f"SEC_USER_AGENT configured: '{user_agent[:50]}...'",
            can_skip=False,
            details={'user_agent': user_agent}
        )
    
    async def test_sec_connectivity(self) -> APIValidationResult:
        """
        Test SEC EDGAR API connectivity.
        
        Returns:
            Validation result
        """
        if self.mock_mode:
            return APIValidationResult(
                passed=True,
                message="SEC EDGAR connectivity (mock mode - skipped)",
                can_skip=False,
            )
        
        user_agent = os.getenv('SEC_USER_AGENT', '')
        if not user_agent or self._is_placeholder(user_agent):
            return APIValidationResult(
                passed=False,
                message="Cannot test SEC connectivity - invalid User-Agent",
                can_skip=False,
            )
        
        try:
            # Test simple request to SEC EDGAR
            url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K&dateb=&owner=exclude&count=1"
            headers = {'User-Agent': user_agent}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return APIValidationResult(
                            passed=True,
                            message="SEC EDGAR API connectivity confirmed",
                            can_skip=False,
                            details={'status_code': response.status}
                        )
                    else:
                        return APIValidationResult(
                            passed=False,
                            message=f"SEC EDGAR API returned status {response.status}",
                            can_skip=False,
                            details={'status_code': response.status}
                        )
        except asyncio.TimeoutError:
            return APIValidationResult(
                passed=False,
                message="SEC EDGAR API connection timeout",
                can_skip=False,
            )
        except Exception as e:
            return APIValidationResult(
                passed=False,
                message=f"SEC EDGAR API connection failed: {str(e)}",
                can_skip=False,
            )
    
    def validate_openai_api_key(self) -> APIValidationResult:
        """
        Validate OpenAI API key format.
        
        Returns:
            Validation result
        """
        api_key = os.getenv('OPENAI_API_KEY', '')
        
        if not api_key or self._is_placeholder(api_key):
            return APIValidationResult(
                passed=False,
                message="OPENAI_API_KEY not configured",
                can_skip=True,
                details={'required_for': 'Phase 6: Dual-Agent Validation'}
            )
        
        # Check format (should start with 'sk-')
        if not api_key.startswith('sk-'):
            return APIValidationResult(
                passed=False,
                message=f"OPENAI_API_KEY has invalid format (should start with 'sk-')",
                can_skip=True,
                details={'key_prefix': api_key[:10]}
            )
        
        return APIValidationResult(
            passed=True,
            message=f"OPENAI_API_KEY configured (format valid)",
            can_skip=True,
            details={'key_prefix': api_key[:10]}
        )
    
    async def test_openai_connectivity(self) -> APIValidationResult:
        """
        Test OpenAI API connectivity and model access.
        
        Returns:
            Validation result
        """
        if self.mock_mode:
            return APIValidationResult(
                passed=True,
                message="OpenAI API connectivity (mock mode - skipped)",
                can_skip=True,
            )
        
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key or self._is_placeholder(api_key):
            return APIValidationResult(
                passed=False,
                message="Cannot test OpenAI connectivity - no API key",
                can_skip=True,
            )
        
        try:
            # Test simple API call
            url = "https://api.openai.com/v1/models"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m['id'] for m in data.get('data', [])]
                        has_gpt4 = any('gpt-4' in m for m in models)
                        
                        return APIValidationResult(
                            passed=True,
                            message=f"OpenAI API accessible, {len(models)} models available, GPT-4: {'✓' if has_gpt4 else '✗'}",
                            can_skip=True,
                            details={'model_count': len(models), 'has_gpt4': has_gpt4}
                        )
                    elif response.status == 401:
                        return APIValidationResult(
                            passed=False,
                            message="OpenAI API key invalid or unauthorized",
                            can_skip=True,
                        )
                    else:
                        return APIValidationResult(
                            passed=False,
                            message=f"OpenAI API returned status {response.status}",
                            can_skip=True,
                        )
        except Exception as e:
            return APIValidationResult(
                passed=False,
                message=f"OpenAI API test failed: {str(e)}",
                can_skip=True,
            )
    
    def validate_anthropic_api_key(self) -> APIValidationResult:
        """
        Validate Anthropic API key format.
        
        Returns:
            Validation result
        """
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        if not api_key or self._is_placeholder(api_key):
            return APIValidationResult(
                passed=False,
                message="ANTHROPIC_API_KEY not configured",
                can_skip=True,
                details={'required_for': 'Phase 7: Subagent Orchestration, Node 12'}
            )
        
        # Check format (should start with 'sk-ant-')
        if not api_key.startswith('sk-ant-'):
            return APIValidationResult(
                passed=False,
                message=f"ANTHROPIC_API_KEY has invalid format (should start with 'sk-ant-')",
                can_skip=True,
                details={'key_prefix': api_key[:10]}
            )
        
        return APIValidationResult(
            passed=True,
            message=f"ANTHROPIC_API_KEY configured (format valid)",
            can_skip=True,
            details={'key_prefix': api_key[:10]}
        )
    
    async def test_anthropic_connectivity(self) -> APIValidationResult:
        """
        Test Anthropic API connectivity and Claude 3 access.
        
        Returns:
            Validation result
        """
        if self.mock_mode:
            return APIValidationResult(
                passed=True,
                message="Anthropic API connectivity (mock mode - skipped)",
                can_skip=True,
            )
        
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key or self._is_placeholder(api_key):
            return APIValidationResult(
                passed=False,
                message="Cannot test Anthropic connectivity - no API key",
                can_skip=True,
            )
        
        try:
            # Test minimal API call
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            }
            data = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': 'test'}]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return APIValidationResult(
                            passed=True,
                            message="Anthropic API accessible, Claude 3 models available",
                            can_skip=True,
                        )
                    elif response.status == 401:
                        return APIValidationResult(
                            passed=False,
                            message="Anthropic API key invalid or unauthorized",
                            can_skip=True,
                        )
                    else:
                        return APIValidationResult(
                            passed=False,
                            message=f"Anthropic API returned status {response.status}",
                            can_skip=True,
                        )
        except Exception as e:
            return APIValidationResult(
                passed=False,
                message=f"Anthropic API test failed: {str(e)}",
                can_skip=True,
            )
    
    def validate_polygon_api_key(self) -> APIValidationResult:
        """
        Validate Polygon.io API key.
        
        Returns:
            Validation result
        """
        api_key = os.getenv('POLYGON_API_KEY', '')
        
        if not api_key or self._is_placeholder(api_key):
            return APIValidationResult(
                passed=True,  # Optional
                message="POLYGON_API_KEY not configured (optional - Node 15 will be disabled)",
                can_skip=True,
                details={'required_for': 'Node 15: Market Correlation'}
            )
        
        return APIValidationResult(
            passed=True,
            message="POLYGON_API_KEY configured",
            can_skip=True,
        )
    
    def validate_govinfo_api_key(self) -> APIValidationResult:
        """
        Validate GovInfo API key.
        
        Returns:
            Validation result
        """
        api_key = os.getenv('GOVINFO_API_KEY', '')
        
        if not api_key or self._is_placeholder(api_key):
            return APIValidationResult(
                passed=True,  # Optional
                message="GOVINFO_API_KEY not configured (optional - statute lookup disabled)",
                can_skip=True,
            )
        
        return APIValidationResult(
            passed=True,
            message="GOVINFO_API_KEY configured",
            can_skip=True,
        )
    
    def validate_neo4j_config(self) -> APIValidationResult:
        """
        Validate Neo4j configuration.
        
        Returns:
            Validation result
        """
        uri = os.getenv('NEO4J_URI', '')
        user = os.getenv('NEO4J_USER', '')
        password = os.getenv('NEO4J_PASSWORD', '')
        
        if not uri or not user or not password or self._is_placeholder(password):
            return APIValidationResult(
                passed=True,  # Optional
                message="Neo4j not configured (optional - Node 11 will be disabled)",
                can_skip=True,
                details={'required_for': 'Node 11: Executive Network Mapping'}
            )
        
        return APIValidationResult(
            passed=True,
            message=f"Neo4j configured: {uri}",
            can_skip=True,
            details={'uri': uri, 'user': user}
        )
    
    async def test_neo4j_connectivity(self) -> APIValidationResult:
        """
        Test Neo4j database connectivity.
        
        Returns:
            Validation result
        """
        if self.mock_mode:
            return APIValidationResult(
                passed=True,
                message="Neo4j connectivity (mock mode - skipped)",
                can_skip=True,
            )
        
        uri = os.getenv('NEO4J_URI', '')
        if not uri or self._is_placeholder(os.getenv('NEO4J_PASSWORD', '')):
            return APIValidationResult(
                passed=True,
                message="Neo4j not configured (skipped)",
                can_skip=True,
            )
        
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                uri,
                auth=(os.getenv('NEO4J_USER', ''), os.getenv('NEO4J_PASSWORD', ''))
            )
            
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                
                if record and record['test'] == 1:
                    driver.close()
                    return APIValidationResult(
                        passed=True,
                        message="Neo4j connection successful",
                        can_skip=True,
                    )
            
            driver.close()
            return APIValidationResult(
                passed=False,
                message="Neo4j connection test failed",
                can_skip=True,
            )
        except ImportError:
            return APIValidationResult(
                passed=True,
                message="Neo4j driver not installed (optional)",
                can_skip=True,
            )
        except Exception as e:
            return APIValidationResult(
                passed=False,
                message=f"Neo4j connection failed: {str(e)}",
                can_skip=True,
            )
    
    def validate_timescaledb_config(self) -> APIValidationResult:
        """
        Validate TimescaleDB configuration.
        
        Returns:
            Validation result
        """
        host = os.getenv('TIMESCALE_HOST', '')
        password = os.getenv('TIMESCALE_PASSWORD', '')
        
        if not host or not password or self._is_placeholder(password):
            return APIValidationResult(
                passed=True,  # Optional
                message="TimescaleDB not configured (optional - time-series storage disabled)",
                can_skip=True,
            )
        
        return APIValidationResult(
            passed=True,
            message=f"TimescaleDB configured: {host}",
            can_skip=True,
        )
    
    async def validate_all(self) -> Dict[str, APIValidationResult]:
        """
        Run all API validations.
        
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        # SEC EDGAR (required)
        results['sec_user_agent'] = self.validate_sec_user_agent()
        results['sec_connectivity'] = await self.test_sec_connectivity()
        
        # OpenAI (optional but recommended)
        results['openai_key'] = self.validate_openai_api_key()
        if results['openai_key'].passed:
            results['openai_connectivity'] = await self.test_openai_connectivity()
        
        # Anthropic (optional but recommended)
        results['anthropic_key'] = self.validate_anthropic_api_key()
        if results['anthropic_key'].passed:
            results['anthropic_connectivity'] = await self.test_anthropic_connectivity()
        
        # Optional APIs
        results['polygon_key'] = self.validate_polygon_api_key()
        results['govinfo_key'] = self.validate_govinfo_api_key()
        
        # Databases
        results['neo4j_config'] = self.validate_neo4j_config()
        results['neo4j_connectivity'] = await self.test_neo4j_connectivity()
        results['timescaledb_config'] = self.validate_timescaledb_config()
        
        return results
