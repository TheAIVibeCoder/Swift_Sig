"""
Main entry point for SwiftSig Trading Platform
"""
import argparse
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from strategies.ma_crossover import MACrossoverStrategy
from backtest import BacktestEngine


def run_backtest(
    pair: str,
    strategy_name: str = "ma_crossover",
    timeframe: str = "1h",
    days_back: int = 30,
    start_date: str = None,
    end_date: str = None,
    export: bool = True
):
    """
    Run a backtest for a given pair and strategy

    Args:
        pair: Trading pair symbol (e.g., 'EURUSD=X', 'BTC-USD', 'AAPL')
        strategy_name: Name of strategy to use
        timeframe: Candlestick interval
        days_back: Days of historical data (if start_date not provided)
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        export: Whether to export results to files
    """
    print(f"\n{'='*60}")
    print(f"SwiftSig Backtesting Platform")
    print(f"{'='*60}\n")

    # Load data
    print(f"Loading data for {pair}...")
    fetcher = DataFetcher()

    # Calculate date range
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = datetime.now() - timedelta(days=days_back)

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end = datetime.now()

    df = fetcher.fetch_ohlcv(
        pair=pair,
        interval=timeframe,
        start_date=start,
        end_date=end
    )

    print(f"Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")

    # Select strategy
    if strategy_name.lower() == "ma_crossover":
        strategy = MACrossoverStrategy(fast_period=50, slow_period=200)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    print(f"Strategy: {strategy}")

    # Run backtest
    engine = BacktestEngine(strategy=strategy, initial_capital=10000.0)

    # Determine pip value based on pair
    if "JPY" in pair:
        pip_value = 0.01
    else:
        pip_value = 0.0001

    results = engine.run(df=df, pair=pair, pip_value=pip_value, lot_size=1.0)

    # Print summary
    engine.print_summary(results)

    # Export results
    if export:
        file_paths = engine.export_results(results, format="both")
        print(f"Results saved:")
        for key, path in file_paths.items():
            print(f"  - {key}: {path}")

    return results


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="SwiftSig Trading Strategy Backtesting Platform"
    )

    parser.add_argument(
        "pair",
        type=str,
        help="Trading pair (e.g., EURUSD, GBPUSD, BTC, ETH, AAPL)"
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default="ma_crossover",
        choices=["ma_crossover"],
        help="Strategy to use (default: ma_crossover)"
    )

    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        choices=["1m", "5m", "15m", "1h", "4h", "1d"],
        help="Candlestick timeframe (default: 1h)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days of historical data to use (default: 30)"
    )

    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD format)"
    )

    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD format)"
    )

    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Don't export results to files"
    )

    parser.add_argument(
        "--forex",
        action="store_true",
        help="Treat pair as forex (e.g., EUR USD becomes EURUSD=X)"
    )

    parser.add_argument(
        "--crypto",
        action="store_true",
        help="Treat pair as crypto (e.g., BTC becomes BTC-USD)"
    )

    args = parser.parse_args()

    # Convert pair format
    pair = args.pair.upper()

    if args.forex:
        # Split into base and quote (e.g., "EUR USD" or "EURUSD")
        if " " in pair:
            base, quote = pair.split()
        elif len(pair) == 6:
            base, quote = pair[:3], pair[3:]
        else:
            raise ValueError("Forex pair format: EUR USD or EURUSD")
        pair = f"{base}{quote}=X"

    elif args.crypto:
        # Handle crypto format
        if " " in pair:
            base, quote = pair.split()
        else:
            base, quote = pair, "USD"
        pair = f"{base}-{quote}"

    # Default: assume forex if 6 characters
    elif len(pair) == 6 and pair.isalpha():
        base, quote = pair[:3], pair[3:]
        pair = f"{base}{quote}=X"

    # Run backtest
    run_backtest(
        pair=pair,
        strategy_name=args.strategy,
        timeframe=args.timeframe,
        days_back=args.days,
        start_date=args.start,
        end_date=args.end,
        export=not args.no_export
    )


if __name__ == "__main__":
    # Example usage for testing
    # Uncomment to run directly:

    # Example 1: Forex
    run_backtest("EURUSD=X", timeframe="1h", days_back=90)

    # Example 2: Crypto
    # run_backtest("BTC-USD", timeframe="4h", days_back=60)

    # Example 3: Stock
    # run_backtest("AAPL", timeframe="1d", days_back=365)

    # For CLI usage, comment out examples above and use:
    # main()
