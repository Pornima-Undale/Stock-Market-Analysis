import talib
from PyQt6.QtWidgets import QMessageBox
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFrame, QStackedWidget, QMenuBar, QMenu, QStatusBar,
                             QToolBar, QSizePolicy, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QScrollArea, QTabWidget, QGridLayout, QDialog)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont
import sys
import pandas as pd
from datetime import datetime
import time
from stock_thread_manager import StockDataManager
from add_to_portfolio_dialog import AddToPortfolioDialog
# from nsepy import get_history
from datetime import date, timedelta
import yfinance as yf  # Keep this as backup for non-NSE stocks

import yfinance as yf

from navigation_windows import (
    PortfolioWindow, WatchlistWindow,
    AnalyticsWindow, ReportsWindow, NewsFeedWindow, AboutUsWindow
)
from PyQt6.QtCore import pyqtSignal
from navigation_windows import (
    PortfolioWindow, WatchlistWindow,
    AnalyticsWindow, ReportsWindow, NewsFeedWindow, AboutUsWindow
)


class AddStockButton(QPushButton):
    def __init__(self, symbol, dashboard, parent=None):
        super().__init__("Add", parent)
        self.symbol = symbol
        self.dashboard = dashboard

        # Style the button to match the screenshot
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;  /* Green background */
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: center;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Connect the click event to show menu
        self.clicked.connect(self.show_add_options)

    def show_add_options(self):
        """Show menu with add options"""
        menu = QMenu(self)

        # Add menu actions
        watchlist_action = menu.addAction("Add to Watchlist")
        portfolio_action = menu.addAction("Add to Portfolio")
        analytics_action = menu.addAction("Add to Analytics")

        # Connect actions to methods
        watchlist_action.triggered.connect(self.add_to_watchlist)
        portfolio_action.triggered.connect(self.add_to_portfolio)
        analytics_action.triggered.connect(self.add_to_analytics)

        # Show menu at button's position
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))

    def add_to_watchlist(self):
        """Add stock to watchlist"""
        try:
            # Ensure watchlist window exists
            if not hasattr(self.dashboard, 'watchlist_window'):
                print("Creating new watchlist window")
                self.dashboard.watchlist_window = WatchlistWindow(user_id=self.dashboard.user_id)
            else:
                print("Using existing watchlist window")

            # Debug information
            print(f"Adding {self.symbol} to watchlist")
            print(f"Watchlist window ID: {id(self.dashboard.watchlist_window)}")

            # Show watchlist window
            self.dashboard.watchlist_window.show()
            self.dashboard.watchlist_window.raise_()
            self.dashboard.watchlist_window.activateWindow()

            # Add stock to watchlist
            self.dashboard.watchlist_window.add_stock(self.symbol)

            # Check if it was actually added
            symbols_after_add = [row[0] for row in self.dashboard.watchlist_window.watchlist_data]
            print(f"Watchlist data after add: {symbols_after_add}")
            print(f"Is {self.symbol} in watchlist: {self.symbol in symbols_after_add}")

            QMessageBox.information(
                self,
                "Success",
                f"{self.symbol} added to Watchlist"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not add {self.symbol} to Watchlist: {str(e)}"
            )
            import traceback
            traceback.print_exc()

    def add_to_portfolio(self):
        """Add stock to portfolio with purchase details"""
        try:
            # Get current price from the dashboard's stock table
            current_price = 0
            for row in range(self.dashboard.stock_table.rowCount()):
                if (self.dashboard.stock_table.item(row, 0) and
                        self.dashboard.stock_table.item(row, 0).text() == self.symbol):
                    # Get the current price from Close column (index 2)
                    price_text = self.dashboard.stock_table.item(row, 2).text()
                    if price_text.startswith('₹'):
                        price_text = price_text[1:]  # Remove the Rupee symbol
                    current_price = float(price_text)
                    break

            # Show the Add to Portfolio dialog
            dialog = AddToPortfolioDialog(self.symbol, current_price, self.dashboard)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                # Get the data from dialog
                stock_data = dialog.get_data()

                # Ensure portfolio window exists
                if not hasattr(self.dashboard, 'portfolio_window'):
                    self.dashboard.portfolio_window = PortfolioWindow(user_id=self.dashboard.user_id)

                # Show portfolio window
                self.dashboard.portfolio_window.show()
                self.dashboard.portfolio_window.raise_()
                self.dashboard.portfolio_window.activateWindow()

                # Add stock to portfolio
                self.dashboard.portfolio_window.add_stock_to_portfolio(stock_data)

                QMessageBox.information(
                    self,
                    "Success",
                    f"{self.symbol} added to Portfolio with {stock_data['quantity']} shares"
                )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not add {self.symbol} to Portfolio: {str(e)}"
            )
            import traceback
            traceback.print_exc()

    def add_to_analytics(self):
        """Add stock to analytics"""
        try:
            # Ensure analytics window exists
            if not hasattr(self.dashboard, 'analytics_window'):
                self.dashboard.analytics_window = AnalyticsWindow(user_id=self.dashboard.user_id)

            # Show analytics window
            self.dashboard.analytics_window.show()
            self.dashboard.analytics_window.raise_()
            self.dashboard.analytics_window.activateWindow()

            # Add stock to analytics
            self.dashboard.analytics_window.add_stock(self.symbol)

            QMessageBox.information(
                self,
                "Success",
                f"{self.symbol} added to Analytics"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not add {self.symbol} to Analytics: {str(e)}"
            )


