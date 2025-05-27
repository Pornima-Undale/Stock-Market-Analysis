from PyQt6.QtWidgets import QPushButton, QMenu, QMessageBox
from PyQt6.QtCore import Qt


class AddStockButton(QPushButton):
    def __init__(self, symbol, parent=None):
        super().__init__("Add", parent)
        self.symbol = symbol

        # Setup button style
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                text-align: center;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton::menu-indicator {
                image: none;
            }
        """)

        # Create dropdown menu
        self.menu = QMenu(self)

        # Add actions to menu
        add_watchlist_action = self.menu.addAction("Add to Watchlist")
        add_analytics_action = self.menu.addAction("Add to Analytics")
        add_portfolio_action = self.menu.addAction("Add to Portfolio")

        # Connect actions to methods
        add_watchlist_action.triggered.connect(self.add_to_watchlist)
        add_analytics_action.triggered.connect(self.add_to_analytics)
        add_portfolio_action.triggered.connect(self.add_to_portfolio)

        # Set menu policy
        self.setMenu(self.menu)

    def add_to_watchlist(self):
        """Add stock to watchlist"""
        try:
            # Traverse up the widget hierarchy to find the main dashboard
            dashboard = self.window()

            # Check if the dashboard has a watchlist window
            if hasattr(dashboard, 'watchlist_window') and dashboard.watchlist_window:
                dashboard.watchlist_window.add_stock(self.symbol)
                dashboard.statusBar().showMessage(f'{self.symbol} added to Watchlist', 3000)
            else:
                print(f"No watchlist window found to add {self.symbol}")
                QMessageBox.warning(self, "Error", "Watchlist window not initialized")
        except Exception as e:
            print(f"Error adding {self.symbol} to watchlist: {e}")
            QMessageBox.warning(self, "Error", f"Could not add {self.symbol} to watchlist: {str(e)}")

    def add_to_analytics(self):
        """Add stock to analytics"""
        try:
            # Traverse up the widget hierarchy to find the main dashboard
            dashboard = self.window()

            # Check if the dashboard has an analytics window
            if hasattr(dashboard, 'analytics_window') and dashboard.analytics_window:
                dashboard.analytics_window.add_stock(self.symbol)
                dashboard.statusBar().showMessage(f'{self.symbol} added to Analytics', 3000)
            else:
                print(f"No analytics window found to add {self.symbol}")
                QMessageBox.warning(self, "Error", "Analytics window not initialized")
        except Exception as e:
            print(f"Error adding {self.symbol} to analytics: {e}")
            QMessageBox.warning(self, "Error", f"Could not add {self.symbol} to analytics: {str(e)}")

    def add_to_portfolio(self):
        """Add stock to portfolio"""
        try:
            # Traverse up the widget hierarchy to find the main dashboard
            from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton

            dashboard = self.window()

            # Check if the dashboard has a portfolio window
            if hasattr(dashboard, 'portfolio_window') and dashboard.portfolio_window:
                dialog = QDialog(dashboard)
                dialog.setWindowTitle(f'Add {self.symbol} to Portfolio')
                layout = QVBoxLayout()

                # Quantity input
                quantity_layout = QHBoxLayout()
                quantity_label = QLabel('Quantity:')
                quantity_input = QLineEdit()
                quantity_layout.addWidget(quantity_label)
                quantity_layout.addWidget(quantity_input)
                layout.addLayout(quantity_layout)

                # Purchase price input
                price_layout = QHBoxLayout()
                price_label = QLabel('Purchase Price:')
                price_input = QLineEdit()
                price_layout.addWidget(price_label)
                price_layout.addWidget(price_input)
                layout.addLayout(price_layout)

                # Buttons
                button_layout = QHBoxLayout()
                add_button = QPushButton('Add')
                cancel_button = QPushButton('Cancel')
                button_layout.addWidget(add_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)

                dialog.setLayout(layout)

                # Button connections
                def on_add():
                    try:
                        quantity = int(quantity_input.text())
                        price = float(price_input.text())

                        # Add to portfolio
                        dashboard.portfolio_window.add_stock(self.symbol, quantity, price)

                        # Close dialog
                        dialog.accept()

                        # Show success message
                        dashboard.statusBar().showMessage(f'{self.symbol} added to Portfolio', 3000)
                    except ValueError:
                        QMessageBox.warning(dialog, "Invalid Input", "Please enter valid quantity and price.")

                def on_cancel():
                    dialog.reject()

                add_button.clicked.connect(on_add)
                cancel_button.clicked.connect(on_cancel)

                # Show the dialog
                dialog.exec()
            else:
                print(f"No portfolio window found to add {self.symbol}")
                QMessageBox.warning(self, "Error", "Portfolio window not initialized")
        except Exception as e:
            print(f"Error adding {self.symbol} to portfolio: {e}")
            QMessageBox.warning(self, "Error", f"Could not add {self.symbol} to portfolio: {str(e)}")