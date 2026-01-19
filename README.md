# SwiftSig - Trading Strategy Backtesting Platform

A professional backtesting engine for trading strategies with realistic trade simulation and comprehensive performance metrics.

## Features

- **Realistic Trade Simulation**: Checks high/low prices for accurate TP/SL execution
- **Comprehensive Metrics**: Win rate, profit factor, Sharpe ratio, max drawdown, and more
- **Modular Strategy Framework**: Easy to add new strategies without touching existing code
- **Multiple Asset Classes**: Support for forex, crypto, and stocks via yfinance
- **Export Results**: Save trades and metrics to CSV/JSON formats
- **Multiple Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d support
- **Trade-by-Trade Analysis**: Track every entry, exit, and outcome

## Project Structure

```
SwiftSig/
├── strategies/          # Individual strategy implementations
│   ├── base_strategy.py # Abstract base class
│   └── ma_crossover.py  # MA crossover strategy with ATR
├── backtest.py         # Backtesting engine
├── data_fetcher.py     # Historical data fetching (yfinance)
├── backtests/          # Exported results (auto-created)
├── main.py            # Entry point
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

### Web Interface (Recommended)

Run the web application for an interactive frontend:

```bash
python app.py
```

Then open your browser to `http://localhost:5000` (or the Replit URL if using Replit).

**Features:**
- Interactive form to configure backtest parameters
- Real-time results with color-coded metrics
- Trade history table
- Download CSV/JSON results
- Mobile-responsive design

### Command Line Interface

Run a backtest from the command line:

```bash
python main.py
```

### Command Line Examples

```bash
# Forex pair
python main.py EURUSD --days 30 --timeframe 1h

# Crypto
python main.py BTC-USD --days 60 --timeframe 4h

# Stock
python main.py AAPL --days 365 --timeframe 1d

# With date range
python main.py GBPUSD --start 2024-01-01 --end 2024-12-31

# Use CLI interface
python main.py --help
```

### Command Line Arguments

- `pair`: Trading pair (EURUSD, BTC-USD, AAPL, etc.)
- `--strategy`: Strategy to use (default: ma_crossover)
- `--timeframe`: Candlestick interval - 1m, 5m, 15m, 1h, 4h, 1d (default: 1h)
- `--days`: Days of historical data (default: 30)
- `--start`: Start date in YYYY-MM-DD format
- `--end`: End date in YYYY-MM-DD format
- `--no-export`: Don't export results to files

### Programmatic Usage

```python
from data_fetcher import DataFetcher
from strategies.ma_crossover import MACrossoverStrategy
from backtest import BacktestEngine
from datetime import datetime, timedelta

# Fetch data
fetcher = DataFetcher()
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

df = fetcher.fetch_ohlcv(
    pair="EURUSD=X",
    interval="1h",
    start_date=start_date,
    end_date=end_date
)

# Create strategy
strategy = MACrossoverStrategy(fast_period=50, slow_period=200)

# Run backtest
engine = BacktestEngine(strategy=strategy, initial_capital=10000.0)
results = engine.run(df=df, pair="EURUSD=X", pip_value=0.0001, lot_size=1.0)

# Print and export
engine.print_summary(results)
engine.export_results(results, format="both")
```

## Creating Custom Strategies

Extend `BaseStrategy` to create your own strategies:

```python
from strategies.base_strategy import BaseStrategy, Signal
import pandas as pd
from typing import List

class MyStrategy(BaseStrategy):
    def __init__(self, param1: int, param2: float):
        super().__init__(name="my_strategy")
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, df: pd.DataFrame, pair: str) -> List[Signal]:
        signals = []

        # Calculate your indicators
        # Identify entry points
        # Create Signal objects with entry, TP, SL prices

        for i in range(100, len(df)):  # Start after warmup period
            if your_entry_condition:
                signal = Signal(
                    pair=pair,
                    entry_time=df.index[i],
                    direction="LONG",  # or "SHORT"
                    strategy_name=self.name,
                    entry_price=df.iloc[i]["Close"],
                    tp_price=df.iloc[i]["Close"] * 1.03,  # 3% profit
                    sl_price=df.iloc[i]["Close"] * 0.98   # 2% stop
                )
                signals.append(signal)

        return signals
```

## Strategies

### MA Crossover Strategy

Classic moving average crossover strategy with ATR-based risk management.

**Parameters:**
- `fast_period`: Fast MA period (default: 50)
- `slow_period`: Slow MA period (default: 200)

**Signals:**
- **LONG**: Fast MA crosses above Slow MA
- **SHORT**: Fast MA crosses below Slow MA

**Risk Management:**
- Stop Loss: 2x ATR
- Take Profit: 3x ATR

## Performance Metrics

The backtesting engine calculates:

- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of winning trades
- **Total Wins/Losses**: Count of winning and losing trades
- **Total Pips**: Net profit/loss in pips
- **Avg Winning/Losing Pips**: Average pips per win/loss
- **Profit Factor**: Gross profit / Gross loss
- **Max Drawdown**: Largest peak-to-trough decline in pips
- **Sharpe Ratio**: Risk-adjusted return metric

## Output Files

Results are automatically exported to the `backtests/` directory:

- `{PAIR}_{STRATEGY}_{TIMESTAMP}_trades.csv`: Individual trade details
- `{PAIR}_{STRATEGY}_{TIMESTAMP}_results.json`: Full results with metrics

Example:
```
backtests/
├── EURUSD_ma_crossover_20260119_143052_trades.csv
└── EURUSD_ma_crossover_20260119_143052_results.json
```

## Roadmap

- [x] Backtesting engine implementation
- [x] Performance metrics and reporting
- [x] MA Crossover strategy
- [ ] More strategy examples (RSI, Bollinger Bands, etc.)
- [ ] TradingView chart integration
- [ ] Telegram bot for signals
- [ ] Web dashboard
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
