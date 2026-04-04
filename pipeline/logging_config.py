import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging():
    handlers = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            "pipeline.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
        ),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
