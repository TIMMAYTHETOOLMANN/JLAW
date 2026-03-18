"""
JLAW Centralized Logging Configuration

Provides structured logging with JSON output, log rotation, and separate audit logs.

Usage:
    from src.core.logging_config import setup_logging, get_logger
    
    # Setup logging (call once at application start)
    setup_logging()
    
    # Get logger for module
    logger = get_logger(__name__)
    logger.info("Analysis started", extra={"cik": "320187"})
"""

import logging
import logging.handlers
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs log records as JSON objects for easy parsing by log aggregation systems
    (CloudWatch, Splunk, ELK, etc.).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log object
        log_obj = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add process/thread info
        if record.process:
            log_obj["process_id"] = record.process
        if record.thread:
            log_obj["thread_id"] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_obj.update(record.extra_data)
        
        # Add any custom attributes from extra= parameter
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'getMessage', 'extra_data']:
                try:
                    # Only add JSON-serializable values
                    json.dumps(value)
                    log_obj[key] = value
                except (TypeError, ValueError) as e:
                    logging.getLogger(__name__).debug(f"Skipping non-serializable log record field '{key}': {e}")
                    pass
        
        return json.dumps(log_obj)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter.
    
    Provides colored output for console and structured text for files.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, use_color: bool = False):
        """
        Initialize formatter.
        
        Args:
            use_color: Enable ANSI color codes for console output
        """
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_color = use_color
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        if self.use_color and record.levelname in self.COLORS:
            # Add color to level name
            original_levelname = record.levelname
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
            formatted = super().format(record)
            record.levelname = original_levelname
            return formatted
        else:
            return super().format(record)


class AuditLogFilter(logging.Filter):
    """Filter to separate audit logs from operational logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if record should be logged to audit log."""
        # Check if record has audit flag
        return getattr(record, 'audit', False)


class OperationalLogFilter(logging.Filter):
    """Filter to exclude audit logs from operational logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if record should be logged to operational log."""
        # Exclude audit records
        return not getattr(record, 'audit', False)


def get_log_level(level_str: Optional[str] = None) -> int:
    """
    Get logging level from string or environment variable.
    
    Args:
        level_str: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logging level constant
    """
    if level_str is None:
        level_str = os.getenv('LOG_LEVEL', 'INFO')
    
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    
    return level_map.get(level_str.upper(), logging.INFO)


