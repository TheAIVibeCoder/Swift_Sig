import pandas as pd
import numpy as np
import datetime

# --- CONFIGURATION ---
CONFIG = {
    'LOOKBACK_DAYS': 14,
    'ZONE_ATR_MULT': 0.15,
    'CLUSTER_ATR_MULT': 0.25,
    'RISK_REWARD': 2.0,
    'MAX_DRAWDOWN': 350.0,
    'LOT_SIZE': 0.10,
    'FILE_M5': 'XAUUSD5 (1).csv',
    'FILE_H1': 'XAUUSD30.csv',
    'INITIAL_CAPITAL': 10000.0,
    'RISK_PER_TRADE_PCT': 1.0  # Risk 1% of capital per trade
}

def calculate_metrics(trades_df, equity_curve):
    """Calculate comprehensive performance metrics"""
    if len(trades_df) == 0:
        return {}

    metrics = {}

    # Basic metrics
    metrics['Total Trades'] = len(trades_df)
    metrics['Winning Trades'] = len(trades_df[trades_df['PnL'] > 0])
    metrics['Losing Trades'] = len(trades_df[trades_df['PnL'] < 0])
    metrics['Win Rate (%)'] = (metrics['Winning Trades'] / metrics['Total Trades'] * 100) if metrics['Total Trades'] > 0 else 0

    # PnL metrics
    metrics['Total PnL ($)'] = trades_df['PnL'].sum()
    metrics['Average Win ($)'] = trades_df[trades_df['PnL'] > 0]['PnL'].mean() if metrics['Winning Trades'] > 0 else 0
    metrics['Average Loss ($)'] = trades_df[trades_df['PnL'] < 0]['PnL'].mean() if metrics['Losing Trades'] > 0 else 0
    metrics['Largest Win ($)'] = trades_df['PnL'].max()
    metrics['Largest Loss ($)'] = trades_df['PnL'].min()

    # Risk metrics
    if metrics['Average Loss ($)'] != 0:
        metrics['Profit Factor'] = abs(metrics['Average Win ($)'] * metrics['Winning Trades'] /
                                       (metrics['Average Loss ($)'] * metrics['Losing Trades']))
    else:
        metrics['Profit Factor'] = 0

    # Drawdown
    equity_curve['Peak'] = equity_curve['Equity'].cummax()
    equity_curve['Drawdown'] = equity_curve['Equity'] - equity_curve['Peak']
    metrics['Max Drawdown ($)'] = equity_curve['Drawdown'].min()
    metrics['Max Drawdown (%)'] = (metrics['Max Drawdown ($)'] / CONFIG['INITIAL_CAPITAL'] * 100)

    # Returns
    final_equity = equity_curve['Equity'].iloc[-1]
    initial_equity = CONFIG['INITIAL_CAPITAL']
    metrics['Total Return (%)'] = ((final_equity - initial_equity) / initial_equity * 100)

    # Sharpe Ratio (simplified - using daily returns)
    daily_returns = equity_curve.set_index('Time')['Equity'].resample('D').last().pct_change().dropna()
    if len(daily_returns) > 1:
        metrics['Sharpe Ratio'] = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
    else:
        metrics['Sharpe Ratio'] = 0

    return metrics

