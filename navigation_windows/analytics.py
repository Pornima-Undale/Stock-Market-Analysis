import yfinance as yf
import traceback
import talib
import requests
import pandas as pd
import numpy as np
import talib
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFrame, QLineEdit)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import pyqtSignal, QTimer
import sys
from database import DatabaseConnection
from navigation_windows import BaseNavigationWindow

class AnalyticsWindow(BaseNavigationWindow):
    switch_to_dashboard = pyqtSignal()

    def __init__(self, title="analytics", user_id=None):
        super().__init__(title, user_id)
        self.setWindowTitle('Stock Technical Analysis')
        self.setGeometry(0, 0, 1400, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #041E42;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            QPushButton#refreshButton {
                min-width: 180px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QPushButton.remove-btn {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: center;
                border-radius: 3px;
            }
            QPushButton.remove-btn:hover {
                background-color: #c82333;
            }
        """)

        # Initialize stocks list and API key
        #self.stocks_list = []
        #self.alpha_vantage_api_key = "HZMCF6BX3B6RURL3"  # Replace with your API key

        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel('Stock Technical Analysis')
        title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        title.setStyleSheet('color: #041E42;')
        header_layout.addWidget(title)

        back_button = QPushButton('Back to Dashboard')
        back_button.clicked.connect(self.switch_to_dashboard_slot)
        header_layout.addStretch()
        header_layout.addWidget(back_button)

        main_layout.addWidget(header_container)

        # Input section
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #ddd; padding: 10px;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 5, 10, 15)

        # Symbol input
        symbol_label = QLabel('Symbol:')
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText('Enter Stock Symbol (e.g., INFY, TCS)')
        self.stock_input.setFixedWidth(250)

        # API Key input
        '''api_key_label = QLabel('API Key:')
        self.api_key_input = QLineEdit(self.alpha_vantage_api_key)
        self.api_key_input.setFixedWidth(250)'''

        # Add to input layout
        input_layout.addWidget(symbol_label)
        input_layout.addWidget(self.stock_input)
        #input_layout.addWidget(api_key_label)
        #input_layout.addWidget(self.api_key_input)
        input_layout.addStretch()

        main_layout.addWidget(input_container)

        # Table section
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 10, 10, 10)


        # Create stocks table with technical indicators
        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(8)
        self.stocks_table.setColumnCount(9)
        self.stocks_table.setHorizontalHeaderLabels([
            'Symbol', 'Current Price', '5D MA', '20D MA',
            '50D MA', '100D MA', 'RSI (14)', 'ADX (14)','Signal'
        ])

        # Style the table header
        self.stocks_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)

        # Set column width behavior
        self.stocks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Add row numbers
        self.stocks_table.verticalHeader().setVisible(True)
        self.stocks_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.stocks_table.verticalHeader().setDefaultSectionSize(40)

        table_layout.addWidget(self.stocks_table)

        # Create a separate table for the remove buttons
        self.remove_buttons_table = QTableWidget()
        self.remove_buttons_table.setColumnCount(1)
        self.remove_buttons_table.setHorizontalHeaderLabels(['Remove'])
        self.remove_buttons_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        self.remove_buttons_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.remove_buttons_table.verticalHeader().setVisible(True)
        self.remove_buttons_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.remove_buttons_table.verticalHeader().setDefaultSectionSize(40)
        self.remove_buttons_table.setFixedWidth(120)

        # Create a horizontal layout to place both tables side by side
        tables_layout = QHBoxLayout()
        tables_layout.addWidget(self.stocks_table)
        tables_layout.addWidget(self.remove_buttons_table)

        # Add the tables layout to the container layout
        table_layout.addLayout(tables_layout)

        main_layout.addWidget(table_container, 1)  # Give it stretch factor

        # Bottom button section
        button_container = QWidget()
        button_container.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 5, 10, 15)
        button_layout.addStretch()

        refresh_button = QPushButton('Refresh Technical Data')
        refresh_button.setObjectName("refreshButton")
        refresh_button.clicked.connect(self.add_stock_from_input)  # First add from input
        refresh_button.clicked.connect(self.refresh_stock_data)  # Then refresh all
        button_layout.addWidget(refresh_button)

        main_layout.addWidget(button_container)

        nav_frame = self.add_bottom_navigation()
        main_layout.addWidget(nav_frame)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Set up status bar
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #041E42;
                color: white; 
                padding: 5px;
            }
        """)
        self.stocks_list = []  # Initialize the stocks list

        # Add the database setup:
        self.setup_database()
        # Then add a new method to load preferences from database:
        self.load_analytics_preferences()

    def setup_database(self):
        """Setup database connection"""
        try:
            self.db = DatabaseConnection()
            print("✅ Database connection established in Analytics")
        except NameError as e:
            print(f"❌ Database module not found: {e}")
            self.db = None
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            self.db = None

    def check_talib_installation(self):
        """Verify TA-Lib installation and functionality"""
        try:
            import talib
            import numpy as np

            # Create simple test data
            data = np.array([10.0, 11.0, 12.0, 11.0, 10.0, 11.0, 13.0, 14.0, 15.0, 16.0,
                             15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0])

            # Test a few indicators
            sma = talib.SMA(data, timeperiod=5)
            rsi = talib.RSI(data, timeperiod=14)

            # If we get here without exception, TA-Lib is working
            self.statusBar().showMessage('TA-Lib is properly installed and working', 3000)
            return True

        except ImportError:
            self.statusBar().showMessage('TA-Lib is not installed. Please install TA-Lib package.', 5000)
            return False

        except Exception as e:
            self.statusBar().showMessage(f'TA-Lib error: {str(e)}', 5000)
            return False

    def switch_to_dashboard_slot(self):
        """Emit signal to switch back to dashboard"""
        self.switch_to_dashboard.emit()
        self.hide()

    def add_stock_from_input(self):
        """Add stock from input field"""
        symbol = self.stock_input.text().strip().upper()
        if symbol:
            # Update API key if it has changed
            #self.alpha_vantage_api_key = self.api_key_input.text().strip()

            # Add .NS suffix if not present (for NSE stocks)
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            self.add_stock(symbol)
            self.stock_input.clear()

    def remove_stock(self, row):
        """Remove a stock from the table with database integration"""
        try:
            # Get the symbol
            symbol = self.stocks_table.item(row, 0).text()

            # Remove from database if available
            if hasattr(self, 'db') and self.db and self.user_id:
                # First need to find the preference_id for this symbol
                preferences = self.db.get_user_analytics_preferences(self.user_id)
                for pref in preferences:
                    if pref['stock_symbol'] == symbol:
                        self.db.remove_analytics_preference(self.user_id, pref['preference_id'])
                        break

            # Remove from stocks list - your existing code
            if symbol in self.stocks_list:
                self.stocks_list.remove(symbol)

            # Remove the rows from both tables - your existing code
            self.stocks_table.removeRow(row)
            self.remove_buttons_table.removeRow(row)

            # Show status message - your existing code
            self.statusBar().showMessage(f'{symbol} removed from analytics', 3000)
        except Exception as e:
            print(f"Error removing stock: {str(e)}")
            self.statusBar().showMessage('Error removing stock', 3000)

    def load_analytics_preferences(self):
        """Load analytics preferences from database"""
        if not hasattr(self, 'db') or self.db is None or not self.user_id:
            print("No database connection or user_id available")
            return

        try:
            # Get analytics preferences from database
            preferences = self.db.get_user_analytics_preferences(self.user_id)

            # Clear existing data
            self.stocks_list = []

            # Add each symbol to the list
            for pref in preferences:
                self.stocks_list.append(pref['stock_symbol'])

            # Add each stock to the table
            self.stocks_table.setRowCount(0)  # Clear existing rows
            for symbol in self.stocks_list:
                self.add_stock(symbol)

        except Exception as e:
            print(f"❌ Error loading analytics preferences: {e}")

    def enhanced_refresh_stock_data(self):
        """Enhanced version of refresh_stock_data with better feedback"""
        self.statusBar().showMessage('Refreshing technical data...')

        # Count total rows for progress reporting
        total_rows = self.stocks_table.rowCount()
        if total_rows == 0:
            self.statusBar().showMessage('No stocks to refresh', 3000)
            return

        success_count = 0
        error_count = 0

        for row in range(total_rows):
            try:
                symbol = self.stocks_table.item(row, 0).text()
                self.statusBar().showMessage(f'Refreshing {symbol} ({row + 1}/{total_rows})...')

                # Call our enhanced version instead
                debug_calculate_technical_indicators(self, symbol, row)
                success_count += 1

                # Add delay to avoid rate limiting
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(3000, lambda: None)  # 3 second delay between stocks

            except Exception as e:
                print(f"Error refreshing data for row {row}: {str(e)}")
                error_count += 1
                # Set placeholder values if no data returned
                for col in range(1, 8):
                    self.stocks_table.setItem(row, col, QTableWidgetItem("--"))

        if error_count > 0:
            self.statusBar().showMessage(f'Technical data updated: {success_count} succeeded, {error_count} failed',
                                         5000)
        else:
            self.statusBar().showMessage('Technical data updated successfully', 3000)

    def calculate_technical_indicators(self, symbol, row):
        try:
            # Ensure proper NSE stock format
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            self.statusBar().showMessage(f'Fetching data for {symbol}...')

            # Download stock data with explicit parameters
            stock_data = yf.download(
                symbol,
                period="1y",  # Get one year of data
                interval="1d",  # Daily data
                auto_adjust=True,  # Auto-adjust for splits
                progress=False
            )

            if stock_data.empty:
                print(f"No data available for {symbol}")
                self.statusBar().showMessage(f"No data available for {symbol}", 5000)

                # Set placeholder values
                for col in range(1, 9):
                    self.stocks_table.setItem(row, col, QTableWidgetItem("No Data"))
                return

            # Make sure we have enough data
            if len(stock_data) < 100:
                print(f"Insufficient data points for {symbol}: only {len(stock_data)} days")
                self.statusBar().showMessage(f"Insufficient history for {symbol}", 5000)

                # Still show current price but mark indicators as insufficient
                if len(stock_data) > 0:
                    current_price = stock_data['Close'].iloc[-1]
                    self.stocks_table.setItem(row, 1, QTableWidgetItem(f"₹{current_price:.2f}"))

                for col in range(2, 9):
                    self.stocks_table.setItem(row, col, QTableWidgetItem("Insuf. Data"))
                return

            # Extract price data as numpy arrays
            close_prices = stock_data['Close'].values
            high_prices = stock_data['High'].values
            low_prices = stock_data['Low'].values

            # Ensure we have 1D arrays for TA-Lib
            if len(close_prices.shape) > 1:
                close_prices = close_prices.flatten()
                high_prices = high_prices.flatten()
                low_prices = low_prices.flatten()

            # Convert to float64 and handle NaN values
            close_prices = np.array(close_prices, dtype=np.float64)
            high_prices = np.array(high_prices, dtype=np.float64)
            low_prices = np.array(low_prices, dtype=np.float64)
            close_prices = np.nan_to_num(close_prices)
            high_prices = np.nan_to_num(high_prices)
            low_prices = np.nan_to_num(low_prices)

            # Get current price
            current_price = close_prices[-1]

            # Calculate indicators with individual try/except blocks for each indicator
            try:
                # Moving Averages with exponential option for shorter periods
                ma_5 = talib.EMA(close_prices, timeperiod=5)[-1]
                ma_20 = talib.EMA(close_prices, timeperiod=20)[-1]
                ma_50 = talib.SMA(close_prices, timeperiod=50)[-1]
                ma_100 = talib.SMA(close_prices, timeperiod=100)[-1]

                # Moving Average slopes (to determine trend direction)
                ma_20_slope = (ma_20 - talib.EMA(close_prices, timeperiod=20)[-6]) / 5  # 5-day slope
                ma_50_slope = (ma_50 - talib.SMA(close_prices, timeperiod=50)[-6]) / 5  # 5-day slope
            except Exception as e:
                print(f"Error calculating moving averages: {str(e)}")
                ma_5, ma_20, ma_50, ma_100 = 0, 0, 0, 0
                ma_20_slope, ma_50_slope = 0, 0

            try:
                # RSI with additional lookback periods
                rsi = talib.RSI(close_prices, timeperiod=14)[-1]
                rsi_5d = talib.RSI(close_prices, timeperiod=14)[-5] if len(close_prices) > 20 else 50
                rsi_trend = "Up" if rsi > rsi_5d else "Down"
            except Exception as e:
                print(f"Error calculating RSI: {str(e)}")
                rsi, rsi_5d = 50, 50
                rsi_trend = "Unknown"

            try:
                # ADX - Direction and strength
                adx = talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)[-1]
                plus_di = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=14)[-1]
                minus_di = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=14)[-1]

                # Trend direction based on DI
                trend_direction = "Up" if plus_di > minus_di else "Down"
            except Exception as e:
                print(f"Error calculating ADX: {str(e)}")
                adx, plus_di, minus_di = 0, 0, 0
                trend_direction = "Unknown"

            try:
                # MACD with histogram momentum
                macd, macd_signal, macd_hist = talib.MACD(
                    close_prices, fastperiod=12, slowperiod=26, signalperiod=9
                )

                # Check if MACD histogram is accelerating/decelerating
                hist_momentum = macd_hist[-1] - macd_hist[-2] if len(macd_hist) > 2 else 0
            except Exception as e:
                print(f"Error calculating MACD: {str(e)}")
                macd = np.array([0])
                macd_signal = np.array([0])
                macd_hist = np.array([0, 0])
                hist_momentum = 0

            try:
                # Bollinger Bands with width calculation
                upper, middle, lower = talib.BBANDS(
                    close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
                )

                # Calculate BB width and %B (position within bands)
                bb_width = (upper[-1] - lower[-1]) / middle[-1] * 100  # As percentage
                bb_percent = (current_price - lower[-1]) / (upper[-1] - lower[-1]) * 100 if (upper[-1] - lower[
                    -1]) > 0 else 50
            except Exception as e:
                print(f"Error calculating Bollinger Bands: {str(e)}")
                upper = np.array([current_price * 1.1])
                middle = np.array([current_price])
                lower = np.array([current_price * 0.9])
                bb_width = 10
                bb_percent = 50

            try:
                # Stochastic oscillator
                slowk, slowd = talib.STOCH(
                    high_prices, low_prices, close_prices,
                    fastk_period=14, slowk_period=3, slowk_matype=0,
                    slowd_period=3, slowd_matype=0
                )
            except Exception as e:
                print(f"Error calculating Stochastic: {str(e)}")
                slowk = np.array([50])
                slowd = np.array([50])

            try:
                # ATR for volatility assessment
                atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)[-1]
                atr_percent = (atr / current_price) * 100  # ATR as percentage of price
            except Exception as e:
                print(f"Error calculating ATR: {str(e)}")
                atr = 0
                atr_percent = 0

            # Skip OBV calculation if it fails - it was causing the main issue
            obv_trend = "Unknown"
            try:
                # Get volume data and ensure it's properly formatted
                if 'Volume' in stock_data.columns:
                    # Extract volume data and ensure it's the same length as close_prices
                    volume = stock_data['Volume'].values

                    # Convert to float64 and handle NaNs - crucial for TA-Lib
                    volume = np.array(volume, dtype=np.float64)
                    volume = np.nan_to_num(volume)

                    # Verify dimensions match
                    if len(volume) == len(close_prices):
                        # OBV calculation
                        obv = talib.OBV(close_prices, volume)
                        # Only proceed if we have enough data
                        if len(obv) > 20:
                            obv_trend = "Up" if obv[-1] > obv[-20] else "Down"
            except Exception as e:
                print(f"Error calculating OBV (skipping): {str(e)}")
                # We'll keep the default "Unknown" trend

            # Integration of all technical indicators for buy/sell signal
            buy_signals = 0
            sell_signals = 0

            # Price vs Moving Averages analysis
            if current_price > ma_20 and current_price > ma_50:
                buy_signals += 1
            elif current_price < ma_20 and current_price < ma_50:
                sell_signals += 1

            # Moving Average crossovers and slopes
            if ma_5 > ma_20 and ma_20_slope > 0:
                buy_signals += 1
            elif ma_5 < ma_20 and ma_20_slope < 0:
                sell_signals += 1

            # RSI signals
            if rsi < 30:
                buy_signals += 1
            elif rsi > 70:
                sell_signals += 1

            # ADX trend strength confirmation
            if adx > 25:
                if trend_direction == "Up":
                    buy_signals += 1
                elif trend_direction == "Down":
                    sell_signals += 1

            # MACD signals
            if len(macd) > 1 and len(macd_signal) > 1:
                if macd[-1] > macd_signal[-1] and macd_hist[-1] > 0:
                    buy_signals += 1
                elif macd[-1] < macd_signal[-1] and macd_hist[-1] < 0:
                    sell_signals += 1

            # MACD histogram momentum
            if hist_momentum > 0 and macd_hist[-1] > 0:
                buy_signals += 1
            elif hist_momentum < 0 and macd_hist[-1] < 0:
                sell_signals += 1

            # Bollinger Band signals
            if bb_percent < 10:  # Price near lower band
                buy_signals += 1
            elif bb_percent > 90:  # Price near upper band
                sell_signals += 1

            # Stochastic signals
            if len(slowk) > 0 and len(slowd) > 0:
                if slowk[-1] < 20 and slowd[-1] < 20:
                    buy_signals += 1
                elif slowk[-1] > 80 and slowd[-1] > 80:
                    sell_signals += 1

            # Volume confirmation - only use if we have a valid trend
            if obv_trend != "Unknown":
                if obv_trend == "Up" and current_price > ma_20:
                    buy_signals += 1
                elif obv_trend == "Down" and current_price < ma_20:
                    sell_signals += 1

            # Determine signal based on overall technical picture
            signal_difference = buy_signals - sell_signals

            if signal_difference >= 2:
                signal = "BUY"
            elif signal_difference <= -2:
                signal = "SELL"
            else:
                signal = "HOLD"

            # Update table with calculated values (only core indicators)
            self.stocks_table.setItem(row, 1, QTableWidgetItem(f"₹{current_price:.2f}"))
            self.stocks_table.setItem(row, 2, QTableWidgetItem(f"₹{ma_5:.2f}"))
            self.stocks_table.setItem(row, 3, QTableWidgetItem(f"₹{ma_20:.2f}"))
            self.stocks_table.setItem(row, 4, QTableWidgetItem(f"₹{ma_50:.2f}"))
            self.stocks_table.setItem(row, 5, QTableWidgetItem(f"₹{ma_100:.2f}"))

            # Color-code RSI values
            rsi_item = QTableWidgetItem(f"{rsi:.2f}")
            if rsi > 70:
                rsi_item.setForeground(Qt.GlobalColor.red)  # Overbought
            elif rsi < 30:
                rsi_item.setForeground(Qt.GlobalColor.green)  # Oversold
            self.stocks_table.setItem(row, 6, rsi_item)

            # ADX with direction
            adx_item = QTableWidgetItem(f"{adx:.2f}")
            if adx > 25:
                if trend_direction == "Up":
                    adx_item.setForeground(Qt.GlobalColor.green)  # Strong uptrend
                else:
                    adx_item.setForeground(Qt.GlobalColor.red)  # Strong downtrend
            self.stocks_table.setItem(row, 7, adx_item)

            # Signal column
            signal_item = QTableWidgetItem(signal)
            if signal == "BUY":
                signal_item.setForeground(Qt.GlobalColor.green)
                signal_item.setFont(QFont('Arial', 9, QFont.Weight.Bold))
            elif signal == "SELL":
                signal_item.setForeground(Qt.GlobalColor.red)
                signal_item.setFont(QFont('Arial', 9, QFont.Weight.Bold))
            else:  # HOLD
                signal_item.setForeground(Qt.GlobalColor.black)
                signal_item.setFont(QFont('Arial', 9, QFont.Weight.Normal))
            self.stocks_table.setItem(row, 8, signal_item)

            # Show status message
            self.statusBar().showMessage(f'Data updated for {symbol}', 3000)

        except Exception as e:
            print(f"Error calculating indicators for {symbol}: {str(e)}")
            traceback.print_exc()
            self.statusBar().showMessage(f'Error calculating indicators for {symbol}', 3000)

            # Set error in cells but keep the stock in the table
            self.stocks_table.setItem(row, 1, QTableWidgetItem("Error"))
            for col in range(2, 9):
                self.stocks_table.setItem(row, col, QTableWidgetItem("--"))

    '''def calculate_technical_indicators(self, symbol, row):
        try:
            # Ensure proper NSE stock format
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            self.statusBar().showMessage(f'Fetching data for {symbol}...')

            # Download stock data with explicit parameters
            stock_data = yf.download(
                symbol,
                period="1y",  # Get one year of data
                interval="1d",  # Daily data
                auto_adjust=True,  # Auto-adjust for splits
                progress=False
            )

            if stock_data.empty:
                print(f"No data available for {symbol}")
                self.statusBar().showMessage(f"No data available for {symbol}", 5000)

                # Set placeholder values
                for col in range(1, 9):  # Updated range for new column
                    self.stocks_table.setItem(row, col, QTableWidgetItem("No Data"))
                return

            # Make sure we have enough data
            if len(stock_data) < 100:
                print(f"Insufficient data points for {symbol}: only {len(stock_data)} days")
                self.statusBar().showMessage(f"Insufficient history for {symbol}", 5000)

                # Still show current price but mark indicators as insufficient
                if len(stock_data) > 0:
                    current_price = stock_data['Close'].iloc[-1]
                    self.stocks_table.setItem(row, 1, QTableWidgetItem(f"₹{current_price:.2f}"))

                for col in range(2, 9):  # Updated range for new column
                    self.stocks_table.setItem(row, col, QTableWidgetItem("Insuf. Data"))
                return

            # Extract price data as numpy arrays
            close_prices = stock_data['Close'].values
            high_prices = stock_data['High'].values
            low_prices = stock_data['Low'].values

            # Ensure we have 1D arrays for TA-Lib
            if len(close_prices.shape) > 1:
                close_prices = close_prices.flatten()
                high_prices = high_prices.flatten()
                low_prices = low_prices.flatten()

            # Convert to float64 and handle NaN values
            close_prices = np.array(close_prices, dtype=np.float64)
            high_prices = np.array(high_prices, dtype=np.float64)
            low_prices = np.array(low_prices, dtype=np.float64)
            close_prices = np.nan_to_num(close_prices)
            high_prices = np.nan_to_num(high_prices)
            low_prices = np.nan_to_num(low_prices)

            # Get current price
            current_price = close_prices[-1]

            # Calculate indicators
            try:
                # Moving Averages
                ma_5 = talib.SMA(close_prices, timeperiod=5)[-1]
                ma_20 = talib.SMA(close_prices, timeperiod=20)[-1]
                ma_50 = talib.SMA(close_prices, timeperiod=50)[-1]
                ma_100 = talib.SMA(close_prices, timeperiod=100)[-1]

                # RSI
                rsi = talib.RSI(close_prices, timeperiod=14)[-1]

                # ADX
                adx = talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)[-1]

                # MACD for trend confirmation
                macd, macd_signal, macd_hist = talib.MACD(
                    close_prices, fastperiod=12, slowperiod=26, signalperiod=9
                )

                # Bollinger Bands for volatility
                upper, middle, lower = talib.BBANDS(
                    close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
                )

                # Stochastic oscillator
                slowk, slowd = talib.STOCH(
                    high_prices, low_prices, close_prices,
                    fastk_period=14, slowk_period=3, slowk_matype=0,
                    slowd_period=3, slowd_matype=0
                )

                # Determine buy/sell signal based on multiple indicators
                signal = self.generate_trading_signal(
                    current_price, ma_5, ma_20, ma_50, ma_100,
                    rsi, adx, macd[-1], macd_signal[-1], macd_hist[-1],
                    upper[-1], middle[-1], lower[-1],
                    slowk[-1], slowd[-1]
                )

                # Update table with calculated values
                self.stocks_table.setItem(row, 1, QTableWidgetItem(f"₹{current_price:.2f}"))
                self.stocks_table.setItem(row, 2, QTableWidgetItem(f"₹{ma_5:.2f}"))
                self.stocks_table.setItem(row, 3, QTableWidgetItem(f"₹{ma_20:.2f}"))
                self.stocks_table.setItem(row, 4, QTableWidgetItem(f"₹{ma_50:.2f}"))
                self.stocks_table.setItem(row, 5, QTableWidgetItem(f"₹{ma_100:.2f}"))

                # Color-code RSI values
                rsi_item = QTableWidgetItem(f"{rsi:.2f}")
                if rsi > 70:
                    rsi_item.setForeground(Qt.GlobalColor.red)  # Overbought
                elif rsi < 30:
                    rsi_item.setForeground(Qt.GlobalColor.green)  # Oversold
                self.stocks_table.setItem(row, 6, rsi_item)

                # ADX
                adx_item = QTableWidgetItem(f"{adx:.2f}")
                if adx > 25:
                    adx_item.setForeground(Qt.GlobalColor.blue)  # Strong trend
                self.stocks_table.setItem(row, 7, adx_item)

                # Signal column
                # Signal column styling
                signal_item = QTableWidgetItem(signal)
                if signal == "BUY":
                    signal_item.setForeground(Qt.GlobalColor.green)
                    signal_item.setFont(QFont('Arial', 9, QFont.Weight.Bold))
                elif signal == "SELL":
                    signal_item.setForeground(Qt.GlobalColor.red)
                    signal_item.setFont(QFont('Arial', 9, QFont.Weight.Bold))
                else:  # HOLD
                    signal_item.setForeground(Qt.GlobalColor.black)
                    signal_item.setFont(QFont('Arial', 9, QFont.Weight.Normal))
                self.stocks_table.setItem(row, 8, signal_item)

                # Show status message
                self.statusBar().showMessage(f'Data updated for {symbol}', 3000)

            except Exception as indicator_error:
                print(f"Error calculating specific indicators: {str(indicator_error)}")
                traceback.print_exc()

                # At least show the current price
                self.stocks_table.setItem(row, 1, QTableWidgetItem(f"₹{current_price:.2f}"))

                # Mark indicators as error
                for col in range(2, 9):  # Updated range for new column
                    self.stocks_table.setItem(row, col, QTableWidgetItem("Calc Error"))

        except Exception as e:
            print(f"Error calculating indicators for {symbol}: {str(e)}")
            traceback.print_exc()
            self.statusBar().showMessage(f'Error calculating indicators for {symbol}', 3000)

            # Set error in cells but keep the stock in the table
            self.stocks_table.setItem(row, 1, QTableWidgetItem("Error"))
            for col in range(2, 9):  # Updated range for new column
                self.stocks_table.setItem(row, col, QTableWidgetItem("--"))'''

    def add_bottom_navigation(self):
        """Add bottom navigation section with back button"""
        nav_frame = QFrame()
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ccc;
                margin-top: 10px;
            }
        """)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(15, 15, 15, 15)

        back_button = QPushButton('Back to Dashboard')
        back_button.setMinimumHeight(40)
        back_button.setMinimumWidth(150)
        back_button.clicked.connect(self.switch_to_dashboard_slot)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)

        nav_layout.addWidget(back_button)
        nav_layout.addStretch()

        return nav_frame

    def generate_trading_signal(self, current_price, ma_5, ma_20, ma_50, ma_100,
                                rsi, adx, macd, macd_signal, macd_hist,
                                bb_upper, bb_middle, bb_lower, slowk, slowd):
        """
        Generate simplified trading signals based on multiple technical indicators
        Returns: "BUY", "SELL", or "HOLD" only
        """
        buy_signals = 0
        sell_signals = 0

        # Moving Average Crossovers
        if ma_5 > ma_20:
            buy_signals += 1
        elif ma_5 < ma_20:
            sell_signals += 1

        # Price relative to longer-term MAs
        if current_price > ma_50:
            buy_signals += 1
        elif current_price < ma_50:
            sell_signals += 1

        if current_price > ma_100:
            buy_signals += 1
        elif current_price < ma_100:
            sell_signals += 1

        # RSI Signals
        if rsi > 50:
            buy_signals += 1
        elif rsi < 50:
            sell_signals += 1

        # Add classic RSI overbought/oversold signals
        if rsi < 30:  # Oversold condition
            buy_signals += 1
        elif rsi > 70:  # Overbought condition
            sell_signals += 1

        # ADX - Trend Strength
        if adx > 25:  # Strong trend
            # Amplify existing signals when trend is strong
            if buy_signals > sell_signals:
                buy_signals += 1
            elif sell_signals > buy_signals:
                sell_signals += 1

        # MACD Signals
        if macd > macd_signal and macd_hist > 0:
            buy_signals += 1
        elif macd < macd_signal and macd_hist < 0:
            sell_signals += 1

        # Bollinger Bands
        if current_price < bb_lower:
            buy_signals += 1  # Price below lower band - potential bounce
        elif current_price > bb_upper:
            sell_signals += 1  # Price above upper band - potential reversal

        # Stochastic Signals
        if slowk < 20 and slowd < 20:
            buy_signals += 1  # Oversold
        elif slowk > 80 and slowd > 80:
            sell_signals += 1  # Overbought

        # Cross signals
        if slowk > slowd and slowk < 30:
            buy_signals += 1  # Stochastic crossover in oversold region
        elif slowk < slowd and slowk > 70:
            sell_signals += 1  # Stochastic crossover in overbought region

        # Determine final signal - simplified to just BUY, SELL, or HOLD
        signal_difference = buy_signals - sell_signals

        if signal_difference >= 2:
            return "BUY"
        elif signal_difference <= -2:
            return "SELL"
        else:
            return "HOLD"

    '''def generate_trading_signal(self, current_price, ma_5, ma_20, ma_50, ma_100,
                                rsi, adx, macd, macd_signal, macd_hist,
                                bb_upper, bb_middle, bb_lower, slowk, slowd):
        """
        Generate trading signals based on multiple technical indicators
        Returns: "BUY", "SELL", "STRONG BUY", "STRONG SELL", or "HOLD"
        """
        
        buy_signals = 0
        sell_signals = 0

        # Moving Average Crossovers
        if ma_5 > ma_20:
            buy_signals += 1
        elif ma_5 < ma_20:
            sell_signals += 1

        # Price relative to longer-term MAs
        if current_price > ma_50:
            buy_signals += 1
        elif current_price < ma_50:
            sell_signals += 1

        if current_price > ma_100:
            buy_signals += 1
        elif current_price < ma_100:
            sell_signals += 1

        # RSI Signals
        if rsi > 50:  # Add this line to give weight to RSI above 50
            buy_signals += 1
        elif rsi < 50:
            sell_signals +=1
        ''if rsi < 30:
            buy_signals += 2  # Oversold - stronger buy signal
        if rsi < 30:
            buy_signals += 2  # Oversold - stronger buy signal
        elif rsi < 40:
            buy_signals += 1  # Approaching oversold
        elif rsi > 70:
            sell_signals += 2  # Overbought - stronger sell signal
        elif rsi > 60:
            sell_signals += 1  # Approaching overbought''


        # ADX - Trend Strength
        trend_strength = 0
        if adx > 25:
            trend_strength = 1  # Strong trend
        if adx > 40:
            trend_strength = 2  # Very strong trend

        # MACD Signals
        if macd > macd_signal and macd_hist > 0:
            buy_signals += 1
        elif macd < macd_signal and macd_hist < 0:
            sell_signals += 1

        # Bollinger Bands
        if current_price < bb_lower:
            buy_signals += 1  # Price below lower band - potential bounce
        elif current_price > bb_upper:
            sell_signals += 1  # Price above upper band - potential reversal

        # Stochastic Signals
        if slowk < 20 and slowd < 20:
            buy_signals += 1  # Oversold
        elif slowk > 80 and slowd > 80:
            sell_signals += 1  # Overbought

        # Cross signals
        if slowk > slowd and slowk < 30:
            buy_signals += 1  # Stochastic crossover in oversold region
        elif slowk < slowd and slowk > 70:
            sell_signals += 1  # Stochastic crossover in overbought region

        # Apply trend strength multiplier
        if trend_strength > 0:
            if buy_signals > sell_signals:
                buy_signals += trend_strength
            elif sell_signals > buy_signals:
                sell_signals += trend_strength

        # Determine final signal
        signal_strength = abs(buy_signals - sell_signals)

        if buy_signals > sell_signals:
            if signal_strength >= 5:
                return "STRONG BUY"
            elif signal_strength >= 2:
                return "BUY"
            else:
                return "HOLD"
        elif sell_signals > buy_signals:
            if signal_strength >= 5:
                return "STRONG SELL"
            elif signal_strength >= 2:
                return "SELL"
            else:
                return "HOLD"
        else:
            return "HOLD"'''
     # Update the method in the class
    def update_calculate_technical_indicators(self, symbol, row):
        return calculate_technical_indicators(self, symbol, row)

    def add_stock(self, symbol):
        """Add a stock to the analytics with database integration"""
        # Check if stock already exists in the list (keep your existing check)
        for i in range(self.stocks_table.rowCount()):
            if self.stocks_table.item(i, 0) and self.stocks_table.item(i, 0).text() == symbol:
                self.statusBar().showMessage(f'{symbol} is already in the analytics list', 3000)
                return

        try:
            # Add to database if available
            if hasattr(self, 'db') and self.db and self.user_id:
                success, message = self.db.add_analytics_preference(self.user_id, symbol)
                if not success and "already in your analytics" not in message:
                    QMessageBox.warning(self, "Error", message)
                    return

            # Add new row to both tables
            row_position = self.stocks_table.rowCount()
            self.stocks_table.insertRow(row_position)
            self.remove_buttons_table.insertRow(row_position)

            # Add symbol to table
            self.stocks_table.setItem(row_position, 0, QTableWidgetItem(symbol))

            # Fill with placeholder values
            for col in range(1, 9):
                self.stocks_table.setItem(row_position, col, QTableWidgetItem("--"))

            # Add remove button
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    text-align: center;
                    border-radius: 3px;  
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            remove_btn.clicked.connect(lambda checked, r=row_position: self.remove_stock(r))
            self.remove_buttons_table.setCellWidget(row_position, 0, remove_btn)

            # Calculate technical indicators for this stock with error handling
            try:
                self.calculate_technical_indicators(symbol, row_position)
            except Exception as tech_error:
                print(f"Warning: Could not calculate technical indicators for {symbol}: {tech_error}")
                # Keep the stock in the table but show warning in status bar
                self.statusBar().showMessage(
                    f'Added {symbol}, but could not fetch technical data. Will retry on refresh.', 5000)

            self.statusBar().showMessage(f'{symbol} added to analytics', 3000)
        except Exception as e:
            print(f"Error adding stock {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error",
                                f"Could not add {symbol}. Please verify the symbol and try again.\n\nError: {str(e)}")
            # Remove the row if there was an error
            if row_position < self.stocks_table.rowCount():
                self.stocks_table.removeRow(row_position)
                self.remove_buttons_table.removeRow(row_position)
            if symbol in self.stocks_list:
                self.stocks_list.remove(symbol)
            self.statusBar().showMessage(f'Error adding {symbol}', 3000)



    def refresh_stock_data(self):
        """Update technical indicators for all stocks in the table"""
        # First check if TA-Lib is working
        if not self.check_talib_installation():
            QMessageBox.warning(
                self,
                "TA-Lib Error",
                "TA-Lib is not working correctly. Technical indicators cannot be calculated."
            )
            return

        self.statusBar().showMessage('Refreshing technical data...')

        for row in range(self.stocks_table.rowCount()):
            try:
                symbol = self.stocks_table.item(row, 0).text()
                # Call the debug version for better error handling
                self.calculate_technical_indicators(symbol, row)
            except Exception as e:
                print(f"Error refreshing data for row {row}: {str(e)}")
                # Set placeholder values if no data returned
                for col in range(1, 8):
                    self.stocks_table.setItem(row, col, QTableWidgetItem("--"))

        self.statusBar().showMessage('Technical data updated', 3000)

    def closeEvent(self, event):
        """Close database connection when window is closed"""
        self.close_database()
        super().closeEvent(event)

    def close_database(self):
        """Close database connection"""
        if hasattr(self, 'db'):
            self.db.close()
            print("Database connection closed")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AnalyticsWindow()
    window.show()
    sys.exit(app.exec())