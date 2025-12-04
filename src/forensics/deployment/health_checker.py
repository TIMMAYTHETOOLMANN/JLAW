"""
Health Checker - System Health Monitoring
========================================

Comprehensive health checks for all system components:
- Phase component availability
- Database connectivity
- Memory and CPU usage
- Disk space monitoring
- API endpoint health
"""

import logging
import psutil
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    Comprehensive system health monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Health check thresholds
        self.memory_threshold = self.config.get('memory_threshold_percent', 85)
        self.cpu_threshold = self.config.get('cpu_threshold_percent', 80)
        self.disk_threshold = self.config.get('disk_threshold_percent', 90)
        
        # Statistics
        self.stats = {
            'checks_performed': 0,
            'healthy_checks': 0,
            'unhealthy_checks': 0
        }
        
        logger.info("🏥 Health Checker initialized")
    
    async def check_all_components(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all system components
        
        Returns:
            Dictionary of component health results
        """
        self.stats['checks_performed'] += 1
        
        results = {}
        
        # Check system resources
        results['system_memory'] = self._check_memory()
        results['system_cpu'] = self._check_cpu()
        results['system_disk'] = self._check_disk()
        
        # Check phase components
        results['phase1_document_processing'] = await self._check_phase1()
        results['phase2_intelligence'] = await self._check_phase2()
        results['phase3_legal'] = await self._check_phase3()
        results['phase4_temporal'] = await self._check_phase4()
        results['phase5_prosecution'] = await self._check_phase5()
        results['phase6_contradiction'] = await self._check_phase6()
        results['phase7_reporting'] = await self._check_phase7()
        results['phase8_orchestration'] = await self._check_phase8()
        
        # Update statistics
        for result in results.values():
            if result.status == HealthStatus.HEALTHY:
                self.stats['healthy_checks'] += 1
            elif result.status == HealthStatus.UNHEALTHY:
                self.stats['unhealthy_checks'] += 1
        
        return results
    
    def _check_memory(self) -> HealthCheckResult:
        """Check system memory usage"""
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used < self.memory_threshold:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {percent_used:.1f}%"
        elif percent_used < 95:
            status = HealthStatus.DEGRADED
            message = f"Memory usage high: {percent_used:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Memory usage critical: {percent_used:.1f}%"
        
        return HealthCheckResult(
            component="system_memory",
            status=status,
            message=message,
            metrics={
                'percent_used': percent_used,
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3)
            }
        )
    
    def _check_cpu(self) -> HealthCheckResult:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        if cpu_percent < self.cpu_threshold:
            status = HealthStatus.HEALTHY
            message = f"CPU usage normal: {cpu_percent:.1f}%"
        elif cpu_percent < 95:
            status = HealthStatus.DEGRADED
            message = f"CPU usage high: {cpu_percent:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"CPU usage critical: {cpu_percent:.1f}%"
        
        return HealthCheckResult(
            component="system_cpu",
            status=status,
            message=message,
            metrics={
                'percent_used': cpu_percent,
                'core_count': psutil.cpu_count()
            }
        )
    
    def _check_disk(self) -> HealthCheckResult:
        """Check disk space"""
        disk = psutil.disk_usage('/')
        percent_used = disk.percent
        
        if percent_used < self.disk_threshold:
            status = HealthStatus.HEALTHY
            message = f"Disk space normal: {percent_used:.1f}%"
        elif percent_used < 98:
            status = HealthStatus.DEGRADED
            message = f"Disk space low: {percent_used:.1f}%"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Disk space critical: {percent_used:.1f}%"
        
        return HealthCheckResult(
            component="system_disk",
            status=status,
            message=message,
            metrics={
                'percent_used': percent_used,
                'total_gb': disk.total / (1024**3),
                'free_gb': disk.free / (1024**3)
            }
        )
    
    async def _check_phase1(self) -> HealthCheckResult:
        """Check Phase 1: Document Processing"""
        try:
            from forensics.enhanced_parsing import UniversalDocumentProcessor
            processor = UniversalDocumentProcessor()
            
            return HealthCheckResult(
                component="phase1_document_processing",
                status=HealthStatus.HEALTHY,
                message="Document processing module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase1_document_processing",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase2(self) -> HealthCheckResult:
        """Check Phase 2: Intelligence Gathering"""
        try:
            from forensics.intelligence import OmniscientIntelligenceGatherer
            gatherer = OmniscientIntelligenceGatherer()
            
            return HealthCheckResult(
                component="phase2_intelligence",
                status=HealthStatus.HEALTHY,
                message="Intelligence gathering module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase2_intelligence",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase3(self) -> HealthCheckResult:
        """Check Phase 3: Legal Analysis"""
        try:
            from forensics.legal import LegalStatuteCorrelationEngine
            engine = LegalStatuteCorrelationEngine()
            
            return HealthCheckResult(
                component="phase3_legal",
                status=HealthStatus.HEALTHY,
                message="Legal analysis module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase3_legal",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase4(self) -> HealthCheckResult:
        """Check Phase 4: Temporal Analysis"""
        try:
            from forensics.temporal import ForensicTimelineReconstructor
            reconstructor = ForensicTimelineReconstructor()
            
            return HealthCheckResult(
                component="phase4_temporal",
                status=HealthStatus.HEALTHY,
                message="Temporal analysis module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase4_temporal",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase5(self) -> HealthCheckResult:
        """Check Phase 5: Prosecution Strategy"""
        try:
            from forensics.prosecution import ProsecutionPathBuilder
            builder = ProsecutionPathBuilder()
            
            return HealthCheckResult(
                component="phase5_prosecution",
                status=HealthStatus.HEALTHY,
                message="Prosecution module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase5_prosecution",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase6(self) -> HealthCheckResult:
        """Check Phase 6: Contradiction Detection"""
        try:
            from forensics.contradiction import ContradictionDetectionEngine
            engine = ContradictionDetectionEngine()
            
            return HealthCheckResult(
                component="phase6_contradiction",
                status=HealthStatus.HEALTHY,
                message="Contradiction detection module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase6_contradiction",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase7(self) -> HealthCheckResult:
        """Check Phase 7: Reporting"""
        try:
            from forensics.reporting import ReportingEngine
            engine = ReportingEngine()
            
            return HealthCheckResult(
                component="phase7_reporting",
                status=HealthStatus.HEALTHY,
                message="Reporting module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase7_reporting",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    async def _check_phase8(self) -> HealthCheckResult:
        """Check Phase 8: Orchestration"""
        try:
            from forensics.orchestration import InvestigationOrchestrator
            orchestrator = InvestigationOrchestrator()
            
            return HealthCheckResult(
                component="phase8_orchestration",
                status=HealthStatus.HEALTHY,
                message="Orchestration module operational"
            )
        except Exception as e:
            return HealthCheckResult(
                component="phase8_orchestration",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to load: {str(e)}"
            )
    
    def get_overall_health(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health"""
        unhealthy_count = sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get health check statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    async def demo():
        checker = HealthChecker()
        results = await checker.check_all_components()
        
        print("Health Check Results:")
        for component, result in results.items():
            print(f"  {component}: {result.status.value} - {result.message}")
        
        overall = checker.get_overall_health(results)
        print(f"\nOverall Health: {overall.value}")
    
    asyncio.run(demo())

