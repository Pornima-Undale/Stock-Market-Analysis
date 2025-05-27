from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QFrame, QGridLayout, QComboBox, QSpacerItem, QSizePolicy,
                             QMessageBox, QDialog, QScrollArea, QHeaderView)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor
import sqlite3
from datetime import datetime, date
import yfinance as yf
from navigation_windows import BaseNavigationWindow


class StyledLabel(QLabel):
    def __init__(self, text, font_size=10, bold=True, color=None):
        super().__init__(text)
        font = QFont('Segoe UI', font_size)
        if bold:
            font.setBold(True)
            font.setWeight(QFont.Weight.Bold)
        self.setFont(font)
        if color:
            self.setStyleSheet(f'color: {color};')


class PortfolioWindow(BaseNavigationWindow):
    switch_to_dashboard = pyqtSignal()

    def __init__(self, title="portfolio", user_id=None):
        super().__init__(title, user_id)
        self.setWindowTitle('SARASFINTECH - Portfolio Dashboard')

        # Initialize portfolio data
        self.portfolio_data = []
        self.user_id = user_id

        # Create the main layout with scrollable content
        self.initUI()

        self.setMinimumSize(1400, 900)

        # Load portfolio data from database
        self.load_portfolio_data()

    def setup_database(self):
        """Setup database connection"""
        try:
            self.db = DatabaseConnection()
            print("✅ Database connection established in Portfolio")
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            self.db = None

    def resizeEvent(self, event):
        """Handle window resize events safely"""
        super().resizeEvent(event)

        # Only update if we have valid widgets
        if hasattr(self, 'portfolio_table') and self.portfolio_table:
            # Make sure portfolio table takes advantage of vertical space
            self.portfolio_table.setMinimumHeight(max(500, self.height() // 2))

    def initUI(self):
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create a scroll area for the portfolio content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create the content that will be inside the scroll area
        portfolio_content = QWidget()
        content_layout = QVBoxLayout(portfolio_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        portfolio_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add page title
        title = QLabel('Portfolio Dashboard')
        title.setObjectName('portfolio_title')
        title.setFont(QFont('Arial', 26, QFont.Weight.Bold))
        title.setStyleSheet('color: #041E42; margin-bottom: 20px; font-weight: bold;')
        content_layout.addWidget(title)

        # Add time period selector and dashboard navigation
        header_layout = QHBoxLayout()

        # Dashboard button with improved styling
        dashboard_button = QPushButton('Back to Dashboard')
        dashboard_button.clicked.connect(self.switch_to_dashboard_slot)
        dashboard_button.setMinimumHeight(40)
        dashboard_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                background-color: #041E42;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)

        # Time period selector with improved styling
        self.period_selector = QComboBox()
        self.period_selector.addItems(['1D', '1W', '1M', '3M', '6M', '1Y', 'All'])
        self.period_selector.setFixedWidth(120)
        self.period_selector.setStyleSheet("""
            QComboBox {
                border: 1px solid #bbb;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #041E42;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #bbb;
                border-left-style: solid;
                border-radius: 0;
            }
        """)

        period_label = QLabel("View Period:")
        period_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #041E42;")

        header_layout.addWidget(dashboard_button)
        header_layout.addStretch()
        header_layout.addWidget(period_label)
        header_layout.addWidget(self.period_selector)

        content_layout.addLayout(header_layout)

        # Portfolio Holdings section
        holdings_frame = QFrame()
        holdings_frame.setFrameShape(QFrame.Shape.NoFrame)  # Remove frame to avoid double border
        holdings_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.08);
            }
        """)
        holdings_layout = QVBoxLayout(holdings_frame)
        holdings_layout.setContentsMargins(25, 25, 25, 25)  # Increased padding

        holdings_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add section title
        holdings_title = QLabel('Portfolio Holdings')
        holdings_title.setObjectName('holdings_title')
        holdings_title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        holdings_title.setStyleSheet('color: #041E42; margin-bottom: 15px; font-weight: bold;')
        holdings_layout.addWidget(holdings_title)

        # Add refresh button and action buttons
        actions_layout = QHBoxLayout()

        refresh_button = QPushButton('Refresh Data')
        refresh_button.clicked.connect(self.refresh_data)
        refresh_button.setMaximumWidth(150)
        refresh_button.setMinimumHeight(40)
        refresh_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                background-color: #041E42;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)

        delete_button = QPushButton('Delete Selected')
        delete_button.clicked.connect(self.delete_selected_stock)
        delete_button.setMaximumWidth(150)
        delete_button.setMinimumHeight(40)
        delete_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        self.last_updated_label = QLabel('Last Updated: Never')
        self.last_updated_label.setStyleSheet('color: #444; margin-left: 20px; font-weight: bold;')

        actions_layout.addWidget(refresh_button)
        actions_layout.addWidget(delete_button)
        actions_layout.addWidget(self.last_updated_label)
        actions_layout.addStretch()

        holdings_layout.addLayout(actions_layout)

        # Portfolio Table with enhanced styling
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(8)
        self.portfolio_table.setHorizontalHeaderLabels([
            'Stock', 'Quantity', 'Avg. Buy Price',
            'Purchase Date', 'Current Price', 'Total Investment',
            'Market Value', 'Profit/Loss'
        ])

        self.portfolio_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set enhanced table properties
        self.portfolio_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.portfolio_table.setMinimumHeight(500)
        self.portfolio_table.setAlternatingRowColors(True)
        self.portfolio_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.portfolio_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 5px;
                gridline-color: #eeeeee;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
            QTableWidget::item:alternate {
                background-color: #f9f9f9;
            }
        """)

        holdings_layout.addWidget(self.portfolio_table)

        # Add summary section below the table
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.NoFrame)
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                border-top: 1px solid #e0e0e0;
                padding: 10px;
                margin-top: 10px;
            }
        """)

        summary_layout = QGridLayout(summary_frame)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        summary_layout.setSpacing(20)

        # Portfolio Value
        portfolio_value_label = QLabel("Total Portfolio Value:")
        portfolio_value_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #444444;")
        self.portfolio_value = QLabel("₹0.00")
        self.portfolio_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.portfolio_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Total Investment
        investment_label = QLabel("Total Investment:")
        investment_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #444444;")
        self.investment_value = QLabel("₹0.00")
        self.investment_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.investment_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Total Returns
        returns_label = QLabel("Total Returns:")
        returns_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #444444;")

        # Create container for returns value with indicator
        returns_container = QWidget()
        returns_layout = QHBoxLayout(returns_container)
        returns_layout.setContentsMargins(0, 0, 0, 0)
        returns_layout.setSpacing(5)
        returns_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.returns_indicator = QLabel()
        self.returns_indicator.setFixedSize(10, 10)
        self.returns_indicator.setStyleSheet('background-color: #00c853; border-radius: 5px;')

        self.returns_value = QLabel("₹0.00 (+0.00%)")
        self.returns_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #008000;")

        returns_layout.addWidget(self.returns_indicator)
        returns_layout.addWidget(self.returns_value)

        # Today's Gain
        gain_label = QLabel("Today's Gain:")
        gain_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #444444;")

        # Create container for today's gain with indicator
        gain_container = QWidget()
        gain_layout = QHBoxLayout(gain_container)
        gain_layout.setContentsMargins(0, 0, 0, 0)
        gain_layout.setSpacing(5)
        gain_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.gain_indicator = QLabel()
        self.gain_indicator.setFixedSize(10, 10)
        self.gain_indicator.setStyleSheet('background-color: #00c853; border-radius: 5px;')

        self.gain_value = QLabel("₹0.00 (+0.00%)")
        self.gain_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #008000;")

        gain_layout.addWidget(self.gain_indicator)
        gain_layout.addWidget(self.gain_value)

        # Add all to the grid layout
        summary_layout.addWidget(portfolio_value_label, 0, 0)
        summary_layout.addWidget(self.portfolio_value, 0, 1)
        summary_layout.addWidget(investment_label, 0, 2)
        summary_layout.addWidget(self.investment_value, 0, 3)
        summary_layout.addWidget(returns_label, 1, 0)
        summary_layout.addWidget(returns_container, 1, 1)
        summary_layout.addWidget(gain_label, 1, 2)
        summary_layout.addWidget(gain_container, 1, 3)

        holdings_layout.addWidget(summary_frame)
        content_layout.addWidget(holdings_frame)

        # Set the portfolio content as the widget for the scroll area
        scroll_area.setWidget(portfolio_content)
        main_layout.addWidget(scroll_area)

        # Status bar with enhanced styling
        self.statusBar().showMessage('Ready')
        self.statusBar().setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #041E42;
                color: white;
                padding: 5px;
            }
        """)

        self.setCentralWidget(central_widget)

        # Apply enhanced style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            /* Style for scrollbars */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 14px;
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
                height: 14px;
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
            QLabel {
                font-size: 13px;
            }
        """)

    def connect_to_database(self):
        """Connect to the SQLite database"""
        try:
            conn = sqlite3.connect('stock_market_app.db')
            cursor = conn.cursor()

            # Create portfolio table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                date_added TEXT NOT NULL
            )
            ''')
            conn.commit()

            return conn, cursor
        except Exception as e:
            print(f"Database error: {str(e)}")
            return None, None

    def load_portfolio_data(self):
        """Load portfolio data from database"""
        if not hasattr(self, 'db') or self.db is None or not self.user_id:
            print("No database connection or user_id available")
            return

        try:
            # Get portfolio items from database
            portfolio_items = self.db.get_user_portfolio(self.user_id)

            # Clear existing data
            self.portfolio_data = []

            # Process portfolio data and update current prices
            for item in portfolio_items:
                stock_symbol = item['stock_symbol']
                quantity = item['quantity']
                purchase_price = item['purchase_price']
                purchase_date = item['purchase_date']

                # Get current price
                current_price = self.get_current_price(stock_symbol)

                # Calculate values
                total_investment = float(quantity) * float(purchase_price)
                market_value = float(quantity) * float(current_price)
                profit_loss = market_value - total_investment
                profit_loss_percent = (profit_loss / total_investment) * 100 if total_investment > 0 else 0

                self.portfolio_data.append({
                    'id': item['portfolio_id'],
                    'symbol': stock_symbol,
                    'quantity': quantity,
                    'purchase_price': purchase_price,
                    'purchase_date': purchase_date.strftime('%Y-%m-%d') if isinstance(purchase_date,
                                                                                      (datetime, date)) else str(purchase_date),
                    'current_price': current_price,
                    'total_investment': total_investment,
                    'market_value': market_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent
                })

            # Update the UI
            self.update_portfolio_table()
            self.update_summary_section()

            # Update the last updated time
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_updated_label.setText(f'Last Updated: {current_time}')

        except Exception as e:
            print(f"Error loading portfolio data: {str(e)}")
            import traceback
            traceback.print_exc()

    def get_current_price(self, symbol):
        """Get current price for a stock symbol"""
        try:
            # First try to get price from main dashboard if available
            if hasattr(self, 'parent') and hasattr(self.parent, 'stock_table'):
                for row in range(self.parent.stock_table.rowCount()):
                    if (self.parent.stock_table.item(row, 0) and
                            self.parent.stock_table.item(row, 0).text() == symbol):
                        price_text = self.parent.stock_table.item(row, 2).text()
                        if price_text.startswith('₹'):
                            price_text = price_text[1:]
                        return float(price_text)

            # If not found in dashboard, use yfinance as fallback
            stock = yf.Ticker(symbol)
            history = stock.history(period="1d")
            if not history.empty:
                return history['Close'].iloc[-1]

            # If all else fails, use a default price
            return 0.00
        except Exception as e:
            print(f"Error getting price for {symbol}: {str(e)}")
            return 0.00

    def update_portfolio_table(self):
        """Update the portfolio table with current data"""
        self.portfolio_table.setRowCount(0)

        for index, stock in enumerate(self.portfolio_data):
            self.portfolio_table.insertRow(index)

            # Symbol
            symbol_item = QTableWidgetItem(stock['symbol'])
            symbol_item.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
            self.portfolio_table.setItem(index, 0, symbol_item)

            # Quantity
            quantity_item = QTableWidgetItem(str(stock['quantity']))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(index, 1, quantity_item)

            # Avg Buy Price
            buy_price_item = QTableWidgetItem(f"₹{stock['purchase_price']:.2f}")
            buy_price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(index, 2, buy_price_item)

            # Purchase Date
            date_item = QTableWidgetItem(str(stock['purchase_date']))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(index, 3, date_item)

            # Current Price
            current_price_item = QTableWidgetItem(f"₹{stock['current_price']:.2f}")
            current_price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(index, 4, current_price_item)

            # Total Investment
            investment_item = QTableWidgetItem(f"₹{stock['total_investment']:.2f}")
            investment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(index, 5, investment_item)

            # Market Value
            market_value_item = QTableWidgetItem(f"₹{stock['market_value']:.2f}")
            market_value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.portfolio_table.setItem(index, 6, market_value_item)

            # Create a widget for Profit/Loss with indicator light
            profit_loss_widget = QWidget()
            profit_loss_layout = QHBoxLayout(profit_loss_widget)
            profit_loss_layout.setContentsMargins(5, 0, 5, 0)
            profit_loss_layout.setSpacing(5)
            profit_loss_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Add indicator light
            indicator = QLabel()
            indicator.setFixedSize(10, 10)
            is_profit = stock['profit_loss'] >= 0
            indicator.setStyleSheet(
                'background-color: #00c853; border-radius: 5px;' if is_profit
                else 'background-color: #ff1744; border-radius: 5px;'
            )

            # Add profit/loss text
            profit_loss_text = f"{'+' if is_profit else ''}₹{stock['profit_loss']:.2f} ({'+' if is_profit else ''}{stock['profit_loss_percent']:.2f}%)"
            profit_loss_label = QLabel(profit_loss_text)
            profit_loss_label.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
            profit_loss_label.setStyleSheet(
                'color: #008000; font-weight: bold;' if is_profit
                else 'color: #ff0000; font-weight: bold;'
            )

            profit_loss_layout.addWidget(indicator)
            profit_loss_layout.addWidget(profit_loss_label)

            # Set the widget in the table cell
            self.portfolio_table.setCellWidget(index, 7, profit_loss_widget)

    def update_summary_section(self):
        """Update summary section with current portfolio totals"""
        total_investment = float(sum(float(stock['total_investment']) for stock in self.portfolio_data))
        total_market_value = float(sum(float(stock['market_value']) for stock in self.portfolio_data))
        total_profit_loss = total_market_value - total_investment
        profit_loss_percent = (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0

        # Today's gain - in a real app, you would calculate this based on previous day closing prices
        # Here we'll simulate with a small percentage of total value
        todays_gain = total_market_value * 0.002  # 0.2% as example
        todays_gain_percent = 0.2  # 0.2% as example

        # Update portfolio value and investment
        self.portfolio_value.setText(f"₹{total_market_value:,.2f}")
        self.investment_value.setText(f"₹{total_investment:,.2f}")

        # Update returns value and color
        returns_text = f"₹{total_profit_loss:,.2f} ({'+' if profit_loss_percent >= 0 else ''}{profit_loss_percent:.2f}%)"
        self.returns_value.setText(returns_text)

        # Update returns indicator and color
        if profit_loss_percent >= 0:
            self.returns_indicator.setStyleSheet('background-color: #00c853; border-radius: 5px;')
            self.returns_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #008000;")
        else:
            self.returns_indicator.setStyleSheet('background-color: #ff1744; border-radius: 5px;')
            self.returns_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff0000;")

        # Update today's gain value and color
        gain_text = f"₹{todays_gain:,.2f} ({'+' if todays_gain_percent >= 0 else ''}{todays_gain_percent:.2f}%)"
        self.gain_value.setText(gain_text)

        # Update gain indicator and color
        if todays_gain_percent >= 0:
            self.gain_indicator.setStyleSheet('background-color: #00c853; border-radius: 5px;')
            self.gain_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #008000;")
        else:
            self.gain_indicator.setStyleSheet('background-color: #ff1744; border-radius: 5px;')
            self.gain_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff0000;")

    def add_stock_to_portfolio(self, stock_data):
        """Add a stock to the portfolio with database integration"""
        try:
            if not hasattr(self, 'db') or self.db is None or not self.user_id:
                print("No database connection or user_id available")
                return False

            # Add to database
            success, message = self.db.add_to_portfolio(
                self.user_id,
                stock_data['symbol'],
                stock_data['quantity'],
                stock_data['purchase_price'],
                stock_data['purchase_date'],
                stock_data.get('notes', '')
            )

            if success:
                # Refresh the portfolio display
                self.load_portfolio_data()
                self.statusBar().showMessage(f"Added {stock_data['symbol']} to portfolio", 3000)
                return True
            else:
                self.statusBar().showMessage(f"Error: {message}", 3000)
                return False

        except Exception as e:
            print(f"Error adding stock to portfolio: {str(e)}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error adding stock to portfolio: {str(e)}", 5000)
            return False

    def delete_selected_stock(self):
        """Delete the selected stock from the portfolio with database integration"""
        selected_rows = self.portfolio_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.information(self, "Selection Required", "Please select a stock to delete.")
            return

        # Get the unique row indices
        rows = set(index.row() for index in selected_rows)

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(rows)} selected stock(s) from your portfolio?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                if not hasattr(self, 'db') or self.db is None or not self.user_id:
                    print("No database connection or user_id available")
                    return

                deleted_count = 0
                for row in sorted(rows, reverse=True):
                    portfolio_id = self.portfolio_data[row]['id']
                    # Delete from database
                    success, _ = self.db.remove_from_portfolio(self.user_id, portfolio_id)
                    if success:
                        deleted_count += 1

                # Refresh the portfolio display
                self.load_portfolio_data()
                self.statusBar().showMessage(f"Successfully deleted {deleted_count} stock(s) from portfolio", 3000)

            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not delete stock(s): {str(e)}"
                )
                print(f"Error deleting stocks: {str(e)}")
                import traceback
                traceback.print_exc()

    def refresh_data(self):
        """Refresh portfolio data with updated current prices"""
        self.statusBar().showMessage("Refreshing portfolio data...", 2000)
        self.load_portfolio_data()
        self.statusBar().showMessage("Portfolio data refreshed with current market prices", 3000)

    def switch_to_dashboard_slot(self):
        self.switch_to_dashboard.emit()
        self.hide()