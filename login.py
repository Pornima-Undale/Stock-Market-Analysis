from database import DatabaseConnection
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFrame, QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor
from signup import SignupWindow
from forgot_pass import ForgotPasswordWindow


class LoginWindow(QMainWindow):
    switch_to_signup = pyqtSignal()  # Class-level signal

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

    def __init__(self):
        super().__init__()
        self.initUI()
        self.forgot_password_window = None
        self.signup_window = None
        self.dashboard = None

    def initUI(self):
        # Set window properties
        self.setWindowTitle('SARASFINTECH - Enterprise Portal')
        self.setMinimumSize(1550, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create left side (branding panel)
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #041E42;
                border: none;
            }
        """)
        left_panel.setFixedWidth(500)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setContentsMargins(40, 40, 40, 40)

        # Company logo/name
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

        # Tagline
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

        # Additional branding text
        branding_text = QLabel("Secure • Reliable • Innovative")
        branding_text.setStyleSheet("""
            QLabel {
                color: #4A5D84;
                font-size: 14px;
                margin-top: 20px;
                letter-spacing: 2px;
            }
        """)
        left_layout.addWidget(branding_text, alignment=Qt.AlignmentFlag.AlignCenter)

        # Create right side (login form)
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: white;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)

        # Create login container
        login_container = QFrame()
        login_container.setFixedWidth(420)
        login_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 4)
        login_container.setGraphicsEffect(shadow)

        # Login form layout
        login_layout = QVBoxLayout(login_container)
        login_layout.setSpacing(15)
        login_layout.setContentsMargins(40, 50, 40, 50)

        # Welcome text
        welcome_label = QLabel("Welcome")
        welcome_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: #041E42; margin-bottom: 5px;")

        subtitle_label = QLabel("Sign in to your account to continue")
        subtitle_label.setStyleSheet("color: #666666; font-size: 15px;")

        login_layout.addWidget(welcome_label)
        login_layout.addWidget(subtitle_label)
        login_layout.addSpacing(20)

        # Username field
        username_label = QLabel("Username")
        username_label.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(55)
        self.username_input.setStyleSheet("""
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

        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)

        # Create password container
        password_container = QFrame()
        password_container.setStyleSheet("""
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
        password_container_layout = QHBoxLayout(password_container)
        password_container_layout.setContentsMargins(20, 0, 10, 0)
        password_container_layout.setSpacing(5)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #041E42;
                font-size: 14px;
                min-height: 45px;
            }
            QLineEdit::placeholder {
                color: #A0AEC0;
            }
        """)

        # Add toggle password visibility
        self.toggle_password = self.CustomCheckBox()
        self.toggle_password.callback = self.toggle_password_visibility

        # Add widgets to password container
        password_container_layout.addWidget(self.password_input)
        password_container_layout.addWidget(self.toggle_password)

        # Forgot password layout
        options_layout = QHBoxLayout()
        options_layout.addStretch()  # This will push the forgot password button to the right

        forgot_password = QPushButton("Forgot password?")
        forgot_password.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot_password.setStyleSheet("""
            QPushButton {
                color: #041E42;
                font-size: 13px;
                font-weight: bold;
                text-align: right;
                border: none;
                background: transparent;
                padding: 5px;
            }
            QPushButton:hover {
                color: #1A365D;
                text-decoration: underline;
            }
        """)
        forgot_password.clicked.connect(self.show_forgot_password)
        options_layout.addWidget(forgot_password)

        # Login button
        login_button = QPushButton("Sign In to Account")
        login_button.setMinimumHeight(55)
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.setStyleSheet("""
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
        login_button.clicked.connect(self.handle_login)

        # Divider
        divider_layout = QHBoxLayout()
        divider_layout.setSpacing(15)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("background-color: #EDF2F7;")

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("background-color: #EDF2F7;")

        divider_layout.addWidget(line1)
        divider_layout.addWidget(line2)

        # Sign up link
        signup_container = QHBoxLayout()
        signup_text = QLabel("Don't have an account?")
        signup_text.setStyleSheet("color: #4A5568; font-size: 14px;")

        signup_link = QPushButton("Sign up here")
        signup_link.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_link.setStyleSheet("""
            QPushButton {
                color: #041E42;
                font-size: 14px;
                text-decoration: underline;
                border: none;
                background: transparent;
                padding: 5px;
                margin-left: 5px;
            }
            QPushButton:hover {
                color: #1A365D;
            }
        """)
        signup_link.clicked.connect(self.switch_to_signup_page)

        signup_container.addStretch()
        signup_container.addWidget(signup_text)
        signup_container.addWidget(signup_link)
        signup_container.addStretch()

        # Add all elements to login layout
        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)
        login_layout.addWidget(password_label)
        login_layout.addWidget(password_container)
        login_layout.addLayout(options_layout)
        login_layout.addSpacing(10)
        login_layout.addWidget(login_button)
        login_layout.addSpacing(20)
        login_layout.addLayout(divider_layout)
        login_layout.addSpacing(20)
        login_layout.addLayout(signup_container)

        # Add a secure connection indicator
        secure_layout = QHBoxLayout()
        secure_text = QLabel("Secure Enterprise Connection")
        secure_text.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 12px;
                margin-left: 5px;
            }
        """)
        secure_layout.addStretch()
        secure_layout.addWidget(secure_text)
        secure_layout.addStretch()
        login_layout.addSpacing(20)
        login_layout.addLayout(secure_layout)

        # Add login container to right panel
        right_layout.addStretch()
        right_layout.addWidget(login_container, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addStretch()

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password.")
            return

        try:
            db = DatabaseConnection()
            success, result = db.verify_login(username, password)

            if success:
                # Store user information in the session
                self.user_id = result['user_id']
                self.username = result['user_name']

                # Create welcome animation as a standalone window
                from welcome_animation import WelcomeAnimation
                self.welcome_screen = WelcomeAnimation(username, parent=self)

                # Make it the same size as login window and in same position
                if self.isMaximized():
                    self.welcome_screen.showMaximized()
                else:
                    self.welcome_screen.setGeometry(self.geometry())
                    self.welcome_screen.show()

                # Hide this login window now that the welcome screen is shown
                self.hide()

                # Process events to ensure animation window is displayed
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
            else:
                QMessageBox.warning(self, "Error", result)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
            import traceback
            traceback.print_exc()

    def create_dashboard(self):
        """Create dashboard only when needed (called by welcome animation)"""
        try:
            print("Starting dashboard creation...")

            from dashboard import StockDashboard

            # Create dashboard with user information
            self.dashboard = StockDashboard(user_id=self.user_id, username=self.username)

            # Set up connections to show windows
            self.dashboard.portfolio_window.user_id = self.user_id
            self.dashboard.watchlist_window.user_id = self.user_id
            self.dashboard.analytics_window.user_id = self.user_id

            # Make dashboard visible
            self.dashboard.showMaximized()
            self.dashboard.statusBar().showMessage(f'Welcome to SARASFINTECH Dashboard, {self.username}')

            print("Dashboard creation and display complete")

        except Exception as e:
            print(f"ERROR creating dashboard: {str(e)}")
            import traceback
            traceback.print_exc()


    def switch_to_signup_page(self):
        self.hide()
        self.switch_to_signup.emit()

    def show_login(self):
        if self.signup_window:
            self.signup_window.hide()
        self.show()

    def closeEvent(self, event):
        if self.signup_window:
            self.signup_window.close()
        if self.forgot_password_window:
            self.forgot_password_window.close()
        event.accept()

    def show_forgot_password(self):
        self.forgot_password_window = ForgotPasswordWindow()
        # Check if signal exists before connecting
        if hasattr(self.forgot_password_window, 'back_to_login'):
            self.forgot_password_window.back_to_login.connect(self.show)
        self.hide()  # Hide login window
        self.forgot_password_window.show()  # Show forgot password window

    def toggle_password_visibility(self, checked):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )


def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()