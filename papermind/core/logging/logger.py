# =============================================================================
# PaperMind AI — Structured Logging
# =============================================================================
# Uses loguru for human-friendly dev output and structlog for JSON in prod.
# This module is imported once at application startup.
# =============================================================================

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from loguru import logger


def _configure_stdlib_logging() -> None:
    """Route stdlib logging through loguru."""

    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno  # type: ignore[assignment]
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back  # type: ignore[assignment]
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "fastapi"):
        _log = logging.getLogger(name)
        _log.handlers = [InterceptHandler()]
        _log.propagate = False


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file: str | None = "logs/papermind.log",
    rotation: str = "10 MB",
    retention: str = "30 days",
) -> None:
    """
    Configure the application logger.

    Args:
        level: Log level (DEBUG / INFO / WARNING / ERROR / CRITICAL)
        log_format: 'json' for structured production logs, 'text' for dev
        log_file: Optional file path for persistent logs
        rotation: Loguru rotation policy
        retention: Loguru retention policy
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    logger.remove()

    if log_format == "json":
        # JSON format for production / log aggregation (Elasticsearch, Loki, etc.)
        logger.add(
            sys.stdout,
            level=level,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        # Human-friendly colored format for development
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        )
        logger.add(sys.stdout, level=level, format=fmt, colorize=True)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path,
            level=level,
            rotation=rotation,
            retention=retention,
            serialize=True,  # always JSON on disk
            enqueue=True,    # async write, non-blocking
            backtrace=True,
            diagnose=False,  # disable in prod to avoid leaking locals
        )

    _configure_stdlib_logging()

    # Configure structlog to use loguru
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    logger.info(
        "PaperMind logging configured",
        level=level,
        format=log_format,
        file=log_file,
    )


def get_logger(name: str) -> Any:
    """
    Get a bound structlog logger for a specific module.

    Usage:
        log = get_logger(__name__)
        log.info("Processing document", doc_id="abc123", page_count=12)
    """
    return structlog.get_logger(name)
