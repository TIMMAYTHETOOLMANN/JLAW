"""
Stealth Browser - Undetectable Web Scraping
===========================================

Headless browser with anti-detection capabilities for forensic intelligence gathering.

Features:
- Playwright-based headless browsing
- User agent rotation
- Fingerprint randomization
- Proxy support
- Rate limiting and delays
- JavaScript execution
- Screenshot capture

Usage:
    browser = StealthBrowser()
    html = await browser.fetch_page("https://example.com")
    await browser.close()
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Browser configuration"""
    headless: bool = True
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    delay_min: float = 1.0
    delay_max: float = 3.0


class StealthBrowser:
    """
    Stealth browser for undetectable web scraping.
    
    Uses Playwright with anti-detection measures to avoid blocking.
    Implements random delays, user agent rotation, and fingerprint randomization.
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._user_agents = self._get_user_agents()
        logger.info("✅ StealthBrowser initialized")
    
    def _get_user_agents(self) -> List[str]:
        """Get list of realistic user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
    
    async def start(self):
        """Initialize browser"""
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            # Launch browser with stealth options
            launch_options = {
                "headless": self.config.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ]
            }
            
            self._browser = await self._playwright.chromium.launch(**launch_options)
            
            # Create context with random fingerprint
            context_options = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                },
                "user_agent": self.config.user_agent or random.choice(self._user_agents),
            }
            
            if self.config.use_proxy and self.config.proxy_url:
                context_options["proxy"] = {"server": self.config.proxy_url}
            
            self._context = await self._browser.new_context(**context_options)
            
            # Add stealth scripts
            await self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            self._page = await self._context.new_page()
            
            logger.info("✅ Stealth browser started")
            
        except ImportError:
            logger.warning("⚠️ Playwright not available - using fallback mode")
            self._browser = None
    
    async def fetch_page(self, url: str, wait_for: Optional[str] = None) -> str:
        """
        Fetch page content with stealth mode.
        
        Args:
            url: URL to fetch
            wait_for: Optional selector to wait for
            
        Returns:
            HTML content
        """
        if not self._page:
            await self.start()
        
        if not self._page:
            # Fallback to simple HTTP request
            logger.warning("Using fallback HTTP request")
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()
        
        try:
            # Random delay before navigation
            delay = random.uniform(self.config.delay_min, self.config.delay_max)
            await asyncio.sleep(delay)
            
            # Navigate to page
            await self._page.goto(url, timeout=self.config.timeout)
            
            # Wait for selector if specified
            if wait_for:
                await self._page.wait_for_selector(wait_for, timeout=self.config.timeout)
            
            # Get content
            content = await self._page.content()
            
            logger.info(f"✅ Fetched page: {url[:100]}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            raise
    
    async def screenshot(self, url: str, path: str):
        """Take screenshot of page"""
        if not self._page:
            await self.start()
        
        if not self._page:
            raise RuntimeError("Browser not available")
        
        await self._page.goto(url, timeout=self.config.timeout)
        await self._page.screenshot(path=path, full_page=True)
        logger.info(f"✅ Screenshot saved: {path}")
    
    async def execute_script(self, url: str, script: str) -> Any:
        """Execute JavaScript on page"""
        if not self._page:
            await self.start()
        
        if not self._page:
            raise RuntimeError("Browser not available")
        
        await self._page.goto(url, timeout=self.config.timeout)
        result = await self._page.evaluate(script)
        return result
    
    async def close(self):
        """Close browser"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("✅ Stealth browser closed")
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


# Singleton instance manager
class StealthBrowserManager:
    """Manages singleton stealth browser instance"""
    
    _instance: Optional[StealthBrowser] = None
    
    @classmethod
    async def get_browser(cls, config: Optional[BrowserConfig] = None) -> StealthBrowser:
        """Get or create browser instance"""
        if cls._instance is None:
            cls._instance = StealthBrowser(config)
            await cls._instance.start()
        return cls._instance
    
    @classmethod
    async def close_browser(cls):
        """Close browser instance"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

