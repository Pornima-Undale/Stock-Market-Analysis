from database import DatabaseConnection
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFrame, QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QSize


class CustomCheckBox(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(18, 18))
        self.checked = False
        self.update_style()

    def mousePressEvent(self, event):
        self.checked = not self.checked
        self.update_style()
        if hasattr(self, 'callback'):
            self.callback(self.checked)

    def update_style(self):
        style = f"""
            QLabel {{
                border: 2px solid {('#041E42' if self.checked else '#A0AEC0')};
                border-radius: 4px;
                background: white;
                font-size: 14px;
                text-align: center;
            }}
        """
        self.setStyleSheet(style)
        self.setText('✓' if self.checked else '')


class PasswordLineEdit(QWidget):
    def __init__(self, placeholder_text):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Create password field container
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #F7F9FC;
                border: 2px solid #EDF2F7;
                border-radius: 10px;
            }
            QFrame:focus-within {
                border: 2px solid #041E42;
                background-color: white;
            }
        """)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(20, 0, 10, 0)
        container_layout.setSpacing(5)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(placeholder_text)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #041E42;
                font-size: 13px;
                min-height: 45px;
            }
            QLineEdit::placeholder {
                color: #A0AEC0;
            }
        """)

        self.toggle_password = CustomCheckBox()
        self.toggle_password.callback = self.toggle_password_visibility

        # Add widgets to container
        container_layout.addWidget(self.password_input)
        container_layout.addWidget(self.toggle_password)

        # Add container to main layout
        self.layout.addWidget(self.container)

    def toggle_password_visibility(self, checked):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

    def text(self):
        return self.password_input.text()

    def clear(self):
        self.password_input.clear()

    def setFocus(self):
        self.password_input.setFocus()



