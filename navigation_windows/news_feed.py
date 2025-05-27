import sys
import requests
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QScrollArea, QHBoxLayout,
                             QLineEdit, QFrame, QComboBox, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from navigation_windows import BaseNavigationWindow


class StyledLabel(QLabel):
    def __init__(self, text, font_size=10, bold=False, color=None):
        super().__init__(text)
        font = QFont('Segoe UI', font_size)
        if bold:
            font.setBold(True)
        self.setFont(font)
        if color:
            self.setStyleSheet(f'color: {color};')


class NewsCard(QFrame):
    def __init__(self, news_data):
        super().__init__()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QComboBox, QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                min-width: 250px;
                background-color: white;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 1px solid #041E42;
            }
            QPushButton {
                background-color: #041E42;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)

        # Keep a reference to the network manager to prevent it from being garbage collected
        self.manager = None

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove internal margins

        # Add horizontal layout for image and text
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Add image if available (larger image like MoneyControl)
        image_url = news_data.get('image', '')
        if image_url:
            try:
                # Create a QLabel for the image
                image_label = QLabel()
                image_label.setFixedSize(180, 120)  # Larger image
                image_label.setStyleSheet("""
                    border: 1px solid #eee; 
                    border-radius: 4px;
                    background-color: #f9f9f9;
                """)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_label.setText("Loading...")

                # Load image asynchronously
                self.manager = QNetworkAccessManager()
                self.manager.finished.connect(lambda reply: self.set_image(reply, image_label))
                self.manager.get(QNetworkRequest(QUrl(image_url)))

                content_layout.addWidget(image_label)
                content_layout.addSpacing(15)
            except Exception as img_error:
                print(f"Error loading image: {img_error}")

        # Create text layout with improved styling
        text_layout = QVBoxLayout()
        text_layout.setSpacing(12)  # More spacing between elements

        # Category tag on top of title (like MoneyControl)
        category_text = str(news_data.get('category', news_data.get('related', 'Markets')))
        category = QLabel(category_text.upper())  # Uppercase for category
        category.setStyleSheet("""
            color: #1665C0;
            font-size: 12px;
            font-weight: bold;
        """)
        text_layout.addWidget(category)

        # Title with better styling
        title_text = str(news_data.get('headline', news_data.get('title', 'Untitled News')))
        title = QLabel(title_text)
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #222;
            line-height: 1.3;
        """)
        title.setWordWrap(True)
        text_layout.addWidget(title)

        # Summary with character limit like MoneyControl (showing partial text)
        desc_text = str(news_data.get('summary', news_data.get('description', 'No summary available')))
        # Limit to ~150 characters
        if len(desc_text) > 150:
            desc_text = desc_text[:147] + '...'

        summary = QLabel(desc_text)
        summary.setStyleSheet("""
            font-size: 14px;
            color: #555;
            line-height: 1.4;
        """)
        summary.setWordWrap(True)
        text_layout.addWidget(summary)

        # Add text layout to content layout with stretch
        content_layout.addLayout(text_layout, 1)

        # Add content layout to main layout
        layout.addLayout(content_layout)

        # Bottom row with source and time
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 0, 10, 10)

        # Source with icon (like MoneyControl)
        source_text = news_data.get('source', 'Finnhub')
        source = QLabel(f"📰 {source_text}")
        source.setStyleSheet("color: #666; font-size: 12px;")

        # Time with icon
        publish_time = news_data.get('datetime', news_data.get('publishedAt', ''))
        time_text = self.format_time(publish_time)
        time = QLabel(f"🕒 {time_text}")
        time.setStyleSheet("color: #666; font-size: 12px;")

        bottom_layout.addWidget(source)
        bottom_layout.addStretch()
        bottom_layout.addWidget(time)

        # Add separator line before bottom layout
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #eee; max-height: 1px; margin: 5px 10px;")
        layout.addWidget(separator)

        layout.addLayout(bottom_layout)

    def set_image(self, reply, label):
        """Set the image from network reply"""
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readAll())
                if not pixmap.isNull():
                    label.setPixmap(pixmap)
                    label.setScaledContents(True)
                else:
                    label.setText("Image Error")
            else:
                label.setText("Load Failed")
            reply.deleteLater()
        except Exception as e:
            print(f"Error in set_image: {e}")
            label.setText("Error")

    def format_time(self, publish_time):
        """Convert time to readable format with robust error handling"""
        if not publish_time:
            return "Unknown time"

        try:
            # Check if timestamp is in Unix format (Finnhub uses this)
            if isinstance(publish_time, (int, float)) or (isinstance(publish_time, str) and publish_time.isdigit()):
                timestamp = int(float(publish_time))
                dt = datetime.fromtimestamp(timestamp)
            else:
                # Try ISO format parsing
                if isinstance(publish_time, str):
                    publish_time = publish_time.replace('Z', '+00:00')
                    try:
                        dt = datetime.fromisoformat(publish_time)
                    except ValueError:
                        try:
                            dt = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            return "Invalid time"
                else:
                    return "Unknown format"

            # Calculate time difference
            now = datetime.now(dt.tzinfo if dt.tzinfo else None)
            time_diff = now - dt

            # Format time
            if time_diff.days > 0:
                return f"{time_diff.days} days ago"
            elif time_diff.seconds // 3600 > 0:
                return f"{time_diff.seconds // 3600} hours ago"
            elif time_diff.seconds // 60 > 0:
                return f"{time_diff.seconds // 60} minutes ago"
            else:
                return "Just now"
        except Exception as e:
            print(f"Time formatting error: {e}")
            return "Unknown time"


class NewsFeedWindow(BaseNavigationWindow):
    switch_to_dashboard = pyqtSignal()

    def __init__(self,title="news_feed"):
        super().__init__(title)
        self.setWindowTitle('SARASFINTECH - Market News')
        self.setGeometry(0, 0, 1700, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QComboBox, QLineEdit {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                font-size: 14px;
                min-width: 250px;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 1px solid #1665C0;
            }
            QPushButton {
                background-color: #1665C0;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        # Create main scrollable widget
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")


        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #041E42;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)

        # Header title (without button)
        header_title = QLabel("Market News & Analysis")
        header_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(header_title)

        # Header subtitle
        header_subtitle = QLabel("Stay updated with the latest market trends and financial insights")
        header_subtitle.setStyleSheet("color: #BBDEFB; font-size: 14px;")
        header_layout.addWidget(header_subtitle)


        main_layout.addWidget(header_frame)

        # Navigation button section (replacing Market Pulse)
        nav_section = QHBoxLayout()
        nav_section.setSpacing(15)

        # Back to Dashboard button
        back_button = QPushButton('Back to Dashboard')
        back_button.setMinimumHeight(40)
        back_button.setMinimumWidth(150)
        back_button.clicked.connect(self.switch_to_dashboard_slot)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)

        nav_section.addWidget(back_button)
        nav_section.addStretch()  # Push button to the left

        main_layout.addLayout(nav_section)

        # News section title
        news_title = QLabel("Latest News")
        news_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; margin-top: 10px;")
        main_layout.addWidget(news_title)

        # Search and Filter Section with improved styling
        search_filter_layout = QHBoxLayout()
        search_filter_layout.setSpacing(15)

        # News Filter Dropdown with better styling
        self.news_filter = QComboBox()
        filter_items = ['All News', 'Markets', 'Companies', 'Economy', 'Technology', 'Finance', 'Commodities']
        self.news_filter.addItems(filter_items)
        self.news_filter.currentIndexChanged.connect(self.filter_news)
        self.news_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                padding: 8px 15px;
                border-radius: 5px;
                background-color: white;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox:focus {
                border: 1px solid #041E42;
            }
        """)

        # Search Bar with better styling
        self.news_search = QLineEdit()
        self.news_search.setPlaceholderText('Search news by keywords...')
        self.news_search.textChanged.connect(self.search_news)
        self.news_search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                padding: 8px 15px;
                border-radius: 5px;
                background-color: white;
                min-width: 300px;
            }
            QLineEdit:focus {
                border: 1px solid #041E42;
            }
        """)

        # Search Button
        search_btn = QPushButton('Search')
        search_btn.clicked.connect(self.fetch_news)

        search_filter_layout.addWidget(self.news_filter)
        search_filter_layout.addWidget(self.news_search)
        search_filter_layout.addWidget(search_btn)
        search_filter_layout.addStretch()

        main_layout.addLayout(search_filter_layout)

        # News Container with grid layout for better organization
        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_layout.setSpacing(15)
        self.news_container.setStyleSheet("background-color: transparent;")

        main_layout.addWidget(self.news_container)

        # Bottom navigation buttons with improved styling
        nav_frame = QFrame()
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                padding: 15px;
            }
        """)
        # Create a separate widget for navigation buttons
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(30, 10, 30, 20)

        # This is already in your code, but let's make sure it matches exactly
        back_button = QPushButton('Back to Dashboard')
        back_button.setMinimumHeight(40)
        back_button.setMinimumWidth(150)
        back_button.clicked.connect(self.switch_to_dashboard_slot)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)

        refresh_button = QPushButton('Refresh News')
        refresh_button.setMinimumHeight(40)
        refresh_button.setMinimumWidth(150)
        refresh_button.clicked.connect(self.fetch_news)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #1665C0;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
        """)

        nav_layout.addWidget(back_button)
        nav_layout.addStretch()
        nav_layout.addWidget(refresh_button)

        # Add the navigation widget directly to the main layout AFTER the scrollable area
        main_layout.addWidget(nav_widget)

        # Set the main scrollable widget
        main_scroll.setWidget(central_widget)
        self.setCentralWidget(main_scroll)

        # Set the main scrollable widget
        main_scroll.setWidget(central_widget)
        self.setCentralWidget(main_scroll)

        # Fetch news on initialization with loading indicator
        self.show_loading_indicator()
        QTimer.singleShot(100, self.fetch_news)

        # Set up periodic news refresh
        self.news_refresh_timer = QTimer(self)
        self.news_refresh_timer.timeout.connect(self.fetch_news)
        self.news_refresh_timer.start(300000)  # Refresh every 5 minutes

        main_layout.addWidget(nav_widget)

        main_scroll.setWidget(central_widget)
        self.setCentralWidget(main_scroll)

    def show_loading_indicator(self):
        """Show loading indicator while fetching news"""
        # Clear existing news first
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add loading message
        loading_frame = QFrame()
        loading_frame.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            margin: 20px 0;
        """)
        loading_layout = QVBoxLayout(loading_frame)

        loading_label = QLabel("Loading latest market news...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("font-size: 18px; color: #1665C0;")

        loading_layout.addWidget(loading_label)
        self.news_layout.addWidget(loading_frame)

    def load_mock_news(self):
        """Load realistic mock news as fallback"""
        mock_news = [
            {
                'headline': 'Nifty, Sensex Close Higher for Fifth Straight Session on Global Cues',
                'summary': 'Indian benchmark indices closed higher for the fifth consecutive session on Thursday, with Nifty gaining 0.5% to close at 22,650 and Sensex rising 0.6% to end at 74,450.',
                'source': 'SARAS Markets',
                'datetime': int(datetime.now().timestamp()),
                'category': 'Markets',
                'image': 'https://placehold.co/600x400/png?text=Nifty+Chart'
            },
            {
                'headline': 'RBI Maintains Repo Rate at 6.5% for Seventh Consecutive Meeting',
                'summary': 'The Reserve Bank of Indias Monetary Policy Committee(MPC) has decided to maintain the reporate at 6.5 %for the seventh consecutive meeting, citing balanced risks to inflation and growth.',
        'source': 'Economic Times',
        'datetime': int((datetime.now() - timedelta(hours=3)).timestamp()),
        'category': 'Economy',
        'image': 'https://placehold.co/600x400/png?text=RBI+Meeting'
        },
        {
            'headline': 'Reliance Industries Reports ₹19,500 Crore Net Profit for Q4',
            'summary': 'Reliance Industries Limited (RIL) reported a consolidated net profit of ₹19,500 crore for the quarter ended March 31, 2025, up 12% from the year-ago period, driven by strong performance in retail and telecom segments.',
            'source': 'Moneycontrol',
            'datetime': int((datetime.now() - timedelta(hours=5)).timestamp()),
            'category': 'Companies',
            'image': 'https://placehold.co/600x400/png?text=Reliance+Industries'
        },
        {
            'headline': 'Crude Oil Prices Drop 2% Amid U.S. Inventory Build',
            'summary': 'Crude oil prices declined by 2% on Thursday after U.S. Energy Information Administration data showed an unexpected build in U.S. crude inventories, raising concerns about demand.',
            'source': 'Reuters',
            'datetime': int((datetime.now() - timedelta(hours=7)).timestamp()),
            'category': 'Commodities',
            'image': 'https://placehold.co/600x400/png?text=Crude+Oil'
        },
        {
            'headline': 'HDFC Banks Advances Grow 15 % YoY in Q4, Deposits Up 17 % ',
                                                                                    'summary': 'HDFC Bank reported a 15% year-on-year growth in advances for the fourth quarter ended March 31, 2025, while deposits grew 17%, outperforming industry averages.',
            'source': 'LiveMint',
            'datetime': int((datetime.now() - timedelta(hours=10)).timestamp()),
            'category': 'Companies',
            'image': 'https://placehold.co/600x400/png?text=HDFC+Bank'
        },
        {
            'headline': 'Indian Rupee Strengthens to 82.30 Against U.S. Dollar',
            'summary': 'The Indian rupee appreciated by 0.2% to close at 82.30 against the U.S. dollar, supported by foreign fund inflows and weakness in the greenback globally.',
            'source': 'Financial Express',
            'datetime': int((datetime.now() - timedelta(hours=12)).timestamp()),
            'category': 'Markets',
            'image': 'https://placehold.co/600x400/png?text=INR+USD'
        },
        {
            'headline': 'TCS Bags $500 Million Multi-Year Deal from European Financial Services Firm',
            'summary': 'Tata Consultancy Services (TCS) has secured a $500 million multi-year digital transformation deal from a leading European financial services company, highlighting strong demand for IT services.',
            'source': 'Business Standard',
            'datetime': int((datetime.now() - timedelta(days=1)).timestamp()),
            'category': 'Technology',
            'image': 'https://placehold.co/600x400/png?text=TCS'
        }
        ]

        # Create news cards from mock data
        breaking_news_count = 0
        for article in mock_news:
            try:
                news_card = NewsCard(article)
                self.news_layout.addWidget(news_card)

                # Count breaking news
                if 'breaking' in article['headline'].lower():
                    breaking_news_count += 1
            except Exception as e:
                print(f"Error creating mock news card: {e}")

        # Update breaking news count
        self.update_breaking_news_count(breaking_news_count)

        # Add stretch to push content to top
        self.news_layout.addStretch()

    def fetch_news(self):
        """Fetch real-time news from Finnhub API with improved formatting"""
        try:
            self.show_loading_indicator()

            # Clear existing news
            while self.news_layout.count():
                item = self.news_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get API key - you need to sign up for a free key at finnhub.io
            api_key = "cv18k09r01qhkk81citgcv18k09r01qhkk81ciu0"

            # Map UI filter categories to Finnhub categories
            category_map = {
                'All News': 'general',
                'Markets': 'general',
                'Companies': 'company',
                'Economy': 'economy',
                'Technology': 'technology',
                'Finance': 'forex',
                'Commodities': 'merger'
            }

            selected_filter = self.news_filter.currentText()
            category = category_map.get(selected_filter, 'general')

            # Set up API URL with parameters
            url = f"https://finnhub.io/api/v1/news?category={category}&token={api_key}"

            # Add search parameter if provided
            search_term = self.news_search.text().strip()
            if search_term:
                # If searching specific terms, switch to company news which allows filtering
                today = datetime.now().strftime('%Y-%m-%d')
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                url = f"https://finnhub.io/api/v1/company-news?symbol=AAPL&from={week_ago}&to={today}&token={api_key}"

            # Make request to Finnhub API
            response = requests.get(url)

            if response.status_code != 200:
                raise Exception(f"API returned status code {response.status_code}")

            # Parse the JSON response
            articles = response.json()

            # Validate articles
            if not articles or len(articles) == 0:
                no_news_label = QLabel("No news articles found. Please try a different category or search term.")
                no_news_label.setStyleSheet("font-size: 16px; color: #666; padding: 20px;")
                no_news_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.news_layout.addWidget(no_news_label)
                return

            # Create section for top story
            if len(articles) > 0:
                top_article = articles[0]

                # Create a highlighted top story card
                top_frame = QFrame()
                top_frame.setStyleSheet("""
                    background-color: #F5F9FF;
                    border-radius: 8px;
                    border: 1px solid #1665C0;
                    padding: 0;
                    margin-bottom: 20px;
                """)

                top_layout = QVBoxLayout(top_frame)
                top_layout.setContentsMargins(0, 0, 0, 0)

                # "Top Story" label
                top_label = QLabel("  TOP STORY")
                top_label.setStyleSheet("""
                    background-color: #1665C0;
                    color: white;
                    font-weight: bold;
                    padding: 5px 15px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                """)
                top_layout.addWidget(top_label)

                # Use our NewsCard class for content but customize it
                try:
                    news_card = NewsCard(top_article)
                    news_card.setStyleSheet("""
                        background-color: transparent;
                        border: none;
                    """)
                    top_layout.addWidget(news_card)

                    self.news_layout.addWidget(top_frame)

                    # Remove top article from the list to avoid duplication
                    articles.pop(0)
                except Exception as e:
                    print(f"Error creating top story card: {e}")
                    # If top story fails, don't pop the first article so we can try it in regular list

            # Add "Latest News" label for remaining articles
            latest_label = QLabel("LATEST UPDATES")
            latest_label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px 0;
            """)
            self.news_layout.addWidget(latest_label)

            # Create remaining news cards
            breaking_news_count = 0
            for article in articles[:14]:  # Limit to 14 more articles
                try:
                    news_card = NewsCard(article)
                    self.news_layout.addWidget(news_card)

                    # Count breaking news
                    if 'breaking' in str(article.get('headline', '')).lower():
                        breaking_news_count += 1
                except Exception as card_error:
                    print(f"Error creating news card: {card_error}")

            # Update breaking news count
            self.update_breaking_news_count(breaking_news_count)

            # Add stretch to push content to top
            self.news_layout.addStretch()

        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            # Show error message
            error_frame = QFrame()
            error_frame.setStyleSheet("""
                background-color: #FFF5F5;
                border-radius: 8px;
                border: 1px solid #dc3545;
                padding: 20px;
                margin: 20px 0;
            """)
            error_layout = QVBoxLayout(error_frame)

            error_label = QLabel(f"Unable to fetch news. We'll show you some relevant content instead.")
            error_label.setStyleSheet("font-size: 16px; color: #dc3545;")

            error_layout.addWidget(error_label)
            self.news_layout.addWidget(error_frame)

            # Fallback to mock news
            self.load_mock_news()

    def update_breaking_news_count(self, count):
        """Update breaking news count in summary cards"""
        try:
            cards = self.findChildren(QFrame)
            summary_cards = []
            for card in cards:
                # Find the summary cards by checking their layout children
                card_labels = card.findChildren(QLabel)
                if len(card_labels) == 3:  # Our summary cards have 3 labels
                    for label in card_labels:
                        if label.text() == "Market Status":
                            summary_cards.append(card)

            # If we found the right card, update it
            if summary_cards:
                labels = summary_cards[0].findChildren(QLabel)
                if len(labels) >= 3:
                    if labels[0].text() == "Market Status":
                        labels[1].setText("Live")
                        labels[2].setText(f"{count} Updates")
        except Exception as e:
            print(f"Error updating breaking news count: {e}")

    def filter_news(self, index):
        """Filter news based on selected category"""
        try:
            selected_category = self.news_filter.currentText()
            print(f"Filtering by: {selected_category}")

            # Just re-fetch news when filter changes
            self.fetch_news()
        except Exception as e:
            print(f"Error filtering news: {e}")

    def search_news(self):
        """Search news based on user input"""
        try:
            search_term = self.news_search.text().strip().lower()
            if len(search_term) >= 3:  # Only search with 3+ characters
                # Re-fetch news with search term
                self.fetch_news()

        except Exception as e:
            print(f"Error searching news: {e}")

    def switch_to_dashboard_slot(self):
        """Switch back to dashboard"""
        self.switch_to_dashboard.emit()
        self.hide()