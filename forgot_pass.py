from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFrame,
                             QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import DatabaseConnection


class ForgotPasswordWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.otp = None
        self.user_email = None

    def initUI(self):
        self.setWindowTitle('SARASFINTECH - Forgot Password')
        self.setMinimumSize(1250, 800)
        self.setStyleSheet("QMainWindow {background-color: #f5f5f5;}")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create container for the form
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        container_layout = QVBoxLayout(container)

        # Form container with shadow
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
        form_layout.setContentsMargins(10, 20, 10, 20)

        # Title
        title_label = QLabel("Forgot Password")
        title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #041E42; margin-bottom: 5px;")

        subtitle_label = QLabel("Enter your email to reset your password")
        subtitle_label.setStyleSheet("color: #666666; font-size: 15px;")

        # Email input
        email_label = QLabel("Email Address")
        email_label.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setMinimumHeight(55)
        self.email_input.setStyleSheet("""
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

        # OTP input (initially hidden)
        self.otp_label = QLabel("Enter OTP")
        self.otp_label.setStyleSheet("""
            QLabel {
                color: #041E42;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        self.otp_label.hide()

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter 6-digit OTP")
        self.otp_input.setMaxLength(6)
        self.otp_input.setMinimumHeight(55)
        self.otp_input.setStyleSheet("""
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
        self.otp_input.hide()

        # Send OTP button
        self.send_otp_button = QPushButton("Send OTP")
        self.send_otp_button.setMinimumHeight(55)
        self.send_otp_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_otp_button.setStyleSheet("""
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
        """)
        self.send_otp_button.clicked.connect(self.send_otp)

        # Verify OTP button (initially hidden)
        self.verify_otp_button = QPushButton("Verify OTP")
        self.verify_otp_button.setMinimumHeight(55)
        self.verify_otp_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.verify_otp_button.setStyleSheet("""
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
        """)
        self.verify_otp_button.clicked.connect(self.verify_otp)
        self.verify_otp_button.hide()

        # Back to login button
        back_button = QPushButton("Back to Login")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet("""
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
        back_button.clicked.connect(self.handle_back)

        # Add widgets to form layout
        form_layout.addWidget(title_label)
        form_layout.addWidget(subtitle_label)
        form_layout.addSpacing(20)
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.otp_label)
        form_layout.addWidget(self.otp_input)
        form_layout.addSpacing(20)
        form_layout.addWidget(self.send_otp_button)
        form_layout.addWidget(self.verify_otp_button)
        form_layout.addSpacing(10)
        form_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add form container to the center of the main layout
        container_layout.addStretch()
        container_layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignCenter)
        container_layout.addStretch()

        main_layout.addWidget(container)

    def send_otp(self):
        email = self.email_input.text()
        if not email:
            QMessageBox.warning(self, "Error", "Please enter your email address.")
            return

        try:
            # Verify email exists in database
            db = DatabaseConnection()
            print(f"Checking email in database: {email}")  # Debug print

            email_exists = db.verify_email(email)
            print(f"Email exists in database: {email_exists}")  # Debug print

            if not email_exists:
                QMessageBox.warning(self, "Error", "Email not found in our records.")
                return

            # Generate OTP
            self.otp = ''.join(random.choices(string.digits, k=6))
            self.user_email = email

            # Email configuration
            sender_email = "pornimaundale@gmail.com"
            sender_password = "bfrx cpoe mxxd xcio"

            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = email
            message["Subject"] = "Password Reset OTP - SARASFINTECH"

            body = f"""
            Your OTP for password reset is: {self.otp}

            This OTP will expire in 10 minutes.
            If you didn't request this, please ignore this email.

            Best regards,
            SARASFINTECH Team
            """
            message.attach(MIMEText(body, "plain"))

            # Create SMTP_SSL session
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, sender_password)
            server.send_message(message)
            server.quit()

            # Show OTP input and verify button
            self.otp_label.show()
            self.otp_input.show()
            self.verify_otp_button.show()
            self.send_otp_button.setText("Resend OTP")

            QMessageBox.information(self, "Success", "OTP has been sent to your email.")

        except Exception as e:
            print(f"Error in send_otp: {str(e)}")  # Debug print
            QMessageBox.critical(self, "Error", f"Failed to send OTP: {str(e)}")

    def verify_otp(self):
        entered_otp = self.otp_input.text()
        if entered_otp == self.otp:
            # Open reset password window
            from reset_password import ResetPasswordWindow
            self.reset_window = ResetPasswordWindow(self.user_email)
            self.reset_window.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Error", "Invalid OTP. Please try again.")

    def handle_back(self):
        from login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.hide()