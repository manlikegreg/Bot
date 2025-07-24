"""
API handlers for fetching market data from multiple sources.
Handles data fetching from CoinGecko, Alpha Vantage, TwelveData and other APIs.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from config import Config

class DataFetcher:
    """Handles fetching market data from multiple API sources."""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.API_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_asset_data(self, symbol: str) -> Dict:
        """
        Get comprehensive market data for an asset from multiple sources.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            
        Returns:
            Dict containing price data, volume data, and metadata
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.API_TIMEOUT)
            )
        
        data = {
            'symbol': symbol,
            'current_price': 0,
            'price_data': [],
            'volume_data': [],
            'timestamp': datetime.now().isoformat(),
            'sources': []
        }
        
        try:
            # Determine which APIs to use based on symbol type
            if self.config.is_crypto_symbol(symbol):
                await self._fetch_crypto_data(symbol, data)
            elif self.config.is_forex_symbol(symbol):
                await self._fetch_forex_data(symbol, data)
            elif self.config.is_commodity_symbol(symbol):
                await self._fetch_commodity_data(symbol, data)
            
            # Ensure we have some price data
            if not data['price_data']:
                self.logger.warning(f"No price data obtained for {symbol}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return data
    
    async def _fetch_crypto_data(self, symbol: str, data: Dict):
        """Fetch cryptocurrency data from multiple sources."""
        tasks = [
            self._fetch_coingecko_data(symbol, data),
            self._fetch_twelvedata_crypto(symbol, data)
        ]
        
        # Run API calls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Crypto API {i} failed for {symbol}: {str(result)}")
    
    async def _fetch_forex_data(self, symbol: str, data: Dict):
        """Fetch forex data from multiple sources."""
        tasks = [
            self._fetch_alpha_vantage_forex(symbol, data),
            self._fetch_twelvedata_forex(symbol, data)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Forex API {i} failed for {symbol}: {str(result)}")
    
    async def _fetch_commodity_data(self, symbol: str, data: Dict):
        """Fetch commodity data (Gold) from multiple sources.""" 
        tasks = [
            self._fetch_alpha_vantage_commodity(symbol, data),
            self._fetch_twelvedata_commodity(symbol, data)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Commodity API {i} failed for {symbol}: {str(result)}")
    
    async def _fetch_coingecko_data(self, symbol: str, data: Dict):
        """Fetch data from CoinGecko API."""
        try:
            coin_id = self.config.get_symbol_for_api(symbol, 'coingecko')
            
            # Get current price
            price_url = self.config.API_ENDPOINTS['coingecko_price']
            price_params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true'
            }
            
            async with self.session.get(price_url, params=price_params) as response:
                if response.status == 200:
                    price_data = await response.json()
                    
                    if coin_id in price_data:
                        current_price = price_data[coin_id]['usd']
                        data['current_price'] = current_price
                        data['sources'].append('coingecko_price')
                        
                        # Add volume if available
                        if 'usd_24h_vol' in price_data[coin_id]:
                            volume = price_data[coin_id]['usd_24h_vol']
                            data['volume_data'].append(volume)
            
            # Get historical data for technical analysis
            history_url = self.config.API_ENDPOINTS['coingecko_history'].format(coin_id)
            history_params = {
                'vs_currency': 'usd',
                'days': '1',
                'interval': 'hourly'
            }
            
            async with self.session.get(history_url, params=history_params) as response:
                if response.status == 200:
                    history_data = await response.json()
                    
                    if 'prices' in history_data:
                        prices = [price[1] for price in history_data['prices']]
                        data['price_data'].extend(prices)
                        data['sources'].append('coingecko_history')
                    
                    if 'total_volumes' in history_data:
                        volumes = [vol[1] for vol in history_data['total_volumes']]
                        data['volume_data'].extend(volumes)
                        
        except Exception as e:
            self.logger.error(f"CoinGecko API error for {symbol}: {str(e)}")
            raise
    
    async def _fetch_alpha_vantage_forex(self, symbol: str, data: Dict):
        """Fetch forex data from Alpha Vantage."""
        try:
            if not self.config.ALPHA_VANTAGE_API_KEY or self.config.ALPHA_VANTAGE_API_KEY == 'demo':
                self.logger.warning("Alpha Vantage API key not available")
                return
            
            url = self.config.API_ENDPOINTS['alpha_vantage_fx']
            params = {
                'function': 'FX_INTRADAY',
                'from_symbol': symbol.split('/')[0],
                'to_symbol': symbol.split('/')[1],
                'interval': '15min',
                'apikey': self.config.ALPHA_VANTAGE_API_KEY
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    av_data = await response.json()
                    
                    if 'Time Series (15min)' in av_data:
                        time_series = av_data['Time Series (15min)']
                        
                        # Extract prices and volumes
                        prices = []
                        volumes = []
                        
                        for timestamp, values in sorted(time_series.items()):
                            prices.append(float(values['4. close']))
                            volumes.append(float(values.get('5. volume', 0)))
                        
                        data['price_data'].extend(prices[-50:])  # Last 50 data points
                        data['volume_data'].extend(volumes[-50:])
                        
                        if prices:
                            data['current_price'] = prices[-1]
                        
                        data['sources'].append('alpha_vantage_forex')
                        
        except Exception as e:
            self.logger.error(f"Alpha Vantage Forex API error for {symbol}: {str(e)}")
            raise
    
    async def _fetch_alpha_vantage_commodity(self, symbol: str, data: Dict):
        """Fetch commodity data from Alpha Vantage."""
        try:
            if not self.config.ALPHA_VANTAGE_API_KEY or self.config.ALPHA_VANTAGE_API_KEY == 'demo':
                self.logger.warning("Alpha Vantage API key not available")
                return
            
            url = self.config.API_ENDPOINTS['alpha_vantage_fx']
            params = {
                'function': 'FX_INTRADAY',
                'from_symbol': 'XAU',
                'to_symbol': 'USD', 
                'interval': '15min',
                'apikey': self.config.ALPHA_VANTAGE_API_KEY
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    av_data = await response.json()
                    
                    if 'Time Series (15min)' in av_data:
                        time_series = av_data['Time Series (15min)']
                        
                        prices = []
                        volumes = []
                        
                        for timestamp, values in sorted(time_series.items()):
                            prices.append(float(values['4. close']))
                            volumes.append(float(values.get('5. volume', 0)))
                        
                        data['price_data'].extend(prices[-50:])
                        data['volume_data'].extend(volumes[-50:])
                        
                        if prices:
                            data['current_price'] = prices[-1]
                        
                        data['sources'].append('alpha_vantage_commodity')
                        
        except Exception as e:
            self.logger.error(f"Alpha Vantage Commodity API error for {symbol}: {str(e)}")
            raise
    
    async def _fetch_twelvedata_crypto(self, symbol: str, data: Dict):
        """Fetch crypto data from TwelveData."""
        await self._fetch_twelvedata_generic(symbol, data, 'crypto')
    
    async def _fetch_twelvedata_forex(self, symbol: str, data: Dict):
        """Fetch forex data from TwelveData."""
        await self._fetch_twelvedata_generic(symbol, data, 'forex')
    
    async def _fetch_twelvedata_commodity(self, symbol: str, data: Dict):
        """Fetch commodity data from TwelveData."""
        await self._fetch_twelvedata_generic(symbol, data, 'commodity')
    
    async def _fetch_twelvedata_generic(self, symbol: str, data: Dict, asset_type: str):
        """Generic TwelveData fetcher."""
        try:
            if not self.config.TWELVEDATA_API_KEY or self.config.TWELVEDATA_API_KEY == 'demo':
                self.logger.warning("TwelveData API key not available")
                return
            
            td_symbol = self.config.get_symbol_for_api(symbol, 'twelvedata')
            url = self.config.API_ENDPOINTS['twelvedata']
            params = {
                'symbol': td_symbol,
                'interval': '15min',
                'outputsize': 50,
                'apikey': self.config.TWELVEDATA_API_KEY
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    td_data = await response.json()
                    
                    if 'values' in td_data and td_data['values']:
                        values = td_data['values']
                        
                        prices = []
                        volumes = []
                        
                        for item in reversed(values):  # Reverse to get chronological order
                            prices.append(float(item['close']))
                            volumes.append(float(item.get('volume', 0)))
                        
                        data['price_data'].extend(prices)
                        data['volume_data'].extend(volumes)
                        
                        if prices:
                            data['current_price'] = prices[-1]
                        
                        data['sources'].append(f'twelvedata_{asset_type}')
                        
        except Exception as e:
            self.logger.error(f"TwelveData API error for {symbol}: {str(e)}")
            raise
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
