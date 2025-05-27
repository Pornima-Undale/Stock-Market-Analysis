from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QFont, QScreen
import sys
from admin_dashboard import AdminDashboard
from database_manager import DatabaseManager


class AdminLoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize database connection
        self.db_manager = DatabaseManager.get_instance()
        self.init_ui()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle('SARASFINTECH - Admin Login')

        # Set window to desktop size
        self.resize_to_desktop()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                font-family: 'Segoe UI';
                color: #333;
                border: none;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #041E42;
            }
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            QPushButton:pressed {
                background-color: #030F21;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)

        # Create a centered login container
        login_container = QFrame()
        login_container.setFixedSize(400, 500)
        login_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ddd;
            }
        """)

        # Center the login container in the window
        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(login_container)
        container_layout.addStretch()

        # Login form layout
        login_layout = QVBoxLayout(login_container)
        login_layout.setContentsMargins(40, 40, 40, 40)
        login_layout.setSpacing(20)

        # Add logo label
        logo_label = QLabel('SARASFINTECH')
        logo_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #041E42;
            margin-bottom: 20px;
            border: none;
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setMinimumHeight(50)  # Set a minimum height for the label

        # Add admin panel label
        admin_label = QLabel('Admin Panel')
        admin_label.setStyleSheet("""
            font-size: 20px;
            color: #555;
            margin-bottom: 30px;
            border: none;
        """)
        admin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        admin_label.setMinimumHeight(30)  # Set a minimum height for the label

        # Add username input
        username_label = QLabel('Username')
        username_label.setStyleSheet("border: none;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter admin username')
        self.username_input.setFixedHeight(40)

        # Add password input
        password_label = QLabel('Password')
        password_label.setStyleSheet("border: none;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter admin password')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(40)

        # Add show password checkbox
        self.show_password_checkbox = QCheckBox('Show password')
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)

        # Add login button
        login_button = QPushButton('Login')
        login_button.setFixedHeight(45)
        login_button.clicked.connect(self.handle_login)

        # Add status label
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #dc3545; font-size: 14px;')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add widgets to login layout
        login_layout.addWidget(logo_label)
        login_layout.addWidget(admin_label)
        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)
        login_layout.addWidget(password_label)
        login_layout.addWidget(self.password_input)
        login_layout.addWidget(self.show_password_checkbox)
        login_layout.addWidget(login_button)
        login_layout.addWidget(self.status_label)
        login_layout.addStretch()

        # Add container to main layout
        main_layout.addStretch()
        main_layout.addLayout(container_layout)
        main_layout.addStretch()

        # Set enter key to trigger login
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    def resize_to_desktop(self):
        """Resize window to match desktop size"""
        # Get the screen size using QScreen (PyQt6 approach)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())

    def handle_login(self):
        # Get username and password
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Validate inputs
        if not username or not password:
            self.status_label.setText("Please enter both username and password")
            self.shake_window()
            return

        try:
            # For debugging: temporary hardcoded login
            if username == "admin" and password == "admin123":
                self.status_label.setText("")
                self.open_admin_dashboard()
                return

            # Check admin credentials in database
            query = "SELECT * FROM admin WHERE admin_name = %s AND password = %s"
            success, error = self.db_manager.execute_query(query, (username, password))

            if not success:
                self.status_label.setText(f"Login error: {error}")
                self.shake_window()
                return

            admin = self.db_manager.fetchone()

            if admin:
                # Update last login time
                update_query = "UPDATE admin SET last_login = NOW() WHERE admin_id = %s"
                self.db_manager.execute_query(update_query, (admin['admin_id'],), commit=True)

                self.status_label.setText("")
                self.open_admin_dashboard()
            else:
                self.status_label.setText("Invalid username or password")
                self.shake_window()

        except Exception as e:
            self.status_label.setText(f"Login error: {str(e)}")
            self.shake_window()

    def shake_window(self):
        # Find the login container (it's the first QFrame in our central widget)
        login_container = self.centralWidget().findChild(QFrame)
        if not login_container:
            return

        # Create shaking effect for invalid login on the container, not the whole window
        original_pos = login_container.pos()
        for i in range(10):
            offset = 5 if i % 2 == 0 else -5
            login_container.move(original_pos.x() + offset, original_pos.y())
            QApplication.processEvents()
            QTimer.singleShot(50, lambda: None)
        login_container.move(original_pos)

    def open_admin_dashboard(self):
        # Hide login window
        self.hide()

        # Open admin dashboard
        self.admin_dashboard = AdminDashboard()
        self.admin_dashboard.show()

        # Connect logout signal
        self.admin_dashboard.logout_signal.connect(self.show_login_again)

    def show_login_again(self):
        # Clear inputs
        self.username_input.clear()
        self.password_input.clear()

        # Show login window again
        self.show()

    def closeEvent(self, event):
        # Close database connection when the window is closed
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        event.accept()

    def toggle_password_visibility(self, state):
        if state == Qt.CheckState.Checked.value:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)