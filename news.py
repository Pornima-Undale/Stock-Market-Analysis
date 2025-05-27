from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QScrollArea, QHBoxLayout,
                             QTextEdit, QLineEdit, QFrame, QSizePolicy, QComboBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import requests
import json
from datetime import datetime
import threading


class NewsAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    def get_market_news(self, category=None):
        """
        Fetch market news from NewsAPI
        Categories: business, technology, general
        """
        try:
            params = {
                'apiKey': self.api_key,
                'language': 'en',
                'category': 'business',
                'pageSize': 10
            }

            if category and category != 'All News':
                params['q'] = category

            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            response.raise_for_status()

            news_data = response.json()
            return self._format_news_data(news_data['articles'])
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def _format_news_data(self, articles):
        """Convert API response to application's news format"""
        formatted_news = []
        for article in articles:
            news_item = {
                'title': article['title'],
                'summary': article['description'] or 'No description available',
                'source': article['source']['name'],
                'time': self._format_time(article['publishedAt']),
                'category': 'Market Updates',
                'impact': self._determine_impact(article['title'])
            }
            formatted_news.append(news_item)
        return formatted_news

    def _format_time(self, timestamp):
        """Convert API timestamp to relative time"""
        pub_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.utcnow()
        diff = now - pub_time

        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds // 3600 > 0:
            return f"{diff.seconds // 3600} hours ago"
        else:
            return f"{diff.seconds // 60} minutes ago"

    def _determine_impact(self, title):
        """Simple impact determination based on keywords"""
        high_impact = ['crash', 'surge', 'plunge', 'soar', 'crisis']
        medium_impact = ['rise', 'fall', 'increase', 'decrease', 'change']

        title_lower = title.lower()
        if any(word in title_lower for word in high_impact):
            return 'High'
        elif any(word in title_lower for word in medium_impact):
            return 'Medium'
        return 'Low'


class NewsFeedWindow(QMainWindow):
    switch_to_dashboard = pyqtSignal()

    def __init__(self, api_key):
        super().__init__()
        self.api_client = NewsAPIClient(api_key)
        self.news_timer = QTimer()
        self.news_timer.timeout.connect(self.refresh_news)
        self.news_timer.start(300000)  # Refresh every 5 minutes
        self.setup_ui()
        self.refresh_news()

    def setup_ui(self):
        # [Previous UI setup code remains the same until news_scroll creation]

        # News Scroll Area
        self.news_scroll = QScrollArea()
        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_layout.setSpacing(10)

        # Set up scroll area
        self.news_scroll.setWidget(self.news_container)
        self.news_scroll.setWidgetResizable(True)
        self.news_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.main_layout.addWidget(self.news_scroll)

        # Connect filter change to refresh
        self.news_filter.currentTextChanged.connect(self.refresh_news)

    def refresh_news(self):
        """Fetch and display fresh news"""

        def fetch_news():
            category = self.news_filter.currentText()
            news_items = self.api_client.get_market_news(category)

            # Update UI in the main thread
            self.update_news_display(news_items)

        # Run news fetching in a separate thread
        threading.Thread(target=fetch_news, daemon=True).start()

    def update_news_display(self, news_items):
        """Update the news display with new items"""
        # Clear existing news cards
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new news cards
        for news in news_items:
            news_card = NewsCard(news)
            self.news_layout.addWidget(news_card)

        self.news_layout.addStretch()

        # Update statistics
        self.update_statistics(news_items)

    def update_statistics(self, news_items):
        """Update the news statistics display"""
        high_impact = sum(1 for item in news_items if item['impact'] == 'High')
        self.stats_label_updates.setText(f"Today's Updates: {len(news_items)}")
        self.stats_label_impact.setText(f"Market Impact News: {high_impact}")

    def search_news(self):
        """Search through current news items"""
        search_term = self.news_search.text().strip().lower()
        if not search_term:
            self.refresh_news()
            return

        # Hide/show news cards based on search term
        for i in range(self.news_layout.count() - 1):  # -1 to exclude stretch
            item = self.news_layout.itemAt(i)
            if item and item.widget():
                news_card = item.widget()
                title = news_card.findChild(QLabel).text().lower()
                summary = news_card.findChildren(QLabel)[1].text().lower()

                if search_term in title or search_term in summary:
                    news_card.show()
                else:
                    news_card.hide()


# Usage Example:
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    API_KEY = "your_newsapi_key_here"  # Replace with your actual API key
    window = NewsFeedWindow(API_KEY)
    window.show()
    sys.exit(app.exec())