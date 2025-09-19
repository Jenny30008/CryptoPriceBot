# CryptoPriceBot Configuration
# Copy this file to config.py and add your actual tokens

# Bot Tokens (REQUIRED)
# Get these from:
# - Telegram: @BotFather on Telegram

# Telegram Bot Configuration
TELEGRAM_API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Bot Settings
BOT_DESCRIPTION = "CryptoPriceBot - Real-time cryptocurrency prices"

# API Settings
API_TIMEOUT = 10  # Request timeout in seconds
CACHE_DURATION = 3600  # Coin list cache duration (1 hour)
TOP_COINS_CACHE_DURATION = 300  # Top coins cache duration (5 minutes)

# Alert Settings
ALERT_THRESHOLD = 5.0  # Price change threshold for alerts (5%)

# Logging Settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True  # Save logs to file
LOG_FILE = "crypto_bot.log"

# Development Settings
DEBUG_MODE = False  # Enable debug mode
TEST_MODE = False   # Enable test mode (no real API calls)