class SignupWindow(QMainWindow):
    # Signal to notify when switching to login
    switch_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.password_strength_label = None
        self.initUI()


    def initUI(self):
        self.setWindowTitle('SARASFINTECH - Create Account')
        self.setMinimumSize(1550, 800)
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left branding panel
        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { background-color: #041E42; border: none; }")
        left_panel.setFixedWidth(500)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setContentsMargins(40, 40, 40, 40)

        company_name = QLabel("SARASFINTECH")
        company_name.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 4px;
            }
        """)
        left_layout.addWidget(company_name, alignment=Qt.AlignmentFlag.AlignCenter)

        tagline = QLabel("Innovating Financial Technology")
        tagline.setStyleSheet("""
            QLabel {
                color: #7E8CAC;
                font-size: 16px;
                margin-top: 15px;
                letter-spacing: 1px;
            }
        """)
        left_layout.addWidget(tagline, alignment=Qt.AlignmentFlag.AlignCenter)

        # Right signup form
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: white; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)

        # Signup container
        signup_container = QFrame()
        signup_container.setFixedWidth(380)
        signup_container.setStyleSheet("QFrame { background-color: white; border-radius: 12px; }")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 4)
        signup_container.setGraphicsEffect(shadow)

        signup_layout = QVBoxLayout(signup_container)
        signup_layout.setSpacing(5)  # Increased spacing between elements
        signup_layout.setContentsMargins(5, 10, 5, 10)

        welcome_label = QLabel("Create Account")
        welcome_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: #041E42; margin-bottom: 5px;")

        subtitle_label = QLabel("Fill in your details to get started")
        subtitle_label.setStyleSheet("color: #666666; font-size: 15px;")

        signup_layout.addWidget(welcome_label)
        signup_layout.addWidget(subtitle_label)
        signup_layout.addSpacing(10)

        # Form fields
        field_style = """
            QLineEdit {
                padding: 5px;
                padding-left: 20px;
                background-color: #F7F9FC;
                border: 2px solid #EDF2F7;
                border-radius: 10px;
                color: #041E42;
                font-size: 13px;
                min-height: 45px;
            }
            QLineEdit:focus {
                border: 2px solid #041E42;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #A0AEC0;
            }
        """

        label_style = """
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """


        # Email
        email_label = QLabel("Email Address")
        email_label.setStyleSheet(label_style)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setStyleSheet(field_style)

        # Username
        username_label = QLabel("Username")
        username_label.setStyleSheet(label_style)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        self.username_input.setStyleSheet(field_style)

        # Password
        password_label = QLabel("Create Password")
        password_label.setStyleSheet(label_style)
        self.password_input = PasswordLineEdit("Create a strong password")

        # Confirm Password
        confirm_password_label = QLabel("Confirm Password")
        confirm_password_label.setStyleSheet(label_style)
        self.confirm_password_input = PasswordLineEdit("Confirm your password")
        # Add password strength indicator
        self.password_strength_label = QLabel()
        self.password_strength_label.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        font-weight: bold;
                        margin-top: 5px;
                    }
                """)




        # Connect password input to strength checker
        self.password_input.password_input.textChanged.connect(self.update_password_strength)
        # Add strength indicators to layout after password field
        signup_layout.addWidget(self.password_strength_label)

        # Add fields to layout with proper spacing
        field_pairs = [
            (username_label, self.username_input),
            (email_label, self.email_input),
            (password_label, self.password_input),
            (confirm_password_label, self.confirm_password_input)
        ]


        # Add fields to layout with proper spacing
        # Username
        signup_layout.addWidget(username_label)
        signup_layout.addWidget(self.username_input)
        signup_layout.addSpacing(20)

        # Email
        signup_layout.addWidget(email_label)
        signup_layout.addWidget(self.email_input)
        signup_layout.addSpacing(20)

        # Password with strength label
        signup_layout.addWidget(password_label)
        signup_layout.addWidget(self.password_input)
        signup_layout.addWidget(self.password_strength_label)
        signup_layout.addSpacing(20)

        # Confirm Password
        signup_layout.addWidget(confirm_password_label)
        signup_layout.addWidget(self.confirm_password_input)
        signup_layout.addSpacing(20)
        # Create Account button
        signup_button = QPushButton("Create Account")
        signup_button.setMinimumHeight(55)
        signup_button.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_button.setStyleSheet("""
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
        signup_button.clicked.connect(self.handle_signup)
        signup_layout.addSpacing(10)
        signup_layout.addWidget(signup_button)

        # Login link
        login_layout = QHBoxLayout()
        login_text = QLabel("Already have an account?")
        login_text.setStyleSheet("color: #4A5568; font-size: 14px;")
        login_button = QPushButton("Sign In")
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.setStyleSheet("""
            QPushButton {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                border: none;
                background: transparent;
                padding: 5px;
            }
            QPushButton:hover {
                color: #1A365D;
                text-decoration: underline;
            }
        """)

        login_button.clicked.connect(self.switch_to_login_page)

        login_layout.addStretch()
        login_layout.addWidget(login_text)
        login_layout.addWidget(login_button)
        login_layout.addStretch()

        signup_layout.addSpacing(20)
        signup_layout.addLayout(login_layout)

        # Add container to right panel
        right_layout.addStretch()
        right_layout.addWidget(signup_container, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addStretch()

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def switch_to_login_page(self):
        self.hide()  # Hide the signup window
        self.switch_to_login.emit()  # Emit the signal to show login window

    def check_password_strength(self, password):
        score = 0
        length = len(password)

        # Length check
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1

        # Complexity checks
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(not c.isalnum() for c in password):
            score += 1

        # Return strength assessment
        if score >= 5:
            return "Strong", "#00AA00"  # Green
        elif score >= 3:
            return "Medium", "#FFA500"  # Orange
        else:
            return "Weak", "#FF4444"  # Red

    def update_password_strength(self):
        password = self.password_input.text()
        strength, color = self.check_password_strength(password)

        self.password_strength_label.setText(f"Password Strength: {strength}")
        self.password_strength_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 13px;
                font-weight: bold;
                margin-top: 5px;
            }}
        """)

    def handle_signup(self):
        # Get input values
        email = self.email_input.text()
        username = self.username_input.text()
        password = self.password_input.text()  # Changed: use text() method
        confirm_password = self.confirm_password_input.text()  # Changed: use text() method

        # Basic validation
        if not all([email, username, password, confirm_password]):
            QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
            return

        # Email validation
        if not '@' in email or not '.' in email:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address.")
            return

        # More comprehensive email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            QMessageBox.warning(self, "Validation Error",
                                "Invalid email format. Please enter a valid email address (e.g., user@example.com)")
            return

        # Check if passwords match
        if password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return

        # Validate password strength
        if len(password) < 8:
            QMessageBox.warning(self, "Validation Error",
                                "Password must be at least 8 characters long.")
            return

        # Check for password complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if not all([has_upper, has_lower, has_digit, has_special]):
            QMessageBox.warning(self, "Validation Error",
                                "Password must contain uppercase, lowercase, number, and special character.")
            return

        try:
            # Create database connection and store user
            db = DatabaseConnection()
            success, message = db.create_user(username, email, password)

            if success:
                QMessageBox.information(self, "Success", "Account created successfully! Please login.")
                # Clear the input fields
                self.email_input.clear()
                self.username_input.clear()
                self.password_input.clear()
                self.confirm_password_input.clear()
                # Switch to login page
                self.hide()
                self.switch_to_login.emit()
            else:
                QMessageBox.warning(self, "Error", message)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = SignupWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()