# Trading Signal Bot

## Overview

This is a quantitative trading signal bot built in Python that analyzes multiple financial assets (BTC/USD, ETH/USD, XAU/USD, EUR/USD, XRP/USD) and generates high-confidence trading signals. The bot fetches data from multiple APIs, calculates technical indicators, processes signals through consensus algorithms, and delivers alerts via Telegram. It includes a web dashboard for monitoring and manual controls.

**Status: FULLY OPERATIONAL** - Bot is live and sending real trading signals with API keys configured.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

**Core Components:**
- **Data Layer**: API handlers for fetching market data from multiple sources
- **Analysis Layer**: Technical indicators calculation and signal processing
- **Communication Layer**: Telegram bot for alert delivery
- **Monitoring Layer**: Web dashboard for real-time status and controls
- **Configuration Layer**: Centralized configuration management

**Architecture Pattern**: The system uses an async/await pattern for concurrent data fetching and implements the context manager pattern for resource management.

## Key Components

### 1. Main Application (`main.py`)
- **Purpose**: Entry point and orchestration
- **Design**: Implements the main `TradingBot` class that coordinates all components
- **Features**: Scheduled analysis every 10 minutes, status tracking, error handling

### 2. Data Fetching (`api_handlers.py`)
- **Purpose**: Multi-source market data retrieval
- **APIs Supported**: CoinGecko, Alpha Vantage, TwelveData
- **Pattern**: Uses async context managers and connection pooling
- **Error Handling**: Implements retry logic and timeout management

### 3. Technical Analysis (`indicators.py`)
- **Purpose**: Calculate trading indicators
- **Indicators**: RSI (14), MACD, Bollinger Bands, Moving Averages, Volume analysis
- **Library**: Uses pandas and numpy for efficient calculations
- **Validation**: Includes data sufficiency checks

### 4. Signal Processing (`signal_processor.py`)
- **Purpose**: Aggregate multiple indicator signals into consensus
- **Algorithm**: Weighted averaging with confidence thresholds
- **Decision Logic**: Requires ≥80% confidence for signal generation
- **Output**: BUY/SELL/HOLD signals with reasoning

### 5. Telegram Integration (`telegram_bot.py`)
- **Purpose**: Alert delivery system
- **Format**: Structured messages with entry/exit levels
- **Features**: HTML formatting, error handling, delivery confirmation

### 6. Web Dashboard (`web_dashboard.py`)
- **Framework**: Flask-based web interface
- **Features**: Real-time status, signal history, start/stop bot controls, manual analysis trigger
- **API**: RESTful endpoints for frontend interaction
- **Controls**: Start/Stop bot buttons with real-time status updates

### 7. Configuration (`config.py`)
- **Purpose**: Centralized settings management
- **Features**: Environment variable support, API keys, trading parameters
- **Security**: Uses environment variables for sensitive data

### 8. Logging (`logger.py`)
- **Purpose**: Structured logging with file rotation
- **Features**: Multiple log levels, formatted output, backup retention

## Data Flow

1. **Data Collection**: Bot fetches market data from multiple APIs concurrently
2. **Indicator Calculation**: Raw price data is processed through technical indicators
3. **Signal Generation**: Each indicator produces individual signals with confidence scores
4. **Consensus Processing**: Signals are aggregated using weighted averaging
5. **Alert Delivery**: High-confidence signals (≥80%) are formatted and sent via Telegram
6. **Status Updates**: Dashboard displays real-time status and signal history

## External Dependencies

### APIs
- **CoinGecko**: Cryptocurrency market data
- **Alpha Vantage**: Forex and commodities data
- **TwelveData**: Multi-asset market data
- **Telegram Bot API**: Message delivery

### Python Libraries
- **aiohttp**: Async HTTP client for API requests
- **pandas/numpy**: Data manipulation and calculations
- **flask**: Web dashboard framework
- **schedule**: Task scheduling

### Configuration Requirements
- Telegram Bot Token and Chat ID (hardcoded in config)
- API keys for data sources (environment variables)

## Deployment Strategy

**Development Setup:**
- All dependencies managed through standard Python imports
- Configuration via environment variables with fallbacks
- File-based logging with rotation

**Runtime Requirements:**
- Python 3.7+ with async/await support
- Network access for API calls and Telegram delivery
- File system access for logging

**Scalability Considerations:**
- Async architecture supports concurrent API calls
- Modular design allows easy addition of new data sources or indicators
- Stateless design enables horizontal scaling

**Monitoring:**
- Web dashboard provides real-time status
- Comprehensive logging for debugging
- Error tracking and retry mechanisms

The system is designed for reliability with multiple fallback mechanisms, comprehensive error handling, and clear separation between data sources, analysis logic, and delivery mechanisms.