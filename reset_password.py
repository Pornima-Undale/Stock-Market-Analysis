from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFrame,
                             QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from database import DatabaseConnection


class ResetPasswordWindow(QMainWindow):
    def __init__(self, email):
        super().__init__()
        self.email = email
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SARASFINTECH - Reset Password')
        self.setMinimumSize(1250, 800)
        self.setStyleSheet("QMainWindow {background-color: #f5f5f5;}")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create container
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        container_layout = QVBoxLayout(container)

        # Form container
        form_container = QFrame()
        form_container.setFixedWidth(420)
        form_container.setStyleSheet("QFrame {background-color: white; border-radius: 12px;}")

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 4)
        form_container.setGraphicsEffect(shadow)

        # Form layout
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(40, 50, 40, 50)

        # Title
        title_label = QLabel("Reset Password")
        title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #041E42; margin-bottom: 5px;")

        subtitle_label = QLabel("Create a new password for your account")
        subtitle_label.setStyleSheet("color: #666666; font-size: 15px;")

        # Password fields
        new_password_label = QLabel("New Password")
        new_password_label.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setMinimumHeight(55)
        self.new_password_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                padding-left: 20px;
                background-color: #F7F9FC;
                border: 2px solid #EDF2F7;
                border-radius: 10px;
                color: #041E42;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #041E42;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #A0AEC0;
            }
        """)

        confirm_password_label = QLabel("Confirm New Password")
        confirm_password_label.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMinimumHeight(55)
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                padding-left: 20px;
                background-color: #F7F9FC;
                border: 2px solid #EDF2F7;
                border-radius: 10px;
                color: #041E42;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #041E42;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #A0AEC0;
            }
        """)

        # Reset button
        reset_button = QPushButton("Reset Password")
        reset_button.setMinimumHeight(55)
        reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            QPushButton:pressed {
                background-color: #041E42;
            }
        """)
        reset_button.clicked.connect(self.reset_password)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setStyleSheet("""
            QPushButton {
                color: #041E42;
                font-size: 14px;
                border: none;
                background: transparent;
                padding: 10px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        cancel_button.clicked.connect(self.handle_cancel)

        # Add all widgets to form layout
        form_layout.addWidget(title_label)
        form_layout.addWidget(subtitle_label)
        form_layout.addSpacing(20)
        form_layout.addWidget(new_password_label)
        form_layout.addWidget(self.new_password_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(confirm_password_label)
        form_layout.addWidget(self.confirm_password_input)
        form_layout.addSpacing(20)
        form_layout.addWidget(reset_button)
        form_layout.addSpacing(10)
        form_layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Password requirements label
        requirements_label = QLabel("""
            Password must contain:
            • At least 8 characters
            • One uppercase letter
            • One lowercase letter
            • One number
            • One special character
        """)
        requirements_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                margin-top: 10px;
            }
        """)
        form_layout.addWidget(requirements_label)

        # Add form container to the center of the main layout
        container_layout.addStretch()
        container_layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignCenter)
        container_layout.addStretch()

        main_layout.addWidget(container)

    def reset_password(self):
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validate password requirements
        if not self.validate_password(new_password):
            QMessageBox.warning(self, "Invalid Password",
                                "Password must contain at least 8 characters, one uppercase letter, "
                                "one lowercase letter, one number, and one special character.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return

        try:
            # Update password in database
            db = DatabaseConnection()
            if db.update_password(self.email, new_password):
                QMessageBox.information(self, "Success",
                                        "Password has been reset successfully. Please log in with your new password.")
                self.show_login()
            else:
                QMessageBox.warning(self, "Error", "Failed to reset password. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")

    def validate_password(self, password):
        if len(password) < 8:
            return False

        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            return False

        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            return False

        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            return False

        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False

        return True

    def handle_cancel(self):
        from login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.hide()

    def show_login(self):
        from login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.hide()