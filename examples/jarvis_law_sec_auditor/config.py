"""
JARVIS:LAW Black Site Protocol - Configuration Module
Centralized configuration with API key management
"""

import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded configuration from {env_path}")
except ImportError:
    print("⚠ python-dotenv not installed. Using system environment variables only.")
    print("  Install with: pip install python-dotenv")


class Config:
    """Centralized configuration for JARVIS:LAW Black Site Protocol"""
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')
    
    # GovInfo API Configuration (also works with SEC EDGAR Online)
    GOVINFO_API_KEY: str = os.getenv('GOVINFO_API_KEY', '')
    SEC_EDGAR_API_KEY: str = os.getenv('SEC_EDGAR_API_KEY', '') or os.getenv('GOVINFO_API_KEY', '')
    
    # SEC.gov Configuration
    SEC_BASE_URL: str = "https://www.sec.gov"
    SEC_USER_AGENT: str = os.getenv('SEC_USER_AGENT', 'JarvisLAW/1.0 (forensics@domain.com)')
    
    # Rate Limiting
    SEC_RATE_LIMIT_REQUESTS_PER_SECOND: int = int(os.getenv('SEC_RATE_LIMIT_REQUESTS_PER_SECOND', '10'))
    SEC_REQUEST_DELAY_MS: int = int(os.getenv('SEC_REQUEST_DELAY_MS', '120'))
    SEC_REQUEST_DELAY_SECONDS: float = SEC_REQUEST_DELAY_MS / 1000.0
    
    # Evidence Chain Configuration
    EVIDENCE_CHAIN_ENABLED: bool = os.getenv('EVIDENCE_CHAIN_ENABLED', 'true').lower() == 'true'
    CRYPTOGRAPHIC_HASHING: str = os.getenv('CRYPTOGRAPHIC_HASHING', 'SHA-256')
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).parent
    MEMORY_DIR: Path = BASE_DIR / 'memory'
    SEC_FILINGS_ARCHIVE_DIR: Path = MEMORY_DIR / 'sec_filings_archive'
    EVIDENCE_CHAIN_DIR: Path = MEMORY_DIR / 'evidence_chain'
    
    # Deployment Configuration
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls) -> dict:
        """Validate configuration and return status"""
        status = {
            'openai_api_key': bool(cls.OPENAI_API_KEY),
            'govinfo_api_key': bool(cls.GOVINFO_API_KEY),
            'sec_edgar_api_key': bool(cls.SEC_EDGAR_API_KEY),
            'directories_exist': all([
                cls.MEMORY_DIR.exists(),
                cls.SEC_FILINGS_ARCHIVE_DIR.exists(),
                cls.EVIDENCE_CHAIN_DIR.exists(),
            ])
        }
        return status
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.MEMORY_DIR.mkdir(exist_ok=True)
        cls.SEC_FILINGS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        cls.EVIDENCE_CHAIN_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_sec_headers(cls) -> dict:
        """Get SEC-compliant HTTP headers"""
        headers = {
            'User-Agent': cls.SEC_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Add API key if available (for SEC EDGAR Online)
        if cls.SEC_EDGAR_API_KEY:
            headers['X-Api-Key'] = cls.SEC_EDGAR_API_KEY
        
        return headers
    
    @classmethod
    def print_status(cls):
        """Print configuration status"""
        print("\n" + "="*70)
        print("JARVIS:LAW BLACK SITE PROTOCOL - CONFIGURATION STATUS")
        print("="*70)
        
        status = cls.validate()
        
        print(f"OpenAI API Key: {'[OK] Configured' if status['openai_api_key'] else '[X] Missing'}")
        print(f"GovInfo API Key: {'[OK] Configured' if status['govinfo_api_key'] else '[X] Missing'}")
        print(f"SEC EDGAR API Key: {'[OK] Configured' if status['sec_edgar_api_key'] else '[X] Missing'}")
        print(f"Directories: {'[OK] Ready' if status['directories_exist'] else '[X] Not Created'}")
        print(f"Environment: {cls.ENVIRONMENT}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Evidence Chain: {'Enabled' if cls.EVIDENCE_CHAIN_ENABLED else 'Disabled'}")
        print(f"Rate Limit: {cls.SEC_RATE_LIMIT_REQUESTS_PER_SECOND} req/sec")
        print("="*70 + "\n")
        
        # Warnings
        if not status['openai_api_key']:
            print("⚠ WARNING: OpenAI API key not configured")
            print("  Set OPENAI_API_KEY in .env file or environment\n")
        
        if not status['govinfo_api_key']:
            print("⚠ WARNING: GovInfo API key not configured (optional)")
            print("  Set GOVINFO_API_KEY in .env file for enhanced metadata\n")
        
        if not status['directories_exist']:
            print("⚠ WARNING: Required directories missing")
            print("  Run Config.ensure_directories() to create them\n")


# Auto-create directories on import
Config.ensure_directories()


# Export configuration instance
config = Config()


if __name__ == "__main__":
    # Display configuration status when run directly
    Config.print_status()