class StockDashboard(QMainWindow):
    # Ensure the signal is defined correctly
    switch_to_watchlist = pyqtSignal()

    '''def show_watchlist_window(self):
        """Emit signal to switch to watchlist"""
        print("[DEBUG] show_watchlist_window method called in dashboard")
        try:
            # Check if signal has connections
            connections = self.switch_to_watchlist.connections()
            print(f"[DEBUG] Number of signal connections: {len(connections)}")

            # Print connection details for debugging
            for i, conn in enumerate(connections):
                print(f"[DEBUG] Connection {i}: {conn}")

            # Emit the signal
            self.switch_to_watchlist.emit()
            print("[DEBUG] Signal emitted in dashboard")

            # Hide the current window
            self.hide()
            print("[DEBUG] Dashboard hidden")

            # Force event processing
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
        except Exception as e:
            print(f"[ERROR] In show_watchlist_window: {e}")
            import traceback
            traceback.print_exc()'''

    def __init__(self, user_id=None, username=None):
        super().__init__()

        self.stock_data_manager = StockDataManager(self)

        self.user_id = user_id if user_id is not None else 1  # Default for testing
        self.username = username

        self.stock_table = QTableWidget()

        stocks_to_fetch = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']
        self.stock_data_manager.fetch_multiple_stocks(
            stocks_to_fetch,
            update_callback=self.update_stock_table
        )

        self.nav_buttons = [
            'Market Overview',
            'Portfolio',
            'Watchlist',
            'Analytics',
            'Reports',
            'News Feed',
            'About Us'
        ]

        # Initialize top stocks list
        self.top_stocks = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
            'ICICIBANK.NS', 'ITC.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'BAJFINANCE.NS',
            'BHARTIARTL.NS', 'LT.NS', 'ASIANPAINT.NS', 'HCLTECH.NS', 'MARUTI.NS',
            'TITAN.NS', 'AXISBANK.NS', 'ULTRACEMCO.NS', 'M&M.NS', 'SUNPHARMA.NS'
        ]

        self.process_next_stock(0)

        # Initialize stock fetch timer
        self.stock_fetch_timer = None

        # Try to connect the watchlist signal with error handling
        try:
            print("[DEBUG] Attempting to connect switch_to_watchlist signal")

            # Disconnect any existing connections first
            try:
                self.switch_to_watchlist.disconnect()
            except TypeError:
                pass  # No existing connections

            # Connect the signal with a method
            self.switch_to_watchlist.connect(self.on_switch_to_watchlist)

            print("[DEBUG] Watchlist signal connection successful")
        except Exception as e:
            print(f"[ERROR] Failed to connect watchlist signal: {e}")

        # Initialize UI components
        self.initUI()

        # Initialize navigation windows
        self.init_navigation_windows()

        # Connect side navigation buttons
        self.connect_side_nav_buttons()

        # Fetch market indices during initialization
        self.fetch_market_indices()

        # Start stock loading with a delay
        QTimer.singleShot(1000, lambda: self.process_next_stock(0))

        # Optional: Start auto update
        self.start_auto_update()

        # Start market indices update timer
        self.start_market_indices_update()

    def start_market_indices_update(self):
        """Start periodic updates for market indices"""
        self.market_indices_timer = QTimer()
        self.market_indices_timer.timeout.connect(self.fetch_market_indices)
        self.market_indices_timer.start(60000)  # Update every minute

    def show_watchlist_window(self):
        # Show the portfolio window
        self.statusBar().showMessage('Navigating to Watchlist...')
        self.hide()  # Hide the dashboard
        self.aboutus_window.show()
        self.aboutus_window.showMaximized()
        self.aboutus_window.raise_()
        self.aboutus_window.activateWindow()
        #self.watchlist_window.show()

    def show_portfolio_window(self):
        # Show the portfolio window
        self.statusBar().showMessage('Navigating to Portfolio...')
        self.hide()  # Hide the dashboard
        self.aboutus_window.show()
        self.aboutus_window.showMaximized()
        self.aboutus_window.raise_()
        self.aboutus_window.activateWindow()
        #self.portfolio_window.show()

    def show_analytics_window(self):
        # Show the analytics window
        self.statusBar().showMessage('Navigating to Analytics...')
        self.hide()  # Hide the dashboard
        self.aboutus_window.show()
        self.aboutus_window.showMaximized()
        self.aboutus_window.raise_()
        self.aboutus_window.activateWindow()
        #self.analytics_window.show()

    def show_reports_window(self):
        # Show the reports window
        self.statusBar().showMessage('Navigating to Reports...')
        self.hide()  # Hide the dashboard
        self.aboutus_window.show()
        self.aboutus_window.showMaximized()
        self.aboutus_window.raise_()
        self.aboutus_window.activateWindow()
        #self.reports_window.show()

    def show_news_feed_window(self):
        # Show the news feed window
        self.statusBar().showMessage('Navigating to News Feed...')
        self.hide()  # Hide the dashboard
        self.aboutus_window.show()
        self.aboutus_window.showMaximized()
        self.aboutus_window.raise_()
        self.aboutus_window.activateWindow()
        #self.news_feed_window.show()

    def show_aboutus_window(self):
        """Show the about us window"""
        self.statusBar().showMessage('Navigating to About Us...')
        self.hide()  # Hide the dashboard
        self.aboutus_window.show()
        self.aboutus_window.showMaximized()
        self.aboutus_window.raise_()
        self.aboutus_window.activateWindow()

    def initUI(self):
        # Set window properties
        self.setWindowTitle('SARASFINTECH - Stock Market Dashboard')
        self.setMinimumSize(1200, 500)

        # Set the main style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
            QPushButton {
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                background-color: #041E42;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            QLineEdit {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            /* Style for scrollbars */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #041E42;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0A3A7A;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #041E42;
                min-width: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #0A3A7A;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                width: 0px;
            }
        """)

        # Create central widget with a main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create menu bar and toolbar (fixed at the top)
        self.create_menu_bar()
        self.create_tool_bar()

        # Create a new widget to hold the main content that will be scrollable
        content_container = QWidget()
        container_layout = QHBoxLayout(content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Create the side navigation (fixed)
        self.create_side_nav()

        # Create a scroll area for the main dashboard content
        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dashboard_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Create the dashboard content that will be inside the scroll area
        dashboard_content = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_content)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        dashboard_layout.setSpacing(20)

        # Add market summary cards
        summary_cards = self.create_market_summary()
        dashboard_layout.addWidget(summary_cards)

        # Create and add market overview section
        market_overview = self.create_market_overview_page()
        dashboard_layout.addWidget(market_overview)

        # Add extra content to ensure scrollability
        #self.add_additional_dashboard_content(dashboard_layout)

        # Set the dashboard content as the widget for the scroll area
        dashboard_scroll.setWidget(dashboard_content)

        # Add side nav and scrollable dashboard to the container
        container_layout.addWidget(self.side_nav)
        container_layout.addWidget(dashboard_scroll, 1)  # Give the dashboard area more stretch

        # Add the container to the main layout
        main_layout.addWidget(content_container)

        # Create status bar at the bottom
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #041E42;
                color: white;
                padding: 5px;
            }
        """)

        self.setCentralWidget(central_widget)

    def switch_to_watchlist(self):
        if not hasattr(self, 'watchlist_window') or not self.watchlist_window:
            self.watchlist_window = WatchlistWindow(user_id=self.user_id)
            self.watchlist_window.switch_to_dashboard.connect(self.show_dashboard)
        self.hide()
        self.watchlist_window.show()
        self.watchlist_window.showMaximized()

    def switch_to_portfolio(self):
        if not hasattr(self, 'portfolio_window') or not self.portfolio_window:
            self.portfolio_window = PortfolioWindow(user_id=self.user_id)
            self.portfolio_window.switch_to_dashboard.connect(self.show_dashboard)
        self.hide()
        self.portfolio_window.show()
        self.portfolio_window.showMaximized()

    def switch_to_analytics(self):
        if not hasattr(self, 'analytics_window') or not self.analytics_window:
            self.analytics_window = AnalyticsWindow(user_id=self.user_id)
            self.analytics_window.switch_to_dashboard.connect(self.show_dashboard)
        self.hide()
        self.analytics_window.show()
        self.analytics_window.showMaximized()

    def load_top_stocks(self):
        self.statusBar().showMessage('Loading top stocks...')
        self.stock_table.setRowCount(0)  # Clear existing data

        for symbol in self.top_stocks:
            try:
                self.fetch_stock_data(symbol)
                # Add a small delay to avoid hitting rate limits
                QTimer.singleShot(500, lambda: None)
            except Exception as e:
                print(f"Error loading stock {symbol}: {str(e)}")
                continue

        self.statusBar().showMessage('Top stocks loaded successfully')

    # Add these two methods to your StockDashboard class

    def process_next_stock(self, index):
        """
        Process one stock at a time with improved open price handling
        """
        # Base case: we've processed all stocks
        if index >= len(self.top_stocks):
            self.statusBar().showMessage('All stocks loaded successfully')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(self, 'last_updated_label'):
                self.last_updated_label.setText(f'Last Updated: {current_time}')
            print("Stock loading process completed.")
            return

        # Process current stock
        symbol = self.top_stocks[index]
        try:
            # Update status bar
            self.statusBar().showMessage(f'Loading stock {index + 1}/{len(self.top_stocks)}: {symbol}')

            # Find if the symbol already exists in the table
            row_exists = -1
            for row in range(self.stock_table.rowCount()):
                if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == symbol:
                    row_exists = row
                    break

            # Use watchlist URL format
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers)
            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                quote = result['indicators']['quote'][0]

                # Get open price with aggressive fallback logic
                open_price = meta.get('regularMarketOpen', 0)
                if open_price == 0 or open_price is None:
                    # Try to get from quote data
                    if 'open' in quote and len(quote['open']) > 0:
                        valid_opens = [o for o in quote['open'] if o is not None and o > 0]
                        if valid_opens:
                            open_price = valid_opens[-1]  # Use the most recent valid open

                    # If still zero, try previous close
                    if open_price == 0 or open_price is None:
                        open_price = meta.get('chartPreviousClose', 0)

                    # If still zero, use current price as last resort
                    if open_price == 0 or open_price is None:
                        open_price = meta.get('regularMarketPrice', 0)

                # Print debug info
                print(f"Symbol: {symbol}, Open price: {open_price}")

                # Use meta data like in watchlist
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('chartPreviousClose', 0)

                # Fallback
                if prev_close == 0 and len(quote['close']) > 1:
                    prev_close = quote['close'][-2]

                # Calculate changes
                price_change = current_price - prev_close
                percent_change = (price_change / prev_close) * 100 if prev_close else 0

                try:
                    from database import DatabaseConnection
                    db_conn = DatabaseConnection()
                    db_conn.save_stock_data(
                        symbol=symbol,
                        current_price=current_price,
                        open_price=open_price,
                        high_price=meta.get('regularMarketDayHigh', current_price),
                        low_price=meta.get('regularMarketDayLow', current_price),
                        volume=int(meta.get('regularMarketVolume', 0)),
                        change_percentage=percent_change
                    )
                except Exception as db_error:
                    print(f"Error saving stock data to database: {db_error}")

                # Add a new row or update existing
                if row_exists == -1:
                    row_position = self.stock_table.rowCount()
                    self.stock_table.insertRow(row_position)
                else:
                    row_position = row_exists

                # Update table with data
                self.stock_table.setItem(row_position, 0, QTableWidgetItem(symbol))
                # KEY CHANGE: Use our enhanced open_price value
                self.stock_table.setItem(row_position, 1, QTableWidgetItem(f"₹{open_price:.2f}"))
                self.stock_table.setItem(row_position, 2, QTableWidgetItem(f"₹{current_price:.2f}"))
                self.stock_table.setItem(row_position, 3,
                                         QTableWidgetItem(f"₹{meta.get('regularMarketDayHigh', current_price):.2f}"))
                self.stock_table.setItem(row_position, 4,
                                         QTableWidgetItem(f"₹{meta.get('regularMarketDayLow', current_price):.2f}"))
                self.stock_table.setItem(row_position, 5,
                                         QTableWidgetItem(f"{int(meta.get('regularMarketVolume', 0)):,}"))

                # Format change with plus/minus and color
                percent_str = f"{'+' if percent_change >= 0 else ''}{percent_change:.2f}%"
                change_item = QTableWidgetItem(percent_str)
                change_item.setForeground(Qt.GlobalColor.green if percent_change >= 0 else Qt.GlobalColor.red)
                self.stock_table.setItem(row_position, 6, change_item)

                # Add "Add" button with dropdown
                add_btn = AddStockButton(symbol, self)
                self.stock_table.setCellWidget(row_position, 7, add_btn)

                print(f"Successfully loaded {symbol}")

        except Exception as e:
            print(f"Error loading stock {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()

        # Schedule next stock with delay
        QTimer.singleShot(1500, lambda: self.process_next_stock(index + 1))

    def create_main_content(self):
        self.main_content = QWidget()  # Use QWidget instead of QStackedWidget for simplicity
        self.main_content.setStyleSheet("""
            background-color: #f5f5f5;
            padding: 20px;
        """)

        # Create layout for main content
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setSpacing(20)

        # Add market summary cards
        summary_cards = self.create_market_summary()
        main_layout.addWidget(summary_cards)

        # Add market overview directly (no filter bar)
        market_overview = self.create_market_overview_page()
        main_layout.addWidget(market_overview)

        # Add some space at the bottom to ensure scrolling works properly
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(spacer)

        # Initialize with market overview data
        self.fetch_stock_data()

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #041E42;
                color: white;
                padding: 5px;
            }
            QMenuBar::item {
                padding: 5px 10px;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #0F2E5A;
            }
            QMenu {
                background-color: white;
                color: #041E42;
                border: 1px solid #ddd;
            }
            QMenu::item:selected {
                background-color: #f0f0f0;
            }
        """)

        # File Menu
        file_menu = menubar.addMenu('File')
        export_action = QAction('Export Data', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        file_menu.addAction('AboutUs')
        file_menu.addSeparator()
        file_menu.addAction('Logout')

        # View Menu
        view_menu = menubar.addMenu('View')
        view_menu.addAction('Dark Mode')
        view_menu.addAction('Full Screen')

        # Tools Menu
        tools_menu = menubar.addMenu('Tools')
        tools_menu.addAction('Set Alerts')
        tools_menu.addAction('Calculator')
        tools_menu.addAction('Notes')

        # Help Menu
        help_menu = menubar.addMenu('Help')
        help_menu.addAction('Documentation')
        help_menu.addAction('About')

    def export_data(self):
        # Get the current time for the filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_data_{current_time}.csv"

        try:
            # Create a list to store the data
            data = []
            for row in range(self.stock_table.rowCount()):
                row_data = []
                for col in range(self.stock_table.columnCount()):
                    item = self.stock_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Convert to DataFrame and save
            df = pd.DataFrame(data, columns=['Stock', 'Open', 'Close', 'High', 'Low', 'Volume', '% Change'])
            df.to_csv(filename, index=False)
            self.statusBar().showMessage(f'Data exported successfully to {filename}')
        except Exception as e:
            self.statusBar().showMessage(f'Error exporting data: {str(e)}')

    def create_tool_bar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: white;
                border-bottom: 1px solid #ddd;
                padding: 5px;
            }
        """)
        self.addToolBar(toolbar)

        # Add search bar
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(10, 0, 10, 0)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Search stocks (e.g., TCS.NS, SBIN.NS)')
        self.search_bar.setFixedWidth(1500)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
        """)

        # Add a search button
        search_button = QPushButton('Search')
        search_button.clicked.connect(lambda: self.perform_stock_search(self.search_bar.text()))

        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(search_button)
        search_layout.addStretch()

        toolbar.addWidget(search_widget)

    def create_market_overview_page(self):
        page_widget = QFrame()
        page_layout = QVBoxLayout(page_widget)

        # Add page title
        title = QLabel('Market Overview')
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title.setStyleSheet('color: #041E42; margin-bottom: 20px;')

        # Add refresh button and last updated label
        refresh_container = QHBoxLayout()

        refresh_button = QPushButton('Refresh Data')
        refresh_button.clicked.connect(self.fetch_stock_data)
        refresh_button.setMaximumWidth(200)

        self.last_updated_label = QLabel('Last Updated: Never')
        self.last_updated_label.setStyleSheet('color: #666; margin-left: 20px;')

        refresh_container.addWidget(refresh_button)
        refresh_container.addWidget(self.last_updated_label)
        refresh_container.addStretch()

        # Create table widget with an extra column for "Add to Analytics" button
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(8)  # Added an extra column for the button
        self.stock_table.setHorizontalHeaderLabels(
            ['Stock', 'Open', 'Close', 'High', 'Low', 'Volume', '% Change', 'Actions'])

        # Set table properties
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(7,
                                                                 QHeaderView.ResizeMode.ResizeToContents)  # For the action column
        self.stock_table.setStyleSheet("""
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
            QTableWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
        """)

        # Set increased minimum height to ensure scrollability
        self.stock_table.setMinimumHeight(600)  # Increased from 400 to 600

        # Add widgets to layout
        page_layout.addWidget(title)
        page_layout.addLayout(refresh_container)
        page_layout.addWidget(self.stock_table)

        return page_widget


    def fetch_stock_data(self, symbol=None):
        try:
            # Validate and format symbol
            if not symbol or not isinstance(symbol, str):
                self.statusBar().showMessage('Invalid stock symbol')
                return

            symbol = symbol.strip().upper()
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            # Use the same URL approach as in the watchlist
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers)
            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                quote = result['indicators']['quote'][0]

                # Get current data - use the meta.regularMarketPrice like in watchlist
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('chartPreviousClose', 0)

                # Add the fallback just like in watchlist
                if prev_close == 0 and len(quote['close']) > 1:
                    prev_close = quote['close'][-2]

                # Calculate changes - exactly as in watchlist
                price_change = current_price - prev_close
                percent_change = (price_change / prev_close) * 100 if prev_close else 0

                # Debug output
                print(
                    f"{symbol} Price: {current_price}, Prev: {prev_close}, Change: {price_change}, %Change: {percent_change}%")

                # Find or create row (keep your existing row handling)
                row_position = -1
                for row in range(self.stock_table.rowCount()):
                    if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == symbol:
                        self.stock_table.removeRow(row)
                        break

                # Insert at top
                self.stock_table.insertRow(0)
                row_position = 0

                # Update table cells
                self.stock_table.setItem(row_position, 0, QTableWidgetItem(symbol))
                self.stock_table.setItem(row_position, 1, QTableWidgetItem(f"₹{meta.get('regularMarketOpen', 0):.2f}"))
                self.stock_table.setItem(row_position, 2, QTableWidgetItem(f"₹{current_price:.2f}"))
                self.stock_table.setItem(row_position, 3,
                                         QTableWidgetItem(f"₹{meta.get('regularMarketDayHigh', 0):.2f}"))
                self.stock_table.setItem(row_position, 4,
                                         QTableWidgetItem(f"₹{meta.get('regularMarketDayLow', 0):.2f}"))
                self.stock_table.setItem(row_position, 5,
                                         QTableWidgetItem(f"{int(meta.get('regularMarketVolume', 0)):,}"))

                # Format the change percent like in watchlist
                percent_str = f"{'+' if percent_change >= 0 else ''}{percent_change:.2f}%"
                change_item = QTableWidgetItem(percent_str)

                # Set color
                if percent_change > 0:
                    change_item.setForeground(Qt.GlobalColor.green)
                elif percent_change < 0:
                    change_item.setForeground(Qt.GlobalColor.red)
                else:
                    change_item.setForeground(Qt.GlobalColor.black)

                self.stock_table.setItem(row_position, 6, change_item)

                # Update timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.last_updated_label.setText(f'Last Updated: {current_time}')
                self.statusBar().showMessage(f'Data updated for {symbol}')


            else:
                self.statusBar().showMessage(f'No data available for {symbol}')

        except Exception as e:
            print(f"Error in fetch_stock_data: {str(e)}")
            self.statusBar().showMessage(f'Error fetching data: {str(e)}')
            import traceback
            traceback.print_exc()

            # Update table cells
            self.stock_table.setItem(row_position, 0, QTableWidgetItem(symbol))

            # Add fallback logic for open price
            open_price = meta.get('regularMarketOpen', 0)
            if open_price == 0:
                # Try previous close as fallback
                open_price = meta.get('previousClose', 0)
                # If still zero, try from quote data
                if open_price == 0 and 'open' in quote and len(quote['open']) > 0:
                    open_price = next((x for x in quote['open'] if x is not None), 0)

            self.stock_table.setItem(row_position, 1, QTableWidgetItem(f"₹{open_price:.2f}"))


    def filter_stocks(self, search_text):
        try:
            # Ensure search_text is a string
            search_text = str(search_text).strip()

            # Cancel any pending timer
            if self.current_search_timer is not None:
                self.current_search_timer.stop()

            # Create new timer for debouncing
            self.current_search_timer = QTimer()
            self.current_search_timer.setSingleShot(True)
            self.current_search_timer.timeout.connect(lambda: self.perform_stock_search(search_text))
            self.current_search_timer.start(1000)  # Wait 1 second before searching
        except Exception as e:
            self.statusBar().showMessage(f'Error in filter_stocks: {str(e)}')

            # After this line: data = response.json()
            print(f"\nDEBUG - Response for {symbol}:")
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                quote = result['indicators']['quote'][0]
                print(f"Available meta keys: {meta.keys()}")
                print(f"regularMarketOpen: {meta.get('regularMarketOpen')}")
                print(f"previousClose: {meta.get('previousClose')}")
                print(f"chartPreviousClose: {meta.get('chartPreviousClose')}")
                if 'open' in quote:
                    print(f"quote open values: {quote['open']}")

    # In StockDashboard class, modify the update_stock_table method:

    def update_stock_table(self, stock_data):
        """Thread-safe update of the stock table"""
        try:
            from PyQt6.QtCore import QTimer, Qt

            # Debug output to verify data
            print(f"Received data for {stock_data['symbol']}:")
            print(f"  - Open: {stock_data['open']}")
            print(f"  - Close: {stock_data['current_price']}")
            print(f"  - High: {stock_data['high']}")
            print(f"  - Low: {stock_data['low']}")

            def update_ui():
                # Find or create row for the stock
                row_position = -1
                for row in range(self.stock_table.rowCount()):
                    if (self.stock_table.item(row, 0) and
                            self.stock_table.item(row, 0).text() == stock_data['symbol']):
                        row_position = row
                        break

                # If row not found, insert new row
                if row_position == -1:
                    self.stock_table.insertRow(0)
                    row_position = 0

                # CRITICAL FIX: Force a valid open price
                open_price = stock_data['open']
                if open_price == 0 or open_price is None:
                    # Try using prev_close as fallback
                    open_price = stock_data.get('prev_close', 0)
                    # If still zero, use current price
                    if open_price == 0 or open_price is None:
                        open_price = stock_data['current_price']

                # Update table cells with explicit conversions to avoid type issues
                self.stock_table.setItem(row_position, 0, QTableWidgetItem(str(stock_data['symbol'])))
                self.stock_table.setItem(row_position, 1, QTableWidgetItem(f"₹{float(open_price):.2f}"))
                self.stock_table.setItem(row_position, 2,
                                         QTableWidgetItem(f"₹{float(stock_data['current_price']):.2f}"))
                self.stock_table.setItem(row_position, 3, QTableWidgetItem(f"₹{float(stock_data['high']):.2f}"))
                self.stock_table.setItem(row_position, 4, QTableWidgetItem(f"₹{float(stock_data['low']):.2f}"))
                self.stock_table.setItem(row_position, 5, QTableWidgetItem(f"{int(stock_data['volume']):,}"))

                # Format change percent
                percent_change = float(stock_data['percent_change'])
                percent_str = f"{'+' if percent_change >= 0 else ''}{percent_change:.2f}%"
                change_item = QTableWidgetItem(percent_str)

                # Set color based on change
                if percent_change > 0:
                    change_item.setForeground(Qt.GlobalColor.green)
                elif percent_change < 0:
                    change_item.setForeground(Qt.GlobalColor.red)
                else:
                    change_item.setForeground(Qt.GlobalColor.black)

                self.stock_table.setItem(row_position, 6, change_item)

                # Add button in the last column
                add_btn = AddStockButton(stock_data['symbol'], self)
                self.stock_table.setCellWidget(row_position, 7, add_btn)

                # Update timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(self, 'last_updated_label'):
                    self.last_updated_label.setText(f'Last Updated: {current_time}')

            # Schedule the UI update on the main thread
            QTimer.singleShot(0, update_ui)

        except Exception as e:
            print(f"Error updating stock table: {str(e)}")
            import traceback
            traceback.print_exc()

    def perform_stock_search(self, search_text):
        try:
            # Validate search text
            if not isinstance(search_text, str) or len(search_text.strip()) < 1:
                return

            search_text = str(search_text).upper().strip()
            self.statusBar().showMessage(f'Searching for {search_text}...')

            # Handle both NSE and international stocks
            if not (search_text.endswith('.NS') or search_text.endswith('.BO')):
                symbol = f"{search_text}.NS"  # Try NSE first
            else:
                symbol = search_text

            # Fetch stock data
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers)
            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                quote = result['indicators']['quote'][0]

                # Use meta data
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('chartPreviousClose', 0)

                # Fallback
                if prev_close == 0 and len(quote['close']) > 1:
                    prev_close = quote['close'][-2]

                # Calculate changes
                price_change = current_price - prev_close
                percent_change = (price_change / prev_close) * 100 if prev_close else 0

                # Find or create row
                row_position = -1
                for row in range(self.stock_table.rowCount()):
                    if self.stock_table.item(row, 0) and self.stock_table.item(row, 0).text() == symbol:
                        self.stock_table.removeRow(row)
                        break

                # Insert at top
                self.stock_table.insertRow(0)
                row_position = 0

                # Update table cells
                self.stock_table.setItem(row_position, 0, QTableWidgetItem(symbol))
                self.stock_table.setItem(row_position, 1, QTableWidgetItem(f"₹{meta.get('regularMarketOpen', 0):.2f}"))
                self.stock_table.setItem(row_position, 2, QTableWidgetItem(f"₹{current_price:.2f}"))
                self.stock_table.setItem(row_position, 3,
                                         QTableWidgetItem(f"₹{meta.get('regularMarketDayHigh', 0):.2f}"))
                self.stock_table.setItem(row_position, 4,
                                         QTableWidgetItem(f"₹{meta.get('regularMarketDayLow', 0):.2f}"))
                self.stock_table.setItem(row_position, 5,
                                         QTableWidgetItem(f"{int(meta.get('regularMarketVolume', 0)):,}"))

                # Format the change percent
                percent_str = f"{'+' if percent_change >= 0 else ''}{percent_change:.2f}%"
                change_item = QTableWidgetItem(percent_str)

                # Set color
                if percent_change > 0:
                    change_item.setForeground(Qt.GlobalColor.green)
                elif percent_change < 0:
                    change_item.setForeground(Qt.GlobalColor.red)
                else:
                    change_item.setForeground(Qt.GlobalColor.black)

                self.stock_table.setItem(row_position, 6, change_item)

                # Add the "Add" button with dropdown menu
                add_btn = AddStockButton(symbol, self)

                # Set the button in the cell
                self.stock_table.setCellWidget(row_position, 7, add_btn)

                # Update timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.last_updated_label.setText(f'Last Updated: {current_time}')
                self.statusBar().showMessage(f'Data updated for {symbol}')

                # Update TA dashboard if needed
                if hasattr(self, 'ta_dashboard'):
                    self.update_ta_dashboard(symbol)
                    self.ta_dashboard.setVisible(True)

            else:
                self.statusBar().showMessage(f'No data available for {symbol}')

        except Exception as e:
            print(f"Error in perform_stock_search: {str(e)}")
            self.statusBar().showMessage(f'Error fetching data: {str(e)}')
            import traceback
            traceback.print_exc()

    def start_auto_update(self):
        # self.update_timer = QTimer()
        # self.update_timer.timeout.connect(self.update_displayed_stocks)
        # self.update_timer.start(60000)  # Update every minute - NSEpy has better rate limits
        pass

    def update_all_data(self):
        """Update all market data with rate limiting"""
        # First update indices
        self.fetch_market_indices()

        # Then update displayed stocks
        self.update_displayed_stocks()

    def add_stock_to_analytics(self, symbol):
        """Add a stock to the analytics page with improved error handling"""
        try:
            # Validate input
            if not symbol:
                QMessageBox.warning(self, "Error", "Invalid stock symbol")
                return

            # Ensure proper symbol format for NSE stocks
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"

            # Check if analytics window exists and is properly initialized
            if not hasattr(self, 'analytics_window') or self.analytics_window is None:
                QMessageBox.warning(self, "Error", "Analytics window not initialized")
                return

            # Check if analytics_window has the stocks_list attribute initialized
            if not hasattr(self.analytics_window, 'stocks_list'):
                self.analytics_window.stocks_list = []

            # Show status message indicating we're processing
            self.statusBar().showMessage(f'Adding {symbol} to Analytics...', 2000)

            # First, show the analytics window
            self.analytics_window.show()
            self.analytics_window.raise_()
            self.analytics_window.activateWindow()

            # Then add the stock to analytics
            self.analytics_window.add_stock(symbol)

            # Show success message
            self.statusBar().showMessage(f'Added {symbol} to Analytics successfully', 3000)

        except Exception as e:
            print(f"Error adding stock to analytics: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "Error",
                f"Could not add {symbol} to analytics. Please verify the symbol and try again.\n\nError: {str(e)}"
            )

    def create_statistics_cards(self):
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setSpacing(20)

        stats = [
            {"icon": "📈", "title": "NIFTY 50", "value": "19,750", "change": "+1.2%"},
            {"icon": "💰", "title": "Market Cap", "value": "₹2.5T", "change": "+0.8%"},
            {"icon": "📊", "title": "Volume", "value": "1.2B", "change": "+15%"},
            {"icon": "🌟", "title": "Top Gainer", "value": "TATASTEEL", "change": "+4.5%"}
        ]

        for stat in stats:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: white;
                    border-radius: 15px;
                    padding: 15px;
                    min-width: 200px;
                }
                QFrame:hover {
                    background: #f8f9fa;
                }
            """)

            layout = QVBoxLayout(card)

            header = QLabel(f"{stat['icon']} {stat['title']}")
            header.setStyleSheet("font-size: 14px; color: #666;")

            value = QLabel(stat['value'])
            value.setStyleSheet("font-size: 24px; font-weight: bold; color: #041E42;")

            change = QLabel(stat['change'])
            change.setStyleSheet("color: #28a745; font-weight: bold;")

            layout.addWidget(header)
            layout.addWidget(value)
            layout.addWidget(change)

            cards_layout.addWidget(card)

        return cards_widget

    def setup_table_style(self):
        self.stock_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 15px;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                border-radius: 0px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 15px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 15px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #041E42;
            }
        """)

    def create_quick_actions(self):
        actions_widget = QFrame()
        actions_widget.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 15px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)

        layout = QHBoxLayout(actions_widget)

        actions = [
            ("📥 Export", self.export_data),
            ("🔄 Refresh", self.fetch_stock_data),
            ("⭐ Favorites", lambda: None),
            ("🔔 Set Alert", lambda: None)
        ]

        for text, callback in actions:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 20px;
                    padding: 8px 15px;
                    color: #333;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #e9ecef;
                }
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()
        return actions_widget

    def update_displayed_stocks(self):
        """Update all displayed stocks with rate limiting"""
        for row in range(self.stock_table.rowCount()):
            try:
                symbol = self.stock_table.item(row, 0).text()
                self.fetch_stock_data(symbol)
                time.sleep(5)  # Wait 5 seconds between updates to avoid rate limits
            except Exception as e:
                print(f"Error updating stock {symbol}: {str(e)}")
                continue

    def create_main_content(self):
        self.main_content = QStackedWidget()
        self.main_content.setStyleSheet("""
            QStackedWidget {
                background-color: #f5f5f5;
                padding: 20px;
            }
        """)

        # Create the market overview page
        market_page = QWidget()
        market_layout = QVBoxLayout(market_page)
        market_layout.setSpacing(20)  # Add space between elements

        # Add market summary cards
        summary_cards = self.create_market_summary()
        market_layout.addWidget(summary_cards)

        # Add simplified filter bar with only refresh button
        # filter_bar = self.create_filter_bar()
        # market_layout.addWidget(filter_bar)

        # Add market overview page
        market_overview = self.create_market_overview_page()
        market_layout.addWidget(market_overview)

        # Add the market page to the stacked widget
        self.main_content.addWidget(market_page)

        # Initialize with market overview
        self.fetch_stock_data()

    def create_market_summary(self):
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)

        self.summary_layout = QHBoxLayout(summary_frame)
        self.summary_layout.setSpacing(15)

        # Create summary cards (removed Market Cap)
        # In create_market_summary, change the initial values
        cards_info = [
            {"title": "NIFTY 50", "value": "Loading...", "change": "0.00%", "color": "#28a745"},
            {"title": "SENSEX", "value": "Loading...", "change": "0.00%", "color": "#28a745"},
            {"title": "BANK NIFTY", "value": "Loading...", "change": "0.00%", "color": "#28a745"}
        ]

        for info in cards_info:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 15px;
                }}
                QFrame:hover {{
                    background-color: #f8f9fa;
                }}
            """)

            card_layout = QVBoxLayout(card)

            title = QLabel(info["title"])
            title.setStyleSheet("color: #666; font-size: 14px;")

            value = QLabel(info["value"])
            value.setStyleSheet("font-size: 20px; font-weight: bold; color: #041E42;")

            change = QLabel(info["change"])
            change.setStyleSheet(f"color: {info['color']}; font-weight: bold;")

            card_layout.addWidget(title)
            card_layout.addWidget(value)
            card_layout.addWidget(change)

            self.summary_layout.addWidget(card)

        return summary_frame


    # In start_market_indices_update
    def start_market_indices_update(self):
        """Start periodic updates for market indices"""
        self.market_indices_timer = QTimer()
        self.market_indices_timer.timeout.connect(self.fetch_market_indices)
        self.market_indices_timer.start(60000)  # Update every minute
        print("DEBUG: Market indices update timer started")

    def fetch_market_indices(self):
        """
        Fetch and update market indices in summary cards using watchlist approach
        """
        try:
            indices = [
                ("^NSEI", "NIFTY 50"),  # Nifty 50 index
                ("^BSESN", "SENSEX"),  # Sensex index
                ("^NSEBANK", "BANK NIFTY")  # Bank Nifty index
            ]

            for symbol, title in indices:
                try:
                    # Use same URL format as watchlist
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }

                    response = requests.get(url, headers=headers)
                    data = response.json()

                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        meta = result['meta']
                        quote = result['indicators']['quote'][0]

                        # Get current price and previous close like in watchlist
                        current_price = meta.get('regularMarketPrice', 0)
                        prev_close = meta.get('chartPreviousClose', 0)

                        # Fallback like in watchlist
                        if prev_close == 0 and len(quote['close']) > 1:
                            prev_close = quote['close'][-2]

                        # Calculate change percentage
                        price_change = current_price - prev_close
                        change_percent = (price_change / prev_close) * 100 if prev_close else 0

                        print(f"Index {title}: Current: {current_price}, Prev: {prev_close}, Change: {change_percent}%")

                        # Update the market summary card
                        self.update_market_summary_card(title, current_price, change_percent)

                except Exception as e:
                    print(f"Error fetching {title} data: {str(e)}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"Error in fetch_market_indices: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_market_summary_card(self, title, value, change_percent):
        """
        Update a specific market summary card with new data
        """
        print(f"DEBUG: Updating {title} card with change {change_percent:.2f}%")

        for i in range(self.summary_layout.count()):
            card_frame = self.summary_layout.itemAt(i).widget()
            if card_frame:
                card_layout = card_frame.layout()
                title_widget = card_layout.itemAt(0).widget()

                if title_widget and title_widget.text() == title:
                    # Update the value (second widget)
                    value_widget = card_layout.itemAt(1).widget()
                    if value_widget:
                        value_widget.setText(f"{value:,.2f}")

                    # Update the change percentage (third widget)
                    change_widget = card_layout.itemAt(2).widget()
                    if change_widget:
                        # Make sure we're setting the actual calculated percentage
                        change_widget.setText(f"{change_percent:+.2f}%")

                        # Set color based on value
                        color = "#28a745" if change_percent >= 0 else "#dc3545"
                        change_widget.setStyleSheet(f"color: {color}; font-weight: bold;")

                    break

    def calculate_market_cap(self):
        """
        Calculate the total market cap of top stocks and update the Market Cap card
        """
        try:
            total_market_cap = 0

            # Use yfinance to get market cap data for top stocks
            for symbol in self.top_stocks[:5]:  # Use first 5 stocks to avoid rate limiting
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    market_cap = info.get('marketCap', 0)
                    total_market_cap += market_cap
                except Exception as e:
                    print(f"Error getting market cap for {symbol}: {str(e)}")

            # Convert to trillions for display
            market_cap_trillion = total_market_cap / 1e12

            # Assume ~20% for top 5 stocks, estimate total
            estimated_total = market_cap_trillion * 5

            # Update the market cap card
            current_time = datetime.now()
            change_percent = 2.1  # Default percentage, could be calculated dynamically

            self.update_market_summary_card("Market Cap", estimated_total, change_percent)

        except Exception as e:
            print(f"Error calculating market cap: {str(e)}")

    # Add these methods to your StockDashboard class

    def connect_side_nav_buttons(self):
        """Connect side navigation buttons to their respective actions"""
        # Get all buttons in the side_nav
        buttons = self.side_nav.findChildren(QPushButton)

        # Connect each button to its action based on text
        for button in buttons:
            text = button.text()
            if text == 'Logout':
                button.clicked.connect(self.handle_logout)
            elif text == 'Market Overview':
                button.clicked.connect(self.show_market_overview)
            elif text == 'Portfolio':
                button.clicked.connect(self.show_portfolio_window)
            elif text == 'Watchlist':
                button.clicked.connect(self.show_watchlist_window)
            elif text == 'Analytics':
                button.clicked.connect(self.show_analytics_window)
            elif text == 'Reports':
                button.clicked.connect(self.show_reports_window)
            elif text == 'News Feed':
                button.clicked.connect(self.show_news_feed_window)
            elif text == 'About Us':
                button.clicked.connect(self.show_aboutus_window)

            print(f"[DEBUG] Connected button '{text}'")

    def show_market_overview(self):
        """Show the main dashboard/market overview"""
        self.statusBar().showMessage('Showing Market Overview...')
        # Just activate the current window since we're already on the dashboard
        self.show()
        self.raise_()
        self.activateWindow()

    def show_portfolio_window(self):
        """Show the portfolio window"""
        self.statusBar().showMessage('Navigating to Portfolio...')
        self.hide()  # Hide the dashboard
        self.portfolio_window.show()
        self.portfolio_window.showMaximized()
        self.portfolio_window.raise_()
        self.portfolio_window.activateWindow()

    def show_watchlist_window(self):
        """Show the watchlist window"""
        self.statusBar().showMessage('Navigating to Watchlist...')
        self.hide()  # Hide the dashboard
        self.watchlist_window.show()
        self.watchlist_window.showMaximized()
        self.watchlist_window.raise_()
        self.watchlist_window.activateWindow()

    def show_analytics_window(self):
        """Show the analytics window"""
        self.statusBar().showMessage('Navigating to Analytics...')
        self.hide()  # Hide the dashboard
        self.analytics_window.show()
        self.analytics_window.showMaximized()
        self.analytics_window.raise_()
        self.analytics_window.activateWindow()

    def show_reports_window(self):
        """Show the reports window"""
        self.statusBar().showMessage('Navigating to Reports...')
        self.hide()  # Hide the dashboard
        self.reports_window.show()
        self.reports_window.showMaximized()
        self.reports_window.raise_()
        self.reports_window.activateWindow()

    def show_news_feed_window(self):
        """Show the news feed window"""
        self.statusBar().showMessage('Navigating to News Feed...')
        self.hide()  # Hide the dashboard
        self.news_feed_window.show()
        self.watchlist_window.showMaximized()
        self.news_feed_window.raise_()
        self.news_feed_window.activateWindow()

    def show_settings_window(self):
        """Show the settings window"""
        self.statusBar().showMessage('Navigating to Settings...')
        self.hide()  # Hide the dashboard
        self.settings_window.show()
        self.watchlist_window.showMaximized()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def connect_window_signals(self):
        """Connect signals for all navigation windows to return to dashboard"""
        windows = [
            self.portfolio_window,
            self.watchlist_window,
            self.analytics_window,
            self.reports_window,
            self.news_feed_window,
            self.settings_window
        ]

        for window in windows:
            try:
                # Disconnect any existing connections to avoid duplicates
                try:
                    window.switch_to_dashboard.disconnect()
                except TypeError:
                    pass  # No connections to disconnect

                # Connect the signal
                window.switch_to_dashboard.connect(self.show)
                print(f"[DEBUG] Connected {window.__class__.__name__} signal to dashboard")
            except Exception as e:
                print(f"[ERROR] Failed to connect window signal: {e}")

    def handle_nav_click(self, button_text):
        # Handle navigation button clicks
        self.statusBar().showMessage(f'Navigating to {button_text}...')
        # Currently only showing Market Overview
        # Add more pages and navigation logic as needed

    def handle_logout(self):
        """Handle logout functionality"""
        from PyQt6.QtWidgets import QMessageBox

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            'Logout Confirmation',
            'Are you sure you want to logout?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Close the dashboard
            self.close()

            # Create and show login window
            from login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()

    def create_side_nav(self):
        self.side_nav = QFrame()
        self.side_nav.setFixedWidth(250)
        self.side_nav.setStyleSheet("""
            QFrame {
                background-color: #041E42;
                border-radius: 0px;
            }
            QPushButton {
                text-align: left;
                padding: 15px 20px;
                border-radius: 0px;
                background-color: transparent;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            #logoutButton {
                text-align: center;
                background-color: #8B0000;
                border-radius: 5px;
                margin: 10px 20px;
                font-weight: bold;
            }
            #logoutButton:hover {
                background-color: #A52A2A;
            }
        """)

        nav_layout = QVBoxLayout(self.side_nav)
        nav_layout.setSpacing(0)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        # Use the self.nav_buttons list defined in __init__ instead of hardcoding
        for button_text in self.nav_buttons:
            button = QPushButton(button_text)
            button.clicked.connect(lambda checked, text=button_text: self.handle_nav_click(text))
            nav_layout.addWidget(button)

        nav_layout.addStretch()  # Push logout to bottom

        # Add logout button
        logout_button = QPushButton('Logout')
        logout_button.setObjectName('logoutButton')
        logout_button.clicked.connect(self.handle_logout)
        nav_layout.addWidget(logout_button)

    def init_navigation_windows(self):
        """
        Initialize all navigation windows with user_id
        """
        from navigation_windows import (
            PortfolioWindow, WatchlistWindow,
            AnalyticsWindow, ReportsWindow, NewsFeedWindow, AboutUsWindow
        )

        # Pass user_id to each window that needs it
        self.portfolio_window = PortfolioWindow(user_id=self.user_id)
        self.watchlist_window = WatchlistWindow(user_id=self.user_id)
        self.analytics_window = AnalyticsWindow(user_id=self.user_id)
        self.reports_window = ReportsWindow()
        self.news_feed_window = NewsFeedWindow()
        self.aboutus_window = AboutUsWindow()

        # Connect each window's switch to dashboard signal
        self.connect_window_signals()

    def connect_window_signals(self):
        """
        Connect signals for all navigation windows
        """
        windows = [
            self.portfolio_window,
            self.watchlist_window,
            self.analytics_window,
            self.reports_window,
            self.news_feed_window,
            self.aboutus_window
        ]

        for window in windows:
            window.switch_to_dashboard.connect(self.show)

    def connect_side_nav_buttons(self):
        self.nav_actions = {
            'Market Overview': lambda: self.show_market_overview(),
            'Portfolio': lambda: self.show_portfolio_window(),
            'Watchlist': lambda: self.show_watchlist_window(),
            'Analytics': lambda: self.show_analytics_window(),
            'Reports': lambda: self.show_reports_window(),
            'News Feed': lambda: self.show_news_feed_window(),
            'About Us': lambda: self.show_aboutus_window()  # Changed 'AboutUs' to 'About Us'
        }

        for button_text in self.nav_buttons:
            button = self.side_nav.findChild(QPushButton, button_text)
            if button:
                button.clicked.connect(lambda _, text=button_text: self.handle_nav_click(text))

    def handle_nav_click(self, button_text):
        print(f"[DEBUG] Navigation clicked: {button_text}")
        self.statusBar().showMessage(f'Navigating to {button_text}...')

        if button_text in self.nav_actions:
            try:
                self.nav_actions[button_text]()
            except Exception as e:
                print(f"[ERROR] Navigation action failed: {e}")



