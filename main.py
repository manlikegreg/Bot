#!/usr/bin/env python3
"""
Quantitative Trading Signal Bot
Main entry point for the trading signal bot that analyzes multiple assets
and sends high-confidence signals to Telegram.
"""

import asyncio
import schedule
import time
import threading
from datetime import datetime
import logging
from typing import Dict, List

from config import Config
from api_handlers import DataFetcher
from indicators import TechnicalIndicators
from signal_processor import SignalProcessor
from telegram_bot import TelegramBot
from logger import setup_logger
from web_dashboard import app

class TradingBot:
    def __init__(self):
        """Initialize the trading bot with all necessary components."""
        self.logger = setup_logger()
        self.config = Config()
        self.data_fetcher = DataFetcher()
        self.indicators = TechnicalIndicators()
        self.signal_processor = SignalProcessor()
        self.telegram_bot = TelegramBot()
        self.last_signals = {}
        self.is_running = True  # Bot starts running by default
        self.bot_status = {
            'running': True,
            'last_run': None,
            'total_signals_sent': 0,
            'errors': [],
            'current_signals': {}
        }
        
    def get_status(self):
        """Get current bot status for web dashboard."""
        self.bot_status['running'] = self.is_running
        return self.bot_status
        
    async def analyze_asset(self, symbol: str) -> Dict:
        """
        Analyze a single asset and generate signals.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            
        Returns:
            Dict containing analysis results and signals
        """
        try:
            self.logger.info(f"Analyzing {symbol}...")
            
            # Fetch data from multiple sources
            data = await self.data_fetcher.get_asset_data(symbol)
            
            if not data or 'price_data' not in data:
                self.logger.warning(f"No data available for {symbol}")
                return {'symbol': symbol, 'signals': [], 'error': 'No data available'}
            
            # Calculate technical indicators
            indicators_data = self.indicators.calculate_all_indicators(data['price_data'])
            
            # Generate signals from each indicator
            signals = []
            
            # RSI Signal
            rsi_signal = self._generate_rsi_signal(indicators_data.get('rsi'))
            if rsi_signal:
                signals.append(rsi_signal)
            
            # MACD Signal
            macd_signal = self._generate_macd_signal(indicators_data.get('macd'))
            if macd_signal:
                signals.append(macd_signal)
            
            # Bollinger Bands Signal
            bb_signal = self._generate_bollinger_signal(
                data['price_data'], indicators_data.get('bollinger')
            )
            if bb_signal:
                signals.append(bb_signal)
            
            # Moving Average Crossover Signal
            ma_signal = self._generate_ma_crossover_signal(indicators_data.get('ma'))
            if ma_signal:
                signals.append(ma_signal)
            
            # Volume Spike Signal
            volume_signal = self._generate_volume_signal(data.get('volume_data'))
            if volume_signal:
                signals.append(volume_signal)
            
            return {
                'symbol': symbol,
                'current_price': data.get('current_price', 0),
                'signals': signals,
                'indicators': indicators_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {str(e)}")
            self.bot_status['errors'].append(f"{symbol}: {str(e)}")
            return {'symbol': symbol, 'signals': [], 'error': str(e)}
    
    def _generate_rsi_signal(self, rsi_data: Dict) -> Dict:
        """Generate RSI-based trading signal."""
        if not rsi_data or 'current' not in rsi_data:
            return None
        
        rsi_value = rsi_data['current']
        confidence = 0
        signal_type = 'HOLD'
        reason = f"RSI: {rsi_value:.2f}"
        
        if rsi_value <= 30:  # Oversold
            signal_type = 'BUY'
            confidence = min(95, (30 - rsi_value) * 3 + 70)
            reason += " (Oversold condition)"
        elif rsi_value >= 70:  # Overbought
            signal_type = 'SELL'
            confidence = min(95, (rsi_value - 70) * 3 + 70)
            reason += " (Overbought condition)"
        elif 45 <= rsi_value <= 55:  # Neutral
            confidence = 60
            reason += " (Neutral zone)"
        
        return {
            'source': 'RSI',
            'signal': signal_type,
            'confidence': confidence,
            'reason': reason
        }
    
    def _generate_macd_signal(self, macd_data: Dict) -> Dict:
        """Generate MACD-based trading signal."""
        if not macd_data or 'macd' not in macd_data or 'signal' not in macd_data:
            return None
        
        macd_line = macd_data['macd']
        signal_line = macd_data['signal']
        histogram = macd_data.get('histogram', 0)
        
        confidence = 0
        signal_type = 'HOLD'
        reason = "MACD analysis"
        
        # MACD crossover signals
        if macd_line > signal_line and histogram > 0:
            signal_type = 'BUY'
            confidence = min(90, abs(histogram) * 20 + 65)
            reason = "MACD bullish crossover"
        elif macd_line < signal_line and histogram < 0:
            signal_type = 'SELL'
            confidence = min(90, abs(histogram) * 20 + 65)
            reason = "MACD bearish crossover"
        
        return {
            'source': 'MACD',
            'signal': signal_type,
            'confidence': confidence,
            'reason': reason
        }
    
    def _generate_bollinger_signal(self, price_data: List, bb_data: Dict) -> Dict:
        """Generate Bollinger Bands-based trading signal."""
        if not bb_data or not price_data or 'upper' not in bb_data:
            return None
        
        current_price = price_data[-1]
        upper_band = bb_data['upper']
        lower_band = bb_data['lower']
        middle_band = bb_data['middle']
        
        confidence = 0
        signal_type = 'HOLD'
        reason = "Bollinger Bands analysis"
        
        # Price near bands
        if current_price <= lower_band:
            signal_type = 'BUY'
            confidence = min(85, ((lower_band - current_price) / lower_band) * 100 + 70)
            reason = "Price touching lower Bollinger Band"
        elif current_price >= upper_band:
            signal_type = 'SELL'
            confidence = min(85, ((current_price - upper_band) / upper_band) * 100 + 70)
            reason = "Price touching upper Bollinger Band"
        
        return {
            'source': 'Bollinger Bands',
            'signal': signal_type,
            'confidence': confidence,
            'reason': reason
        }
    
    def _generate_ma_crossover_signal(self, ma_data: Dict) -> Dict:
        """Generate Moving Average crossover signal."""
        if not ma_data or 'ma50' not in ma_data or 'ma200' not in ma_data:
            return None
        
        ma50 = ma_data['ma50']
        ma200 = ma_data['ma200']
        ma50_prev = ma_data.get('ma50_prev', ma50)
        ma200_prev = ma_data.get('ma200_prev', ma200)
        
        confidence = 0
        signal_type = 'HOLD'
        reason = "MA crossover analysis"
        
        # Golden Cross (50 MA crosses above 200 MA)
        if ma50 > ma200 and ma50_prev <= ma200_prev:
            signal_type = 'BUY'
            confidence = 80
            reason = "Golden Cross: 50 MA crossed above 200 MA"
        # Death Cross (50 MA crosses below 200 MA)
        elif ma50 < ma200 and ma50_prev >= ma200_prev:
            signal_type = 'SELL'
            confidence = 80
            reason = "Death Cross: 50 MA crossed below 200 MA"
        
        return {
            'source': 'MA Crossover',
            'signal': signal_type,
            'confidence': confidence,
            'reason': reason
        }
    
    def _generate_volume_signal(self, volume_data: List) -> Dict:
        """Generate volume-based trading signal."""
        if not volume_data or len(volume_data) < 20:
            return None
        
        current_volume = volume_data[-1]
        avg_volume = sum(volume_data[-20:]) / 20
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        confidence = 0
        signal_type = 'HOLD'
        reason = f"Volume analysis (ratio: {volume_ratio:.2f})"
        
        # Volume spike detection
        if volume_ratio >= 2.0:  # Volume is 2x average
            signal_type = 'BUY'  # Assuming volume spike indicates buying interest
            confidence = min(75, (volume_ratio - 2) * 15 + 60)
            reason = f"Strong volume spike: {volume_ratio:.2f}x average"
        
        return {
            'source': 'Volume Analysis',
            'signal': signal_type,
            'confidence': confidence,
            'reason': reason
        }
    
    async def run_analysis_cycle(self):
        """Run a complete analysis cycle for all assets."""
        try:
            # Check if bot is running
            if not self.is_running:
                self.logger.info("Bot is stopped, skipping analysis cycle")
                return
                
            self.bot_status['running'] = self.is_running
            self.bot_status['last_run'] = datetime.now().isoformat()
            self.logger.info("Starting analysis cycle...")
            
            # Analyze all assets
            analysis_tasks = [
                self.analyze_asset(symbol) for symbol in self.config.TRADING_SYMBOLS
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and generate consensus signals
            for result in results:
                if isinstance(result, dict) and 'signals' in result:
                    symbol = result['symbol']
                    
                    # Process signals and determine consensus
                    consensus = self.signal_processor.process_signals(result['signals'])
                    
                    # Store current signals for dashboard
                    self.bot_status['current_signals'][symbol] = {
                        'consensus': consensus,
                        'price': result.get('current_price', 0),
                        'timestamp': result.get('timestamp')
                    }
                    
                    # Send Telegram alert if consensus is strong enough
                    if consensus['confidence'] >= 80 and consensus['signal'] != 'HOLD':
                        await self.send_trading_alert(symbol, result, consensus)
            
            self.logger.info("Analysis cycle completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {str(e)}")
            self.bot_status['errors'].append(f"Analysis cycle error: {str(e)}")
        finally:
            self.bot_status['running'] = False
    
    async def send_trading_alert(self, symbol: str, analysis: Dict, consensus: Dict):
        """Send trading alert to Telegram."""
        try:
            current_price = analysis.get('current_price', 0)
            
            # Calculate entry, stop loss, and take profit levels
            entry_price = current_price
            
            if consensus['signal'] == 'BUY':
                stop_loss = entry_price * 0.99  # 1% stop loss
                take_profit = entry_price * 1.02  # 2% take profit
            else:  # SELL
                stop_loss = entry_price * 1.01  # 1% stop loss
                take_profit = entry_price * 0.98  # 2% take profit
            
            # Format message
            message = f"""📊 Strong Signal Alert
Pair: {symbol}
Signal: {consensus['signal']}
Entry: ${entry_price:.2f}
SL: ${stop_loss:.2f}
TP: ${take_profit:.2f}
Timeframe: 15min to 1hr
Confidence: {consensus['confidence']:.0f}%
Reason: {consensus['reason']}"""
            
            # Send to Telegram
            success = await self.telegram_bot.send_message(message)
            
            if success:
                self.bot_status['total_signals_sent'] += 1
                self.logger.info(f"Alert sent for {symbol}: {consensus['signal']}")
            else:
                self.logger.error(f"Failed to send alert for {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error sending alert for {symbol}: {str(e)}")
    
    def schedule_bot(self):
        """Schedule the bot to run every 10 minutes."""
        schedule.every(10).minutes.do(lambda: asyncio.run(self.run_analysis_cycle()))
        
        self.logger.info("Bot scheduled to run every 10 minutes")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def run_web_dashboard():
    """Run the web dashboard in a separate thread."""
    app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    """Main entry point."""
    # Initialize bot
    bot = TradingBot()
    
    # Share bot instance with web dashboard
    app.bot = bot
    
    # Start web dashboard in separate thread
    dashboard_thread = threading.Thread(target=run_web_dashboard, daemon=True)
    dashboard_thread.start()
    
    print("🚀 Trading Signal Bot Started!")
    print("📊 Web Dashboard: http://localhost:5000")
    print("⏰ Analysis runs every 10 minutes")
    print("📱 Telegram alerts enabled")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Run initial analysis
        asyncio.run(bot.run_analysis_cycle())
        
        # Start scheduled runs
        bot.schedule_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {str(e)}")

if __name__ == "__main__":
    main()
