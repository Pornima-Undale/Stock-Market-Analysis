from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHBoxLayout, QLineEdit, QFrame, QHeaderView,
                             QMessageBox, QStatusBar, QSizePolicy, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import requests
import yfinance as yf
from datetime import datetime
from database import DatabaseConnection
import mysql.connector
from mysql.connector import Error

from navigation_windows import BaseNavigationWindow


class StyledLabel(QLabel):
    def __init__(self, text, font_size=10, bold=False, color=None):
        super().__init__(text)
        font = QFont('Segoe UI', font_size)
        if bold:
            font.setBold(True)
        self.setFont(font)
        if color:
            self.setStyleSheet(f'color: {color};')


class WatchlistWindow(BaseNavigationWindow):
    switch_to_dashboard = pyqtSignal()

    def __init__(self, title="watchlist", user_id=None):
        super().__init__(title, user_id=user_id)
        self.setWindowTitle('SARASFINTECH - Watchlist')
        self.setMinimumSize(1400, 900)

        self.setup_database()

        # Enhanced styling with smaller text
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QFrame.card {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            QFrame.header-card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #041E42, stop:1 #0A3A7A);
                border-radius: 10px;
                color: white;
            }
            QPushButton {
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                background-color: #041E42;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            QPushButton.accent-btn {
                background-color: #1565C0;
            }
            QPushButton.accent-btn:hover {
                background-color: #0D47A1;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #1565C0;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #f0f0f0;
                selection-background-color: #E3F2FD;
                font-size: 11px;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #041E42, stop:1 #0A3A7A);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: black;
            }
            QPushButton#removeBtn {
                background-color: #dc3545;
                padding: 4px 8px;
                font-size: 11px;
                max-width: 70px;
            }
            QPushButton#removeBtn:hover {
                background-color: #bb2d3b;
            }
            QLabel {
                font-size: 12px;
            }
        """)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(60000)  # Refresh every minute

        # Initialize watchlist data with default stocks
        self.watchlist_data = [
            ['RELIANCE.NS', '₹0.00', '₹0.00', '0.00%', '0', '0 Cr', ''],
            ['TCS.NS', '₹0.00', '₹0.00', '0.00%', '0', '0 Cr', ''],
            ['HDFCBANK.NS', '₹0.00', '₹0.00', '0.00%', '0', '0 Cr', '']
        ]

        # Initialize empty watchlist data
        self.watchlist_data = []

        # Create the UI
        self.setup_ui()

        # Load data from database
        self.load_watchlist_from_db()
        if not self.watchlist_data:
            self.watchlist_data = [
                ['RELIANCE.NS', '₹0.00', '₹0.00', '0.00%', '0', '0 Cr', ''],
                ['TCS.NS', '₹0.00', '₹0.00', '0.00%', '0', '0 Cr', ''],
                ['HDFCBANK.NS', '₹0.00', '₹0.00', '0.00%', '0', '0 Cr', '']
            ]
            self.update_watchlist_table()

        # Create the UI
        self.setup_ui()

        # Initial data load
        self.fetch_real_data()



    def setup_ui(self):
        # Create central widget
        central_widget = QWidget()

        # Create main layout with zero margins
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create a scroll area as the main container (like in dashboard)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create a widget to hold the scrollable content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Header section with title - using gradient background
        header_frame = QFrame()
        header_frame.setObjectName("header-card")
        header_frame.setProperty("class", "header-card")
        header_frame.setMinimumHeight(80)  # Reduced height
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)  # Reduced padding

        # Title and summary row
        title_row = QHBoxLayout()

        # Title with white text on gradient background (smaller font)
        title = QLabel('Watchlist Dashboard')
        title.setFont(QFont('Arial', 20, QFont.Weight.Bold))  # Smaller font
        title.setStyleSheet('color: white;')
        title_row.addWidget(title)

        # Add spacer to push stats to the right
        title_row.addStretch()

        # Stats section with smaller font
        self.stats_layout = QHBoxLayout()
        self.total_stocks_label = QLabel(f'Total Stocks: {len(self.watchlist_data)}')
        self.total_stocks_label.setStyleSheet('color: white; font-size: 12px;')

        # Last updated time label
        self.last_update_label = QLabel('Last Updated: Never')
        self.last_update_label.setStyleSheet('color: #BBDEFB; font-size: 12px; margin-left: 15px;')

        self.stats_layout.addWidget(self.total_stocks_label)
        self.stats_layout.addWidget(self.last_update_label)

        title_row.addLayout(self.stats_layout)

        header_layout.addLayout(title_row)

        # Top gainers and losers summary
        summary_row = QHBoxLayout()
        self.top_gainer_label = QLabel('Top Gainer: Loading...')
        self.top_gainer_label.setStyleSheet('color: #AEEA00; font-weight: bold; font-size: 12px;')

        self.top_loser_label = QLabel('Top Loser: Loading...')
        self.top_loser_label.setStyleSheet('color: #FF8A80; font-weight: bold; font-size: 12px;')

        summary_row.addWidget(self.top_gainer_label)
        summary_row.addSpacing(20)
        summary_row.addWidget(self.top_loser_label)
        summary_row.addStretch()

        header_layout.addLayout(summary_row)

        content_layout.addWidget(header_frame)

        # Add Stock Section with improved styling
        add_stock_frame = QFrame()
        add_stock_frame.setProperty("class", "card")
        add_stock_layout = QHBoxLayout(add_stock_frame)
        add_stock_layout.setContentsMargins(15, 15, 15, 15)  # Reduced padding

        add_label = QLabel('Add to Watchlist:')
        add_label.setFont(QFont('Segoe UI', 12))
        add_label.setStyleSheet('color: #333;')

        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText('Enter Stock Symbol (e.g., RELIANCE.NS)')
        self.stock_input.setMinimumWidth(300)
        self.stock_input.setMinimumHeight(32)  # Reduced height

        add_stock_btn = QPushButton('Add Stock')
        add_stock_btn.setProperty("class", "accent-btn")
        add_stock_btn.setMinimumHeight(32)  # Reduced height
        add_stock_btn.setMinimumWidth(100)
        add_stock_btn.clicked.connect(self.add_stock)

        add_stock_layout.addWidget(add_label)
        add_stock_layout.addWidget(self.stock_input)
        add_stock_layout.addWidget(add_stock_btn)
        add_stock_layout.addStretch()

        content_layout.addWidget(add_stock_frame)

        # Watchlist data frame with enhanced styling - larger table
        data_frame = QFrame()
        data_frame.setProperty("class", "card")
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(15, 15, 15, 15)
        data_layout.setSpacing(10)

        # Table header with title and controls
        table_header = QHBoxLayout()

        table_title = QLabel("My Watchlist")
        table_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        table_title.setStyleSheet('color: #041E42;')

        table_header.addWidget(table_title)
        table_header.addStretch()

        refresh_button = QPushButton('Refresh Data')
        refresh_button.setProperty("class", "accent-btn")
        refresh_button.setMinimumHeight(30)
        refresh_button.clicked.connect(self.refresh_data)

        table_header.addWidget(refresh_button)

        data_layout.addLayout(table_header)

        # Enhanced table widget
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(7)
        self.watchlist_table.setHorizontalHeaderLabels([
            'Stock', 'Last Price', 'Change', '% Change',
            'Volume', 'Market Cap', 'Action'
        ])

        # Set alternating row colors for better readability
        self.watchlist_table.setAlternatingRowColors(True)
        self.watchlist_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f9f9f9;
            }
        """)

        # Set row height to be smaller for the table
        self.watchlist_table.verticalHeader().setDefaultSectionSize(36)

        # Set table properties
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.watchlist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Make table take up more space - this frame should be much taller
        data_frame.setMinimumHeight(500)  # Increased height for the table
        self.update_watchlist_table()
        data_layout.addWidget(self.watchlist_table)

        content_layout.addWidget(data_frame)
        # Set the data_frame to have a stretch factor to make it larger
        content_layout.setStretchFactor(data_frame, 10)  # Give more stretch to the table

        # Bottom navigation buttons with improved styling
        nav_frame = QFrame()
        nav_frame.setProperty("class", "card")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(15, 15, 15, 15)

        back_button = QPushButton('Back to Dashboard')
        back_button.setMinimumHeight(32)
        back_button.setMinimumWidth(150)
        back_button.clicked.connect(self.switch_to_dashboard_slot)

        nav_layout.addWidget(back_button)
        nav_layout.addStretch()

        content_layout.addWidget(nav_frame)

        # Set up scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Add status bar (like dashboard)
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("""
            QStatusBar {
                background-color: #041E42;
                color: white;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.statusBar.showMessage('Ready')
        self.setStatusBar(self.statusBar)

        self.setCentralWidget(central_widget)

    def setup_database(self):
        """Setup database connection"""
        try:
            # Use the imported DatabaseConnection
            self.db = DatabaseConnection()
            print("✅ Database connection established in Watchlist")
        except NameError as e:
            print(f"❌ Database module not found: {e}")
            self.db = None
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            self.db = None

    def update_watchlist_table(self):
        self.watchlist_table.setRowCount(len(self.watchlist_data))
        for row, data in enumerate(self.watchlist_data):
            for col, value in enumerate(data):
                if col < 6:  # Regular columns
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Use a smaller font for better readability
                    font = QFont("Segoe UI", 11)
                    if col == 0:  # Make stock symbols bold
                        font.setBold(True)
                    item.setFont(font)

                    # Enhanced color coding for change columns
                    if col in [2, 3]:  # Change and % Change columns
                        if '+' in value:
                            item.setForeground(QColor('#28a745'))  # Green for positive
                            item.setBackground(QColor('#f0fff0'))  # Light green background
                        elif '-' in value:
                            item.setForeground(QColor('#dc3545'))  # Red for negative
                            item.setBackground(QColor('#fff5f5'))  # Light red background

                    self.watchlist_table.setItem(row, col, item)

            # Add remove button in the last column with improved styling
            remove_btn = QPushButton('Remove')
            remove_btn.setObjectName('removeBtn')
            remove_btn.setMinimumHeight(24)
            remove_btn.clicked.connect(lambda checked, row=row: self.remove_stock(row))
            self.watchlist_table.setCellWidget(row, 6, remove_btn)

    def add_stock(self, symbol):
        """Add a stock to the watchlist with database integration"""
        stock_symbol = self.stock_input.text().strip().upper() if not symbol else symbol.strip().upper()

        if not stock_symbol:
            return

        # Add .NS suffix if missing
        if not stock_symbol.endswith('.NS') and not stock_symbol.endswith('.BO'):
            stock_symbol = f"{stock_symbol}.NS"

        # Check if stock already exists
        existing_symbols = [row[0] for row in self.watchlist_data]
        if stock_symbol in existing_symbols:
            QMessageBox.warning(self, 'Warning',
                                f'{stock_symbol} is already in your watchlist!')
            return

        # Add to database
        try:
            if hasattr(self, 'db') and self.db:
                success, message = self.db.add_to_watchlist(self.user_id, stock_symbol)
                if not success:
                    QMessageBox.warning(self, 'Warning', message)
                    return
        except Exception as e:
            print(f"❌ Database error in add_stock: {e}")
            QMessageBox.warning(self, 'Database Error', f"Could not add stock to database: {str(e)}")
            return  # Don't continue if database operation failed

        # Add new stock with placeholder data - OUTSIDE the try/except block
        new_stock = [
            stock_symbol,
            '₹0.00',
            '₹0.00',
            '0.00%',
            '0',
            '0 Cr',
            ''
        ]
        self.watchlist_data.append(new_stock)
        self.update_watchlist_table()
        self.stock_input.clear()

        # Update UI
        self.watchlist_table.repaint()
        self.total_stocks_label.setText(f'Total Stocks: {len(self.watchlist_data)}')
        self.statusBar.showMessage(f'Added {stock_symbol} to watchlist')

        # Fetch data for the new stock
        self.fetch_stock_data(stock_symbol)

    def remove_stock(self, row):
        """Remove a stock from the watchlist with database integration"""
        stock_symbol = self.watchlist_data[row][0]

        reply = QMessageBox.question(self, 'Confirm Removal',
                                     f'Are you sure you want to remove {stock_symbol} from your watchlist?',
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from database
            if hasattr(self, 'db') and self.db and self.user_id:
                self.db.remove_from_watchlist(self.user_id, stock_symbol)

            # Remove from local data
            del self.watchlist_data[row]
            self.update_watchlist_table()

            # Update statistics
            self.total_stocks_label.setText(f'Total Stocks: {len(self.watchlist_data)}')
            self.update_top_performers()
            self.statusBar.showMessage(f'Removed {stock_symbol} from watchlist')

    def refresh_data(self):
        """Manually triggered refresh of all stock data"""
        self.fetch_real_data()

    def auto_refresh_data(self):
        """Automatically triggered refresh by timer"""
        self.fetch_real_data(show_message=False)

    def fetch_real_data(self, show_message=True):
        """Fetch real-time data for all stocks in watchlist"""
        if show_message:
            self.statusBar.showMessage('Refreshing watchlist data...')

        # Process stocks one by one to avoid rate limiting
        self.current_stock_index = 0
        self.process_next_stock()

    def process_next_stock(self):
        """Process one stock at a time and schedule the next"""
        # Base case: all stocks processed
        if self.current_stock_index >= len(self.watchlist_data):
            self.update_top_performers()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_update_label.setText(f'Last Updated: {current_time}')
            self.statusBar.showMessage('Watchlist updated successfully')
            return

        # Get current stock and fetch data
        symbol = self.watchlist_data[self.current_stock_index][0]
        self.statusBar.showMessage(f'Updating {symbol} ({self.current_stock_index + 1}/{len(self.watchlist_data)})')
        self.fetch_stock_data(symbol, self.current_stock_index)

        # Schedule next stock with delay
        self.current_stock_index += 1
        QTimer.singleShot(1000, self.process_next_stock)

    def fetch_stock_data(self, symbol, row_index=None):
        """Fetch data for a specific stock with improved accuracy"""
        try:
            # If row_index is None, find it
            if row_index is None:
                for i, row in enumerate(self.watchlist_data):
                    if row[0] == symbol:
                        row_index = i
                        break
                if row_index is None:
                    return  # Stock not found

            # Debug message
            print(f"Fetching data for {symbol}...")

            # Try a more direct approach with Yahoo Finance API
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

                # Debug data structure
                print(f"Got data for {symbol}: {meta}")

                # Current data
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('chartPreviousClose', 0)

                # If we don't have previous close, try to get it from the time series
                if prev_close == 0 and len(quote['close']) > 1:
                    prev_close = quote['close'][-2]

                # Calculate changes
                price_change = current_price - prev_close
                percent_change = (price_change / prev_close) * 100 if prev_close else 0

                # Get volume
                volume = meta.get('regularMarketVolume', 0)

                # Format values
                price_str = f"₹{current_price:.2f}"
                change_str = f"{'+' if price_change >= 0 else ''}{price_change:.2f}"
                percent_str = f"{'+' if percent_change >= 0 else ''}{percent_change:.2f}%"
                volume_str = f"{volume:,}"

                # Get market cap
                market_cap = self.get_market_cap(symbol)

                # Debug output
                print(f"{symbol} Price: {price_str}, Change: {change_str}, %Change: {percent_str}")

                # Update watchlist data
                self.watchlist_data[row_index] = [
                    symbol,
                    price_str,
                    change_str,
                    percent_str,
                    volume_str,
                    market_cap,
                    ''
                ]

                # Update table display
                self.update_watchlist_table()
                return True

            else:
                print(f"No data available for {symbol}")
                return False

        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return False

    def load_watchlist_from_db(self):
        """Load user's watchlist from database"""
        if not hasattr(self, 'db') or self.db is None or not self.user_id:
            print("No database connection or user_id available")
            return

        try:
            # Get watchlist items from database
            watchlist_items = self.db.get_user_watchlist(self.user_id)

            if watchlist_items:
                # Clear existing data
                self.watchlist_data = []

                # Add each stock to our watchlist with placeholder data
                for item in watchlist_items:
                    self.watchlist_data.append([
                        item['stock_symbol'],
                        '₹0.00',
                        '₹0.00',
                        '0.00%',
                        '0',
                        '0 Cr',
                        ''
                    ])

                self.update_watchlist_table()
                print(f"Loaded {len(watchlist_items)} stocks from database")
                if hasattr(self, 'statusBar'):
                    self.statusBar.showMessage(f'Loaded {len(watchlist_items)} stocks from database')

                # Update total count if the label exists
                if hasattr(self, 'total_stocks_label'):
                    self.total_stocks_label.setText(f'Total Stocks: {len(self.watchlist_data)}')

        except Exception as e:
            print(f"❌ Error loading watchlist: {e}")
            if hasattr(self, 'statusBar'):
                self.statusBar.showMessage(f'Error loading watchlist: {str(e)}')

    def refresh_data(self):
        """Manually triggered refresh of all stock data"""
        self.statusBar.showMessage('Refreshing data for all stocks...')

        # Clear existing data from the display
        for row_index in range(len(self.watchlist_data)):
            self.watchlist_data[row_index] = [
                self.watchlist_data[row_index][0],  # Keep symbol
                '₹0.00',
                '₹0.00',
                '0.00%',
                '0',
                'N/A',
                ''
            ]

        # Update table first with placeholders
        self.update_watchlist_table()

        # Now fetch fresh data
        self.fetch_real_data()

    def get_market_cap(self, symbol):
        """Get market cap for a stock using yfinance"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            market_cap = info.get('marketCap', 0)

            # Format market cap
            if market_cap >= 10_000_000_000:  # Crores
                return f"{market_cap / 10_000_000:.2f}L Cr"
            elif market_cap >= 100_000_000:  # Crores
                return f"{market_cap / 10_000_000:.2f} Cr"
            elif market_cap >= 10_000_000:  # Lakhs
                return f"{market_cap / 100_000:.2f}L"
            else:
                return f"{market_cap:,}"

        except Exception as e:
            print(f"Error getting market cap for {symbol}: {str(e)}")
            return "N/A"

    def update_top_performers(self):
        """Update top gainer and loser labels"""
        if not self.watchlist_data:
            self.top_gainer_label.setText("Top Gainer: None")
            self.top_loser_label.setText("Top Loser: None")
            return

        # Find top gainer and loser
        best_change = -float('inf')
        worst_change = float('inf')
        best_stock = ""
        worst_stock = ""

        for row in self.watchlist_data:
            symbol = row[0]
            change_text = row[3]

            try:
                # Extract percentage value
                percent = float(change_text.replace('%', '').replace('+', ''))

                if percent > best_change:
                    best_change = percent
                    best_stock = symbol

                if percent < worst_change:
                    worst_change = percent
                    worst_stock = symbol
            except:
                continue

        # Update labels
        if best_stock:
            self.top_gainer_label.setText(f"Top Gainer: {best_stock} +{best_change:.2f}%")

        if worst_stock:
            self.top_loser_label.setText(f"Top Loser: {worst_stock} {worst_change:.2f}%")

    def switch_to_dashboard_slot(self):

        self.close_database()
        self.switch_to_dashboard.emit()
        self.hide()
        self.switch_to_dashboard.emit()
        self.hide()

    def closeEvent(self, event):
        """Clean up database connection when window is closed"""
        self.close_database()
        event.accept()

    def close_database(self):
        """Close database connection"""
        try:
            if hasattr(self, 'db') and self.db is not None:
                self.db.close()
                print("Database connection closed")
        except Exception as e:
            print(f"Error closing database: {e}")