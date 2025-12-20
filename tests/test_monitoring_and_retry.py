"""
Monitoring and Retry Handler Tests
==================================

Tests for the execution metrics monitoring and retry handler infrastructure.
"""

import pytest
import asyncio
from datetime import datetime
from src.infrastructure.monitoring.metrics import (
    MetricsCollector,
    NodeMetrics,
    ExecutionMetrics,
    PhaseMetrics,
    MetricStatus
)
from src.core.retry_handler import (
    RetryHandler,
    RetryConfig,
    RetryExhausted,
    with_retry,
    NODE_RETRY_HANDLER,
    API_RETRY_HANDLER,
    SEC_EDGAR_RETRY_HANDLER
)


# ═══════════════════════════════════════════════════════════════
# MONITORING TESTS
# ═══════════════════════════════════════════════════════════════

def test_metrics_collector_initialization():
    """Test MetricsCollector initialization."""
    collector = MetricsCollector("TEST-001", "0000320187", "NIKE, Inc.")
    
    assert collector.metrics.execution_id == "TEST-001"
    assert collector.metrics.cik == "0000320187"
    assert collector.metrics.company_name == "NIKE, Inc."
    assert collector.metrics.start_time is not None
    assert collector.metrics.nodes_executed == 0
    assert collector.metrics.nodes_successful == 0


def test_node_metrics_tracking():
    """Test node execution metrics."""
    collector = MetricsCollector("TEST-002")
    
    # Start node
    collector.start_node(1, "Form 4 Insider Trading")
    assert 1 in collector.metrics.node_metrics
    assert collector.metrics.node_metrics[1].status == MetricStatus.RUNNING
    
    # End node successfully
    collector.end_node(
        1,
        status="success",
        findings_count=5,
        violations_count=2,
        api_calls=3
    )
    
    node = collector.metrics.node_metrics[1]
    assert node.status == MetricStatus.SUCCESS
    assert node.findings_count == 5
    assert node.violations_count == 2
    assert node.api_calls == 3
    assert collector.metrics.nodes_successful == 1
    assert collector.metrics.nodes_executed == 1


def test_phase_metrics_tracking():
    """Test phase execution metrics."""
    collector = MetricsCollector("TEST-003")
    
    # Start phase
    collector.start_phase("Phase 1: Configuration", phase_number=1, items_expected=5)
    assert "Phase 1: Configuration" in collector.metrics.phase_metrics
    
    # End phase
    collector.end_phase(
        "Phase 1: Configuration",
        status="success",
        items_processed=5,
        errors=0
    )
    
    phase = collector.metrics.phase_metrics["Phase 1: Configuration"]
    assert phase.status == MetricStatus.SUCCESS
    assert phase.items_processed == 5
    assert phase.items_expected == 5
    assert collector.metrics.phases_completed == 1


def test_metrics_finalization():
    """Test metrics finalization."""
    collector = MetricsCollector("TEST-004", "0000320187", "NIKE, Inc.")
    
    # Simulate some activity
    collector.start_node(1)
    collector.end_node(1, status="success", findings_count=10)
    
    collector.start_phase("Phase 1", phase_number=1)
    collector.end_phase("Phase 1", status="success", items_processed=1)
    
    # Finalize
    metrics = collector.finalize()
    
    assert metrics.end_time is not None
    assert metrics.total_duration_seconds > 0
    assert metrics.nodes_executed == 1
    assert metrics.phases_completed == 1
    assert metrics.total_findings == 10


def test_metrics_to_dict():
    """Test metrics serialization."""
    collector = MetricsCollector("TEST-005")
    collector.start_node(1)
    collector.end_node(1, status="success", findings_count=5)
    
    metrics = collector.finalize()
    data = metrics.to_dict()
    
    assert isinstance(data, dict)
    assert data["execution_id"] == "TEST-005"
    assert "summary" in data
    assert "resources" in data
    assert "node_details" in data
    assert 1 in data["node_details"]


def test_skip_node():
    """Test skipping a node."""
    collector = MetricsCollector("TEST-006")
    
    collector.skip_node(1, reason="Missing data")
    
    assert 1 in collector.metrics.node_metrics
    assert collector.metrics.node_metrics[1].status == MetricStatus.SKIPPED
    assert collector.metrics.nodes_skipped == 1
    assert "Missing data" in collector.metrics.node_metrics[1].error_message


def test_error_tracking():
    """Test error recording."""
    collector = MetricsCollector("TEST-007")
    
    collector.start_node(1)
    collector.end_node(1, status="failed", errors=1, error_message="Test error")
    
    assert collector.metrics.total_errors == 1
    assert len(collector.metrics.error_messages) == 1
    assert collector.metrics.nodes_failed == 1


# ═══════════════════════════════════════════════════════════════
# RETRY HANDLER TESTS
# ═══════════════════════════════════════════════════════════════

def test_retry_config_defaults():
    """Test RetryConfig default values."""
    config = RetryConfig()
    
    assert config.max_retries == 3
    assert config.initial_delay == 1.0
    assert config.max_delay == 60.0
    assert config.exponential_base == 2.0
    assert config.jitter is True


