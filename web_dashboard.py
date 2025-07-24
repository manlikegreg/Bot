"""
Web dashboard for monitoring the Trading Signal Bot.
Provides real-time status, signal history, and bot controls.
"""

from flask import Flask, render_template, jsonify, request
import json
from datetime import datetime
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading_bot_dashboard_2024'

# Setup logger for web dashboard
logger = logging.getLogger(__name__)

# Global bot instance (will be set by main.py)
app.bot = None

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current bot status."""
    try:
        if app.bot:
            status = app.bot.get_status()
            return jsonify({
                'success': True,
                'data': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/signals/current')
def get_current_signals():
    """Get current trading signals."""
    try:
        if app.bot:
            status = app.bot.get_status()
            current_signals = status.get('current_signals', {})
            
            # Format signals for display
            formatted_signals = []
            for symbol, data in current_signals.items():
                consensus = data.get('consensus', {})
                formatted_signals.append({
                    'symbol': symbol,
                    'signal': consensus.get('signal', 'HOLD'),
                    'confidence': consensus.get('confidence', 0),
                    'price': data.get('price', 0),
                    'timestamp': data.get('timestamp', ''),
                    'reason': consensus.get('reason', 'No analysis available'),
                    'individual_signals': consensus.get('individual_signals', [])
                })
            
            return jsonify({
                'success': True,
                'data': formatted_signals
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/signals/history')
def get_signal_history():
    """Get signal history."""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Try to read from signal log file
        history = []
        try:
            with open('signals.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        signal_data = json.loads(line.strip())
                        history.append(signal_data)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass  # No history file yet
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/errors')
def get_errors():
    """Get recent errors."""
    try:
        if app.bot:
            status = app.bot.get_status()
            errors = status.get('errors', [])
            
            # Also try to read from error log file
            error_history = []
            try:
                limit = request.args.get('limit', 20, type=int)
                with open('errors.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-limit:]
                    for line in lines:
                        try:
                            error_data = json.loads(line.strip())
                            error_history.append(error_data)
                        except json.JSONDecodeError:
                            continue
            except FileNotFoundError:
                pass
            
            return jsonify({
                'success': True,
                'data': {
                    'recent_errors': errors,
                    'error_history': error_history
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/config')
def get_config():
    """Get bot configuration."""
    try:
        from config import Config
        config = Config()
        
        # Return safe configuration (no sensitive data)
        safe_config = {
            'trading_symbols': config.TRADING_SYMBOLS,
            'confidence_threshold': config.CONFIDENCE_THRESHOLD,
            'rsi_period': config.RSI_PERIOD,
            'macd_periods': {
                'fast': config.MACD_FAST_PERIOD,
                'slow': config.MACD_SLOW_PERIOD,
                'signal': config.MACD_SIGNAL_PERIOD
            },
            'bollinger_period': config.BOLLINGER_PERIOD,
            'ma_periods': {
                'short': config.MA_SHORT_PERIOD,
                'long': config.MA_LONG_PERIOD
            },
            'telegram_configured': bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)
        }
        
        return jsonify({
            'success': True,
            'data': safe_config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/test-telegram', methods=['POST'])
def test_telegram():
    """Test Telegram connection."""
    try:
        if app.bot:
            # Import here to avoid circular imports
            import asyncio
            from telegram_bot import TelegramBot
            
            async def test_connection():
                telegram_bot = TelegramBot()
                return await telegram_bot.test_connection()
            
            success = asyncio.run(test_connection())
            
            return jsonify({
                'success': success,
                'message': 'Test message sent successfully' if success else 'Failed to send test message'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/run-analysis', methods=['POST'])
def trigger_analysis():
    """Manually trigger analysis cycle."""
    try:
        if app.bot:
            import asyncio
            
            # Queue a manual analysis - safer approach
            try:
                app.bot.manual_analysis_requested = True
                logger.info("Manual analysis requested via web dashboard")
            except Exception as e:
                logger.error(f"Error queuing manual analysis: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Analysis cycle triggered'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/start-bot', methods=['POST'])
def start_bot():
    """Start the trading bot."""
    try:
        if app.bot:
            app.bot.is_running = True
            logger.info("Trading bot started via web dashboard")
            return jsonify({
                'success': True,
                'message': 'Bot started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stop-bot', methods=['POST'])
def stop_bot():
    """Stop the trading bot."""
    try:
        if app.bot:
            app.bot.is_running = False
            logger.info("Trading bot stopped via web dashboard")
            return jsonify({
                'success': True,
                'message': 'Bot stopped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot not initialized'
            })
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats')
def get_stats():
    """Get bot statistics."""
    try:
        stats = {
            'uptime': 'N/A',
            'total_cycles': 0,
            'successful_cycles': 0,
            'total_signals': 0,
            'signals_by_type': {'BUY': 0, 'SELL': 0, 'HOLD': 0},
            'avg_confidence': 0,
            'api_success_rate': 0
        }
        
        if app.bot:
            status = app.bot.get_status()
            stats['total_signals'] = status.get('total_signals_sent', 0)
            
            # Try to calculate stats from log files
            try:
                # Read signal history
                with open('signals.log', 'r', encoding='utf-8') as f:
                    signal_count = 0
                    confidence_sum = 0
                    
                    for line in f:
                        try:
                            signal_data = json.loads(line.strip())
                            signal = signal_data.get('signal', 'HOLD')
                            confidence = signal_data.get('confidence', 0)
                            
                            if signal in stats['signals_by_type']:
                                stats['signals_by_type'][signal] += 1
                            
                            confidence_sum += confidence
                            signal_count += 1
                        except json.JSONDecodeError:
                            continue
                    
                    if signal_count > 0:
                        stats['avg_confidence'] = confidence_sum / signal_count
                        stats['total_cycles'] = signal_count
                        stats['successful_cycles'] = signal_count  # Simplified
                        
            except FileNotFoundError:
                pass
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # This won't be used when imported by main.py
    app.run(host='0.0.0.0', port=5000, debug=True)
