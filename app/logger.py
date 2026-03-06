import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist at the root level
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

# Define the structured log format
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] [%(module)s:%(lineno)d] - %(message)s"
)

# Setup rotating file handler (5 MB per file, max 5 files of history)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, "app.log"), maxBytes=5 * 1024 * 1024, backupCount=5
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Setup console handler for local development visibility
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)

# Get the centralized application logger
logger = logging.getLogger("socialease")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
