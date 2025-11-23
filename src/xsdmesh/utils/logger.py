"""Structured logging setup for XSDMesh.

Provides contextualized logging with performance metrics and debug info.
Uses stdlib logging with structured context for parse/validation events.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

# Default format: timestamp, level, name, message
DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DEBUG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s"

# Logger namespace
ROOT_LOGGER = "xsdmesh"


def setup_logging(
    level: int = logging.INFO,
    *,
    debug: bool = False,
    file_path: str | None = None,
) -> None:
    """Configure logging for XSDMesh.

    Args:
        level: Logging level (default: INFO)
        debug: Enable debug mode with verbose format
        file_path: Optional file path for log output
    """
    # Select format based on debug mode
    fmt = DEBUG_FORMAT if debug else DEFAULT_FORMAT
    formatter = logging.Formatter(fmt)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    # File handler if path provided
    handlers: list[logging.Handler] = [console_handler]
    if file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    root = logging.getLogger(ROOT_LOGGER)
    root.setLevel(level)
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)

    # Suppress verbose lxml logging
    logging.getLogger("lxml").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger for module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance with xsdmesh namespace
    """
    # Ensure name is under xsdmesh namespace
    if not name.startswith(ROOT_LOGGER):
        name = f"{ROOT_LOGGER}.{name}"
    return logging.getLogger(name)


class LogContext:
    """Context manager for structured logging with extra fields.

    Adds temporary context fields to log records.
    """

    def __init__(self, logger: logging.Logger, **extra: Any) -> None:
        """Initialize log context.

        Args:
            logger: Logger instance
            **extra: Extra fields to add to log records
        """
        self.logger = logger
        self.extra = extra
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self) -> LogContext:
        """Enter context and install record factory."""

        def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = self.old_factory(*args, **kwargs)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(factory)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and restore factory."""
        logging.setLogRecordFactory(self.old_factory)


def log_parse_event(
    logger: logging.Logger,
    event: str,
    *,
    element: str | None = None,
    namespace: str | None = None,
    location: str | None = None,
    **extra: Any,
) -> None:
    """Log XSD parse event with context.

    Args:
        logger: Logger instance
        event: Event description
        element: Element name
        namespace: Namespace URI
        location: Schema location
        **extra: Additional context fields
    """
    ctx = {"event": "parse"}
    if element:
        ctx["element"] = element
    if namespace:
        ctx["namespace"] = namespace
    if location:
        ctx["location"] = location
    ctx.update(extra)

    logger.debug(event, extra=ctx)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **extra: Any,
) -> None:
    """Log performance metric.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **extra: Additional context
    """
    ctx = {"event": "performance", "operation": operation, "duration_ms": duration_ms}
    ctx.update(extra)

    if duration_ms > 1000:  # >1s
        logger.warning(f"Slow operation: {operation} took {duration_ms:.1f}ms", extra=ctx)
    else:
        logger.debug(f"{operation}: {duration_ms:.1f}ms", extra=ctx)
