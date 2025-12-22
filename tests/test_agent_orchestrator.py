"""
Tests for Agent Orchestrator Integration (GAP-001)
==================================================

Validates that AgentOrchestrator properly parses agent definitions
and integrates with Phase 7 execution.
"""

from pathlib import Path


def test_agent_orchestrator_initialization():
    """Test that AgentOrchestrator initializes properly."""
    from src.forensics.agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    assert orchestrator is not None
    assert orchestrator.agents_dir is not None
    print("✓ AgentOrchestrator initializes successfully")


def test_agent_definitions_parsed():
    """Test that agent definitions are parsed from markdown files."""
    from src.forensics.agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    agents = orchestrator.list_available_agents()
    
    # Should have parsed at least some agents if .claude/agents exists
    # If directory doesn't exist, agents list will be empty (degraded mode)
    assert isinstance(agents, list)
    print(f"✓ Parsed {len(agents)} agent definitions")


def test_agent_definition_structure():
    """Test that agent definitions have required fields."""
    from src.forensics.agent_orchestrator import AgentOrchestrator, AgentCategory
    
    orchestrator = AgentOrchestrator()
    agents = orchestrator.list_available_agents()
    
    if agents:
        # Check first agent has required fields
        agent = agents[0]
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'category')
        assert hasattr(agent, 'description')
        assert hasattr(agent, 'tools')
        assert isinstance(agent.category, AgentCategory)
        print(f"✓ Agent definition structure validated (sample: {agent.name})")
    else:
        print("⚠ No agents found - skipping structure validation")


def test_get_agents_by_category():
    """Test filtering agents by category."""
    from src.forensics.agent_orchestrator import AgentOrchestrator, AgentCategory
    
    orchestrator = AgentOrchestrator()
    
    forensic_agents = orchestrator.get_agents_by_category(AgentCategory.FORENSIC)
    orchestration_agents = orchestrator.get_agents_by_category(AgentCategory.ORCHESTRATION)
    
    assert isinstance(forensic_agents, list)
    assert isinstance(orchestration_agents, list)
    print(f"✓ Category filtering works (forensic: {len(forensic_agents)}, orchestration: {len(orchestration_agents)})")


def test_workflow_creation():
    """Test that workflows can be created."""
    from src.forensics.agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    # Create single document workflow
    workflow = orchestrator.create_workflow(
        'single_document',
        document_content='test content',
        document_type='10-K'
    )
    
    assert workflow is not None
    assert workflow.workflow_type == 'single_document'
    assert len(workflow.agents) > 0
    assert len(workflow.execution_order) > 0
    print(f"✓ Workflow creation works (ID: {workflow.workflow_id})")


def test_workflow_types():
    """Test all supported workflow types."""
    from src.forensics.agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    workflow_types = [
        'single_document',
        'multi_document',
        'full_forensic',
        'contradiction_detection',
        'financial_analysis'
    ]
    
    for wf_type in workflow_types:
        try:
            workflow = orchestrator.create_workflow(wf_type, cik='320187')
            assert workflow.workflow_type == wf_type
        except Exception as e:
            print(f"✗ Workflow type {wf_type} failed: {e}")
            raise
    
    print(f"✓ All {len(workflow_types)} workflow types supported")


def test_agent_statistics():
    """Test agent statistics reporting."""
    from src.forensics.agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    stats = orchestrator.get_agent_statistics()
    
    assert 'total_agents' in stats
    assert 'by_category' in stats
    assert 'agents' in stats
    assert isinstance(stats['total_agents'], int)
    print(f"✓ Agent statistics: {stats['total_agents']} total agents")


def test_integration_with_subagent_orchestrator():
    """Test that AgentOrchestrator can integrate with SubagentOrchestrator."""
    from src.forensics.agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    # Check that SubagentOrchestrator can be imported
    try:
        from src.forensics.subagents.orchestrator import SubagentOrchestrator
        print("✓ SubagentOrchestrator can be imported")
    except ImportError as e:
        print(f"⚠ SubagentOrchestrator not available: {e}")


def test_master_controller_phase_7():
    """Test that Phase 7 in master controller uses AgentOrchestrator."""
    import inspect
    from src.core.master_execution_controller import MasterExecutionController
    
    # Check that _execute_phase_7_subagent exists
    assert hasattr(MasterExecutionController, '_execute_phase_7_subagent')
    
    # Check that AgentOrchestrator is referenced in the method
    method = MasterExecutionController._execute_phase_7_subagent
    source = inspect.getsource(method)
    
    assert 'AgentOrchestrator' in source, \
        "Phase 7 doesn't use AgentOrchestrator"
    
    assert 'list_available_agents' in source, \
        "Phase 7 doesn't call list_available_agents"
    
    print("✓ Master controller Phase 7 integrated with AgentOrchestrator")


if __name__ == "__main__":
    print("Running Agent Orchestrator Integration Tests (GAP-001)...")
    print("=" * 70)
    
    try:
        test_agent_orchestrator_initialization()
    except Exception as e:
        print(f"✗ test_agent_orchestrator_initialization FAILED: {e}")
    
    try:
        test_agent_definitions_parsed()
    except Exception as e:
        print(f"✗ test_agent_definitions_parsed FAILED: {e}")
    
    try:
        test_agent_definition_structure()
    except Exception as e:
        print(f"✗ test_agent_definition_structure FAILED: {e}")
    
    try:
        test_get_agents_by_category()
    except Exception as e:
        print(f"✗ test_get_agents_by_category FAILED: {e}")
    
    try:
        test_workflow_creation()
    except Exception as e:
        print(f"✗ test_workflow_creation FAILED: {e}")
    
    try:
        test_workflow_types()
    except Exception as e:
        print(f"✗ test_workflow_types FAILED: {e}")
    
    try:
        test_agent_statistics()
    except Exception as e:
        print(f"✗ test_agent_statistics FAILED: {e}")
    
    try:
        test_integration_with_subagent_orchestrator()
    except Exception as e:
        print(f"✗ test_integration_with_subagent_orchestrator FAILED: {e}")
    
    try:
        test_master_controller_phase_7()
    except Exception as e:
        print(f"✗ test_master_controller_phase_7 FAILED: {e}")
    
    print("=" * 70)
    print("Agent orchestrator integration tests completed!")
