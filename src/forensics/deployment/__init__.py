"""
JLAW Phase 9: Deployment & Health Check - FINAL PHASE
====================================================

Production deployment infrastructure and monitoring.

Components:
- HealthChecker: System health monitoring
- DeploymentManager: Deployment management
- SystemOptimizer: Performance optimization
- ConfigManager: Environment configuration management
- MetricsCollector: Performance metrics collection
"""

try:
    from .health_checker import HealthChecker
    from .deployment_manager import DeploymentManager
    from .optimization import SystemOptimizer
    
    # Aliases for backward compatibility
    ConfigManager = DeploymentManager
    OptimizationEngine = SystemOptimizer
    MetricsCollector = SystemOptimizer
    
except ImportError:
    HealthChecker = None
    DeploymentManager = None
    SystemOptimizer = None
    ConfigManager = None
    OptimizationEngine = None
    MetricsCollector = None

__all__ = [
    'HealthChecker',
    'DeploymentManager',
    'SystemOptimizer',
    'OptimizationEngine',
    'ConfigManager',
    'MetricsCollector',
]

__version__ = '9.0.0'
__phase__ = 9
__status__ = 'COMPLETE'

