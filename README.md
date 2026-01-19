# SwiftSig - Trading Strategy Backtesting Platform

A professional, **local-first** backtesting engine for testing trading strategies with realistic trade simulation and comprehensive performance metrics.

## Philosophy: Local Development First

This project is designed to run **100% locally on your machine**. No cloud deployment, no complex CI/CD, no remote dependencies. Build and test strategies locally, then optionally deploy when ready.

## Features

- **Realistic Trade Simulation**: Checks high/low prices for accurate TP/SL execution
- **Comprehensive Metrics**: Win rate, profit factor, Sharpe ratio, max drawdown, and more
- **Beautiful Web Interface**: Modern, responsive UI for running backtests
- **Modular Strategy Framework**: Easy to add new strategies without touching existing code
- **Multiple Asset Classes**: Forex, crypto, and stocks via yfinance
- **Export Results**: Save trades and metrics to CSV/JSON formats
- **Multiple Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d support
- **Trade-by-Trade Analysis**: Track every entry, exit, and outcome

## Project Structure

```
SwiftSig/
├── app.py              # Flask web application
├── backtest.py         # Backtesting engine
├── data_fetcher.py     # Historical data fetching (yfinance)
├── main.py             # CLI entry point
├── strategies/         # Strategy implementations
│   ├── base_strategy.py
│   └── ma_crossover.py
├── templates/          # HTML templates
│   └── index.html
├── backtests/          # Exported results (auto-created)
└── requirements.txt    # Python dependencies
```

## Quick Start (5 Minutes)

### 1. Install Python

