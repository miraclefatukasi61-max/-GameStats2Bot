import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
    logger.error("Please add TELEGRAM_BOT_TOKEN to Railway environment variables")
    raise ValueError("TELEGRAM_BOT_TOKEN is required!")

logger.info("✅ Bot configuration loaded")
