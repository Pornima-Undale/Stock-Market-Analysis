from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFrame, QScrollArea, QWidget, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from navigation_windows import BaseNavigationWindow
import os


class AboutUsWindow(BaseNavigationWindow):
    """About Us window for SARASFINTECH"""

    def __init__(self, title="About Us", user_id=None):
        super().__init__(title, user_id)

        # Initialize UI
        self.setup_ui()

    def setup_ui(self):
        """Set up the About Us UI"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
            QScrollBar:vertical {
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #041E42;
                border-radius: 5px;
            }
        """)

        # Create content widget for scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 20, 40, 40)
        content_layout.setSpacing(30)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Hero section
        hero_frame = QWidget()
        hero_layout = QHBoxLayout(hero_frame)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Left side - Stock market image
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # In your setup_ui method, replace the existing image loading code with this:

        image_label = QLabel()
        image_path = "images/stock_market.jpeg"  # The path to your image

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
            print(f"Successfully loaded image from: {image_path}")
        else:
            # Display a message if the image can't be found
            image_label.setText("Image Not Found")
            image_label.setStyleSheet("""
                background-color: #f0f0f0; 
                padding: 80px; 
                border-radius: 10px;
                font-weight: bold;
                color: #777;
                text-align: center;
            """)
            print(f"Could not find image at: {image_path}")
            # Print the current working directory to help with debugging
            print(f"Current working directory: {os.getcwd()}")

        '''if pixmap:
            pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)'''

        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(image_label)

        # Right side - Company info
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Company name
        company_title = QLabel("SARASFINTECH")
        company_title.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        company_title.setStyleSheet("color: #041E42;")
        company_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tagline
        tagline = QLabel("Empowering Investors with Smart Financial Technology")
        tagline.setFont(QFont("Segoe UI", 16))
        tagline.setStyleSheet("color: #1565C0; margin-top: 10px;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Brief intro
        intro = QLabel("we're on a mission to simplify the complex world of investing")
        intro.setFont(QFont("Segoe UI", 12))
        intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro.setWordWrap(True)

        info_layout.addWidget(company_title)
        info_layout.addWidget(tagline)
        info_layout.addWidget(intro)

        # Add to hero layout
        hero_layout.addWidget(image_container)
        hero_layout.addWidget(info_container)

        content_layout.addWidget(hero_frame)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0; min-height: 2px;")
        content_layout.addWidget(separator)

        # Sections with consistent styling
        sections = [
            {
                "title": "About Us",
                "content": "SARASFINTECH is a leading financial technology company specializing in stock market analysis and portfolio management "
                          "solutions. We provide cutting-edge tools and insights to help investors make informed decisions and achieve their "
                          "financial goals. Our platform combines real-time market data, advanced analytics, and a user-friendly interface to deliver a "
                          "comprehensive investment experience."
            },
            {
                "title": "Our Mission",
                "content": "To democratize financial markets by providing accessible, powerful, and intuitive tools that empower investors "
                          "of all levels to make informed decisions, manage risk effectively, and achieve their financial objectives."
            }
        ]

        for section in sections:
            # Section Title
            section_title = QLabel(section["title"])
            section_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            section_title.setStyleSheet("color: #041E42; margin-top: 10px;")
            section_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(section_title)

            # Section Content
            section_content = QLabel(section["content"])
            section_content.setFont(QFont("Segoe UI", 12))
            section_content.setWordWrap(True)
            section_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            section_content.setMaximumWidth(1000)  # Control line length
            section_content.setStyleSheet("""
                padding: 0 20px;
                line-height: 1.6;
            """)
            content_layout.addWidget(section_content)

        # Leadership section
        team_title = QLabel("Our Leadership Team")
        team_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        team_title.setStyleSheet("color: #041E42; margin-top: 10px;")
        team_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(team_title)

        # Team member
        member = QLabel("Deepali Bhangale - Founder & CEO")
        member.setFont(QFont("Segoe UI", 14))
        member.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(member)

        # Contact section
        contact_title = QLabel("Contact Us")
        contact_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        contact_title.setStyleSheet("color: #041E42; margin-top: 10px;")
        contact_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(contact_title)

        address = QLabel(
            "Address: SARASFINTECH, B2/105, Atul Nagar Phase-2, Warje, Pune-411058")
        address.setFont(QFont("Segoe UI", 12))
        address.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address.setWordWrap(True)
        address.setStyleSheet("""
            padding: 0 20px;
            line-height: 1.6;
        """)
        content_layout.addWidget(address)

        # Add final spacing
        content_layout.addStretch()

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(scroll_area)