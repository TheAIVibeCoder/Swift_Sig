"""
Data loading and management utilities using yfinance
"""
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Literal
import pytz


class DataLoader:
    """Handles fetching and caching market data from yfinance"""

    CACHE_DIR = "data"

    # Timeframe mapping for yfinance
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d"
    }

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize DataLoader

        Args:
            cache_enabled: Whether to use local cache for historical data
        """
        self.cache_enabled = cache_enabled
        if cache_enabled and not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)

    def _get_cache_path(self, symbol: str, timeframe: str, start: str, end: str) -> str:
        """Generate cache file path"""
        return os.path.join(
            self.CACHE_DIR,
            f"{symbol}_{timeframe}_{start}_{end}.csv"
        )

    def fetch_data(
        self,
        symbol: str,
        timeframe: Literal["1m", "5m", "15m", "1h", "4h", "1d"] = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_back: int = 30
    ) -> pd.DataFrame:
        """
        Fetch market data for a given symbol and timeframe

        Args:
            symbol: Trading pair (e.g., 'EURUSD=X' for forex, 'BTC-USD' for crypto)
            timeframe: Candlestick interval
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            days_back: Days to look back if start_date not provided

        Returns:
            DataFrame with OHLCV data and timezone-aware timestamps
        """
        # Handle date defaults
        if end_date is None:
            end_date = datetime.now(pytz.UTC).strftime("%Y-%m-%d")

        if start_date is None:
            start_date = (datetime.now(pytz.UTC) - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Check cache first
        cache_path = self._get_cache_path(symbol, timeframe, start_date, end_date)
        if self.cache_enabled and os.path.exists(cache_path):
            print(f"Loading {symbol} from cache...")
            df = pd.read_csv(cache_path, parse_dates=["Datetime"])
            df.set_index("Datetime", inplace=True)
            # Ensure timezone awareness
            if df.index.tz is None:
                df.index = df.index.tz_localize(pytz.UTC)
            return df

        # Fetch from yfinance
        print(f"Fetching {symbol} data from {start_date} to {end_date}...")
        ticker = yf.Ticker(symbol)

        try:
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=self.TIMEFRAME_MAP[timeframe]
            )

            if df.empty:
                raise ValueError(f"No data returned for {symbol}")

            # Standardize column names
            df.columns = [col.lower().capitalize() for col in df.columns]

            # Ensure timezone awareness
            if df.index.tz is None:
                df.index = df.index.tz_localize(pytz.UTC)
            else:
                df.index = df.index.tz_convert(pytz.UTC)

            # Save to cache
            if self.cache_enabled:
                df_to_save = df.copy()
                df_to_save.index.name = "Datetime"
                df_to_save.to_csv(cache_path)
                print(f"Cached data to {cache_path}")

            return df

        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {symbol}: {str(e)}")

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached data

        Args:
            symbol: If provided, only clear cache for this symbol. Otherwise clear all.
        """
        if not os.path.exists(self.CACHE_DIR):
            return

        files = os.listdir(self.CACHE_DIR)
        for file in files:
            if symbol is None or file.startswith(symbol):
                os.remove(os.path.join(self.CACHE_DIR, file))
                print(f"Removed cache file: {file}")


def get_forex_pair(base: str, quote: str = "USD") -> str:
    """
    Convert currency pair to yfinance format

    Args:
        base: Base currency (e.g., 'EUR')
        quote: Quote currency (default: 'USD')

    Returns:
        Yahoo Finance forex symbol (e.g., 'EURUSD=X')
    """
    return f"{base}{quote}=X"


def get_crypto_pair(base: str, quote: str = "USD") -> str:
    """
    Convert crypto pair to yfinance format

    Args:
        base: Base cryptocurrency (e.g., 'BTC')
        quote: Quote currency (default: 'USD')

    Returns:
        Yahoo Finance crypto symbol (e.g., 'BTC-USD')
    """
    return f"{base}-{quote}"


if __name__ == "__main__":
    # Test the data loader
    loader = DataLoader()

    # Fetch EURUSD data
    eurusd = get_forex_pair("EUR", "USD")
    df = loader.fetch_data(eurusd, timeframe="1h", days_back=7)

    print(f"\nFetched {len(df)} candles for {eurusd}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nData info:")
    print(df.info())
