import structlog
import logging


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


logger = structlog.get_logger()