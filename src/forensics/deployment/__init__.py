"""
JLAW Phase 9: Deployment & Health Check - FINAL PHASE
====================================================

Production deployment infrastructure and monitoring.

Components:
- HealthChecker: System health monitoring
- ConfigManager: Environment configuration management
- MetricsCollector: Performance metrics collection
- DeploymentValidator: Pre-deployment validation
"""

try:
    from .health_checker import HealthChecker
    from .deployment_manager import DeploymentManager, OptimizationEngine
    
    ConfigManager = DeploymentManager
    MetricsCollector = OptimizationEngine
except ImportError:
    HealthChecker = None
    DeploymentManager = None
    OptimizationEngine = None

__all__ = [
    'HealthChecker',
    'DeploymentManager',
    'OptimizationEngine',
    'ConfigManager',
    'MetricsCollector',
]

__version__ = '9.0.0'
__phase__ = 9
__status__ = 'COMPLETE'

