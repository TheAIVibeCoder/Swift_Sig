"""
Flask web application for SwiftSig backtesting
"""
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import os
import json
from data_fetcher import DataFetcher
from strategies.ma_crossover import MACrossoverStrategy
from backtest import BacktestEngine

app = Flask(__name__)

# Store last results in memory for quick access
last_results = None


@app.route('/')
def index():
    """Main page with backtest form"""
    return render_template('index.html')


@app.route('/run-backtest', methods=['POST'])
def run_backtest():
    """Run backtest with user parameters"""
    global last_results

    try:
        # Get form data
        pair = request.form.get('pair', 'EURUSD=X').upper()
        timeframe = request.form.get('timeframe', '1h')
        days_back = int(request.form.get('days_back', 90))
        fast_period = int(request.form.get('fast_period', 50))
        slow_period = int(request.form.get('slow_period', 200))

        # Validate pair format
        if len(pair) == 6 and pair.isalpha():
            # Convert EURUSD to EURUSD=X
            pair = f"{pair}=X"

        # Fetch data
        fetcher = DataFetcher()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        df = fetcher.fetch_ohlcv(
            pair=pair,
            interval=timeframe,
            start_date=start_date,
            end_date=end_date
        )

        # Create strategy
        strategy = MACrossoverStrategy(fast_period=fast_period, slow_period=slow_period)

        # Determine pip value
        pip_value = 0.01 if "JPY" in pair else 0.0001

        # Run backtest
        engine = BacktestEngine(strategy=strategy, initial_capital=10000.0)
        results = engine.run(df=df, pair=pair, pip_value=pip_value, lot_size=1.0)

        # Export results
        file_paths = engine.export_results(results, format="both")

        # Store results
        last_results = results

        # Prepare response data
        metrics = results['metrics']

        # Get sample trades (first 10)
        trades_data = []
        if not results['trades'].empty:
            trades_df = results['trades'].head(10)
            trades_data = trades_df.to_dict('records')

        response = {
            'success': True,
            'pair': results['pair'],
            'strategy': results['strategy'],
            'period': results['period'],
            'metrics': metrics,
            'sample_trades': trades_data,
            'total_trades_count': len(results['trades']) if not results['trades'].empty else 0,
            'files': file_paths
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/download/<file_type>')
def download_results(file_type):
    """Download CSV or JSON results"""
    if last_results is None:
        return "No results available", 404

    engine = BacktestEngine(strategy=None, initial_capital=10000.0)
    file_paths = engine.export_results(last_results, format=file_type)

    if file_type == 'csv' and 'trades_csv' in file_paths:
        return send_file(file_paths['trades_csv'], as_attachment=True)
    elif file_type == 'json' and 'results_json' in file_paths:
        return send_file(file_paths['results_json'], as_attachment=True)

    return "File not found", 404


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # Create backtests directory
    os.makedirs('backtests', exist_ok=True)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
