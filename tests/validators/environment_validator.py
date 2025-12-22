"""
Environment Validator - Validate Python version, dependencies, and system resources.
"""

import sys
import os
import importlib
import platform
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class EnvironmentValidationResult:
    """Result from environment validation."""
    passed: bool
    message: str
    details: Optional[Dict] = None


class EnvironmentValidator:
    """
    Validate environment and dependencies.
    
    Checks:
    - Python version (3.10+ required)
    - All pip packages from requirements.txt
    - Optional heavy dependencies (torch, transformers, DeBERTa)
    - Virtual environment detection
    - System resources (RAM, disk space, CPU cores)
    """
    
    # Minimum requirements
    MIN_PYTHON_VERSION = (3, 10)
    MIN_RAM_GB = 4
    MIN_DISK_GB = 5
    MIN_CPU_CORES = 2
    
    # Optional dependencies that system can gracefully degrade without
    OPTIONAL_DEPENDENCIES = {
        'torch',
        'transformers',
        'neo4j',
        'websockets',
        'redis',
        'psycopg2',
        'asyncpg',
        'faiss',
        'optuna',
        'streamlit',
    }
    
    def __init__(self):
        """Initialize environment validator."""
        self.project_root = self._find_project_root()
    
    def _find_project_root(self) -> Path:
        """Find project root directory."""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / 'requirements.txt').exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def validate_python_version(self) -> EnvironmentValidationResult:
        """
        Validate Python version.
        
        Returns:
            Validation result with pass/fail status
        """
        current_version = sys.version_info[:2]
        
        if current_version >= self.MIN_PYTHON_VERSION:
            return EnvironmentValidationResult(
                passed=True,
                message=f"Python {current_version[0]}.{current_version[1]} is compatible (requires {self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]}+)",
                details={
                    'version': f"{current_version[0]}.{current_version[1]}.{sys.version_info[2]}",
                    'executable': sys.executable,
                }
            )
        else:
            return EnvironmentValidationResult(
                passed=False,
                message=f"Python {current_version[0]}.{current_version[1]} is too old (requires {self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]}+)",
                details={
                    'version': f"{current_version[0]}.{current_version[1]}.{sys.version_info[2]}",
                    'required': f"{self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]}",
                }
            )
    
    def validate_virtual_environment(self) -> EnvironmentValidationResult:
        """
        Check if running in a virtual environment.
        
        Returns:
            Validation result (warning if not in venv, not a failure)
        """
        in_venv = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
        
        if in_venv:
            return EnvironmentValidationResult(
                passed=True,
                message="Running in virtual environment",
                details={'prefix': sys.prefix}
            )
        else:
            return EnvironmentValidationResult(
                passed=True,  # Not a failure, just a warning
                message="⚠️ Not running in virtual environment (recommended but not required)",
                details={'prefix': sys.prefix}
            )
    
    def get_installed_packages(self) -> Dict[str, str]:
        """
        Get dictionary of installed packages and their versions.
        
        Returns:
            Dictionary mapping package name to version
        """
        try:
            import pkg_resources
            installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
            return installed
        except Exception:
            # Fallback: try importlib.metadata (Python 3.8+)
            try:
                from importlib import metadata
                return {dist.name.lower().replace('_', '-'): dist.version for dist in metadata.distributions()}
            except Exception:
                return {}
    
    def parse_requirements(self) -> List[Tuple[str, Optional[str]]]:
        """
        Parse requirements.txt file.
        
        Returns:
            List of (package_name, version_spec) tuples
        """
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            return []
        
        requirements = []
        
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse package name and version
                if '>=' in line:
                    pkg_name, version = line.split('>=', 1)
                elif '==' in line:
                    pkg_name, version = line.split('==', 1)
                elif '~=' in line:
                    pkg_name, version = line.split('~=', 1)
                else:
                    pkg_name = line
                    version = None
                
                pkg_name = pkg_name.strip()
                version = version.strip() if version else None
                
                requirements.append((pkg_name, version))
        
        return requirements
    
    def validate_dependencies(self, mock_mode: bool = False) -> Tuple[List[str], List[str], List[str]]:
        """
        Validate all dependencies from requirements.txt.
        
        Args:
            mock_mode: If True, skip checking optional heavy dependencies
            
        Returns:
            Tuple of (installed, missing, optional_missing) package names
        """
        requirements = self.parse_requirements()
        installed_packages = self.get_installed_packages()
        
        installed = []
        missing = []
        optional_missing = []
        
        for pkg_name, version in requirements:
            # Normalize package name
            pkg_key = pkg_name.lower().replace('_', '-')
            
            # Check if it's optional
            is_optional = any(opt in pkg_key for opt in self.OPTIONAL_DEPENDENCIES)
            
            # Skip optional deps in mock mode
            if mock_mode and is_optional:
                continue
            
            # Check if installed
            if pkg_key in installed_packages:
                installed.append(pkg_name)
            else:
                # Try importing directly
                try:
                    importlib.import_module(pkg_name.replace('-', '_'))
                    installed.append(pkg_name)
                except ImportError:
                    if is_optional:
                        optional_missing.append(pkg_name)
                    else:
                        missing.append(pkg_name)
        
        return installed, missing, optional_missing
    
    def validate_system_resources(self) -> EnvironmentValidationResult:
        """
        Validate system resources (RAM, disk space, CPU).
        
        Returns:
            Validation result with resource details
        """
        if not HAS_PSUTIL:
            return EnvironmentValidationResult(
                passed=True,  # Don't fail if psutil not available
                message="System resource check skipped (psutil not installed)",
                details={'psutil_available': False}
            )
        
        try:
            # RAM
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            ram_available_gb = psutil.virtual_memory().available / (1024 ** 3)
            
            # Disk space
            disk = psutil.disk_usage(str(self.project_root))
            disk_free_gb = disk.free / (1024 ** 3)
            
            # CPU
            cpu_count = psutil.cpu_count(logical=True)
            
            # Check minimums
            issues = []
            if ram_gb < self.MIN_RAM_GB:
                issues.append(f"RAM: {ram_gb:.1f}GB < {self.MIN_RAM_GB}GB minimum")
            if disk_free_gb < self.MIN_DISK_GB:
                issues.append(f"Disk space: {disk_free_gb:.1f}GB < {self.MIN_DISK_GB}GB minimum")
            if cpu_count < self.MIN_CPU_CORES:
                issues.append(f"CPU cores: {cpu_count} < {self.MIN_CPU_CORES} minimum")
            
            if issues:
                return EnvironmentValidationResult(
                    passed=False,
                    message=f"Insufficient system resources: {', '.join(issues)}",
                    details={
                        'ram_total_gb': round(ram_gb, 2),
                        'ram_available_gb': round(ram_available_gb, 2),
                        'disk_free_gb': round(disk_free_gb, 2),
                        'cpu_cores': cpu_count,
                    }
                )
            else:
                return EnvironmentValidationResult(
                    passed=True,
                    message=f"System resources sufficient: {ram_gb:.1f}GB RAM, {disk_free_gb:.1f}GB disk, {cpu_count} CPU cores",
                    details={
                        'ram_total_gb': round(ram_gb, 2),
                        'ram_available_gb': round(ram_available_gb, 2),
                        'disk_free_gb': round(disk_free_gb, 2),
                        'cpu_cores': cpu_count,
                        'platform': platform.platform(),
                    }
                )
        except Exception as e:
            return EnvironmentValidationResult(
                passed=False,
                message=f"Failed to check system resources: {str(e)}",
            )
    
    def test_import(self, module_name: str) -> bool:
        """
        Test if a module can be imported.
        
        Args:
            module_name: Name of module to import
            
        Returns:
            True if module can be imported
        """
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
    
    def validate_all(self, mock_mode: bool = False) -> Dict[str, EnvironmentValidationResult]:
        """
        Run all environment validations.
        
        Args:
            mock_mode: If True, skip optional dependencies
            
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        # Python version
        results['python_version'] = self.validate_python_version()
        
        # Virtual environment
        results['virtual_env'] = self.validate_virtual_environment()
        
        # Dependencies
        installed, missing, optional_missing = self.validate_dependencies(mock_mode)
        
        if missing:
            results['dependencies'] = EnvironmentValidationResult(
                passed=False,
                message=f"{len(missing)} required package(s) missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}",
                details={
                    'installed_count': len(installed),
                    'missing_count': len(missing),
                    'missing_packages': missing,
                }
            )
        else:
            results['dependencies'] = EnvironmentValidationResult(
                passed=True,
                message=f"All {len(installed)} required packages installed",
                details={
                    'installed_count': len(installed),
                    'optional_missing_count': len(optional_missing),
                }
            )
        
        # Optional dependencies
        if optional_missing:
            results['optional_dependencies'] = EnvironmentValidationResult(
                passed=True,  # Not a failure
                message=f"{len(optional_missing)} optional package(s) missing (graceful degradation): {', '.join(optional_missing[:3])}",
                details={
                    'optional_missing': optional_missing,
                }
            )
        
        # System resources
        results['system_resources'] = self.validate_system_resources()
        
        return results
