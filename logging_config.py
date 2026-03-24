import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        filename="pipeline.log",
        encoding="utf-8",
    )


# TODO: RotatingFileHandler
# TODO: print to console and save to file using handlers?
