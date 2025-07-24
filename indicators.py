"""
Technical indicators calculation module.
Implements RSI, MACD, Bollinger Bands, Moving Averages, and Volume analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging
from config import Config

class TechnicalIndicators:
    """Calculate various technical indicators for trading signals."""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_indicators(self, price_data: List[float]) -> Dict:
        """
        Calculate all technical indicators for given price data.
        
        Args:
            price_data: List of price values (chronological order)
            
        Returns:
            Dict containing all calculated indicators
        """
        if not price_data or len(price_data) < 50:
            self.logger.warning("Insufficient price data for technical analysis")
            return {}
        
        try:
            # Convert to pandas Series for easier calculation
            prices = pd.Series(price_data)
            
            indicators = {}
            
            # Calculate RSI
            indicators['rsi'] = self._calculate_rsi(prices)
            
            # Calculate MACD
            indicators['macd'] = self._calculate_macd(prices)
            
            # Calculate Bollinger Bands
            indicators['bollinger'] = self._calculate_bollinger_bands(prices)
            
            # Calculate Moving Averages
            indicators['ma'] = self._calculate_moving_averages(prices)
            
            # Calculate additional indicators
            indicators['stochastic'] = self._calculate_stochastic(prices)
            indicators['momentum'] = self._calculate_momentum(prices)
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {str(e)}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series) -> Dict:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Price series
            
        Returns:
            Dict with RSI values
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.RSI_PERIOD).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'current': float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50,
                'previous': float(rsi.iloc[-2]) if len(rsi) > 1 and not np.isnan(rsi.iloc[-2]) else 50,
                'series': rsi.dropna().tolist()[-20:]  # Last 20 values
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return {'current': 50, 'previous': 50, 'series': []}
    
    def _calculate_macd(self, prices: pd.Series) -> Dict:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Price series
            
        Returns:
            Dict with MACD values
        """
        try:
            # Calculate EMAs
            ema_fast = prices.ewm(span=self.config.MACD_FAST_PERIOD).mean()
            ema_slow = prices.ewm(span=self.config.MACD_SLOW_PERIOD).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line (EMA of MACD)
            signal_line = macd_line.ewm(span=self.config.MACD_SIGNAL_PERIOD).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]) if not np.isnan(macd_line.iloc[-1]) else 0,
                'signal': float(signal_line.iloc[-1]) if not np.isnan(signal_line.iloc[-1]) else 0,
                'histogram': float(histogram.iloc[-1]) if not np.isnan(histogram.iloc[-1]) else 0,
                'macd_prev': float(macd_line.iloc[-2]) if len(macd_line) > 1 and not np.isnan(macd_line.iloc[-2]) else 0,
                'signal_prev': float(signal_line.iloc[-2]) if len(signal_line) > 1 and not np.isnan(signal_line.iloc[-2]) else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {str(e)}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'macd_prev': 0, 'signal_prev': 0}
    
    def _calculate_bollinger_bands(self, prices: pd.Series) -> Dict:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            
        Returns:
            Dict with Bollinger Bands values
        """
        try:
            # Simple Moving Average
            sma = prices.rolling(window=self.config.BOLLINGER_PERIOD).mean()
            
            # Standard Deviation
            std = prices.rolling(window=self.config.BOLLINGER_PERIOD).std()
            
            # Bollinger Bands
            upper_band = sma + (std * self.config.BOLLINGER_STD_DEV)
            lower_band = sma - (std * self.config.BOLLINGER_STD_DEV)
            
            # Band width and %B
            band_width = (upper_band - lower_band) / sma * 100
            percent_b = (prices - lower_band) / (upper_band - lower_band) * 100
            
            return {
                'upper': float(upper_band.iloc[-1]) if not np.isnan(upper_band.iloc[-1]) else 0,
                'middle': float(sma.iloc[-1]) if not np.isnan(sma.iloc[-1]) else 0,
                'lower': float(lower_band.iloc[-1]) if not np.isnan(lower_band.iloc[-1]) else 0,
                'width': float(band_width.iloc[-1]) if not np.isnan(band_width.iloc[-1]) else 0,
                'percent_b': float(percent_b.iloc[-1]) if not np.isnan(percent_b.iloc[-1]) else 50
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return {'upper': 0, 'middle': 0, 'lower': 0, 'width': 0, 'percent_b': 50}
    
    def _calculate_moving_averages(self, prices: pd.Series) -> Dict:
        """
        Calculate Moving Averages (50 and 200 period).
        
        Args:
            prices: Price series
            
        Returns:
            Dict with moving average values
        """
        try:
            ma50 = prices.rolling(window=self.config.MA_SHORT_PERIOD).mean()
            ma200 = prices.rolling(window=self.config.MA_LONG_PERIOD).mean()
            
            return {
                'ma50': float(ma50.iloc[-1]) if not np.isnan(ma50.iloc[-1]) else 0,
                'ma200': float(ma200.iloc[-1]) if not np.isnan(ma200.iloc[-1]) else 0,
                'ma50_prev': float(ma50.iloc[-2]) if len(ma50) > 1 and not np.isnan(ma50.iloc[-2]) else 0,
                'ma200_prev': float(ma200.iloc[-2]) if len(ma200) > 1 and not np.isnan(ma200.iloc[-2]) else 0,
                'ma50_slope': self._calculate_slope(ma50.dropna().iloc[-5:]),
                'ma200_slope': self._calculate_slope(ma200.dropna().iloc[-5:])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating moving averages: {str(e)}")
            return {'ma50': 0, 'ma200': 0, 'ma50_prev': 0, 'ma200_prev': 0, 'ma50_slope': 0, 'ma200_slope': 0}
    
    def _calculate_stochastic(self, prices: pd.Series) -> Dict:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            prices: Price series (assuming close prices)
            
        Returns:
            Dict with stochastic values
        """
        try:
            # For simplicity, using prices as both high, low, and close
            high = prices.rolling(window=14).max()
            low = prices.rolling(window=14).min()
            
            k_percent = ((prices - low) / (high - low)) * 100
            d_percent = k_percent.rolling(window=3).mean()
            
            return {
                'k': float(k_percent.iloc[-1]) if not np.isnan(k_percent.iloc[-1]) else 50,
                'd': float(d_percent.iloc[-1]) if not np.isnan(d_percent.iloc[-1]) else 50
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating stochastic: {str(e)}")
            return {'k': 50, 'd': 50}
    
    def _calculate_momentum(self, prices: pd.Series) -> Dict:
        """
        Calculate price momentum.
        
        Args:
            prices: Price series
            
        Returns:
            Dict with momentum values
        """
        try:
            momentum_10 = prices / prices.shift(10) - 1  # 10-period momentum
            momentum_20 = prices / prices.shift(20) - 1  # 20-period momentum
            
            return {
                'momentum_10': float(momentum_10.iloc[-1]) if not np.isnan(momentum_10.iloc[-1]) else 0,
                'momentum_20': float(momentum_20.iloc[-1]) if not np.isnan(momentum_20.iloc[-1]) else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum: {str(e)}")
            return {'momentum_10': 0, 'momentum_20': 0}
    
    def _calculate_slope(self, series: pd.Series) -> float:
        """
        Calculate the slope of a series (trend direction).
        
        Args:
            series: Data series
            
        Returns:
            Slope value
        """
        try:
            if len(series) < 2:
                return 0
            
            x = np.arange(len(series))
            y = series.values
            
            # Linear regression slope
            slope = np.polyfit(x, y, 1)[0]
            return float(slope)
            
        except Exception as e:
            return 0
    
    def calculate_volume_indicators(self, price_data: List[float], volume_data: List[float]) -> Dict:
        """
        Calculate volume-based indicators.
        
        Args:
            price_data: List of prices
            volume_data: List of volumes
            
        Returns:
            Dict with volume indicators
        """
        try:
            if not volume_data or len(volume_data) < 20:
                return {'volume_sma': 0, 'volume_ratio': 1, 'vwap': 0}
            
            volumes = pd.Series(volume_data)
            prices = pd.Series(price_data)
            
            # Volume Simple Moving Average
            volume_sma = volumes.rolling(window=20).mean()
            
            # Current volume vs average ratio
            current_volume = volumes.iloc[-1]
            avg_volume = volume_sma.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volume Weighted Average Price (approximation)
            typical_price = prices  # Using close price as typical price
            vwap = (typical_price * volumes).sum() / volumes.sum() if volumes.sum() > 0 else 0
            
            return {
                'volume_sma': float(avg_volume) if not np.isnan(avg_volume) else 0,
                'volume_ratio': float(volume_ratio),
                'vwap': float(vwap) if not np.isnan(vwap) else 0,
                'volume_trend': self._calculate_slope(volumes.iloc[-10:])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating volume indicators: {str(e)}")
            return {'volume_sma': 0, 'volume_ratio': 1, 'vwap': 0, 'volume_trend': 0}
