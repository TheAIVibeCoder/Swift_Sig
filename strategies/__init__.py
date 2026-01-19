"""Trading strategy modules"""
from .base_strategy import BaseStrategy, Signal, TradeResult
from .ma_crossover import MACrossoverStrategy

__all__ = ["BaseStrategy", "Signal", "TradeResult", "MACrossoverStrategy"]
