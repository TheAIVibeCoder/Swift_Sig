# SwiftSig - Trading Strategy Backtesting & Signal Platform

A modular, maintainable trading analysis platform with backtesting capabilities, real-time data integration, and signal distribution via Telegram.

## Features

- **Modular Strategy Framework**: Easy to add new strategies without touching existing code
- **Multiple Asset Classes**: Support for forex, crypto, and stocks via yfinance
- **Backtesting Engine**: Test strategies on historical data with comprehensive metrics
- **Real-time Signals**: Telegram bot integration for instant trade alerts
- **Multiple Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d support
- **Data Caching**: Avoid rate limits with local data storage
- **TradingView Charts**: Visualize strategies with interactive charts

## Project Structure

```
SwiftSig/
├── strategies/          # Individual strategy implementations
│   ├── base_strategy.py # Abstract base class
│   └── ma_crossover.py  # Example MA crossover strategy
├── data/               # Cached historical data (gitignored)
├── backtests/          # Saved backtest results (gitignored)
├── configs/            # Strategy configurations
├── utils/              # Helper functions
│   └── data_loader.py  # Data fetching and caching
├── templates/          # HTML/chart templates
├── main.py            # Entry point
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd SwiftSig
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file for secrets:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_IDS=123456789,987654321
```

### Replit Setup

1. Import this repository to Replit
2. Replit will auto-detect dependencies from `requirements.txt`
3. Add secrets in Replit's Secrets tab:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_IDS`
4. Run the application

## Quick Start

### Test Data Loading

```python
from utils import DataLoader, get_forex_pair

loader = DataLoader()
eurusd = get_forex_pair("EUR", "USD")
df = loader.fetch_data(eurusd, timeframe="1h", days_back=7)
print(df.head())
```

### Run a Strategy

```python
from strategies import MACrossoverStrategy
from utils import DataLoader, get_forex_pair

# Load data
loader = DataLoader()
eurusd = get_forex_pair("EUR", "USD")
df = loader.fetch_data(eurusd, timeframe="1h", days_back=30)

# Create and run strategy
strategy = MACrossoverStrategy(params={
    "fast_period": 20,
    "slow_period": 50
})

signals = strategy.generate_signals(df, eurusd)
print(f"Generated {len(signals)} signals")
```

## Creating a New Strategy

1. Create a new file in `strategies/` directory
2. Inherit from `BaseStrategy`
3. Implement required methods:
   - `generate_signals()`: Analyze data and produce signals
   - `calculate_tp_sl()`: Determine TP/SL levels

Example:

```python
from strategies.base_strategy import BaseStrategy, Signal
from typing import List, Tuple
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, params: dict = None):
        super().__init__(name="My_Strategy", params=params or {})

    def generate_signals(self, df: pd.DataFrame, pair: str) -> List[Signal]:
        # Your logic here
        signals = []
        # ... analyze data and create signals
        return signals

    def calculate_tp_sl(self, df, entry_price, direction, entry_index) -> Tuple[float, float]:
        # Your TP/SL logic here
        tp = entry_price * 1.02  # Example: 2% profit
        sl = entry_price * 0.99  # Example: 1% loss
        return tp, sl
```

## Supported Assets

### Forex
```python
from utils import get_forex_pair
eurusd = get_forex_pair("EUR", "USD")  # Returns "EURUSD=X"
gbpjpy = get_forex_pair("GBP", "JPY")  # Returns "GBPJPY=X"
```

### Crypto
```python
from utils import get_crypto_pair
btc = get_crypto_pair("BTC", "USD")    # Returns "BTC-USD"
eth = get_crypto_pair("ETH", "USD")    # Returns "ETH-USD"
```

### Stocks
```python
# Use ticker symbol directly
df = loader.fetch_data("AAPL", timeframe="1d", days_back=365)
```

## Testing

Run the included examples:

```bash
# Test data loader
python utils/data_loader.py

# Test MA crossover strategy
python strategies/ma_crossover.py
```

## Roadmap

- [ ] Backtesting engine implementation
- [ ] TradingView chart integration
- [ ] Telegram bot for signals
- [ ] Web dashboard (Flask)
- [ ] More strategy examples (RSI, Bollinger Bands, etc.)
- [ ] Performance metrics and reporting
- [ ] Unit tests

## Contributing

This project follows clean code principles:
- Minimal, surgical edits only
- No code duplication
- Type hints and docstrings required
- Meaningful commit messages

## License

MIT License - feel free to use and modify.

## Disclaimer

This software is for educational purposes only. Use at your own risk. Past performance does not guarantee future results. Always do your own research before trading.
