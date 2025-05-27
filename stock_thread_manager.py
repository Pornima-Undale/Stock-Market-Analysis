import sys
import requests
import yfinance as yf
import traceback
import time
from datetime import datetime
from PyQt6.QtCore import (QObject, QRunnable, QThreadPool,
                          pyqtSignal, pyqtSlot, Qt)
from PyQt6.QtWidgets import QMessageBox


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    result = pyqtSignal(object)
    error = pyqtSignal(tuple)
    finished = pyqtSignal(bool)


class StockFetchWorker(QRunnable):
    """
    Worker thread for fetching stock data asynchronously
    """

    def __init__(self, symbol, fetch_method='yahoo', max_retries=2):
        super().__init__()
        self.symbol = symbol
        self.fetch_method = fetch_method
        self.max_retries = max_retries
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # Choose fetch method
                if self.fetch_method == 'yahoo':
                    stock_data = self.fetch_yahoo_data()
                else:
                    stock_data = self.fetch_alternative_data()

                # Emit the result and break the retry loop
                self.signals.result.emit(stock_data)
                self.signals.finished.emit(True)
                return

            except Exception as e:
                retry_count += 1
                print(f"Error fetching {self.symbol}, attempt {retry_count}/{self.max_retries}: {str(e)}")

                if retry_count > self.max_retries:
                    # If all retries failed, emit error
                    error_tuple = (str(e), traceback.format_exc())
                    self.signals.error.emit(error_tuple)
                    self.signals.finished.emit(False)
                else:
                    # Wait before retrying - increase backoff time with each retry
                    time.sleep(1 * retry_count)

    def fetch_yahoo_data(self):
        """
        Fetch stock data from Yahoo Finance with improved open price handling
        """
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.symbol}?interval=1d&range=2d"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            meta = result['meta']
            quote = result['indicators']['quote'][0]

            # Extract and process stock data
            current_price = meta.get('regularMarketPrice', 0)
            prev_close = meta.get('chartPreviousClose', 0)

            # Get open price with aggressive fallback logic
            open_price = meta.get('regularMarketOpen', 0)

            # Try multiple fallback options for open price
            if open_price == 0 or open_price is None:
                # Try to get from quote data
                if 'open' in quote and len(quote['open']) > 0:
                    valid_opens = [o for o in quote['open'] if o is not None and o > 0]
                    if valid_opens:
                        open_price = valid_opens[-1]  # Use the most recent valid open

                # If still zero, try previous close
                if open_price == 0 or open_price is None:
                    open_price = prev_close

                # If still zero, use current price
                if open_price == 0 or open_price is None:
                    open_price = current_price

            # Ensure we always have a valid open price
            if open_price == 0 or open_price is None:
                open_price = current_price  # Final fallback

            # Print debug info for troubleshooting
            print(f"Symbol: {self.symbol}, Open: {open_price}, Current: {current_price}")

            return {
                'symbol': self.symbol,
                'current_price': current_price,
                'prev_close': prev_close,
                'price_change': current_price - prev_close,
                'percent_change': (current_price - prev_close) * 100 / prev_close if prev_close else 0,
                'open': open_price,  # Enhanced open price with fallbacks
                'high': meta.get('regularMarketDayHigh', current_price),
                'low': meta.get('regularMarketDayLow', current_price),
                'volume': meta.get('regularMarketVolume', 0)
            }

        raise ValueError(f"No data available for {self.symbol}")

    def fetch_alternative_data(self):
        """
        Alternative method to fetch stock data using yfinance as a backup
        """
        stock = yf.Ticker(self.symbol)
        history = stock.history(period="2d")

        if not history.empty:
            # Get today's data
            if len(history) > 1:
                today_data = history.iloc[-1]
                yesterday_data = history.iloc[-2]

                return {
                    'symbol': self.symbol,
                    'current_price': today_data['Close'],
                    'prev_close': yesterday_data['Close'],
                    'price_change': today_data['Close'] - yesterday_data['Close'],
                    'percent_change': ((today_data['Close'] - yesterday_data['Close']) / yesterday_data['Close']) * 100,
                    'open': today_data['Open'],
                    'high': today_data['High'],
                    'low': today_data['Low'],
                    'volume': today_data['Volume']
                }
            else:
                # Only have one day of data
                current_row = history.iloc[-1]
                return {
                    'symbol': self.symbol,
                    'current_price': current_row['Close'],
                    'prev_close': current_row['Open'],
                    'price_change': current_row['Close'] - current_row['Open'],
                    'percent_change': ((current_row['Close'] - current_row['Open']) / current_row['Open']) * 100,
                    'open': current_row['Open'],
                    'high': current_row['High'],
                    'low': current_row['Low'],
                    'volume': current_row['Volume']
                }

        raise ValueError(f"No data available for {self.symbol}")


class StockDataManager:
    """
    Manages stock data fetching using thread pool
    """

    def __init__(self, main_window=None):
        self.main_window = main_window
        self.threadpool = QThreadPool()

        # Increase thread count for better performance
        self.threadpool.setMaxThreadCount(10)
        print(f"Maximum thread count: {self.threadpool.maxThreadCount()}")

    def fetch_stock_data(self, symbol, update_callback=None, error_callback=None):
        """
        Fetch stock data asynchronously
        """
        worker = StockFetchWorker(symbol)

        if update_callback:
            worker.signals.result.connect(update_callback)

        if error_callback:
            worker.signals.error.connect(error_callback)
        else:
            worker.signals.error.connect(self.handle_worker_error)

        self.threadpool.start(worker)

    def fetch_multiple_stocks(self, symbols, update_callback=None, error_callback=None):
        """
        Fetch multiple stock data with improved batching
        """
        batch_size = 3  # Reduced from 5 to 3

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]

            for symbol in batch:
                worker = StockFetchWorker(symbol)

                if update_callback:
                    worker.signals.result.connect(update_callback)

                if error_callback:
                    worker.signals.error.connect(error_callback)
                else:
                    worker.signals.error.connect(self.handle_worker_error)

                self.threadpool.start(worker)

            # Add a larger delay between batches to prevent API rate limiting
            if i + batch_size < len(symbols):
                from PyQt6.QtCore import QTimer
                timer = QTimer()
                timer.singleShot(3000, lambda: None)  # Increased from 2000 to 3000

    def handle_worker_error(self, error_tuple):
        """
        Default error handler for worker threads
        """
        error_msg, traceback_str = error_tuple
        print(f"Stock Fetch Error: {error_msg}")
        print(f"Traceback: {traceback_str}")

        if self.main_window:
            QMessageBox.warning(
                self.main_window,
                "Stock Fetch Error",
                f"Could not fetch stock data: {error_msg}"
            )