###############################################################################
# src/utils/logging_utils.py
#
# Logging utility module.
# Sets up file and console logging with daily log files organized by month.
# Provides a simple log() function for logging messages at different levels.
###############################################################################

import logging
import os
from datetime import datetime

## Folder setup ##
# Base logs folder
folder = os.path.abspath(os.path.join(__file__, "../../../logs"))

# Subfolder for the current month (YYYY-MM)
month_folder = os.path.join(folder, datetime.now().strftime("%Y-%m"))
os.makedirs(month_folder, exist_ok=True)  # create folder if it doesn't exist

# Log file for today (YYYY-MM-DD.log)
log_filename = os.path.join(month_folder, f"{datetime.now().strftime('%Y-%m-%d')}.log")

### Logger setup ##
logger = logging.getLogger("logger")  # create/get a named logger
logger.setLevel(logging.DEBUG)        # minimum logging level (DEBUG and above)

# Avoid adding handlers multiple times
if not logger.handlers:

    # File handler (writes logs to file)
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    )
    logger.addHandler(file_handler)

    # Console handler (prints logs to console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    )
    logger.addHandler(console_handler)

    # Initial message if the log file was just created
    if os.path.getsize(log_filename) == 0:
        with open(log_filename, "a", encoding="utf-8") as f:
            f.write(f"=== Log file created for {datetime.now().strftime('%Y-%m-%d')} ===\n\n")

### Wrapper function for logging ##
def log(message, level="INFO"):
    """
    Log a message with a given level.

    Parameters:
    message (str): The message to log
    level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    level = level.upper()
    log_func = getattr(logger, level.lower(), logger.info)  # select correct logging function
    log_func(message)