def run_backtest(config=None, start_date=None, end_date=None):
    """
    Run backtest with optional custom config and date filtering
    Returns: (trades_df, equity_curve_df, metrics_dict, levels_history)
    """
    if config is None:
        config = CONFIG.copy()
    else:
        config = {**CONFIG, **config}

    # 1. Load Data
    print("Loading data...")
    cols = ['Time', 'Open', 'High', 'Low', 'Close', 'Vol']

    # Load M5
    m5 = pd.read_csv(config['FILE_M5'], sep='\t', names=cols, parse_dates=['Time'])

    # Load and Resample M30 to H1
    m30 = pd.read_csv(config['FILE_H1'], sep='\t', names=cols, parse_dates=['Time'])
    m30.set_index('Time', inplace=True)
    h1 = m30.resample('1H').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
    }).dropna().reset_index()

    # Apply date filters if provided
    if start_date:
        m5 = m5[m5['Time'] >= pd.to_datetime(start_date)]
        h1 = h1[h1['Time'] >= pd.to_datetime(start_date)]
    if end_date:
        m5 = m5[m5['Time'] <= pd.to_datetime(end_date)]
        h1 = h1[h1['Time'] <= pd.to_datetime(end_date)]

    # 2. Indicators
    # H1 ATR & EMAs
    h1['ATR'] = (h1['High'] - h1['Low']).rolling(14).mean()
    h1['EMA50'] = h1['Close'].ewm(span=50).mean()
    h1['EMA200'] = h1['Close'].ewm(span=200).mean()

    # H1 Structure (Fractals)
    h1['is_swing_high'] = ((h1['High'] > h1['High'].shift(1)) &
                           (h1['High'] > h1['High'].shift(-1))).shift(1).fillna(False)
    h1['is_swing_low'] = ((h1['Low'] < h1['Low'].shift(1)) &
                          (h1['Low'] < h1['Low'].shift(-1))).shift(1).fillna(False)

    # M5 Rejections
    m5['ATR'] = (m5['High'] - m5['Low']).rolling(14).mean()
    rng = m5['High'] - m5['Low']
    body = abs(m5['Close'] - m5['Open'])
    upper_wick = m5['High'] - m5[['Open', 'Close']].max(axis=1)
    lower_wick = m5[['Open', 'Close']].min(axis=1) - m5['Low']

    m5['is_bear_reject'] = (upper_wick > 0.55 * rng) & (body < 0.35 * rng)
    m5['is_bull_reject'] = (lower_wick > 0.55 * rng) & (body < 0.35 * rng)

    # 3. Simulation Loop
    equity = config['INITIAL_CAPITAL']
    watermark = config['INITIAL_CAPITAL']
    trades = []
    open_trades = []
    equity_curve = []
    levels_history = []
    active_levels = []
    last_update_hour = -1

    print(f"Starting simulation on {len(m5)} M5 bars...")

    # Iterate M5
    for i, row in m5.iterrows():
        curr_time = row['Time']
        curr_price = row['Close']

        # Update equity curve
        equity_curve.append({'Time': curr_time, 'Equity': equity})

        # Check open trades for SL/TP hits
        for trade in open_trades[:]:
            hit_sl = False
            hit_tp = False

            if trade['Type'] == 'BUY':
                if row['Low'] <= trade['SL']:
                    hit_sl = True
                    exit_price = trade['SL']
                elif row['High'] >= trade['TP']:
                    hit_tp = True
                    exit_price = trade['TP']
            else:  # SELL
                if row['High'] >= trade['SL']:
                    hit_sl = True
                    exit_price = trade['SL']
                elif row['Low'] <= trade['TP']:
                    hit_tp = True
                    exit_price = trade['TP']

            if hit_sl or hit_tp:
                # Calculate PnL
                if trade['Type'] == 'BUY':
                    pnl = (exit_price - trade['Entry']) * trade['Position_Size']
                else:
                    pnl = (trade['Entry'] - exit_price) * trade['Position_Size']

                trade['Exit'] = exit_price
                trade['Exit_Time'] = curr_time
                trade['PnL'] = pnl
                trade['Outcome'] = 'TP' if hit_tp else 'SL'

                equity += pnl
                watermark = max(watermark, equity)
                trades.append(trade)
                open_trades.remove(trade)

        # Hard Stop
        if (watermark - equity) > config['MAX_DRAWDOWN']:
            continue

        # A. Update Levels (Hourly)
        if curr_time.hour != last_update_hour:
            last_update_hour = curr_time.hour

            # Get H1 history
            start_hist = curr_time - datetime.timedelta(days=config['LOOKBACK_DAYS'])
            hist = h1[(h1['Time'] >= start_hist) & (h1['Time'] < curr_time)]

            if len(hist) > 20:
                current_h1_atr = hist['ATR'].iloc[-1]

                # Collect levels
                candidates = hist[hist['is_swing_high']]['High'].tolist() + \
                             hist[hist['is_swing_low']]['Low'].tolist()
                candidates.sort()

                # Cluster
                active_levels = []
                if candidates:
                    cluster = [candidates[0]]
                    for price in candidates[1:]:
                        if price - cluster[-1] < (config['CLUSTER_ATR_MULT'] * current_h1_atr):
                            cluster.append(price)
                        else:
                            active_levels.append(np.mean(cluster))
                            cluster = [price]
                    active_levels.append(np.mean(cluster))

                    # Keep Top 6
                    active_levels = active_levels[-6:]

                levels_history.append({
                    'Time': curr_time,
                    'Levels': active_levels.copy(),
                    'ATR': current_h1_atr
                })

        # B. Check Window (9:00-13:30, 15:00-20:30)
        t_float = curr_time.hour + curr_time.minute/60.0
        in_window = (9 <= t_float <= 13.5) or (15 <= t_float <= 20.5)

        if in_window and active_levels and len(open_trades) < 3:  # Max 3 concurrent trades
            zone_w = config['ZONE_ATR_MULT'] * row['ATR']

            # Check Signals
            for lvl in active_levels:
                # Sell Logic
                if row['is_bear_reject'] and (lvl - zone_w < row['High'] < lvl + zone_w):
                    if row['Close'] < (row['High'] + row['Low'])/2:
                        sl = lvl + zone_w + (0.2 * row['ATR'])
                        tp = row['Close'] - config['RISK_REWARD'] * (sl - row['Close'])

                        # Position sizing based on risk
                        risk_amount = equity * (config['RISK_PER_TRADE_PCT'] / 100)
                        position_size = risk_amount / abs(sl - row['Close'])

                        open_trades.append({
                            'Type': 'SELL',
                            'Entry': row['Close'],
                            'SL': sl,
                            'TP': tp,
                            'Time': curr_time,
                            'Position_Size': position_size,
                            'Level': lvl
                        })
                        break

                # Buy Logic
                elif row['is_bull_reject'] and (lvl - zone_w < row['Low'] < lvl + zone_w):
                    if row['Close'] > (row['High'] + row['Low'])/2:
                        sl = lvl - zone_w - (0.2 * row['ATR'])
                        tp = row['Close'] + config['RISK_REWARD'] * (row['Close'] - sl)

                        # Position sizing
                        risk_amount = equity * (config['RISK_PER_TRADE_PCT'] / 100)
                        position_size = risk_amount / abs(row['Close'] - sl)

                        open_trades.append({
                            'Type': 'BUY',
                            'Entry': row['Close'],
                            'SL': sl,
                            'TP': tp,
                            'Time': curr_time,
                            'Position_Size': position_size,
                            'Level': lvl
                        })
                        break

    # Close any remaining open trades at final price
    for trade in open_trades:
        final_price = m5.iloc[-1]['Close']
        if trade['Type'] == 'BUY':
            pnl = (final_price - trade['Entry']) * trade['Position_Size']
        else:
            pnl = (trade['Entry'] - final_price) * trade['Position_Size']

        trade['Exit'] = final_price
        trade['Exit_Time'] = m5.iloc[-1]['Time']
        trade['PnL'] = pnl
        trade['Outcome'] = 'OPEN'
        trades.append(trade)

    print(f"Total Trades Executed: {len(trades)}")

    # Convert to DataFrames
    trades_df = pd.DataFrame(trades)
    equity_curve_df = pd.DataFrame(equity_curve)

    # Calculate metrics
    metrics = calculate_metrics(trades_df, equity_curve_df.copy())

    return trades_df, equity_curve_df, metrics, m5, h1

if __name__ == "__main__":
    trades_df, equity_df, metrics, m5, h1 = run_backtest()
    print("\n=== BACKTEST RESULTS ===")
    for key, value in metrics.items():
        print(f"{key}: {value:.2f}")
