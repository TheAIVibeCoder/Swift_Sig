"""
Moving Average Crossover Strategy

Generates LONG signal when fast MA crosses above slow MA
Generates SHORT signal when fast MA crosses below slow MA
"""
from typing import List, Tuple
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal


class MACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy

    Parameters:
        fast_period (int): Period for fast moving average (default: 20)
        slow_period (int): Period for slow moving average (default: 50)
        atr_period (int): Period for ATR calculation (default: 14)
        sl_atr_mult (float): Stop loss as multiple of ATR (default: 2.0)
        tp_atr_mult (float): Take profit as multiple of ATR (default: 3.0)
    """

    def __init__(self, params: dict = None):
        """Initialize MA Crossover strategy with parameters"""
        default_params = {
            "fast_period": 20,
            "slow_period": 50,
            "atr_period": 14,
            "sl_atr_mult": 2.0,
            "tp_atr_mult": 3.0
        }

        # Merge provided params with defaults
        if params:
            default_params.update(params)

        super().__init__(name="MA_Crossover", params=default_params)

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to dataframe

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()

        # Calculate Moving Averages
        fast_period = self.get_param("fast_period")
        slow_period = self.get_param("slow_period")
        atr_period = self.get_param("atr_period")

        df["MA_Fast"] = df["Close"].rolling(window=fast_period).mean()
        df["MA_Slow"] = df["Close"].rolling(window=slow_period).mean()

        # Calculate ATR (Average True Range)
        df["TR"] = np.maximum(
            df["High"] - df["Low"],
            np.maximum(
                abs(df["High"] - df["Close"].shift(1)),
                abs(df["Low"] - df["Close"].shift(1))
            )
        )
        df["ATR"] = df["TR"].rolling(window=atr_period).mean()

        # Detect crossovers
        df["MA_Diff"] = df["MA_Fast"] - df["MA_Slow"]
        df["MA_Diff_Prev"] = df["MA_Diff"].shift(1)

        # Bullish crossover: fast MA crosses above slow MA
        df["Bullish_Cross"] = (df["MA_Diff"] > 0) & (df["MA_Diff_Prev"] <= 0)

        # Bearish crossover: fast MA crosses below slow MA
        df["Bearish_Cross"] = (df["MA_Diff"] < 0) & (df["MA_Diff_Prev"] >= 0)

        return df

    def generate_signals(self, df: pd.DataFrame, pair: str) -> List[Signal]:
        """
        Generate trading signals based on MA crossovers

        Args:
            df: DataFrame with OHLCV data
            pair: Trading pair symbol

        Returns:
            List of Signal objects
        """
        # Validate input
        self.validate_dataframe(df)

        # Calculate indicators
        df = self._calculate_indicators(df)

        signals = []

        # Iterate through dataframe to find crossovers
        for i in range(len(df)):
            row = df.iloc[i]

            # Skip if indicators not yet calculated
            if pd.isna(row["MA_Fast"]) or pd.isna(row["MA_Slow"]) or pd.isna(row["ATR"]):
                continue

            # Bullish crossover - LONG signal
            if row["Bullish_Cross"]:
                tp, sl = self.calculate_tp_sl(df, row["Close"], "LONG", i)
                signal = Signal(
                    pair=pair,
                    direction="LONG",
                    entry_time=df.index[i],
                    entry_price=row["Close"],
                    tp_price=tp,
                    sl_price=sl,
                    strategy_name=self.name
                )
                signals.append(signal)

            # Bearish crossover - SHORT signal
            elif row["Bearish_Cross"]:
                tp, sl = self.calculate_tp_sl(df, row["Close"], "SHORT", i)
                signal = Signal(
                    pair=pair,
                    direction="SHORT",
                    entry_time=df.index[i],
                    entry_price=row["Close"],
                    tp_price=tp,
                    sl_price=sl,
                    strategy_name=self.name
                )
                signals.append(signal)

        return signals

    def calculate_tp_sl(
        self,
        df: pd.DataFrame,
        entry_price: float,
        direction: str,
        entry_index: int
    ) -> Tuple[float, float]:
        """
        Calculate TP/SL based on ATR multiples

        Args:
            df: DataFrame with OHLCV data (must have ATR calculated)
            entry_price: Entry price
            direction: "LONG" or "SHORT"
            entry_index: Index in dataframe where entry occurs

        Returns:
            Tuple of (tp_price, sl_price)
        """
        atr = df.iloc[entry_index]["ATR"]
        sl_mult = self.get_param("sl_atr_mult")
        tp_mult = self.get_param("tp_atr_mult")

        if direction == "LONG":
            sl_price = entry_price - (atr * sl_mult)
            tp_price = entry_price + (atr * tp_mult)
        else:  # SHORT
            sl_price = entry_price + (atr * sl_mult)
            tp_price = entry_price - (atr * tp_mult)

        return tp_price, sl_price


if __name__ == "__main__":
    # Test the strategy
    from utils.data_loader import DataLoader, get_forex_pair

    # Load data
    loader = DataLoader()
    eurusd = get_forex_pair("EUR", "USD")
    df = loader.fetch_data(eurusd, timeframe="1h", days_back=30)

    # Create strategy
    strategy = MACrossoverStrategy(params={
        "fast_period": 20,
        "slow_period": 50
    })

    # Generate signals
    signals = strategy.generate_signals(df, eurusd)

    print(f"\n{strategy}")
    print(f"Generated {len(signals)} signals for {eurusd}")
    print(f"\nFirst 5 signals:")
    for signal in signals[:5]:
        print(f"{signal.entry_time} - {signal.direction} @ {signal.entry_price:.5f} "
              f"(TP: {signal.tp_price:.5f}, SL: {signal.sl_price:.5f})")
