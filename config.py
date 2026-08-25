import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration - CRITICAL: Must be set in Railway environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
    logger.error("Please add TELEGRAM_BOT_TOKEN to Railway environment variables")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required!")

logger.info("✅ Bot configuration loaded successfully")
