import logging
import sys
import os
from colorlog import ColoredFormatter

APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "dev").lower()

# Create logger
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# Remove any pre-existing handlers to prevent duplication
if logger.hasHandlers():
    logger.handlers.clear()

# Color formatter for console
color_formatter = ColoredFormatter(
    fmt="[%(log_color)s%(levelname)s%(reset)s] [%(asctime)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",           # RED for error
        "CRITICAL": "bold_red"    # Bold red for critical
    }
)

# Plain formatter for file (no colors)
file_formatter = logging.Formatter(
    "%(levelname)s %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

if APP_ENVIRONMENT == "dev":
    # Log to terminal with color
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)
else:
    # Log to file without color
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