Download Python 3.8+ from [python.org](https://www.python.org/downloads/)

### 2. Install Dependencies

Open Command Prompt or PowerShell in the project folder:

```bash
pip install -r requirements.txt
```

### 3. Run the Web App

```bash
python app.py
```

### 4. Open Your Browser

Navigate to `http://localhost:5000`

That's it! You're ready to backtest strategies.

## Usage

### Web Interface (Recommended)

The web interface provides an intuitive way to run backtests:

1. **Start the app**: `python app.py`
2. **Open browser**: `http://localhost:5000`
3. **Configure backtest**:
   - Enter trading pair (EURUSD, BTC-USD, AAPL, etc.)
   - Select timeframe (1h, 4h, 1d, etc.)
   - Set date range or days back
   - Adjust MA periods
4. **Run backtest**: Click "Run Backtest"
5. **View results**: See metrics, trade history, download CSV/JSON

### Command Line Interface

For automated testing or scripting:

```bash
# Basic usage
python main.py

# Custom pair and timeframe
python main.py EURUSD --days 90 --timeframe 1h

# Crypto
python main.py BTC-USD --days 60 --timeframe 4h

# Stocks
python main.py AAPL --days 365 --timeframe 1d

# Date range
python main.py GBPUSD --start 2024-01-01 --end 2024-12-31

# See all options
python main.py --help
```

### Programmatic Usage

For integrating into your own scripts:

```python
from data_fetcher import DataFetcher
from strategies.ma_crossover import MACrossoverStrategy
from backtest import BacktestEngine
from datetime import datetime, timedelta

# Fetch data
fetcher = DataFetcher()
df = fetcher.fetch_ohlcv(
    pair="EURUSD=X",
    interval="1h",
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now()
)

# Create strategy and run backtest
strategy = MACrossoverStrategy(fast_period=50, slow_period=200)
engine = BacktestEngine(strategy=strategy, initial_capital=10000.0)
results = engine.run(df=df, pair="EURUSD=X", pip_value=0.0001)

# Print results
engine.print_summary(results)
engine.export_results(results, format="both")
```

## Current Strategy: MA Crossover with ATR

The implemented strategy uses moving average crossovers with ATR-based risk management:

**How It Works:**
- **Fast MA (50)** crosses above **Slow MA (200)** → LONG signal
- **Fast MA (50)** crosses below **Slow MA (200)** → SHORT signal
- **Stop Loss**: 2× ATR from entry
- **Take Profit**: 3× ATR from entry
- **Risk/Reward Ratio**: 1:1.5

**Why This Strategy:**
- Classic trend-following approach
- ATR adapts to market volatility
- Works across multiple asset classes
- Simple to understand and modify

## Creating Custom Strategies

Add your own strategies by extending `BaseStrategy`:

```python
from strategies.base_strategy import BaseStrategy, Signal
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, param1: int = 20):
        super().__init__(name="my_strategy")
        self.param1 = param1

    def generate_signals(self, df: pd.DataFrame, pair: str):
        signals = []

        # Your indicator calculations
        # ...

        # Generate signals
        for i in range(100, len(df)):
            if your_long_condition:
                signal = Signal(
                    pair=pair,
                    entry_time=df.index[i],
                    direction="LONG",
                    strategy_name=self.name,
                    entry_price=df.iloc[i]["Close"],
                    tp_price=df.iloc[i]["Close"] * 1.02,
                    sl_price=df.iloc[i]["Close"] * 0.99
                )
                signals.append(signal)

        return signals
```

Save to `strategies/my_strategy.py`, then update `main.py` and `app.py` to include it.

## Performance Metrics

The backtesting engine calculates:

| Metric | Description |
|--------|-------------|
| **Total Trades** | Number of trades executed |
| **Win Rate** | Percentage of winning trades |
| **Total Pips** | Net profit/loss in pips |
| **Profit Factor** | Gross profit ÷ Gross loss |
| **Avg Win/Loss** | Average pips per winning/losing trade |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Sharpe Ratio** | Risk-adjusted return metric |

## Output Files

Results are automatically saved to `backtests/`:

- `{PAIR}_{STRATEGY}_{TIMESTAMP}_trades.csv` - Trade-by-trade details
- `{PAIR}_{STRATEGY}_{TIMESTAMP}_results.json` - Full results with metrics

## TradingView Integration (Coming Soon)

Two ways to integrate with TradingView:

### Option 1: Pine Script (Immediate)
Convert the strategy to Pine Script and backtest directly on TradingView charts.

### Option 2: Webhook Integration (Future)
- TradingView sends alerts via webhook
- Flask app receives signals
- Telegram bot notifies you instantly
- Requires TradingView Premium

## Development Workflow

```
1. Write/modify strategy in strategies/
2. Test locally using web interface (python app.py)
3. Review results and iterate
4. Export successful strategies
5. (Optional) Deploy to VPS when ready for live monitoring
```

## Local Development & Deployment

**Current Phase: Local Development**
- Run everything locally with `python app.py`
- Web dashboard at `http://localhost:5000`
- Use Git for version control (optional)
- Test strategies thoroughly before considering deployment

**Future: Deployment Options**
When you're ready to deploy (not required):
- **Option 1**: Render (free tier)
- **Option 2**: Railway (free tier)
- **Option 3**: DigitalOcean VPS ($4/month)
- **Option 4**: Keep running locally (recommended for now)

## Roadmap

**Completed:**
- [x] Backtesting engine with realistic execution
- [x] Web interface with real-time results
- [x] MA Crossover strategy with ATR
- [x] Performance metrics and reporting
- [x] CSV/JSON export

**Next Steps:**
- [ ] More strategies (RSI, Bollinger Bands, MACD)
- [ ] Parameter optimization
- [ ] TradingView webhook integration
- [ ] Telegram notifications
- [ ] Position sizing calculator
- [ ] Walk-forward analysis

## Troubleshooting

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**Port already in use:**
The app runs on port 5000. Change it in `app.py` if needed:
```python
port = int(os.environ.get('PORT', 8080))  # Change to 8080
```

**No data fetched:**
- Check your internet connection
- Verify the trading pair format (EURUSD=X for forex, BTC-USD for crypto)
- Try a different timeframe

## Contributing

Clean code principles:
- Minimal, surgical edits only
- No code duplication
- Type hints and docstrings
- Meaningful commit messages

## License

MIT License - free to use and modify.

## Disclaimer

**Educational purposes only.** This software is for learning and strategy development. Use at your own risk. Past performance does not guarantee future results. Always do your own research before trading with real money.
