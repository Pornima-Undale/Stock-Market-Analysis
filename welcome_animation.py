from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QApplication, QMainWindow)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt6.QtGui import QFont
import sys


class WelcomeAnimation(QWidget):
    def __init__(self, username, parent=None, dashboard=None):
        super().__init__(None)  # Create as independent window
        self.username = username
        self.dashboard = dashboard
        self.parent_window = parent  # Store reference to parent window
        self.animation_finished = False
        self.animation_started = False
        self.initUI()

    def initUI(self):
        # Set window properties
        self.setWindowTitle('SARASFINTECH - Welcome')
        self.setMinimumSize(1550, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create animation container frame
        self.animation_container = QFrame()
        self.animation_container.setFixedSize(1200, 300)
        self.animation_container.setStyleSheet("background-color: white;")

        # Welcome message with username in one frame
        self.welcome_frame = QFrame(self.animation_container)
        self.welcome_frame.setFixedSize(1100, 150)
        self.welcome_frame.setStyleSheet("background-color: white;")
        welcome_layout = QVBoxLayout(self.welcome_frame)
        welcome_layout.setContentsMargins(0, 0, 0, 0)

        # Create combined welcome message with username
        welcome_text = QLabel(f"Welcome to SARASFINTECH, {self.username}")
        welcome_text.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 48px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        welcome_layout.addWidget(welcome_text)

        # Position welcome text off-screen to the left initially
        self.welcome_frame.move(-1100, 100)

        # Add container to main layout
        main_layout.addWidget(self.animation_container)

        # Print a debug message to show we've initialized the UI
        print("Welcome animation UI initialized")

        # Install event filter to track painting events
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        # Check for paint event to ensure the window is actually being drawn
        if event.type() == QEvent.Type.Paint and not self.animation_started:
            print("Paint event detected - starting animation")
            self.animation_started = True
            QTimer.singleShot(50, self.start_animation_sequence)
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        # This ensures the animation starts only when the widget is actually shown
        super().showEvent(event)
        print("Welcome animation window shown")

        # Ensure window is at the front
        self.raise_()
        self.activateWindow()

        # Force a repaint to trigger the event filter
        self.repaint()

    def start_animation_sequence(self):
        # Print debug message
        print("Animation sequence started")

        # Slide in welcome text from left
        self.welcome_anim = QPropertyAnimation(self.welcome_frame, b"pos")
        self.welcome_anim.setDuration(500)  # Slightly slower for better effect
        self.welcome_anim.setStartValue(QPoint(-1100, 100))
        self.welcome_anim.setEndValue(QPoint(100, 100))
        self.welcome_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.welcome_anim.finished.connect(self.prepare_exit)
        self.welcome_anim.start()

        # Process events to ensure animation is visible
        QApplication.processEvents()

    def prepare_exit(self):
        # Print debug message
        print("Welcome text animation finished, preparing to exit")
        self.animation_finished = True

        # Wait 1.5 seconds to let user see the welcome message, then transition
        QTimer.singleShot(30, self.transition_to_dashboard)

    def transition_to_dashboard(self):
        try:
            print("Starting dashboard transition...")
            from dashboard import StockDashboard

            # Create dashboard with proper parameters
            user_id = 1  # Default value
            if hasattr(self.parent_window, 'user_id'):
                user_id = self.parent_window.user_id

            if hasattr(self.parent_window, 'username_input'):
                username = self.parent_window.username_input.text()
            else:
                username = self.username

            # Create dashboard
            dashboard = StockDashboard(user_id=user_id, username=username)

            # Get current window position and size
            current_pos = self.pos()
            current_size = self.size()
            is_maximized = self.isMaximized()

            # Close the welcome animation window
            self.hide()  # Hide first to avoid flickering
            self.close()

            # Set dashboard window position and size to match welcome window
            if is_maximized:
                dashboard.showMaximized()
            else:
                dashboard.setGeometry(current_pos.x(), current_pos.y(),
                                      current_size.width(), current_size.height())
                dashboard.show()

            # Update dashboard status bar
            dashboard.statusBar().showMessage(f'Welcome to SARASFINTECH Dashboard, {username}')

            # Trigger initial data fetch
            dashboard.fetch_stock_data()

            print("Dashboard transition complete")

        except Exception as e:
            print(f"ERROR in transition_to_dashboard: {str(e)}")
            import traceback
            traceback.print_exc()

            # If dashboard creation fails, return to login window
            try:
                if self.parent_window and hasattr(self.parent_window, 'show'):
                    self.close()
                    self.parent_window.show()
            except:
                pass