"""
Telegram bot integration for sending trading alerts.
Handles message formatting and delivery to Telegram chat.
"""

import aiohttp
import asyncio
import logging
from typing import Optional
from datetime import datetime

from config import Config

class TelegramBot:
    """Handle Telegram bot operations for sending trading alerts."""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Validate Telegram configuration
        if not self.config.TELEGRAM_BOT_TOKEN:
            self.logger.error("Telegram bot token not configured")
        if not self.config.TELEGRAM_CHAT_ID:
            self.logger.error("Telegram chat ID not configured")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message to the configured Telegram chat.
        
        Args:
            message: Message text to send
            parse_mode: Message parsing mode (HTML, Markdown, or None)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.config.TELEGRAM_BOT_TOKEN or not self.config.TELEGRAM_CHAT_ID:
            self.logger.error("Telegram configuration missing")
            return False
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )
            
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                'chat_id': self.config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    self.logger.info("Telegram message sent successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Telegram API error {response.status}: {error_text}")
                    return False
                    
        except asyncio.TimeoutError:
            self.logger.error("Telegram message timeout")
            return False
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    async def send_trading_alert(self, symbol: str, signal_data: dict) -> bool:
        """
        Send a formatted trading alert message.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USD')
            signal_data: Dict containing signal information
            
        Returns:
            bool: True if alert sent successfully
        """
        try:
            message = self._format_trading_alert(symbol, signal_data)
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending trading alert for {symbol}: {str(e)}")
            return False
    
    def _format_trading_alert(self, symbol: str, signal_data: dict) -> str:
        """
        Format a trading alert message for Telegram.
        
        Args:
            symbol: Trading symbol
            signal_data: Signal information dict
            
        Returns:
            Formatted message string
        """
        try:
            signal = signal_data.get('signal', 'HOLD')
            confidence = signal_data.get('confidence', 0)
            reason = signal_data.get('reason', 'Technical analysis')
            current_price = signal_data.get('current_price', 0)
            
            # Calculate entry, stop loss, and take profit
            entry_price = current_price
            
            if signal == 'BUY':
                emoji = "🟢"
                stop_loss = entry_price * 0.98  # 2% stop loss
                take_profit = entry_price * 1.04  # 4% take profit
            elif signal == 'SELL':
                emoji = "🔴"
                stop_loss = entry_price * 1.02  # 2% stop loss
                take_profit = entry_price * 0.96  # 4% take profit
            else:
                emoji = "⚪"
                stop_loss = entry_price
                take_profit = entry_price
            
            # Get risk metrics if available
            risk_metrics = signal_data.get('risk_metrics', {})
            risk_reward = risk_metrics.get('risk_reward_ratio', 2.0)
            position_size = risk_metrics.get('position_size_suggestion', 'Medium')
            
            # Format timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            message = f"""🎯 <b>TRADING SIGNAL ALERT</b>
            
{emoji} <b>Pair:</b> {symbol}
📊 <b>Signal:</b> {signal}
💰 <b>Entry:</b> ${entry_price:.4f}
🛑 <b>Stop Loss:</b> ${stop_loss:.4f}
🎯 <b>Take Profit:</b> ${take_profit:.4f}
⏰ <b>Timeframe:</b> 15min to 1hr
🔥 <b>Confidence:</b> {confidence:.1f}%
📈 <b>Risk/Reward:</b> 1:{risk_reward:.1f}
📦 <b>Position Size:</b> {position_size}

💡 <b>Analysis:</b> {reason}

⏰ <b>Time:</b> {timestamp}

<i>⚠️ This is not financial advice. Trade at your own risk.</i>"""
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting trading alert: {str(e)}")
            return f"🚨 Trading Alert: {symbol} - {signal_data.get('signal', 'UNKNOWN')} signal detected"
    
    async def send_bot_status(self, status_data: dict) -> bool:
        """
        Send bot status update to Telegram.
        
        Args:
            status_data: Dict containing bot status information
            
        Returns:
            bool: True if status sent successfully
        """
        try:
            message = self._format_status_message(status_data)
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending bot status: {str(e)}")
            return False
    
    def _format_status_message(self, status_data: dict) -> str:
        """
        Format bot status message for Telegram.
        
        Args:
            status_data: Status information dict
            
        Returns:
            Formatted status message
        """
        try:
            running = status_data.get('running', False)
            last_run = status_data.get('last_run', 'Never')
            total_signals = status_data.get('total_signals_sent', 0)
            errors = status_data.get('errors', [])
            current_signals = status_data.get('current_signals', {})
            
            status_emoji = "🟢" if running else "🔴"
            status_text = "Running" if running else "Stopped"
            
            # Format last run time
            if last_run and last_run != 'Never':
                try:
                    last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
                    last_run_str = last_run_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    last_run_str = last_run
            else:
                last_run_str = "Never"
            
            message = f"""🤖 <b>BOT STATUS UPDATE</b>

{status_emoji} <b>Status:</b> {status_text}
⏰ <b>Last Run:</b> {last_run_str}
📡 <b>Signals Sent:</b> {total_signals}
⚠️ <b>Recent Errors:</b> {len(errors)}

<b>📊 Current Market Signals:</b>"""
            
            # Add current signals summary
            if current_signals:
                for symbol, data in current_signals.items():
                    consensus = data.get('consensus', {})
                    signal = consensus.get('signal', 'HOLD')
                    confidence = consensus.get('confidence', 0)
                    price = data.get('price', 0)
                    
                    signal_emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "⚪"
                    message += f"\n{signal_emoji} {symbol}: {signal} ({confidence:.0f}%) - ${price:.4f}"
            else:
                message += "\nNo active signals"
            
            # Add recent errors if any
            if errors:
                message += f"\n\n<b>⚠️ Recent Errors:</b>"
                for error in errors[-3:]:  # Show last 3 errors
                    message += f"\n• {error}"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            message += f"\n\n<i>Updated: {timestamp}</i>"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting status message: {str(e)}")
            return f"🤖 Bot Status: {status_data.get('running', 'Unknown')}"
    
    async def send_error_alert(self, error_message: str) -> bool:
        """
        Send error alert to Telegram.
        
        Args:
            error_message: Error message to send
            
        Returns:
            bool: True if error alert sent successfully
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            message = f"""🚨 <b>BOT ERROR ALERT</b>

⚠️ <b>Error:</b> {error_message}
⏰ <b>Time:</b> {timestamp}

<i>Please check bot logs for more details.</i>"""
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending error alert: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            test_message = f"🧪 Bot connection test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            return await self.send_message(test_message)
            
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {str(e)}")
            return False
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
