"""Global configuration constants for the breakout scalping signal bot."""
from pathlib import Path

# Telegram credentials
TELEGRAM_BOT_TOKEN: str = "7260596079:AAHBHvXe-mskrRGCBGDNCeB1CeLAvM3dhQY"
TELEGRAM_CHAT_ID: str = "6534876476"

# External API keys (replace the placeholder strings with your real keys)
ALPHA_VANTAGE_API_KEY: str = "YOUR_ALPHA_VANTAGE_API_KEY"
COINMARKETCAP_API_KEY: str = "YOUR_COINMARKETCAP_API_KEY"
# Add additional keys as needed

# Asset universe to analyse
ASSETS = [
    "BTC/USD",
    "ETH/USD",
    "XAU/USD",
    "EUR/USD",
    "XRP/USD",
]

# Scheduling interval (in minutes)
SCHEDULE_INTERVAL_MINUTES: int = 10

# Directory for log files (ensures it exists at runtime)
LOG_DIR: Path = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)