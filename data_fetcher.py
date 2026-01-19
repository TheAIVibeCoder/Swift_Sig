"""
Historical data fetcher using yfinance
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz


class DataFetcher:
    """
    Fetch historical OHLCV data from Yahoo Finance
    """

    def __init__(self):
        """Initialize data fetcher"""
        pass

    def fetch_ohlcv(
        self,
        pair: str,
        interval: str = "1h",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a trading pair

        Args:
            pair: Trading pair symbol (e.g., "EURUSD=X", "BTC-USD", "AAPL")
            interval: Data interval - valid values: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with OHLCV data and timezone-aware index
        """
        # Download data from yfinance
        ticker = yf.Ticker(pair)

        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=True
        )

        if df.empty:
            raise ValueError(f"No data available for {pair} with interval {interval}")

        # Ensure timezone-aware index
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')

        # Standardize column names
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        return df

    def validate_pair(self, pair: str) -> bool:
        """
        Check if a trading pair is valid

        Args:
            pair: Trading pair symbol

        Returns:
            True if pair exists, False otherwise
        """
        try:
            ticker = yf.Ticker(pair)
            info = ticker.info
            return 'symbol' in info or 'shortName' in info
        except:
            return False


# Helper functions for pair formatting
def get_forex_pair(base: str, quote: str) -> str:
    """
    Format forex pair for yfinance

    Args:
        base: Base currency (e.g., "EUR")
        quote: Quote currency (e.g., "USD")

    Returns:
        Formatted pair (e.g., "EURUSD=X")
    """
    return f"{base}{quote}=X"


def get_crypto_pair(base: str, quote: str = "USD") -> str:
    """
    Format crypto pair for yfinance

    Args:
        base: Base crypto (e.g., "BTC")
        quote: Quote currency (default: "USD")

    Returns:
        Formatted pair (e.g., "BTC-USD")
    """
    return f"{base}-{quote}"
