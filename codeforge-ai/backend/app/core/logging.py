"""Structured logging configuration."""
import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
import logging

def configure_logging():
    logging.basicConfig(level=logging.INFO)
    structlog.configure(
        processors=[
            add_log_level,
            TimeStamper(fmt="iso"),
            JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

def get_logger(name: str = "codeforge"):
    return structlog.get_logger(name)
