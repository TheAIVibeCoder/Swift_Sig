"""
Base strategy class that all trading strategies inherit from
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime
import pandas as pd
import pytz


@dataclass
class Signal:
    """Represents a trading signal"""
    pair: str
    direction: str  # "LONG" or "SHORT"
    entry_time: datetime
    entry_price: float
    tp_price: float
    sl_price: float
    strategy_name: str
    confidence: Optional[float] = None  # Optional confidence score 0-1

    def to_dict(self) -> dict:
        """Convert signal to dictionary"""
        return {
            "pair": self.pair,
            "direction": self.direction,
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "tp_price": self.tp_price,
            "sl_price": self.sl_price,
            "strategy_name": self.strategy_name,
            "confidence": self.confidence
        }


@dataclass
class TradeResult:
    """Represents a completed trade result"""
    pair: str
    entry_time: datetime
    exit_time: datetime
    direction: str  # "LONG" or "SHORT"
    strategy_name: str
    entry_price: float
    tp_price: float
    sl_price: float
    exit_price: float
    status: str  # "WIN", "LOSS", "BREAK_EVEN"
    pips: float

    def to_dict(self) -> dict:
        """Convert trade result to dictionary"""
        return {
            "pair": self.pair,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "direction": self.direction,
            "strategy_name": self.strategy_name,
            "entry_price": self.entry_price,
            "tp_price": self.tp_price,
            "sl_price": self.sl_price,
            "exit_price": self.exit_price,
            "status": self.status,
            "pips": self.pips
        }


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies

    All strategies must implement:
    - generate_signals(): Analyze data and produce trading signals
    - calculate_tp_sl(): Determine take profit and stop loss levels
    """

    def __init__(self, name: str, params: Optional[dict] = None):
        """
        Initialize strategy

        Args:
            name: Strategy name (should be unique)
            params: Dictionary of strategy parameters
        """
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, pair: str) -> List[Signal]:
        """
        Analyze price data and generate trading signals

        Args:
            df: DataFrame with OHLCV data (must have timezone-aware index)
            pair: Trading pair symbol

        Returns:
            List of Signal objects
        """
        pass

    @abstractmethod
    def calculate_tp_sl(
        self,
        df: pd.DataFrame,
        entry_price: float,
        direction: str,
        entry_index: int
    ) -> Tuple[float, float]:
        """
        Calculate take profit and stop loss levels

        Args:
            df: DataFrame with OHLCV data
            entry_price: Entry price
            direction: "LONG" or "SHORT"
            entry_index: Index in dataframe where entry occurs

        Returns:
            Tuple of (tp_price, sl_price)
        """
        pass

    def get_param(self, key: str, default=None):
        """
        Get strategy parameter with fallback to default

        Args:
            key: Parameter key
            default: Default value if key not found

        Returns:
            Parameter value or default
        """
        return self.params.get(key, default)

    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Validate that dataframe has required columns and format

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        required_cols = ["Open", "High", "Low", "Close"]

        # Check required columns
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")

        # Check timezone awareness
        if df.index.tz is None:
            raise ValueError("DataFrame index must be timezone-aware")

        # Check for empty data
        if df.empty:
            raise ValueError("DataFrame is empty")

        return True

    def __str__(self) -> str:
        """String representation of strategy"""
        return f"{self.name} (params: {self.params})"

    def __repr__(self) -> str:
        """Developer representation of strategy"""
        return f"<{self.__class__.__name__}: {self.name}>"
