import logging
import sys
from app.config import settings

def setup_logger(name: str):
    """
    Setup a standard logger for the application.
    """
    logger = logging.getLogger(name)
    

    if logger.handlers:
        return logger

    
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)

    return logger

logger = setup_logger("omnibrain")