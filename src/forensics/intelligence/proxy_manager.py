"""
Proxy Rotation Manager - Anti-Detection Infrastructure
====================================================

Advanced proxy management for:
- Rotating residential proxies
- Datacenter proxy pools
- Rate limit distribution
- Geographic distribution
- Automatic failure detection and rotation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class ProxyServer:
    """Proxy server configuration"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    country: Optional[str] = None
    provider: str = "unknown"
    
    # Performance metrics
    success_count: int = 0
    failure_count: int = 0
    avg_latency: float = 0.0
    last_used: Optional[datetime] = None
    is_active: bool = True
    
    def get_url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total


class ProxyRotationManager:
    """
    Intelligent proxy rotation with failure detection and optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.proxies: List[ProxyServer] = []
        self.proxy_pool: Dict[str, List[ProxyServer]] = defaultdict(list)
        
        # Configuration
        self.min_success_rate = self.config.get('min_success_rate', 0.5)
        self.max_failures_before_disable = self.config.get('max_failures', 5)
        self.cooldown_period = timedelta(minutes=self.config.get('cooldown_minutes', 15))
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxies_rotated': 0,
            'proxies_disabled': 0
        }
        
        # Load proxies from config
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxy list from configuration"""
        proxy_configs = self.config.get('proxies', [])
        
        for proxy_config in proxy_configs:
            proxy = ProxyServer(
                host=proxy_config['host'],
                port=proxy_config['port'],
                username=proxy_config.get('username'),
                password=proxy_config.get('password'),
                protocol=proxy_config.get('protocol', 'http'),
                country=proxy_config.get('country'),
                provider=proxy_config.get('provider', 'manual')
            )
            
            self.proxies.append(proxy)
            
            # Organize by country
            if proxy.country:
                self.proxy_pool[proxy.country].append(proxy)
            else:
                self.proxy_pool['global'].append(proxy)
        
        logger.info(f"✓ Loaded {len(self.proxies)} proxy servers")
    
    def add_proxy(self, proxy: ProxyServer):
        """Add proxy to pool"""
        self.proxies.append(proxy)
        
        if proxy.country:
            self.proxy_pool[proxy.country].append(proxy)
        else:
            self.proxy_pool['global'].append(proxy)
    
    def get_proxy(
        self,
        country: Optional[str] = None,
        strategy: str = 'round_robin'
    ) -> Optional[ProxyServer]:
        """
        Get next proxy based on strategy
        
        Args:
            country: Target country (None for any)
            strategy: Selection strategy
                - 'round_robin': Sequential rotation
                - 'random': Random selection
                - 'best_performance': Select by success rate
                - 'least_used': Select least recently used
        
        Returns:
            ProxyServer or None if no proxies available
        """
        # Get candidate pool
        if country:
            candidates = self.proxy_pool.get(country, [])
        else:
            candidates = self.proxies
        
        # Filter active proxies
        active = [p for p in candidates if p.is_active and self._is_proxy_available(p)]
        
        if not active:
            logger.warning("⚠️ No active proxies available")
            return None
        
        # Apply selection strategy
        if strategy == 'random':
            proxy = random.choice(active)
        
        elif strategy == 'best_performance':
            # Sort by success rate, then by avg latency
            proxy = max(active, key=lambda p: (p.success_rate(), -p.avg_latency))
        
        elif strategy == 'least_used':
            # Sort by last used time
            proxy = min(active, key=lambda p: p.last_used or datetime.min)
        
        else:  # round_robin
            # Get least recently used
            proxy = min(active, key=lambda p: p.last_used or datetime.min)
        
        proxy.last_used = datetime.now()
        self.stats['proxies_rotated'] += 1
        
        return proxy
    
    def _is_proxy_available(self, proxy: ProxyServer) -> bool:
        """Check if proxy is available (not in cooldown)"""
        if not proxy.last_used:
            return True
        
        # Check if cooldown period has passed
        if datetime.now() - proxy.last_used < self.cooldown_period:
            # Allow if success rate is high
            if proxy.success_rate() < 0.8:
                return False
        
        return True
    
    def record_success(
        self,
        proxy: ProxyServer,
        latency: float
    ):
        """Record successful proxy usage"""
        proxy.success_count += 1
        
        # Update average latency
        if proxy.avg_latency == 0.0:
            proxy.avg_latency = latency
        else:
            # Exponential moving average
            proxy.avg_latency = 0.7 * proxy.avg_latency + 0.3 * latency
        
        self.stats['successful_requests'] += 1
        self.stats['total_requests'] += 1
    
    def record_failure(
        self,
        proxy: ProxyServer,
        error: str
    ):
        """Record proxy failure"""
        proxy.failure_count += 1
        
        self.stats['failed_requests'] += 1
        self.stats['total_requests'] += 1
        
        # Check if proxy should be disabled
        if proxy.failure_count >= self.max_failures_before_disable:
            if proxy.success_rate() < self.min_success_rate:
                logger.warning(
                    f"⚠️ Disabling proxy {proxy.host}:{proxy.port} "
                    f"(success rate: {proxy.success_rate():.2%})"
                )
                proxy.is_active = False
                self.stats['proxies_disabled'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get proxy pool statistics"""
        active_count = sum(1 for p in self.proxies if p.is_active)
        
        return {
            'total_proxies': len(self.proxies),
            'active_proxies': active_count,
            'disabled_proxies': len(self.proxies) - active_count,
            'countries': list(self.proxy_pool.keys()),
            'usage_stats': self.stats.copy(),
            'overall_success_rate': (
                self.stats['successful_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0.0
            )
        }
    
    def reset_proxy(self, proxy: ProxyServer):
        """Reset proxy statistics and reactivate"""
        proxy.success_count = 0
        proxy.failure_count = 0
        proxy.is_active = True
        proxy.last_used = None
        
        logger.info(f"✓ Reset proxy {proxy.host}:{proxy.port}")
    
    async def test_proxies(self, test_url: str = "https://httpbin.org/ip"):
        """
        Test all proxies for connectivity
        
        Args:
            test_url: URL to test against
        """
        import aiohttp
        
        logger.info(f"🧪 Testing {len(self.proxies)} proxies...")
        
        async def test_proxy(proxy: ProxyServer):
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = datetime.now()
                    
                    async with session.get(
                        test_url,
                        proxy=proxy.get_url(),
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        latency = (datetime.now() - start_time).total_seconds()
                        
                        if response.status == 200:
                            self.record_success(proxy, latency)
                            logger.info(f"✓ {proxy.host}:{proxy.port} - {latency:.2f}s")
                            return True
                        else:
                            self.record_failure(proxy, f"HTTP {response.status}")
                            return False
            
            except Exception as e:
                self.record_failure(proxy, str(e))
                logger.warning(f"✗ {proxy.host}:{proxy.port} - {e}")
                return False
        
        # Test all proxies in parallel
        tasks = [test_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(results)
        logger.info(
            f"✓ Proxy test complete: {success_count}/{len(self.proxies)} working "
            f"({success_count/len(self.proxies):.1%})"
        )


if __name__ == "__main__":
    # Demo
    async def demo():
        # Example configuration
        config = {
            'proxies': [
                {
                    'host': '1.2.3.4',
                    'port': 8080,
                    'country': 'US'
                },
                {
                    'host': '5.6.7.8',
                    'port': 8080,
                    'country': 'UK'
                }
            ]
        }
        
        manager = ProxyRotationManager(config)
        
        # Get proxy
        proxy = manager.get_proxy(strategy='best_performance')
        if proxy:
            print(f"Selected proxy: {proxy.get_url()}")
        
        # Statistics
        stats = manager.get_statistics()
        print(f"Statistics: {stats}")
    
    asyncio.run(demo())

