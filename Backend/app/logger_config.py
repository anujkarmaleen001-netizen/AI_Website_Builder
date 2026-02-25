"""
Structured logging configuration for production environments.
"""
import logging
import json
import sys
import time
from typing import Any, Dict, Optional
from contextvars import ContextVar
from datetime import datetime

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        record.correlation_id = correlation_id_var.get() or "N/A"
        return True


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""
    
    def __init__(self, include_trace: bool = True):
        """
        Initialize JSON formatter.
        
        Args:
            include_trace: Whether to include stack traces
        """
        super().__init__()
        self.include_trace = include_trace
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', 'N/A'),
        }
        
        # Add module and function info
        if record.funcName:
            log_data["function"] = record.funcName
        if record.module:
            log_data["module"] = record.module
        if record.lineno:
            log_data["line"] = record.lineno
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info and self.include_trace:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info and self.include_trace:
            log_data["stack_info"] = self.formatStack(record.stack_info)
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Enhanced text formatter for development."""
    
    def __init__(self):
        """Initialize text formatter."""
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class PerformanceLogger:
    """Logger for tracking performance metrics."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize performance logger.
        
        Args:
            logger: Base logger to use
        """
        self.logger = logger
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log elapsed time."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.logger.info(
                f"Operation completed in {elapsed:.3f}s",
                extra={'extra_fields': {'elapsed_time': elapsed}}
            )
    
    def log_metric(self, metric_name: str, value: Any, **kwargs):
        """
        Log a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            **kwargs: Additional fields
        """
        extra_fields = {
            'metric_name': metric_name,
            'metric_value': value,
            **kwargs
        }
        self.logger.info(
            f"Metric: {metric_name}={value}",
            extra={'extra_fields': extra_fields}
        )


def setup_logging(
    level: str = "INFO",
    format_type: str = "text",
    include_trace: bool = True
) -> None:
    """
    Setup application logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ("json" or "text")
        include_trace: Whether to include stack traces
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter based on format type
    if format_type == "json":
        formatter = JSONFormatter(include_trace=include_trace)
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    console_handler.addFilter(correlation_filter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Get a performance logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        PerformanceLogger instance
    """
    logger = get_logger(name)
    return PerformanceLogger(logger)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for current context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID.
    
    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    correlation_id_var.set(None)
