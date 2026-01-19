"""
Backtesting Engine for Trading Strategies
"""
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import json
import os
from strategies.base_strategy import BaseStrategy, Signal, TradeResult


class BacktestEngine:
    """
    Backtesting engine that simulates strategy execution on historical data

    Features:
    - Realistic trade execution (checks high/low for TP/SL hits)
    - Comprehensive performance metrics
    - Trade-by-trade results tracking
    - Export to CSV/JSON
    """

    def __init__(self, strategy: BaseStrategy, initial_capital: float = 10000.0):
        """
        Initialize backtesting engine

        Args:
            strategy: Trading strategy to backtest
            initial_capital: Starting capital for simulation
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.trades: List[TradeResult] = []
        self.equity_curve: List[Dict] = []

    def run(
        self,
        df: pd.DataFrame,
        pair: str,
        pip_value: float = 0.0001,
        lot_size: float = 1.0
    ) -> Dict:
        """
        Run backtest on historical data

        Args:
            df: DataFrame with OHLCV data (timezone-aware index required)
            pair: Trading pair symbol
            pip_value: Value of one pip (0.0001 for most forex, 0.01 for JPY pairs)
            lot_size: Position size multiplier

        Returns:
            Dictionary with trade results, equity curve, and metrics
        """
        # Validate input
        self.strategy.validate_dataframe(df)

        # Generate all signals from the strategy
        print(f"Generating signals for {pair} using {self.strategy.name}...")
        signals = self.strategy.generate_signals(df, pair)
        print(f"Generated {len(signals)} signals")

        if not signals:
            print("No signals generated. Backtest complete.")
            return self._compile_results(df, pair)

        # Reset state
        self.trades = []
        self.equity_curve = []
        equity = self.initial_capital

        print(f"Simulating trades...")

        # Process each signal
        for signal in signals:
            # Find the entry point in dataframe
            entry_idx = df.index.get_indexer([signal.entry_time], method='nearest')[0]

            if entry_idx == -1 or entry_idx >= len(df) - 1:
                continue

            # Simulate trade execution from entry point forward
            trade_result = self._simulate_trade(
                df=df,
                signal=signal,
                entry_idx=entry_idx,
                pip_value=pip_value,
                lot_size=lot_size
            )

            if trade_result:
                self.trades.append(trade_result)

                # Update equity
                equity += trade_result.pips * pip_value * lot_size * 100000  # Standard lot
                self.equity_curve.append({
                    "time": trade_result.exit_time,
                    "equity": equity,
                    "trade_pips": trade_result.pips
                })

        print(f"Completed simulation: {len(self.trades)} trades executed")

        # Compile and return results
        return self._compile_results(df, pair)

    def _simulate_trade(
        self,
        df: pd.DataFrame,
        signal: Signal,
        entry_idx: int,
        pip_value: float,
        lot_size: float
    ) -> Optional[TradeResult]:
        """
        Simulate a single trade from entry to exit

        Args:
            df: Price data
            signal: Trade signal
            entry_idx: Index where trade enters
            pip_value: Pip value for calculation
            lot_size: Position size

        Returns:
            TradeResult if trade completed, None otherwise
        """
        entry_price = signal.entry_price
        tp_price = signal.tp_price
        sl_price = signal.sl_price
        direction = signal.direction

        # Scan forward from entry to find TP or SL hit
        for i in range(entry_idx + 1, len(df)):
            bar = df.iloc[i]
            bar_time = df.index[i]

            # Check for TP/SL hits based on direction
            if direction == "LONG":
                # Check stop loss first (conservative approach)
                if bar["Low"] <= sl_price:
                    # SL hit - LOSS
                    exit_price = sl_price
                    pips = (exit_price - entry_price) / pip_value
                    status = "LOSS"
                    exit_time = bar_time
                    break

                # Check take profit
                elif bar["High"] >= tp_price:
                    # TP hit - WIN
                    exit_price = tp_price
                    pips = (exit_price - entry_price) / pip_value
                    status = "WIN"
                    exit_time = bar_time
                    break

            else:  # SHORT
                # Check stop loss first
                if bar["High"] >= sl_price:
                    # SL hit - LOSS
                    exit_price = sl_price
                    pips = (entry_price - exit_price) / pip_value
                    status = "LOSS"
                    exit_time = bar_time
                    break

                # Check take profit
                elif bar["Low"] <= tp_price:
                    # TP hit - WIN
                    exit_price = tp_price
                    pips = (entry_price - exit_price) / pip_value
                    status = "WIN"
                    exit_time = bar_time
                    break
        else:
            # Trade didn't close - use last available price
            exit_price = df.iloc[-1]["Close"]
            exit_time = df.index[-1]

            if direction == "LONG":
                pips = (exit_price - entry_price) / pip_value
            else:
                pips = (entry_price - exit_price) / pip_value

            # Determine status
            if abs(pips) < 1:
                status = "BREAK_EVEN"
            elif pips > 0:
                status = "WIN"
            else:
                status = "LOSS"

        # Create trade result
        return TradeResult(
            pair=signal.pair,
            entry_time=signal.entry_time,
            exit_time=exit_time,
            direction=direction,
            strategy_name=signal.strategy_name,
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            exit_price=exit_price,
            status=status,
            pips=pips
        )

    def _compile_results(self, df: pd.DataFrame, pair: str) -> Dict:
        """
        Compile backtest results with metrics

        Args:
            df: Original price data
            pair: Trading pair

        Returns:
            Dictionary with trades, equity curve, and metrics
        """
        # Convert trades to dataframe
        if self.trades:
            trades_df = pd.DataFrame([t.to_dict() for t in self.trades])
        else:
            trades_df = pd.DataFrame()

        # Calculate metrics
        metrics = self._calculate_metrics(trades_df)

        return {
            "pair": pair,
            "strategy": self.strategy.name,
            "period": {
                "start": df.index[0].isoformat(),
                "end": df.index[-1].isoformat(),
                "bars": len(df)
            },
            "trades": trades_df,
            "equity_curve": pd.DataFrame(self.equity_curve) if self.equity_curve else pd.DataFrame(),
            "metrics": metrics
        }

    def _calculate_metrics(self, trades_df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive performance metrics

        Args:
            trades_df: DataFrame of trade results

        Returns:
            Dictionary of performance metrics
        """
        if trades_df.empty:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_wins": 0,
                "total_losses": 0,
                "total_pips": 0.0,
                "avg_winning_pips": 0.0,
                "avg_losing_pips": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pips": 0.0,
                "sharpe_ratio": 0.0
            }

        # Basic metrics
        total_trades = len(trades_df)
        wins = trades_df[trades_df["status"] == "WIN"]
        losses = trades_df[trades_df["status"] == "LOSS"]

        total_wins = len(wins)
        total_losses = len(losses)
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0

        # Pip metrics
        total_pips = trades_df["pips"].sum()
        avg_winning_pips = wins["pips"].mean() if not wins.empty else 0.0
        avg_losing_pips = losses["pips"].mean() if not losses.empty else 0.0

        # Profit factor
        gross_profit = wins["pips"].sum() if not wins.empty else 0.0
        gross_loss = abs(losses["pips"].sum()) if not losses.empty else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0

        # Drawdown
        cumulative_pips = trades_df["pips"].cumsum()
        running_max = cumulative_pips.cummax()
        drawdown = cumulative_pips - running_max
        max_drawdown_pips = abs(drawdown.min()) if not drawdown.empty else 0.0

        # Sharpe ratio (simplified)
        if len(trades_df) > 1:
            returns = trades_df["pips"]
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(len(returns)) if returns.std() > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        return {
            "total_trades": int(total_trades),
            "win_rate": float(win_rate),
            "total_wins": int(total_wins),
            "total_losses": int(total_losses),
            "total_pips": float(total_pips),
            "avg_winning_pips": float(avg_winning_pips),
            "avg_losing_pips": float(avg_losing_pips),
            "profit_factor": float(profit_factor),
            "max_drawdown_pips": float(max_drawdown_pips),
            "sharpe_ratio": float(sharpe_ratio)
        }

    def export_results(
        self,
        results: Dict,
        output_dir: str = "backtests",
        format: str = "both"
    ) -> Dict[str, str]:
        """
        Export backtest results to file

        Args:
            results: Results dictionary from run()
            output_dir: Directory to save results
            format: "csv", "json", or "both"

        Returns:
            Dictionary with file paths
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pair = results["pair"].replace("=X", "").replace("-", "")
        strategy = results["strategy"]
        base_filename = f"{pair}_{strategy}_{timestamp}"

        file_paths = {}

        # Export trades to CSV
        if format in ["csv", "both"]:
            csv_path = os.path.join(output_dir, f"{base_filename}_trades.csv")
            if not results["trades"].empty:
                results["trades"].to_csv(csv_path, index=False)
                file_paths["trades_csv"] = csv_path
                print(f"Trades exported to: {csv_path}")

        # Export full results to JSON
        if format in ["json", "both"]:
            json_path = os.path.join(output_dir, f"{base_filename}_results.json")

            # Prepare JSON-serializable results
            json_results = {
                "pair": results["pair"],
                "strategy": results["strategy"],
                "period": results["period"],
                "metrics": results["metrics"],
                "trades": results["trades"].to_dict(orient="records") if not results["trades"].empty else []
            }

            with open(json_path, "w") as f:
                json.dump(json_results, f, indent=2, default=str)

            file_paths["results_json"] = json_path
            print(f"Results exported to: {json_path}")

        return file_paths

    def print_summary(self, results: Dict):
        """
        Print backtest summary to console

        Args:
            results: Results dictionary from run()
        """
        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {results['pair']}")
        print("="*60)
        print(f"Strategy: {results['strategy']}")
        print(f"Period: {results['period']['start'][:10]} to {results['period']['end'][:10]}")
        print(f"Bars: {results['period']['bars']}")
        print("-"*60)

        metrics = results['metrics']
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.2f}%")
        print(f"Total Wins: {metrics['total_wins']}")
        print(f"Total Losses: {metrics['total_losses']}")
        print("-"*60)
        print(f"Total Pips: {metrics['total_pips']:.2f}")
        print(f"Avg Winning Pips: {metrics['avg_winning_pips']:.2f}")
        print(f"Avg Losing Pips: {metrics['avg_losing_pips']:.2f}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"Max Drawdown: {metrics['max_drawdown_pips']:.2f} pips")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print("="*60 + "\n")