def test_retry_handler_success():
    """Test successful execution without retry."""
    handler = RetryHandler(RetryConfig(max_retries=3))
    
    def successful_func():
        return "success"
    
    result = handler.execute(successful_func)
    assert result == "success"


def test_retry_handler_eventual_success():
    """Test retry with eventual success."""
    handler = RetryHandler(RetryConfig(max_retries=3, initial_delay=0.1))
    
    call_count = [0]
    
    def flaky_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Transient error")
        return "success"
    
    result = handler.execute(flaky_func)
    assert result == "success"
    assert call_count[0] == 3


def test_retry_handler_exhausted():
    """Test retry exhaustion."""
    handler = RetryHandler(RetryConfig(max_retries=2, initial_delay=0.1))
    
    def always_fails():
        raise ValueError("Persistent error")
    
    with pytest.raises(RetryExhausted) as exc_info:
        handler.execute(always_fails)
    
    assert "failed after 3 attempts" in str(exc_info.value)
    assert isinstance(exc_info.value.last_exception, ValueError)


@pytest.mark.asyncio
async def test_retry_handler_async_success():
    """Test async function retry with success."""
    handler = RetryHandler(RetryConfig(max_retries=3, initial_delay=0.1))
    
    call_count = [0]
    
    async def async_flaky_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise ValueError("Transient error")
        return "async success"
    
    result = await handler.execute_async(async_flaky_func)
    assert result == "async success"
    assert call_count[0] == 2


@pytest.mark.asyncio
async def test_retry_handler_async_exhausted():
    """Test async function retry exhaustion."""
    handler = RetryHandler(RetryConfig(max_retries=2, initial_delay=0.1))
    
    async def async_always_fails():
        raise ValueError("Persistent async error")
    
    with pytest.raises(RetryExhausted):
        await handler.execute_async(async_always_fails)


def test_retry_handler_non_retryable_exception():
    """Test non-retryable exceptions."""
    config = RetryConfig(
        max_retries=3,
        non_retryable_exceptions=[KeyboardInterrupt, SystemExit]
    )
    handler = RetryHandler(config)
    
    def raises_keyboard_interrupt():
        raise KeyboardInterrupt("User interrupt")
    
    with pytest.raises(KeyboardInterrupt):
        handler.execute(raises_keyboard_interrupt)


def test_with_retry_decorator():
    """Test @with_retry decorator."""
    call_count = [0]
    
    @with_retry(max_retries=3, initial_delay=0.1)
    def decorated_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise ValueError("Transient error")
        return "decorated success"
    
    result = decorated_func()
    assert result == "decorated success"
    assert call_count[0] == 2


@pytest.mark.asyncio
async def test_with_retry_decorator_async():
    """Test @with_retry decorator on async function."""
    call_count = [0]
    
    @with_retry(max_retries=3, initial_delay=0.1)
    async def async_decorated_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise ValueError("Transient error")
        return "async decorated success"
    
    result = await async_decorated_func()
    assert result == "async decorated success"
    assert call_count[0] == 2


def test_pre_configured_handlers():
    """Test pre-configured retry handlers."""
    assert NODE_RETRY_HANDLER.config.max_retries == 2
    assert API_RETRY_HANDLER.config.max_retries == 3
    assert SEC_EDGAR_RETRY_HANDLER.config.max_retries == 5


def test_exponential_backoff_calculation():
    """Test exponential backoff delay calculation."""
    handler = RetryHandler(RetryConfig(
        initial_delay=1.0,
        exponential_base=2.0,
        max_delay=10.0,
        jitter=False
    ))
    
    # Test delays without jitter
    assert handler._calculate_delay(0) == 1.0  # 1 * 2^0
    assert handler._calculate_delay(1) == 2.0  # 1 * 2^1
    assert handler._calculate_delay(2) == 4.0  # 1 * 2^2
    assert handler._calculate_delay(3) == 8.0  # 1 * 2^3
    assert handler._calculate_delay(4) == 10.0  # Capped at max_delay


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════

def test_metrics_and_retry_integration():
    """Test metrics collection with retry handler."""
    collector = MetricsCollector("TEST-INT-001")
    handler = RetryHandler(RetryConfig(max_retries=2, initial_delay=0.1))
    
    call_count = [0]
    
    def flaky_task():
        call_count[0] += 1
        if call_count[0] < 2:
            raise ValueError("Transient error")
        return {"findings": 5}
    
    # Start node
    collector.start_node(1, "Test Node")
    
    try:
        result = handler.execute(flaky_task)
        collector.end_node(1, status="success", findings_count=result["findings"])
    except Exception as e:
        collector.end_node(1, status="failed", error_message=str(e))
    
    assert collector.metrics.nodes_successful == 1
    assert collector.metrics.total_findings == 5


def test_metrics_summary_generation():
    """Test human-readable summary generation."""
    collector = MetricsCollector("TEST-SUM-001", "0000320187", "NIKE, Inc.")
    collector.set_investigation_type("insider_trading")
    
    collector.start_node(1)
    collector.end_node(1, status="success", findings_count=10)
    
    metrics = collector.finalize()
    summary = collector.get_summary()
    
    assert "TEST-SUM-001" in summary
    assert "NIKE, Inc." in summary
    assert "insider_trading" in summary
    assert "1/1 successful" in summary
