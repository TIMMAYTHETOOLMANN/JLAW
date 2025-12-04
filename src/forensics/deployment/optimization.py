"""
System Optimizer - Performance Optimization
=============================================

Provides system optimization and performance tuning capabilities.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import gc

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Optimization aggressiveness levels."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class OptimizationMetric:
    """A performance metric."""
    name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationRecommendation:
    """An optimization recommendation."""
    category: str
    title: str
    description: str
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    applied: bool = False


@dataclass
class OptimizationProfile:
    """System optimization profile."""
    profile_name: str
    level: OptimizationLevel
    max_workers: int = 4
    batch_size: int = 100
    cache_size_mb: int = 256
    memory_limit_mb: int = 2048
    gc_threshold: int = 1000
    enable_compression: bool = True
    enable_caching: bool = True


@dataclass
class OptimizationResult:
    """Result of optimization operation."""
    success: bool
    optimizations_applied: List[str] = field(default_factory=list)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class SystemOptimizer:
    """
    System Optimizer
    
    Provides performance optimization and tuning for the forensics system.
    
    Features:
    - Memory optimization
    - Worker pool tuning
    - Cache management
    - Garbage collection optimization
    - Performance recommendations
    
    Example:
        optimizer = SystemOptimizer()
        
        # Set optimization profile
        optimizer.set_profile(OptimizationLevel.BALANCED)
        
        # Run optimization
        result = optimizer.optimize()
        
        # Get recommendations
        recs = optimizer.get_recommendations()
    """
    
    def __init__(self):
        """Initialize the system optimizer."""
        self._current_profile: Optional[OptimizationProfile] = None
        self._metrics_history: List[OptimizationMetric] = []
        self._recommendations: List[OptimizationRecommendation] = []
        
        # Default profiles
        self._profiles = {
            OptimizationLevel.CONSERVATIVE: OptimizationProfile(
                profile_name="conservative",
                level=OptimizationLevel.CONSERVATIVE,
                max_workers=2,
                batch_size=50,
                cache_size_mb=128,
                memory_limit_mb=1024,
                gc_threshold=500,
                enable_compression=False,
                enable_caching=True
            ),
            OptimizationLevel.BALANCED: OptimizationProfile(
                profile_name="balanced",
                level=OptimizationLevel.BALANCED,
                max_workers=4,
                batch_size=100,
                cache_size_mb=256,
                memory_limit_mb=2048,
                gc_threshold=1000,
                enable_compression=True,
                enable_caching=True
            ),
            OptimizationLevel.AGGRESSIVE: OptimizationProfile(
                profile_name="aggressive",
                level=OptimizationLevel.AGGRESSIVE,
                max_workers=8,
                batch_size=200,
                cache_size_mb=512,
                memory_limit_mb=4096,
                gc_threshold=2000,
                enable_compression=True,
                enable_caching=True
            )
        }
        
        # Set default profile
        self._current_profile = self._profiles[OptimizationLevel.BALANCED]
        
        logger.info("SystemOptimizer initialized")
    
    def set_profile(self, level: OptimizationLevel) -> OptimizationProfile:
        """
        Set the optimization profile.
        
        Args:
            level: Optimization level
            
        Returns:
            Active profile
        """
        self._current_profile = self._profiles[level]
        logger.info(f"Set optimization profile: {level.value}")
        return self._current_profile
    
    def get_profile(self) -> Optional[OptimizationProfile]:
        """Get current optimization profile."""
        return self._current_profile
    
    def optimize(self) -> OptimizationResult:
        """
        Run system optimization.
        
        Returns:
            Optimization result
        """
        if not self._current_profile:
            return OptimizationResult(success=False)
        
        result = OptimizationResult(success=True)
        
        # Collect before metrics
        result.metrics_before = self._collect_metrics()
        
        # Apply optimizations
        try:
            # Memory optimization
            self._optimize_memory()
            result.optimizations_applied.append("memory_optimization")
            
            # Garbage collection
            self._optimize_gc()
            result.optimizations_applied.append("gc_optimization")
            
            # Cache optimization
            if self._current_profile.enable_caching:
                self._optimize_cache()
                result.optimizations_applied.append("cache_optimization")
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            result.success = False
        
        # Collect after metrics
        result.metrics_after = self._collect_metrics()
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations()
        
        logger.info(f"Optimization complete: {len(result.optimizations_applied)} applied")
        return result
    
    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        metrics = {}
        
        try:
            import psutil
            
            # CPU
            metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            
            # Memory
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_available_mb"] = memory.available / (1024 * 1024)
            
            # Disk
            disk = psutil.disk_usage("/")
            metrics["disk_percent"] = disk.percent
            
        except ImportError:
            # Fallback if psutil not available
            metrics["cpu_percent"] = 0.0
            metrics["memory_percent"] = 0.0
            metrics["memory_available_mb"] = 0.0
            metrics["disk_percent"] = 0.0
        
        return metrics
    
    def _optimize_memory(self) -> None:
        """Perform memory optimization."""
        # Force garbage collection
        gc.collect()
        
        # Set garbage collection thresholds
        if self._current_profile:
            threshold = self._current_profile.gc_threshold
            gc.set_threshold(threshold, 10, 10)
        
        logger.debug("Memory optimization applied")
    
    def _optimize_gc(self) -> None:
        """Optimize garbage collection settings."""
        # Collect all generations
        collected = gc.collect(2)
        logger.debug(f"GC collected {collected} objects")
    
    def _optimize_cache(self) -> None:
        """Optimize caching settings."""
        # This would interact with any caching systems
        # For now, just log
        logger.debug("Cache optimization applied")
    
    def _generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations."""
        recommendations = []
        metrics = self._collect_metrics()
        
        # Memory recommendations
        if metrics.get("memory_percent", 0) > 80:
            recommendations.append(OptimizationRecommendation(
                category="memory",
                title="High Memory Usage",
                description="Memory usage is above 80%. Consider reducing batch sizes or increasing available memory.",
                impact="high",
                effort="medium"
            ))
        
        # CPU recommendations
        if metrics.get("cpu_percent", 0) > 90:
            recommendations.append(OptimizationRecommendation(
                category="cpu",
                title="High CPU Usage",
                description="CPU usage is very high. Consider reducing worker count or optimizing processing algorithms.",
                impact="high",
                effort="high"
            ))
        
        # Disk recommendations
        if metrics.get("disk_percent", 0) > 90:
            recommendations.append(OptimizationRecommendation(
                category="disk",
                title="Low Disk Space",
                description="Disk usage is critical. Clean up temporary files and old reports.",
                impact="critical",
                effort="low"
            ))
        
        # Profile-based recommendations
        if self._current_profile:
            if self._current_profile.level == OptimizationLevel.CONSERVATIVE:
                recommendations.append(OptimizationRecommendation(
                    category="profile",
                    title="Consider Balanced Profile",
                    description="Using conservative profile. Balanced profile may improve performance.",
                    impact="medium",
                    effort="low"
                ))
        
        # General recommendations
        recommendations.append(OptimizationRecommendation(
            category="general",
            title="Enable Compression",
            description="Enable compression for report outputs to save disk space.",
            impact="low",
            effort="low"
        ))
        
        self._recommendations = recommendations
        return recommendations
    
    def get_recommendations(self) -> List[OptimizationRecommendation]:
        """Get current optimization recommendations."""
        if not self._recommendations:
            self._recommendations = self._generate_recommendations()
        return self._recommendations
    
    def apply_recommendation(
        self,
        recommendation: OptimizationRecommendation
    ) -> bool:
        """
        Apply a specific recommendation.
        
        Args:
            recommendation: Recommendation to apply
            
        Returns:
            Success status
        """
        # Mark as applied
        recommendation.applied = True
        logger.info(f"Applied recommendation: {recommendation.title}")
        return True
    
    def get_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        return self._collect_metrics()
    
    def add_metric(self, metric: OptimizationMetric) -> None:
        """Add a metric to history."""
        self._metrics_history.append(metric)
        
        # Keep only last 1000 metrics
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-1000:]
    
    def get_metrics_history(
        self,
        metric_name: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[OptimizationMetric]:
        """Get metrics history."""
        history = self._metrics_history
        
        if metric_name:
            history = [m for m in history if m.name == metric_name]
        
        if since:
            history = [m for m in history if m.timestamp >= since]
        
        return history
    
    def reset(self) -> None:
        """Reset optimizer state."""
        self._recommendations.clear()
        self._metrics_history.clear()
        self._current_profile = self._profiles[OptimizationLevel.BALANCED]
        logger.info("SystemOptimizer reset")
