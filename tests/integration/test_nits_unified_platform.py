"""
NITS Unified Platform Enhancement Patch Test Suite
===================================================
Validates the unified platform enhancement patch integration.
"""

import pytest
import tempfile
from pathlib import Path


class TestNITSUnifiedPlatformEnhancement:
    """Tests for NITS Unified Platform Enhancement Patch."""
    
    def test_module_registry_import(self):
        """Verify ModuleRegistry can be imported."""
        from nits_unified_platform_enhancement import ModuleRegistry
        registry = ModuleRegistry()
        assert registry is not None
        assert registry.total_modules == 0  # Not yet discovered
    
    def test_unified_platform_config_import(self):
        """Verify UnifiedPlatformConfig can be imported and created."""
        from nits_unified_platform_enhancement import UnifiedPlatformConfig, AnalysisMode
        
        config = UnifiedPlatformConfig(
            company_name="Test Company",
            cik="0000123456",
            start_date="2020-01-01",
            end_date="2020-12-31"
        )
        
        assert config.company_name == "Test Company"
        assert config.cik == "0000123456"
        assert config.mode == AnalysisMode.UNIFIED_NEXUS
        assert config.case_id is not None  # Auto-generated
    
    def test_cik_normalization(self):
        """Verify CIK is properly normalized to 10 digits."""
        from nits_unified_platform_enhancement import UnifiedPlatformConfig
        
        config = UnifiedPlatformConfig(
            company_name="Test",
            cik="123456",  # Short CIK
            start_date="2020-01-01",
            end_date="2020-12-31"
        )
        
        assert config.cik == "0000123456"  # Zero-padded to 10 digits
    
    def test_enhancement_phases_enum(self):
        """Verify all 9 enhancement phases are defined."""
        from nits_unified_platform_enhancement import EnhancementPhase
        
        phases = list(EnhancementPhase)
        assert len(phases) == 9
        
        # Verify phase names
        phase_names = [p.name for p in phases]
        assert "PHASE_1_PARSING" in phase_names
        assert "PHASE_2_INTELLIGENCE" in phase_names
        assert "PHASE_3_LEGAL" in phase_names
        assert "PHASE_4_TEMPORAL" in phase_names
        assert "PHASE_5_PROSECUTION" in phase_names
        assert "PHASE_6_CONTRADICTION" in phase_names
        assert "PHASE_7_REPORTING" in phase_names
        assert "PHASE_8_ORCHESTRATION" in phase_names
        assert "PHASE_9_DEPLOYMENT" in phase_names
    
    def test_analysis_modes_enum(self):
        """Verify all analysis modes are defined."""
        from nits_unified_platform_enhancement import AnalysisMode
        
        modes = list(AnalysisMode)
        assert len(modes) == 5
        
        # Verify mode values
        mode_values = [m.value for m in modes]
        assert "standard" in mode_values
        assert "enhanced" in mode_values
        assert "maximum" in mode_values
        assert "doj_grade" in mode_values
        assert "unified_nexus" in mode_values
    
    def test_module_manifest_completeness(self):
        """Verify MODULE_MANIFEST contains all 9 phases."""
        from nits_unified_platform_enhancement import ModuleRegistry, EnhancementPhase
        
        manifest = ModuleRegistry.MODULE_MANIFEST
        
        # All 9 phases should be in the manifest
        for phase in EnhancementPhase:
            assert phase in manifest, f"Phase {phase} missing from MODULE_MANIFEST"
            assert len(manifest[phase]) > 0, f"Phase {phase} has no modules defined"
    
    def test_module_discovery(self):
        """Verify module discovery works."""
        from nits_unified_platform_enhancement import ModuleRegistry
        
        registry = ModuleRegistry()
        modules = registry.discover_all_modules()
        
        # Should have all 9 phases
        assert len(modules) == 9
        
        # Total modules should be 42
        assert registry.total_modules == 42
        
        # Available + Unavailable should equal Total
        assert registry.available_modules + registry.unavailable_modules == registry.total_modules
    
    def test_unified_platform_engine_init(self):
        """Verify UnifiedPlatformEngine can be initialized."""
        from nits_unified_platform_enhancement import UnifiedPlatformEngine, UnifiedPlatformConfig
        
        config = UnifiedPlatformConfig(
            company_name="Test Corp",
            cik="0000999999",
            start_date="2021-01-01",
            end_date="2021-12-31"
        )
        
        engine = UnifiedPlatformEngine(config)
        
        assert engine.config == config
        assert engine.registry is not None
        assert len(engine.phase_results) == 0  # No phases executed yet


class TestNITSDocumentation:
    """Tests for NITS documentation files."""
    
    # Documentation file path as class constant
    DOC_PATH = Path("docs/scripts/NITS_UNIFIED_PLATFORM_ENHANCEMENT_PATCH.txt")
    
    def test_enhancement_patch_doc_exists(self):
        """Verify NITS_UNIFIED_PLATFORM_ENHANCEMENT_PATCH.txt exists."""
        assert self.DOC_PATH.exists(), "NITS enhancement patch documentation not found"
    
    def test_enhancement_patch_doc_content(self):
        """Verify enhancement patch doc contains key sections."""
        content = self.DOC_PATH.read_text()
        
        # Check for key sections
        assert "NITS UNIFIED PLATFORM ENHANCEMENT PATCH" in content
        assert "9-PHASE ENHANCEMENT PROTOCOL" in content
        assert "PHASE 1:" in content
        assert "PHASE 9:" in content
        assert "USAGE INSTRUCTIONS" in content
        assert "COMPLIANCE STANDARDS" in content


class TestPlatformIntegration:
    """Integration tests for the unified platform."""
    
    @pytest.mark.asyncio
    async def test_unified_analysis_execution(self, tmp_path):
        """Test that unified analysis can execute (discovery only)."""
        from nits_unified_platform_enhancement import UnifiedPlatformEngine, UnifiedPlatformConfig
        
        config = UnifiedPlatformConfig(
            company_name="Integration Test",
            cik="0000111111",
            start_date="2022-01-01",
            end_date="2022-12-31",
            output_directory=str(tmp_path / "forensic_reports")
        )
        
        engine = UnifiedPlatformEngine(config)
        
        # Just initialize (discovery)
        result = await engine.initialize()
        
        assert result is True
        assert len(engine.active_modules) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
