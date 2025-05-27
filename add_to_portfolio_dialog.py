import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QDateEdit, QFormLayout,
                             QMessageBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate


class AddToPortfolioDialog(QDialog):
    """Dialog for adding stock to portfolio with quantity and purchase details"""

    def __init__(self, symbol, current_price, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.current_price = current_price
        self.result_data = None

        self.setWindowTitle(f"Add {symbol} to Portfolio")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 13px;
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
            QPushButton#cancelButton {
                background-color: #f5f5f5;
                color: #041E42;
                border: 1px solid #041E42;
            }
            QPushButton#cancelButton:hover {
                background-color: #e5e5e5;
            }
            QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Stock info
        info_layout = QVBoxLayout()
        stock_label = QLabel(f"<b>{self.symbol}</b>")
        stock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stock_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")

        current_price_label = QLabel(f"Current Price: ₹{self.current_price:.2f}")
        current_price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(stock_label)
        info_layout.addWidget(current_price_label)
        layout.addLayout(info_layout)

        # Add a separator line
        separator = QLabel()
        separator.setStyleSheet("border-bottom: 1px solid #ddd; margin: 10px 0;")
        layout.addWidget(separator)

        # Form layout for input fields
        form_layout = QFormLayout()

        # Quantity field
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.update_total)
        form_layout.addRow("Quantity:", self.quantity_spin)

        # Purchase price field
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMinimum(0.01)
        self.price_spin.setMaximum(1000000.00)
        self.price_spin.setValue(self.current_price)
        self.price_spin.setDecimals(2)
        self.price_spin.setSingleStep(0.01)
        self.price_spin.valueChanged.connect(self.update_total)
        form_layout.addRow("Purchase Price (₹):", self.price_spin)

        # Purchase date field
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Purchase Date:", self.date_edit)

        # Total investment field (non-editable)
        self.total_investment = QLineEdit()
        self.total_investment.setReadOnly(True)
        self.update_total()  # Initial calculation
        form_layout.addRow("Total Investment (₹):", self.total_investment)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)

        add_button = QPushButton("Add to Portfolio")
        add_button.clicked.connect(self.accept_with_validation)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(add_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def update_total(self):
        """Update the total investment field based on quantity and price"""
        quantity = self.quantity_spin.value()
        price = self.price_spin.value()
        total = quantity * price
        self.total_investment.setText(f"{total:.2f}")

    def accept_with_validation(self):
        """Validate inputs before accepting"""
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid Input", "Quantity must be greater than zero.")
            return

        if self.price_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid Input", "Purchase price must be greater than zero.")
            return

        # Store the result data
        self.result_data = {
            'symbol': self.symbol,
            'quantity': self.quantity_spin.value(),
            'purchase_price': self.price_spin.value(),
            'purchase_date': self.date_edit.date().toString("yyyy-MM-dd"),
            'total_investment': float(self.total_investment.text()),
            'current_price': self.current_price
        }

        # Accept the dialog
        self.accept()

    def get_data(self):
        """Return the collected data"""
        return self.result_data