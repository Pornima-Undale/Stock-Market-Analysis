from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class BaseNavigationWindow(QMainWindow):
    """Base class for all navigation windows"""
    switch_to_dashboard = pyqtSignal()

    def __init__(self, title, user_id=None):
        """
        Initialize the base navigation window.

        :param title: Window title
        :param user_id: Optional user ID
        """
        super().__init__()

        # Store user_id if passed
        self.user_id = user_id

        try:
            from database import DatabaseConnection
            self.db = DatabaseConnection()
            print(f"✅ Database connection established in {title}")
        except Exception as e:
            print(f"❌ Database connection error in {title}: {e}")
            self.db = None

        # Set window title
        self.setWindowTitle(f"SARASFINTECH - {title}")

        self.setMinimumSize(1400, 900)

        # Set base style
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
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #041E42;
                margin-bottom: 20px;
            }
            #backButton {
                background-color: #666;
                color: white;
                font-weight: bold;
            }
            #backButton:hover {
                background-color: #444;
            }
        """)

        # Create central widget
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.setCentralWidget(self.central_widget)

        # Create header with title
        self.create_header(title)

        # Create status bar
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #041E42;
                color: white;
                padding: 5px;
            }
        """)

    def create_header(self, title):
        """Create header with title and back button"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)

        # Back button
        back_button = QPushButton("← Back to Dashboard")
        back_button.setObjectName("backButton")
        back_button.setMaximumWidth(200)
        back_button.clicked.connect(self.return_to_dashboard)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add to layout
        header_layout.addWidget(back_button)
        header_layout.addWidget(title_label)
        header_layout.addStretch()  # Push title to center

        self.main_layout.addWidget(header_frame)

    def return_to_dashboard(self):
        """Return to the main dashboard"""
        self.hide()
        self.switch_to_dashboard.emit()
        self.statusBar().showMessage('Returning to Dashboard...')