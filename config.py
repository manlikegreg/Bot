"""
Configuration settings for the Trading Signal Bot
Contains all constants and configuration parameters.
"""

import os
from typing import List

class Config:
    """Configuration class containing all bot settings."""
    
    # Trading symbols to analyze
    TRADING_SYMBOLS: List[str] = [
        'BTC/USD',
        'ETH/USD', 
        'XAU/USD',  # Gold
        'EUR/USD',
        'XRP/USD'
    ]
    
    # API Keys (from environment variables with fallbacks)
    COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
    TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY', 'demo')
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7260596079:AAHBHvXe-mskrRGCBGDNCeB1CeLAvM3dhQY')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '6534876476')
    
    # Technical Indicator Parameters
    RSI_PERIOD = 14
    MACD_FAST_PERIOD = 12
    MACD_SLOW_PERIOD = 26
    MACD_SIGNAL_PERIOD = 9
    BOLLINGER_PERIOD = 20
    BOLLINGER_STD_DEV = 2
    MA_SHORT_PERIOD = 50
    MA_LONG_PERIOD = 200
    
    # Signal Processing Parameters
    CONFIDENCE_THRESHOLD = 80  # Minimum confidence for sending alerts
    
    # API Rate Limits and Timeouts
    API_TIMEOUT = 30  # seconds
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 5  # seconds
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'trading_bot.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Symbol mapping for different APIs
    SYMBOL_MAPPING = {
        'BTC/USD': {
            'coingecko': 'bitcoin',
            'coinmarketcap': 'BTC',
            'twelvedata': 'BTC/USD',
            'alpha_vantage': 'BTC'
        },
        'ETH/USD': {
            'coingecko': 'ethereum', 
            'coinmarketcap': 'ETH',
            'twelvedata': 'ETH/USD',
            'alpha_vantage': 'ETH'
        },
        'XAU/USD': {
            'alpha_vantage': 'XAU/USD',
            'twelvedata': 'XAU/USD',
            'forex_api': 'XAUUSD'
        },
        'EUR/USD': {
            'alpha_vantage': 'EUR/USD',
            'twelvedata': 'EUR/USD', 
            'forex_api': 'EURUSD'
        },
        'XRP/USD': {
            'coingecko': 'ripple',
            'coinmarketcap': 'XRP',
            'twelvedata': 'XRP/USD',
            'alpha_vantage': 'XRP'
        }
    }
    
    # API Endpoints
    API_ENDPOINTS = {
        'coingecko_price': 'https://api.coingecko.com/api/v3/simple/price',
        'coingecko_history': 'https://api.coingecko.com/api/v3/coins/{}/market_chart',
        'alpha_vantage_fx': 'https://www.alphavantage.co/query',
        'alpha_vantage_crypto': 'https://www.alphavantage.co/query',
        'twelvedata': 'https://api.twelvedata.com/time_series',
        'telegram': f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    }
    
    @classmethod
    def get_symbol_for_api(cls, symbol: str, api: str) -> str:
        """
        Get the symbol format for a specific API.
        
        Args:
            symbol: Standard symbol (e.g., 'BTC/USD')
            api: API name (e.g., 'coingecko')
            
        Returns:
            Symbol in API-specific format
        """
        return cls.SYMBOL_MAPPING.get(symbol, {}).get(api, symbol)
    
    @classmethod
    def is_crypto_symbol(cls, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency."""
        crypto_symbols = ['BTC/USD', 'ETH/USD', 'XRP/USD']
        return symbol in crypto_symbols
    
    @classmethod
    def is_forex_symbol(cls, symbol: str) -> bool:
        """Check if symbol is a forex pair."""
        forex_symbols = ['EUR/USD']
        return symbol in forex_symbols
    
    @classmethod
    def is_commodity_symbol(cls, symbol: str) -> bool:
        """Check if symbol is a commodity."""
        commodity_symbols = ['XAU/USD']
        return symbol in commodity_symbols