def get_log_format() -> str:
    """
    Get log format from environment variable.
    
    Returns:
        'json' or 'text'
    """
    return os.getenv('LOG_FORMAT', 'text').lower()


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    audit_log_file: Optional[str] = None,
    console_output: bool = True,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
) -> None:
    """
    Configure centralized logging for JLAW.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')
        log_file: Path to operational log file
        audit_log_file: Path to audit log file
        console_output: Enable console output
        max_bytes: Max log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Get configuration from environment if not provided
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    if log_format is None:
        log_format = get_log_format()
    
    if log_file is None:
        log_file = os.getenv('LOG_FILE', '/var/log/jlaw/execution.log')
    
    if audit_log_file is None:
        audit_log_file = os.getenv('AUDIT_LOG_FILE', '/var/log/jlaw/audit.log')
    
    if max_bytes is None:
        max_bytes = int(os.getenv('LOG_ROTATION_MAX_BYTES', '104857600'))  # 100MB
    
    if backup_count is None:
        backup_count = int(os.getenv('LOG_ROTATION_BACKUP_COUNT', '10'))
    
    # Get log level
    level = get_log_level(log_level)
    
    # Create formatters
    if log_format == 'json':
        file_formatter = JSONFormatter()
        console_formatter = TextFormatter(use_color=True)
    else:
        file_formatter = TextFormatter(use_color=False)
        console_formatter = TextFormatter(use_color=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (operational logs only)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(OperationalLogFilter())
        root_logger.addHandler(console_handler)
    
    # Operational log file handler
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(OperationalLogFilter())
        root_logger.addHandler(file_handler)
    
    except (OSError, PermissionError) as e:
        # If can't write to /var/log, try local directory
        local_log_file = Path('logs/execution.log')
        local_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            str(local_log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(OperationalLogFilter())
        root_logger.addHandler(file_handler)
        
        root_logger.warning(
            f"Could not write to {log_file}, using {local_log_file} instead: {e}"
        )
    
    # Audit log file handler (separate file, audit logs only)
    try:
        audit_path = Path(audit_log_file)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)  # Always log audit events
        audit_handler.setFormatter(file_formatter)
        audit_handler.addFilter(AuditLogFilter())
        root_logger.addHandler(audit_handler)
    
    except (OSError, PermissionError) as e:
        # If can't write to /var/log, try local directory
        local_audit_file = Path('logs/audit.log')
        local_audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        audit_handler = logging.handlers.RotatingFileHandler(
            str(local_audit_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(file_formatter)
        audit_handler.addFilter(AuditLogFilter())
        root_logger.addHandler(audit_handler)
        
        root_logger.warning(
            f"Could not write to {audit_log_file}, using {local_audit_file} instead: {e}"
        )
    
    # Log configuration
    root_logger.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'log_format': log_format,
            'log_file': log_file,
            'audit_log_file': audit_log_file
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)


def log_audit_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    **kwargs: Any
) -> None:
    """
    Log an audit event.
    
    Audit events are logged separately from operational logs for compliance tracking.
    
    Args:
        logger: Logger instance
        event_type: Type of audit event (e.g., 'document_acquisition', 'analysis_start')
        message: Human-readable message
        **kwargs: Additional event data
    """
    extra_data = {
        'audit': True,
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        **kwargs
    }
    
    logger.info(message, extra=extra_data)


def log_execution_trace(
    logger: logging.Logger,
    phase: str,
    component: str,
    action: str,
    **kwargs: Any
) -> None:
    """
    Log execution trace for debugging.
    
    Args:
        logger: Logger instance
        phase: Execution phase (e.g., 'PHASE_4')
        component: Component name (e.g., 'node1_form4')
        action: Action performed (e.g., 'start', 'complete', 'error')
        **kwargs: Additional trace data
    """
    extra_data = {
        'trace': True,
        'phase': phase,
        'component': component,
        'action': action,
        **kwargs
    }
    
    logger.debug(f"[TRACE] {phase} > {component} > {action}", extra=extra_data)


# Convenience functions for common log patterns

def log_node_start(logger: logging.Logger, node_id: int, node_name: str) -> None:
    """Log node execution start."""
    log_execution_trace(
        logger,
        phase='PHASE_4',
        component=f'node{node_id}',
        action='start',
        node_name=node_name
    )


def log_node_complete(
    logger: logging.Logger,
    node_id: int,
    node_name: str,
    violations_found: int,
    execution_time: float
) -> None:
    """Log node execution completion."""
    log_execution_trace(
        logger,
        phase='PHASE_4',
        component=f'node{node_id}',
        action='complete',
        node_name=node_name,
        violations_found=violations_found,
        execution_time=execution_time
    )


def log_phase_gate(
    logger: logging.Logger,
    phase: str,
    passed: bool,
    threshold: float,
    actual: float
) -> None:
    """Log phase gate validation."""
    log_audit_event(
        logger,
        event_type='phase_gate',
        message=f"{phase} gate {'PASSED' if passed else 'FAILED'}",
        phase=phase,
        passed=passed,
        threshold=threshold,
        actual=actual
    )


def log_evidence_chain_event(
    logger: logging.Logger,
    event: str,
    document_id: str,
    **kwargs: Any
) -> None:
    """Log evidence chain event."""
    log_audit_event(
        logger,
        event_type='evidence_chain',
        message=f"Evidence chain: {event} - {document_id}",
        event=event,
        document_id=document_id,
        **kwargs
    )
