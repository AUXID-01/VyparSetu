import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Central logger factory for Paytm VyaparSetu.
    Ensures standard formatting (asctime | level | name | message) directed to stdout
    and prevents duplicate handlers across imports.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger
