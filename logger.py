"""
Logging configuration for the Trading Signal Bot.
Sets up structured logging with file rotation and console output.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config import Config

def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up and configure logger for the trading bot.
    
    Args:
        name: Logger name (defaults to root logger)
        
    Returns:
        Configured logger instance
    """
    config = Config()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.LOG_FILE,
            maxBytes=config.MAX_LOG_SIZE,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info("="*60)
    logger.info("Trading Signal Bot Logger Initialized")
    logger.info(f"Log Level: {config.LOG_LEVEL}")
    logger.info(f"Log File: {config.LOG_FILE}")
    logger.info("="*60)
    
    return logger

class TradingBotLogger:
    """Custom logger class with trading-specific methods."""
    
    def __init__(self, name: str = None):
        self.logger = setup_logger(name)
        self.signal_log_file = 'signals.log'
        self.error_log_file = 'errors.log'
    
    def log_signal(self, symbol: str, signal_data: dict):
        """
        Log trading signal with structured format.
        
        Args:
            symbol: Trading symbol
            signal_data: Signal information dict
        """
        try:
            timestamp = datetime.now().isoformat()
            signal = signal_data.get('signal', 'UNKNOWN')
            confidence = signal_data.get('confidence', 0)
            reason = signal_data.get('reason', '')
            
            log_entry = {
                'timestamp': timestamp,
                'symbol': symbol,
                'signal': signal,
                'confidence': confidence,
                'reason': reason,
                'individual_signals': signal_data.get('individual_signals', [])
            }
            
            # Log to main logger
            self.logger.info(f"SIGNAL | {symbol} | {signal} | {confidence:.1f}% | {reason}")
            
            # Log to signals file
            self._write_to_file(self.signal_log_file, log_entry)
            
        except Exception as e:
            self.logger.error(f"Error logging signal: {str(e)}")
    
    def log_api_call(self, api_name: str, symbol: str, success: bool, response_time: float = None, error: str = None):
        """
        Log API call results.
        
        Args:
            api_name: Name of the API
            symbol: Symbol being fetched
            success: Whether the call was successful
            response_time: Response time in seconds
            error: Error message if call failed
        """
        try:
            status = "SUCCESS" if success else "FAILED"
            time_str = f" | {response_time:.2f}s" if response_time else ""
            error_str = f" | {error}" if error else ""
            
            self.logger.info(f"API | {api_name} | {symbol} | {status}{time_str}{error_str}")
            
        except Exception as e:
            self.logger.error(f"Error logging API call: {str(e)}")
    
    def log_bot_cycle(self, cycle_duration: float, signals_processed: int, alerts_sent: int):
        """
        Log bot cycle completion.
        
        Args:
            cycle_duration: Duration of the cycle in seconds
            signals_processed: Number of signals processed
            alerts_sent: Number of alerts sent
        """
        try:
            self.logger.info(
                f"CYCLE | Duration: {cycle_duration:.2f}s | "
                f"Signals: {signals_processed} | Alerts: {alerts_sent}"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging bot cycle: {str(e)}")
    
    def log_error_with_context(self, error: Exception, context: dict = None):
        """
        Log error with additional context information.
        
        Args:
            error: Exception object
            context: Additional context information
        """
        try:
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {}
            }
            
            # Log to main logger
            self.logger.error(f"ERROR | {type(error).__name__} | {str(error)}")
            
            # Log context if provided
            if context:
                for key, value in context.items():
                    self.logger.error(f"CONTEXT | {key}: {value}")
            
            # Log to errors file
            self._write_to_file(self.error_log_file, error_data)
            
        except Exception as e:
            self.logger.error(f"Error logging error: {str(e)}")
    
    def _write_to_file(self, filename: str, data: dict):
        """
        Write structured data to log file.
        
        Args:
            filename: Log file name
            data: Data to write
        """
        try:
            import json
            
            # Ensure log directory exists
            log_dir = os.path.dirname(filename) if os.path.dirname(filename) else '.'
            os.makedirs(log_dir, exist_ok=True)
            
            # Append to file
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, default=str) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error writing to log file {filename}: {str(e)}")
    
    def get_recent_signals(self, limit: int = 10) -> list:
        """
        Get recent signals from log file.
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of recent signal dicts
        """
        try:
            import json
            
            if not os.path.exists(self.signal_log_file):
                return []
            
            signals = []
            with open(self.signal_log_file, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-limit:]:
                    try:
                        signal_data = json.loads(line.strip())
                        signals.append(signal_data)
                    except json.JSONDecodeError:
                        continue
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error reading recent signals: {str(e)}")
            return []
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """
        Get recent errors from log file.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent error dicts
        """
        try:
            import json
            
            if not os.path.exists(self.error_log_file):
                return []
            
            errors = []
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-limit:]:
                    try:
                        error_data = json.loads(line.strip())
                        errors.append(error_data)
                    except json.JSONDecodeError:
                        continue
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error reading recent errors: {str(e)}")
            return []
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up old log entries.
        
        Args:
            days_to_keep: Number of days of logs to keep
        """
        try:
            import json
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for log_file in [self.signal_log_file, self.error_log_file]:
                if not os.path.exists(log_file):
                    continue
                
                temp_file = f"{log_file}.temp"
                kept_entries = 0
                
                with open(log_file, 'r', encoding='utf-8') as infile, \
                     open(temp_file, 'w', encoding='utf-8') as outfile:
                    
                    for line in infile:
                        try:
                            entry = json.loads(line.strip())
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            
                            if entry_date >= cutoff_date:
                                outfile.write(line)
                                kept_entries += 1
                                
                        except (json.JSONDecodeError, KeyError, ValueError):
                            # Keep malformed entries
                            outfile.write(line)
                            kept_entries += 1
                
                # Replace original file
                os.replace(temp_file, log_file)
                self.logger.info(f"Cleaned up {log_file}, kept {kept_entries} entries")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up logs: {str(e)}")
