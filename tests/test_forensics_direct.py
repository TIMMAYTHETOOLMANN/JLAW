"""
JARVIS 2.0 - MCP Forensics Direct Validation
Tests forensic modules directly without full agent SDK dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_direct_forensics():
    """Test forensic modules directly."""
    print("=" * 80)
    print("JARVIS 2.0 - DIRECT FORENSICS VALIDATION")
    print("=" * 80)
    print()
    
    # Test 1: Import forensics module
    print("Test 1: Import forensics module...")
    try:
        from agents.mcp.forensics import (
            AuditTracker,
            ToolExecutionProfile,
            ExecutionProfiler,
            ForensicStateTracker,
            ServerState,
            ForensicArchive,
            ErrorForensics,
            ForensicManager,
        )
        print("✓ Forensics module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import: {e}")
        return False
    
    # Test 2: Create AuditTracker
    print("\nTest 2: Create and use AuditTracker...")
    try:
        tracker = AuditTracker("test_server")
        await tracker.record_audit(
            operation="test",
            start_time=asyncio.get_event_loop().time(),
            cache_state="clean",
            tools_cached=0,
        )
        summary = tracker.get_audit_summary()
        assert summary["total_operations"] == 1
        print(f"✓ AuditTracker works: {summary['total_operations']} operation(s) tracked")
    except Exception as e:
        print(f"✗ AuditTracker failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Create ExecutionProfiler
    print("\nTest 3: Create and use ExecutionProfiler...")
    try:
        profile = await ExecutionProfiler.get_or_create_profile("test_tool")
        profile.record_execution(
            start_time=asyncio.get_event_loop().time(),
            duration_ms=100.0,
            input_json='{"test": "input"}',
            output="test output",
        )
        summary = profile.get_profile_summary()
        assert summary["execution_count"] == 1
        print(f"✓ ExecutionProfiler works: {summary['execution_count']} execution(s) profiled")
    except Exception as e:
        print(f"✗ ExecutionProfiler failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Create ForensicStateTracker
    print("\nTest 4: Create and use ForensicStateTracker...")
    try:
        state_tracker = ForensicStateTracker("test_server")
        await state_tracker.transition(
            ServerState.CONNECTING,
            "test_trigger",
            {"test": "metadata"},
        )
        assert state_tracker.current_state == ServerState.CONNECTING
        print(f"✓ ForensicStateTracker works: Current state = {state_tracker.current_state.value}")
    except Exception as e:
        print(f"✗ ForensicStateTracker failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Create ForensicArchive
    print("\nTest 5: Create and use ForensicArchive...")
    try:
        archive = ForensicArchive()
        await archive.archive_operation(
            operation_type="test_op",
            server_name="test_server",
            tool_name="test_tool",
            request_data={"arg": "value"},
            response_data={"result": "success"},
            metadata={"test": True},
        )
        summary = archive.get_archive_summary()
        assert summary["total_entries"] == 1
        print(f"✓ ForensicArchive works: {summary['total_entries']} operation(s) archived")
    except Exception as e:
        print(f"✗ ForensicArchive failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Create ErrorForensics
    print("\nTest 6: Create and use ErrorForensics...")
    try:
        error_tracker = ErrorForensics("test_server")
        test_error = ValueError("Test error")
        await error_tracker.record_error(
            error=test_error,
            context={"operation": "test_op"},
        )
        summary = error_tracker.get_error_summary()
        assert summary["total_errors"] == 1
        print(f"✓ ErrorForensics works: {summary['total_errors']} error(s) tracked")
    except Exception as e:
        print(f"✗ ErrorForensics failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 7: ForensicManager
    print("\nTest 7: Test ForensicManager...")
    try:
        ForensicManager.set_enabled(True)
        assert ForensicManager.is_enabled() == True
        ForensicManager.set_enabled(False)
        assert ForensicManager.is_enabled() == False
        ForensicManager.set_enabled(True)
        print("✓ ForensicManager works: Enable/disable functional")
    except Exception as e:
        print(f"✗ ForensicManager failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 80)
    print("✓ ALL FORENSIC MODULES VALIDATED SUCCESSFULLY")
    print("=" * 80)
    print()
    print("Core forensic functionality is operational:")
    print("  • AuditTracker - Operation audit trail")
    print("  • ExecutionProfiler - Tool performance profiling")
    print("  • ForensicStateTracker - State machine tracking")
    print("  • ForensicArchive - Request/response archive")
    print("  • ErrorForensics - Error pattern analysis")
    print("  • ForensicManager - Global control")
    print()
    return True


if __name__ == "__main__":
    success = asyncio.run(test_direct_forensics())
    sys.exit(0 if success else 1)

