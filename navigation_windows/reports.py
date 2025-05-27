import os
import requests
import pandas as pd
import openpyxl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# Fix matplotlib backend - must be done before importing pyplot
import matplotlib

matplotlib.use('QtAgg')
import matplotlib.pyplot as plt

# Now import PyQt6 related modules
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
                             QFrame, QHeaderView, QSizePolicy, QFileDialog, QMessageBox,
                             QTabWidget, QScrollArea, QGridLayout, QSplitter, QDateEdit,
                             QCheckBox, QGroupBox, QRadioButton, QSpacerItem, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QIcon

# Now import matplotlib PyQt6 canvas
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


# Skip mplfinance for now to simplify
# We'll implement an alternative method for candlestick charts


class StockInfoCard(QFrame):
    """Card widget to display stock information"""

    def __init__(self, title, value="--", subtitle=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                border: 1px solid #bdbdbd;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #666666; font-weight: normal;")
        layout.addWidget(title_label)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #041E42;")
        layout.addWidget(self.value_label)

        # Subtitle (optional, for change percentages)
        if subtitle:
            subtitle_container = QWidget()
            subtitle_layout = QHBoxLayout(subtitle_container)
            subtitle_layout.setContentsMargins(0, 0, 0, 0)
            subtitle_layout.setSpacing(5)

            # Indicator for positive/negative change
            self.indicator = QLabel()
            self.indicator.setFixedSize(8, 8)
            self.indicator.setStyleSheet('background-color: #00c853; border-radius: 4px;')

            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #00c853;")

            subtitle_layout.addWidget(self.indicator)
            subtitle_layout.addWidget(self.subtitle_label)
            subtitle_layout.addStretch()

            layout.addWidget(subtitle_container)

    def update_value(self, value, change_value=None, change_percent=None):
        """Update the card with new value and change information"""
        self.value_label.setText(value)

        # Update subtitle if provided
        if hasattr(self, 'subtitle_label') and change_percent is not None:
            # Format the change text
            if change_value is not None:
                change_text = f"{change_value:+.2f} ({change_percent:+.2f}%)"
            else:
                change_text = f"{change_percent:+.2f}%"

            self.subtitle_label.setText(change_text)

            # Update color based on direction
            if change_percent >= 0:
                self.subtitle_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #00c853;")
                self.indicator.setStyleSheet('background-color: #00c853; border-radius: 4px;')
            else:
                self.subtitle_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ff1744;")
                self.indicator.setStyleSheet('background-color: #ff1744; border-radius: 4px;')


class StockChart(QFrame):
    """Widget for displaying stock charts with enhanced visualization"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        # Chart controls
        controls_layout = QHBoxLayout()

        # Chart type selector
        self.chart_type = QComboBox()
        self.chart_type.addItems(['Line', 'Candlestick'])
        self.chart_type.setCurrentIndex(1)  # Default to candlestick
        self.chart_type.currentIndexChanged.connect(self.update_chart)

        # Timeframe selector
        self.timeframe = QComboBox()
        self.timeframe.addItems(['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'Max'])
        self.timeframe.setCurrentIndex(2)  # Default to 1 month
        self.timeframe.currentIndexChanged.connect(self.update_chart)

        # Custom date range
        self.use_custom_dates = QCheckBox("Custom Range")
        self.use_custom_dates.stateChanged.connect(self.toggle_date_range)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setEnabled(False)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)

        # Add indicators section
        indicators_label = QLabel("Indicators:")

        self.show_ma = QCheckBox("MAs")
        self.show_ma.setChecked(True)
        self.show_ma.setToolTip("Show Moving Averages (5, 10, 50, 100 periods)")
        self.show_ma.stateChanged.connect(self.update_chart)

        self.show_volume = QCheckBox("Volume")
        self.show_volume.setChecked(True)
        self.show_volume.setToolTip("Show volume bars")
        self.show_volume.stateChanged.connect(self.update_chart)

        self.show_grid = QCheckBox("Grid")
        self.show_grid.setChecked(True)
        self.show_grid.setToolTip("Show grid lines")
        self.show_grid.stateChanged.connect(self.update_chart)

        # Theme selector
        theme_label = QLabel("Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(['Default', 'Dark', 'Light'])
        self.theme_selector.setCurrentIndex(0)
        self.theme_selector.currentIndexChanged.connect(self.update_chart)

        # Add refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_chart)

        # Add controls to layout
        controls_layout.addWidget(QLabel("Chart Type:"))
        controls_layout.addWidget(self.chart_type)
        controls_layout.addWidget(QLabel("Timeframe:"))
        controls_layout.addWidget(self.timeframe)
        controls_layout.addWidget(self.use_custom_dates)
        controls_layout.addWidget(QLabel("From:"))
        controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(QLabel("To:"))
        controls_layout.addWidget(self.end_date)
        controls_layout.addWidget(indicators_label)
        controls_layout.addWidget(self.show_ma)
        controls_layout.addWidget(self.show_volume)
        controls_layout.addWidget(self.show_grid)
        controls_layout.addWidget(theme_label)
        controls_layout.addWidget(self.theme_selector)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()

        self.layout.addLayout(controls_layout)

        # Create figure for matplotlib
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.canvas)

        # Initialize variables
        self.ticker_data = None
        self.ticker_symbol = None

    def toggle_date_range(self, state):
        """Enable/disable custom date range controls"""
        enabled = state == Qt.CheckState.Checked
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
        self.timeframe.setEnabled(not enabled)

        if enabled:
            self.update_chart()

    def set_ticker(self, ticker_symbol):
        """Set the ticker symbol and update the chart"""
        self.ticker_symbol = ticker_symbol
        self.update_chart()

    def update_chart(self):
        """Update the chart with current ticker and settings"""
        if not self.ticker_symbol:
            return

        try:
            # Clear the figure
            self.figure.clear()

            # Get timeframe
            if self.use_custom_dates.isChecked():
                start_date = self.start_date.date().toPyDate()
                end_date = self.end_date.date().toPyDate()
                period = None
            else:
                timeframe = self.timeframe.currentText()

                # Map timeframe to period parameter for yfinance
                period_map = {
                    '1D': '1d',
                    '5D': '5d',
                    '1M': '1mo',
                    '3M': '3mo',
                    '6M': '6mo',
                    'YTD': 'ytd',
                    '1Y': '1y',
                    '5Y': '5y',
                    'Max': 'max'
                }

                # Set start/end dates based on timeframe
                period = period_map[timeframe]
                end_date = datetime.now().date()

                if timeframe == '1D':
                    start_date = end_date - timedelta(days=1)
                elif timeframe == '5D':
                    start_date = end_date - timedelta(days=5)
                elif timeframe == '1M':
                    start_date = end_date - timedelta(days=30)
                elif timeframe == '3M':
                    start_date = end_date - timedelta(days=90)
                elif timeframe == '6M':
                    start_date = end_date - timedelta(days=180)
                elif timeframe == 'YTD':
                    start_date = datetime(end_date.year, 1, 1).date()
                elif timeframe == '1Y':
                    start_date = end_date - timedelta(days=365)
                elif timeframe == '5Y':
                    start_date = end_date - timedelta(days=365 * 5)
                else:  # Max
                    start_date = None

            # Determine interval based on timeframe
            if period in ['1d', '5d']:
                interval = '5m'  # 5-minute intervals for short timeframes
            elif period in ['1mo', '3mo']:
                interval = '1h'  # Hourly for medium timeframes
            else:
                interval = '1d'  # Daily for longer timeframes

            # Fetch data using yfinance
            ticker = yf.Ticker(self.ticker_symbol)

            if period:
                data = ticker.history(period=period, interval=interval)
            else:
                data = ticker.history(start=start_date, end=end_date + timedelta(days=1))

            # Check if data is available
            if data.empty:
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, "No data available for the selected timeframe",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes, fontsize=12)
                self.canvas.draw()
                return

            # Store data for reference
            self.ticker_data = data

            # Apply chart theme
            theme = self.theme_selector.currentText()
            if theme == 'Dark':
                plt.style.use('dark_background')
                grid_color = '#555555'
                text_color = 'white'
                up_color = '#00ff7f'  # Brighter green on dark background
                down_color = '#ff4757'  # Brighter red on dark background
                volume_up_color = '#00ff7f'
                volume_down_color = '#ff4757'
                volume_alpha = 0.4
                ma_colors = ['#fffa65', '#70a1ff', '#7bed9f', '#5352ed']  # Bright colors for dark theme
            elif theme == 'Light':
                plt.style.use('default')
                grid_color = '#dddddd'
                text_color = 'black'
                up_color = '#2ed573'  # Darker green on light background
                down_color = '#ff4757'  # Red on light background
                volume_up_color = '#2ed573'
                volume_down_color = '#ff4757'
                volume_alpha = 0.4
                ma_colors = ['#ff6b6b', '#48dbfb', '#1dd1a1', '#5f27cd']  # Vibrant colors
            else:  # Default
                plt.style.use('default')
                grid_color = '#e0e0e0'
                text_color = '#333333'
                up_color = '#00c853'  # Original green
                down_color = '#ff1744'  # Original red
                volume_up_color = '#00c853'
                volume_down_color = '#ff1744'
                volume_alpha = 0.3
                ma_colors = ['red', 'blue', 'green', 'purple']  # Original colors

            # Calculate Moving Averages if needed
            if self.show_ma.isChecked():
                # Only calculate MAs that make sense for the timeframe
                if len(data) >= 5:
                    data['MA5'] = data['Close'].rolling(window=5).mean()
                if len(data) >= 10:
                    data['MA10'] = data['Close'].rolling(window=10).mean()
                if len(data) >= 50:
                    data['MA50'] = data['Close'].rolling(window=50).mean()
                if len(data) >= 100:
                    data['MA100'] = data['Close'].rolling(window=100).mean()

            # Setup main plot area
            # Define dimensions - main chart takes more space, volume takes less
            if self.show_volume.isChecked():
                gs = self.figure.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0)
                ax = self.figure.add_subplot(gs[0])
                volume_ax = self.figure.add_subplot(gs[1], sharex=ax)
            else:
                ax = self.figure.add_subplot(111)
                volume_ax = None

            # Get chart type
            chart_type = self.chart_type.currentText()

            # Create chart based on type
            if chart_type == 'Line':
                # Create a line chart with enhanced appearance
                ax.plot(data.index, data['Close'], linewidth=2, color=text_color, label='Close')

                # Add Moving Averages to line chart if enabled
                if self.show_ma.isChecked():
                    for i, ma in enumerate(['MA5', 'MA10', 'MA50', 'MA100']):
                        if ma in data.columns:
                            ax.plot(data.index, data[ma], linewidth=1.5,
                                    color=ma_colors[i],
                                    label=ma,
                                    alpha=0.8)

                # Add volume if enabled
                if self.show_volume.isChecked() and volume_ax:
                    # Color volume bars based on price movement
                    volume_colors = np.where(
                        data['Close'] >= data['Close'].shift(1),
                        volume_up_color,
                        volume_down_color
                    )

                    # Plot volume with colors
                    volume_ax.bar(data.index, data['Volume'], color=volume_colors, alpha=volume_alpha, width=0.8)
                    volume_ax.set_ylabel('Volume', color=text_color)
                    volume_ax.tick_params(colors=text_color)

                    # Remove x-axis label from main chart (will be on volume chart)
                    ax.set_xlabel('')

                    # Add grid to volume chart if enabled
                    if self.show_grid.isChecked():
                        volume_ax.grid(True, linestyle='--', alpha=0.6, color=grid_color)
                        volume_ax.set_axisbelow(True)  # Put grid behind the bars

            elif chart_type == 'Candlestick':
                # Create an enhanced candlestick chart
                # Use wider bodies and thinner wicks for better visualization
                width_body = 0.8
                width_wick = 0.2

                # Separate up and down days
                up = data[data.Close >= data.Open]
                down = data[data.Close < data.Open]

                # Plot up candles with enhanced appearance
                ax.bar(up.index, up.Close - up.Open, width_body, bottom=up.Open,
                       color=up_color, alpha=1, zorder=3, edgecolor='black', linewidth=0.5)

                # Plot down candles with enhanced appearance
                ax.bar(down.index, down.Open - down.Close, width_body, bottom=down.Close,
                       color=down_color, alpha=1, zorder=3, edgecolor='black', linewidth=0.5)

                # Add wicks (high-low lines) with better appearance
                for i, (idx, row) in enumerate(data.iterrows()):
                    # Plot high wick
                    ax.plot([idx, idx], [max(row.Open, row.Close), row.High],
                            color='black', linewidth=1, alpha=0.8, zorder=4)
                    # Plot low wick
                    ax.plot([idx, idx], [min(row.Open, row.Close), row.Low],
                            color='black', linewidth=1, alpha=0.8, zorder=4)

                # Add Moving Averages to candlestick chart if enabled
                if self.show_ma.isChecked():
                    for i, ma in enumerate(['MA5', 'MA10', 'MA50', 'MA100']):
                        if ma in data.columns:
                            ax.plot(data.index, data[ma], linewidth=1.5,
                                    color=ma_colors[i],
                                    label=ma,
                                    alpha=0.8,
                                    zorder=5)  # Put MA lines on top of candles

                # Add volume if enabled
                if self.show_volume.isChecked() and volume_ax:
                    # Color volume bars to match candle colors
                    volume_colors = np.where(
                        data['Close'] >= data['Open'],
                        volume_up_color,
                        volume_down_color
                    )

                    # Plot volume with enhanced appearance
                    volume_ax.bar(data.index, data['Volume'], color=volume_colors,
                                  alpha=volume_alpha, width=0.8, edgecolor='black', linewidth=0.2)
                    volume_ax.set_ylabel('Volume', color=text_color)
                    volume_ax.tick_params(colors=text_color)

                    # Remove x-axis label from main chart (will be on volume chart)
                    ax.set_xlabel('')

                    # Add grid to volume chart if enabled
                    if self.show_grid.isChecked():
                        volume_ax.grid(True, linestyle='--', alpha=0.6, color=grid_color)
                        volume_ax.set_axisbelow(True)

            # Add legend if MAs are shown
            if self.show_ma.isChecked():
                ax.legend(loc='upper left', framealpha=0.9)

            # Format the chart
            ax.set_title(f"{self.ticker_symbol} - {chart_type} Chart", fontweight='bold', color=text_color, size=14)

            if not self.show_volume.isChecked() or volume_ax is None:
                ax.set_xlabel('Date', color=text_color)

            ax.set_ylabel('Price (₹)', color=text_color)

            # Add grid if enabled
            if self.show_grid.isChecked():
                ax.grid(True, linestyle='--', alpha=0.6, color=grid_color)
                ax.set_axisbelow(True)  # Put grid behind the data

            # Format ticks to match theme
            ax.tick_params(colors=text_color)
            if volume_ax:
                volume_ax.tick_params(colors=text_color)

            # Format dates on x-axis based on timeframe
            if period in ['1d', '5d']:
                formatter = mdates.DateFormatter('%H:%M')
            elif period in ['1mo', '3mo', '6mo']:
                formatter = mdates.DateFormatter('%d %b')
            else:
                formatter = mdates.DateFormatter('%b %Y')

            if volume_ax:
                volume_ax.xaxis.set_major_formatter(formatter)
                plt.setp(volume_ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            else:
                ax.xaxis.set_major_formatter(formatter)
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

            # Set better tick frequency
            if len(data) > 30:
                # Limit to ~10 ticks on x-axis for better readability
                n_points = len(data.index)
                interval = max(1, n_points // 10)
                if volume_ax:
                    volume_ax.xaxis.set_major_locator(plt.MaxNLocator(10))
                else:
                    ax.xaxis.set_major_locator(plt.MaxNLocator(10))

            # Add price padding to y-axis (5% above highest and below lowest)
            y_range = data['High'].max() - data['Low'].min()
            y_padding = y_range * 0.05
            ax.set_ylim(data['Low'].min() - y_padding, data['High'].max() + y_padding)

            # Adjust layout to prevent cutting off labels
            self.figure.tight_layout()

            # Draw the canvas
            self.canvas.draw()

        except Exception as e:
            # Show error on chart
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"Error loading chart: {str(e)}",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=12)
            self.canvas.draw()

            print(f"Chart error: {str(e)}")


class HistoricalDataWidget(QFrame):
    """Widget for downloading and analyzing historical data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Create tab widget for different historical data features
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e0e0e0;
            }
        """)

        # Create download tab
        self.download_tab = QWidget()
        self.setup_download_tab()
        self.tabs.addTab(self.download_tab, "Download Data")

        # Create preview tab
        self.preview_tab = QWidget()
        self.setup_preview_tab()
        self.tabs.addTab(self.preview_tab, "Data Preview")

        # Create analysis tab
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "Quick Analysis")

        # Add tabs to main layout
        layout.addWidget(self.tabs)

        # Initialize state variables
        self.ticker_symbol = None
        self.historical_data = None

    def setup_download_tab(self):
        """Set up the download tab UI"""
        layout = QVBoxLayout(self.download_tab)

        # Title
        title = QLabel("Download Historical Data")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #041E42; margin-bottom: 10px;")
        layout.addWidget(title)

        # Description
        description = QLabel("Download historical price data for your analysis.")
        description.setStyleSheet("color: #666666; margin-bottom: 15px;")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Form for downloading data
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)

        # Period selection
        period_label = QLabel("Time Period:")
        period_label.setStyleSheet("font-weight: bold;")

        self.period_group = QGroupBox()
        self.period_group.setStyleSheet("border: none;")
        period_layout = QVBoxLayout(self.period_group)

        # Predefined periods
        self.period_preset = QRadioButton("Preset Period")
        self.period_preset.setChecked(True)
        self.period_preset.toggled.connect(self.toggle_period_controls)

        self.period_custom = QRadioButton("Custom Range")
        self.period_custom.toggled.connect(self.toggle_period_controls)

        period_layout.addWidget(self.period_preset)
        period_layout.addWidget(self.period_custom)

        # Period selector
        self.period_selector = QComboBox()
        self.period_selector.addItems(['1 Month', '3 Months', '6 Months', 'Year to Date', '1 Year', '5 Years', 'Max'])

        # Custom date range
        dates_layout = QHBoxLayout()

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setEnabled(False)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)

        dates_layout.addWidget(QLabel("From:"))
        dates_layout.addWidget(self.start_date)
        dates_layout.addWidget(QLabel("To:"))
        dates_layout.addWidget(self.end_date)

        # Interval selection
        interval_label = QLabel("Interval:")
        interval_label.setStyleSheet("font-weight: bold;")

        self.interval_selector = QComboBox()
        self.interval_selector.addItems(['Daily', 'Weekly', 'Monthly', 'Hourly', '15 Minutes'])
        self.interval_selector.setToolTip("Note: Hourly and minute data may only be available for recent periods")

        # Add form controls to grid
        form_layout.addWidget(period_label, 0, 0)
        form_layout.addWidget(self.period_group, 0, 1)
        form_layout.addWidget(self.period_selector, 1, 1)
        form_layout.addLayout(dates_layout, 2, 1)
        form_layout.addWidget(interval_label, 3, 0)
        form_layout.addWidget(self.interval_selector, 3, 1)

        # Adjusted close option
        self.adjust_checkbox = QCheckBox("Include adjusted prices (for dividends and splits)")
        self.adjust_checkbox.setChecked(True)
        form_layout.addWidget(self.adjust_checkbox, 4, 1)

        # Format options
        format_label = QLabel("Format:")
        format_label.setStyleSheet("font-weight: bold;")

        self.format_selector = QComboBox()
        self.format_selector.addItems(['CSV', 'Excel', 'JSON'])

        form_layout.addWidget(format_label, 5, 0)
        form_layout.addWidget(self.format_selector, 5, 1)

        # Add the form layout
        layout.addLayout(form_layout)

        # Add spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Preview button
        self.preview_btn = QPushButton("Preview Data")
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.preview_btn.clicked.connect(self.preview_data)

        # Download button
        self.download_btn = QPushButton("Download Data")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)
        self.download_btn.clicked.connect(self.download_historical_data)

        buttons_layout.addWidget(self.preview_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.download_btn)

        layout.addLayout(buttons_layout)

    def setup_preview_tab(self):
        """Set up the data preview tab UI"""
        layout = QVBoxLayout(self.preview_tab)

        # Controls layout
        controls_layout = QHBoxLayout()

        # Refresh button
        self.refresh_preview_btn = QPushButton("Refresh Data")
        self.refresh_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)
        self.refresh_preview_btn.clicked.connect(self.refresh_preview)

        # Filter options
        filter_label = QLabel("Filter:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter data (e.g., date, price range)")
        self.filter_input.textChanged.connect(self.apply_filter)

        # Row limit
        limit_label = QLabel("Max Rows:")
        self.limit_selector = QComboBox()
        self.limit_selector.addItems(['100', '500', '1000', 'All'])
        self.limit_selector.currentIndexChanged.connect(self.refresh_preview)

        # Add controls to layout
        controls_layout.addWidget(self.refresh_preview_btn)
        controls_layout.addWidget(filter_label)
        controls_layout.addWidget(self.filter_input, 1)  # give it more space
        controls_layout.addWidget(limit_label)
        controls_layout.addWidget(self.limit_selector)

        layout.addLayout(controls_layout)

        # Data table
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)

        layout.addWidget(self.preview_table)

        # Status and info layout
        status_layout = QHBoxLayout()

        self.preview_status = QLabel("No data loaded")
        self.data_stats = QLabel("")

        status_layout.addWidget(self.preview_status)
        status_layout.addStretch()
        status_layout.addWidget(self.data_stats)

        layout.addLayout(status_layout)

        # Action buttons
        action_layout = QHBoxLayout()

        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.clicked.connect(self.copy_selected_data)

        self.export_preview_btn = QPushButton("Export Preview")
        self.export_preview_btn.clicked.connect(self.export_preview_data)

        action_layout.addStretch()
        action_layout.addWidget(self.copy_selected_btn)
        action_layout.addWidget(self.export_preview_btn)

        layout.addLayout(action_layout)

    def setup_analysis_tab(self):
        """Set up the analysis tab UI"""
        layout = QVBoxLayout(self.analysis_tab)

        # Instruction label
        instruction = QLabel("Generate quick statistics and analysis of the historical data:")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        # Analysis options
        options_layout = QGridLayout()

        # Statistical analysis checkboxes
        self.show_summary_stats = QCheckBox("Summary Statistics")
        self.show_summary_stats.setChecked(True)
        self.show_summary_stats.setToolTip("Show mean, median, min, max, std dev of price and volume")

        self.show_returns = QCheckBox("Return Analysis")
        self.show_returns.setChecked(True)
        self.show_returns.setToolTip("Calculate daily/weekly/monthly returns and volatility")

        self.show_correlation = QCheckBox("Price-Volume Correlation")
        self.show_correlation.setToolTip("Calculate correlation between price and volume")

        self.show_trends = QCheckBox("Trend Analysis")
        self.show_trends.setToolTip("Identify trends in the price movement")

        # Time period options
        period_label = QLabel("Analysis Period:")
        self.analysis_period = QComboBox()
        self.analysis_period.addItems(['All Data', 'Last Month', 'Last 3 Months', 'Last Year', 'YTD'])

        # Add options to grid
        options_layout.addWidget(self.show_summary_stats, 0, 0)
        options_layout.addWidget(self.show_returns, 0, 1)
        options_layout.addWidget(self.show_correlation, 1, 0)
        options_layout.addWidget(self.show_trends, 1, 1)
        options_layout.addWidget(period_label, 2, 0)
        options_layout.addWidget(self.analysis_period, 2, 1)

        layout.addLayout(options_layout)

        # Generate button
        self.generate_analysis_btn = QPushButton("Generate Analysis")
        self.generate_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)
        self.generate_analysis_btn.clicked.connect(self.generate_analysis)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.generate_analysis_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Results area
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        self.analysis_results.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                font-family: Consolas, monospace;
            }
        """)

        layout.addWidget(self.analysis_results)

        # Action buttons
        action_layout = QHBoxLayout()

        self.copy_analysis_btn = QPushButton("Copy Analysis")
        self.copy_analysis_btn.clicked.connect(self.copy_analysis)

        self.save_analysis_btn = QPushButton("Save Analysis")
        self.save_analysis_btn.clicked.connect(self.save_analysis)

        action_layout.addStretch()
        action_layout.addWidget(self.copy_analysis_btn)
        action_layout.addWidget(self.save_analysis_btn)

        layout.addLayout(action_layout)

    def toggle_period_controls(self):
        """Enable/disable period controls based on selection"""
        use_preset = self.period_preset.isChecked()
        self.period_selector.setEnabled(use_preset)
        self.start_date.setEnabled(not use_preset)
        self.end_date.setEnabled(not use_preset)

    def set_ticker(self, ticker_symbol):
        """Set the ticker symbol and reset the UI"""
        self.ticker_symbol = ticker_symbol
        self.historical_data = None
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.preview_status.setText(f"Ticker set to {ticker_symbol}. Use Preview or Download to fetch data.")
        self.data_stats.setText("")
        self.analysis_results.clear()

    def fetch_historical_data(self):
        """Fetch historical data based on user settings"""
        if not self.ticker_symbol:
            QMessageBox.warning(self, "Error", "No stock selected. Please search and select a stock first.")
            return None

        try:
            # Get period settings
            if self.period_preset.isChecked():
                period_text = self.period_selector.currentText()

                # Map period text to yfinance parameter
                period_map = {
                    '1 Month': '1mo',
                    '3 Months': '3mo',
                    '6 Months': '6mo',
                    'Year to Date': 'ytd',
                    '1 Year': '1y',
                    '5 Years': '5y',
                    'Max': 'max'
                }

                period = period_map[period_text]
                start_date = None
                end_date = None
            else:
                # Use custom date range
                period = None
                start_date = self.start_date.date().toPyDate()
                end_date = self.end_date.date().toPyDate()

                # Validate date range
                if start_date >= end_date:
                    QMessageBox.warning(self, "Invalid Date Range",
                                        "Start date must be before end date.")
                    return None

            # Get interval
            interval_text = self.interval_selector.currentText()
            interval_map = {
                'Daily': '1d',
                'Weekly': '1wk',
                'Monthly': '1mo',
                'Hourly': '1h',
                '15 Minutes': '15m'
            }
            interval = interval_map[interval_text]

            # Fetch data
            ticker = yf.Ticker(self.ticker_symbol)

            if period:
                data = ticker.history(period=period, interval=interval, auto_adjust=self.adjust_checkbox.isChecked())
            else:
                data = ticker.history(start=start_date, end=end_date + timedelta(days=1),
                                      interval=interval, auto_adjust=self.adjust_checkbox.isChecked())

            # Check if data is available
            if data.empty:
                QMessageBox.warning(self, "No Data",
                                    "No data available for the selected time period.")
                return None

            # Add ticker column
            data['Ticker'] = self.ticker_symbol

            # Store the data and return it
            self.historical_data = data
            return data

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch historical data: {str(e)}")
            print(f"Fetch error: {str(e)}")
            return None

    def preview_data(self):
        """Fetch and display a preview of the historical data"""
        data = self.fetch_historical_data()
        if data is not None:
            self.tabs.setCurrentIndex(1)  # Switch to preview tab
            self.populate_preview_table(data)

    def refresh_preview(self):
        """Refresh the preview table with current data"""
        if self.historical_data is None:
            data = self.fetch_historical_data()
            if data is None:
                return
        else:
            data = self.historical_data

        self.populate_preview_table(data)

    def populate_preview_table(self, data):
        """Populate the preview table with data"""
        # Clear the table
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)

        if data.empty:
            self.preview_status.setText("No data available")
            return

        # Get row limit
        limit_text = self.limit_selector.currentText()
        if limit_text == 'All':
            limit = len(data)
        else:
            limit = min(int(limit_text), len(data))

        # Apply filter if needed
        filter_text = self.filter_input.text().strip().lower()
        if filter_text:
            try:
                # Try to filter based on date or price
                filtered_data = data

                # Check if it's a date filter (YYYY-MM-DD)
                if filter_text.count('-') == 2:
                    filtered_data = data[data.index.strftime('%Y-%m-%d').str.contains(filter_text)]
                # Check if it's a price range filter (e.g., >100, <50, 100-200)
                elif '>' in filter_text:
                    value = float(filter_text.replace('>', '').strip())
                    filtered_data = data[data['Close'] > value]
                elif '<' in filter_text:
                    value = float(filter_text.replace('<', '').strip())
                    filtered_data = data[data['Close'] < value]
                elif '-' in filter_text and filter_text.count('-') == 1:
                    min_val, max_val = map(float, filter_text.split('-'))
                    filtered_data = data[(data['Close'] >= min_val) & (data['Close'] <= max_val)]
                else:
                    # Generic filter on any column that might contain the text
                    filtered_data = data[
                        data.astype(str).apply(lambda x: x.str.lower().str.contains(filter_text)).any(axis=1)]

                data = filtered_data

            except Exception as e:
                print(f"Filter error: {str(e)}")
                # If filter fails, use original data
                pass

        # Limit rows after filtering
        limited_data = data.head(limit)

        # Set up table columns
        columns = ['Date'] + list(data.columns)
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)

        # Add data rows
        self.preview_table.setRowCount(len(limited_data))

        for i, (idx, row) in enumerate(limited_data.iterrows()):
            # Add date from index
            date_item = QTableWidgetItem(idx.strftime('%Y-%m-%d %H:%M:%S'))
            self.preview_table.setItem(i, 0, date_item)

            # Add other columns
            for j, col in enumerate(data.columns):
                value = row[col]
                if isinstance(value, (int, float)):
                    # Format numbers
                    if 'Volume' in col:
                        text = f"{value:,.0f}"
                    else:
                        text = f"{value:.2f}"
                else:
                    text = str(value)

                item = QTableWidgetItem(text)
                self.preview_table.setItem(i, j + 1, item)

        # Resize columns to content
        self.preview_table.resizeColumnsToContents()

        # Update status
        self.preview_status.setText(f"Showing {len(limited_data)} of {len(data)} rows")

        # Update stats
        stats_text = f"Date Range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}"
        if 'Close' in data.columns:
            stats_text += f" | Price Range: {data['Close'].min():.2f} - {data['Close'].max():.2f}"
        self.data_stats.setText(stats_text)

    def apply_filter(self):
        """Apply filter to the preview table"""
        if self.historical_data is not None:
            self.populate_preview_table(self.historical_data)

    def copy_selected_data(self):
        """Copy selected rows to clipboard"""
        selected_rows = self.preview_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        # Build CSV data
        columns = [self.preview_table.horizontalHeaderItem(i).text() for i in range(self.preview_table.columnCount())]
        rows = []

        # Add header
        rows.append(",".join(columns))

        # Add selected rows
        for row_idx in sorted([index.row() for index in selected_rows]):
            row_data = []
            for col_idx in range(self.preview_table.columnCount()):
                item = self.preview_table.item(row_idx, col_idx)
                row_data.append(item.text() if item else "")
            rows.append(",".join(row_data))

        # Copy to clipboard
        QApplication.clipboard().setText("\n".join(rows))
        self.preview_status.setText(f"Copied {len(selected_rows)} rows to clipboard")

    def export_preview_data(self):
        """Export current preview data to file"""
        if self.historical_data is None or self.preview_table.rowCount() == 0:
            return

        # Ask user for save location
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Preview Data",
            f"{self.ticker_symbol}_preview_data.csv",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)")

        if not filename:
            return

        try:
            # Get data from preview table
            columns = [self.preview_table.horizontalHeaderItem(i).text() for i in
                       range(self.preview_table.columnCount())]
            data = []

            for row_idx in range(self.preview_table.rowCount()):
                row_data = {}
                for col_idx, col_name in enumerate(columns):
                    item = self.preview_table.item(row_idx, col_idx)
                    row_data[col_name] = item.text() if item else ""
                data.append(row_data)

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Save based on file extension
            if filename.endswith('.csv'):
                df.to_csv(filename, index=False)
            elif filename.endswith('.xlsx'):
                df.to_excel(filename, index=False)
            elif filename.endswith('.json'):
                df.to_json(filename, orient='records')

            self.preview_status.setText(f"Exported data to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
            print(f"Export error: {str(e)}")

    def download_historical_data(self):
        """Download historical data based on user settings"""
        data = self.fetch_historical_data()
        if data is None:
            return

        try:
            # Ask user for save location
            file_format = self.format_selector.currentText()

            if file_format == 'CSV':
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Save Historical Data",
                    f"{self.ticker_symbol}_historical_data.csv",
                    "CSV Files (*.csv)")

                if filename:
                    data.to_csv(filename)
            elif file_format == 'Excel':
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Save Historical Data",
                    f"{self.ticker_symbol}_historical_data.xlsx",
                    "Excel Files (*.xlsx)")

                if filename:
                    data.to_excel(filename)
            else:  # JSON
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Save Historical Data",
                    f"{self.ticker_symbol}_historical_data.json",
                    "JSON Files (*.json)")

                if filename:
                    data.to_json(filename, orient='split')

            # Show success message if file was saved
            if filename:
                QMessageBox.information(self, "Download Complete",
                                        f"Historical data saved to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download historical data: {str(e)}")
            print(f"Download error: {str(e)}")

    def generate_analysis(self):
        """Generate analysis based on the historical data"""
        if self.historical_data is None:
            data = self.fetch_historical_data()
            if data is None:
                QMessageBox.warning(self, "No Data", "Please fetch data first by using the Preview button.")
                return
        else:
            data = self.historical_data.copy()

        # Filter data based on selected period
        period = self.analysis_period.currentText()
        if period != 'All Data':
            today = datetime.now().date()

            if period == 'Last Month':
                start_date = today - timedelta(days=30)
            elif period == 'Last 3 Months':
                start_date = today - timedelta(days=90)
            elif period == 'Last Year':
                start_date = today - timedelta(days=365)
            elif period == 'YTD':
                start_date = datetime(today.year, 1, 1).date()

            data = data[data.index >= pd.Timestamp(start_date)]

        if data.empty:
            QMessageBox.warning(self, "No Data", "No data available for the selected period.")
            return

        # Generate the analysis
        analysis_text = f"Analysis for {self.ticker_symbol} - {period}\n"
        analysis_text += f"Date Range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}\n"
        analysis_text += f"Total Trading Days: {len(data)}\n\n"

        try:
            # Summary Statistics
            if self.show_summary_stats.isChecked():
                analysis_text += "===== SUMMARY STATISTICS =====\n"

                # Price statistics
                if 'Close' in data.columns:
                    analysis_text += "PRICE (Close):\n"
                    analysis_text += f"  Current: {data['Close'].iloc[-1]:.2f}\n"
                    analysis_text += f"  Min: {data['Close'].min():.2f}\n"
                    analysis_text += f"  Max: {data['Close'].max():.2f}\n"
                    analysis_text += f"  Mean: {data['Close'].mean():.2f}\n"
                    # Continuing from where we left off in the generate_analysis method
                    analysis_text += f"  Median: {data['Close'].median():.2f}\n"
                    analysis_text += f"  Std Dev: {data['Close'].std():.2f}\n"

                    # Calculate price change
                    first_price = data['Close'].iloc[0]
                    last_price = data['Close'].iloc[-1]
                    change = last_price - first_price
                    pct_change = (change / first_price) * 100

                    analysis_text += f"  Change: {change:.2f} ({pct_change:.2f}%)\n"

                    # Volume statistics
                if 'Volume' in data.columns:
                    analysis_text += "\nVOLUME:\n"
                    analysis_text += f"  Average: {data['Volume'].mean():.0f}\n"
                    analysis_text += f"  Median: {data['Volume'].median():.0f}\n"
                    analysis_text += f"  Min: {data['Volume'].min():.0f}\n"
                    analysis_text += f"  Max: {data['Volume'].max():.0f}\n"

                    # Calculate volume change trend
                    vol_first_half = data['Volume'].iloc[:len(data) // 2].mean()
                    vol_second_half = data['Volume'].iloc[len(data) // 2:].mean()
                    vol_change = (vol_second_half - vol_first_half) / vol_first_half * 100

                    trend = "increasing" if vol_change > 5 else "decreasing" if vol_change < -5 else "stable"
                    analysis_text += f"  Volume Trend: {trend} ({vol_change:.2f}% change)\n"

                analysis_text += "\n"

                # Return Analysis
                if self.show_returns.isChecked():
                    analysis_text += "===== RETURN ANALYSIS =====\n"

                    if 'Close' in data.columns:
                        # Calculate daily returns
                        data['Daily Return'] = data['Close'].pct_change() * 100

                        analysis_text += "DAILY RETURNS:\n"
                        analysis_text += f"  Average: {data['Daily Return'].mean():.2f}%\n"
                        analysis_text += f"  Median: {data['Daily Return'].median():.2f}%\n"
                        analysis_text += f"  Min: {data['Daily Return'].min():.2f}%\n"
                        analysis_text += f"  Max: {data['Daily Return'].max():.2f}%\n"
                        analysis_text += f"  Std Dev (Volatility): {data['Daily Return'].std():.2f}%\n"

                        # Calculate positive vs negative days
                        pos_days = sum(data['Daily Return'] > 0)
                        neg_days = sum(data['Daily Return'] < 0)
                        flat_days = sum(data['Daily Return'] == 0)

                        pos_pct = pos_days / len(data) * 100
                        neg_pct = neg_days / len(data) * 100

                        analysis_text += f"  Positive Days: {pos_days} ({pos_pct:.1f}%)\n"
                        analysis_text += f"  Negative Days: {neg_days} ({neg_pct:.1f}%)\n"
                        analysis_text += f"  Flat Days: {flat_days}\n"

                        # Calculate annualized return
                        if len(data) > 1:
                            days = (data.index.max() - data.index.min()).days
                            if days > 0:
                                years = days / 365.0
                                total_return = (data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1
                                annualized = ((1 + total_return) ** (1 / years)) - 1

                                analysis_text += f"\nPERIOD RETURNS:\n"
                                analysis_text += f"  Total Return: {total_return * 100:.2f}%\n"
                                analysis_text += f"  Annualized Return: {annualized * 100:.2f}%\n"

                        # Calculate drawdowns
                        roll_max = data['Close'].cummax()
                        drawdown = (data['Close'] - roll_max) / roll_max * 100
                        max_dd = drawdown.min()

                        analysis_text += f"\nDRAWDOWNS:\n"
                        analysis_text += f"  Maximum Drawdown: {max_dd:.2f}%\n"

                        # Find date of max drawdown
                        dd_date = drawdown.idxmin().strftime('%Y-%m-%d')
                        analysis_text += f"  Date of Max Drawdown: {dd_date}\n"

                    analysis_text += "\n"

                # Price-Volume Correlation
                if self.show_correlation.isChecked():
                    analysis_text += "===== CORRELATION ANALYSIS =====\n"

                    if 'Close' in data.columns and 'Volume' in data.columns:
                        # Calculate correlation
                        corr = data['Close'].corr(data['Volume'])
                        analysis_text += f"Price-Volume Correlation: {corr:.4f}\n"

                        if corr > 0.5:
                            analysis_text += "Strong positive correlation between price and volume\n"
                        elif corr > 0.2:
                            analysis_text += "Moderate positive correlation between price and volume\n"
                        elif corr > -0.2:
                            analysis_text += "Weak/no correlation between price and volume\n"
                        elif corr > -0.5:
                            analysis_text += "Moderate negative correlation between price and volume\n"
                        else:
                            analysis_text += "Strong negative correlation between price and volume\n"

                        # Calculate correlation on daily changes
                        data['Price Change'] = data['Close'].pct_change()
                        data['Volume Change'] = data['Volume'].pct_change()

                        change_corr = data['Price Change'].corr(data['Volume Change'])
                        analysis_text += f"\nPrice Change - Volume Change Correlation: {change_corr:.4f}\n"

                    analysis_text += "\n"

                # Trend Analysis
                if self.show_trends.isChecked():
                    analysis_text += "===== TREND ANALYSIS =====\n"

                    if 'Close' in data.columns:
                        # Calculate short and long-term trend using moving averages
                        if len(data) >= 20:
                            data['MA20'] = data['Close'].rolling(window=20).mean()
                            current_price = data['Close'].iloc[-1]
                            current_ma20 = data['MA20'].iloc[-1]

                            trend_status = "bullish" if current_price > current_ma20 else "bearish"
                            distance = abs(current_price - current_ma20) / current_ma20 * 100

                            analysis_text += f"20-day Moving Average: {current_ma20:.2f}\n"
                            analysis_text += f"Current Price vs MA20: {trend_status.upper()} ({distance:.2f}% {trend_status})\n"

                        if len(data) >= 50:
                            data['MA50'] = data['Close'].rolling(window=50).mean()
                            current_ma50 = data['MA50'].iloc[-1]

                            trend_status = "bullish" if current_price > current_ma50 else "bearish"
                            distance = abs(current_price - current_ma50) / current_ma50 * 100

                            analysis_text += f"50-day Moving Average: {current_ma50:.2f}\n"
                            analysis_text += f"Current Price vs MA50: {trend_status.upper()} ({distance:.2f}% {trend_status})\n"

                        # Calculate recent trend
                        if len(data) >= 10:
                            last_10_days = data['Close'].iloc[-10:].values
                            # Count consecutive up or down days
                            up_streak = 0
                            down_streak = 0
                            current_streak = 0

                            for i in range(1, len(last_10_days)):
                                if last_10_days[i] > last_10_days[i - 1]:
                                    if current_streak > 0:
                                        current_streak += 1
                                    else:
                                        current_streak = 1
                                elif last_10_days[i] < last_10_days[i - 1]:
                                    if current_streak < 0:
                                        current_streak -= 1
                                    else:
                                        current_streak = -1

                                if current_streak > up_streak:
                                    up_streak = current_streak
                                elif current_streak < down_streak:
                                    down_streak = current_streak

                            analysis_text += f"\nRecent Price Action:\n"
                            if current_streak > 0:
                                analysis_text += f"  Current Streak: {current_streak} days UP\n"
                            elif current_streak < 0:
                                analysis_text += f"  Current Streak: {abs(current_streak)} days DOWN\n"
                            else:
                                analysis_text += f"  Current Streak: Unchanged\n"

                            analysis_text += f"  Longest Up Streak (last 10 days): {up_streak} days\n"
                            analysis_text += f"  Longest Down Streak (last 10 days): {abs(down_streak)} days\n"

                        # Simple trend direction and strength
                        first_price = data['Close'].iloc[0]
                        last_price = data['Close'].iloc[-1]
                        pct_change = (last_price - first_price) / first_price * 100

                        trend_strength = "Strong" if abs(pct_change) > 20 else "Moderate" if abs(
                            pct_change) > 10 else "Weak"
                        trend_direction = "Bullish" if pct_change > 0 else "Bearish"

                        analysis_text += f"\nOverall Trend: {trend_strength} {trend_direction} ({pct_change:.2f}%)\n"

                    analysis_text += "\n"

                # Display the analysis
                self.analysis_results.setText(analysis_text)

        except Exception as e:
            error_msg = f"Error generating analysis: {str(e)}"
            self.analysis_results.setText(error_msg)
            print(error_msg)

    def copy_analysis(self):
        """Copy the analysis to clipboard"""
        text = self.analysis_results.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copy Complete", "Analysis copied to clipboard")

    def save_analysis(self):
        """Save the analysis to a text file"""
        text = self.analysis_results.toPlainText()
        if not text:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Analysis",
            f"{self.ticker_symbol}_analysis.txt",
            "Text Files (*.txt)")

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(text)
                QMessageBox.information(self, "Save Complete", f"Analysis saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save analysis: {str(e)}")


class StockDetailTable(QTableWidget):
    """Custom table for displaying detailed stock information"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up table appearance
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Metric", "Value"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #041E42;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)

    def update_data(self, data_dict):
        """Update table with dictionary of stock information"""
        # Clear existing rows
        self.setRowCount(0)

        if not data_dict:
            return

        # Add rows for each item
        for key, value in data_dict.items():
            row = self.rowCount()
            self.insertRow(row)

            # Add key
            key_item = QTableWidgetItem(key)
            key_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.setItem(row, 0, key_item)

            # Add value
            value_item = QTableWidgetItem(str(value))
            self.setItem(row, 1, value_item)

            # Color positive/negative values
            if isinstance(value, str) and ("+" in value or "-" in value) and ("%" in value):
                if "+" in value:
                    value_item.setForeground(QColor("#00c853"))
                else:
                    value_item.setForeground(QColor("#ff1744"))


class StockReportsPage(QWidget):
    """Main stock reports page widget"""
    # Signal to switch back to dashboard
    switch_to_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # Set a timer for auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_current_stock)
        self.refresh_timer.start(60000)  # Refresh every minute

    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        header_layout = QHBoxLayout()

        # Back button
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        back_btn.clicked.connect(self.switch_to_dashboard.emit)

        # Title
        title = QLabel("Stock Reports & Analysis")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #041E42;")

        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add header to main layout
        main_layout.addLayout(header_layout)

        # Search bar section
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 10, 15, 10)

        # Search label
        search_label = QLabel("Search Stock:")
        search_label.setStyleSheet("font-weight: bold;")

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter stock symbol or name (e.g., RELIANCE, TCS)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QLineEdit:focus {
                border: 1px solid #041E42;
                background-color: white;
            }
        """)
        self.search_input.returnPressed.connect(self.search_stock)

        # Search button
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)
        search_btn.clicked.connect(self.search_stock)

        # Add widgets to search layout
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)  # Give search input more space
        search_layout.addWidget(search_btn)

        # Add search frame to main layout
        main_layout.addWidget(search_frame)

        # Create stock info area
        self.stock_info_area = QScrollArea()
        self.stock_info_area.setWidgetResizable(True)
        self.stock_info_area.setFrameShape(QFrame.Shape.NoFrame)
        self.stock_info_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.stock_info_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create container for stock info
        self.stock_info_container = QWidget()
        self.stock_info_layout = QVBoxLayout(self.stock_info_container)
        self.stock_info_layout.setContentsMargins(0, 0, 0, 0)
        self.stock_info_layout.setSpacing(15)

        # Set container as the widget for the scroll area
        self.stock_info_area.setWidget(self.stock_info_container)

        # Add empty state message
        self.empty_state = QLabel("Search for a stock to view detailed information and charts")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setStyleSheet("font-size: 16px; color: #666; margin: 50px 0;")
        self.stock_info_layout.addWidget(self.empty_state)

        # Create stock detail section (initially hidden)
        self.detail_section = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_section)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(15)

        # Stock header with title and last updated
        self.stock_header = QWidget()
        header_layout = QHBoxLayout(self.stock_header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.stock_title = QLabel()
        self.stock_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #041E42;")

        self.last_updated = QLabel()
        self.last_updated.setStyleSheet("color: #666;")

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #041E42;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0F2E5A;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_current_stock)

        header_layout.addWidget(self.stock_title)
        header_layout.addStretch()
        header_layout.addWidget(self.last_updated)
        header_layout.addWidget(self.refresh_btn)

        self.detail_layout.addWidget(self.stock_header)

        # Quick info cards
        cards_frame = QFrame()
        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(15)

        # Create info cards
        self.price_card = StockInfoCard("Current Price", "--")
        self.prev_close_card = StockInfoCard("Previous Close", "--")
        self.open_card = StockInfoCard("Open", "--")
        self.day_range_card = StockInfoCard("Day Range", "--")
        self.volume_card = StockInfoCard("Volume", "--")
        self.change_card = StockInfoCard("Change", "--", "+0.00%")

        # Add cards to layout
        cards_layout.addWidget(self.price_card)
        cards_layout.addWidget(self.prev_close_card)
        cards_layout.addWidget(self.open_card)
        cards_layout.addWidget(self.day_range_card)
        cards_layout.addWidget(self.volume_card)
        cards_layout.addWidget(self.change_card)

        self.detail_layout.addWidget(cards_frame)

        # Create tabs for different sections
        self.detail_tabs = QTabWidget()
        self.detail_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e0e0e0;
            }
        """)

        # Add chart tab
        self.chart_widget = StockChart()
        self.detail_tabs.addTab(self.chart_widget, "Price Chart")

        # Add historical data tab
        self.historical_widget = HistoricalDataWidget()
        self.detail_tabs.addTab(self.historical_widget, "Historical Data")

        # Add company info tab
        self.company_info = QWidget()
        company_layout = QVBoxLayout(self.company_info)

        # Company profile table
        self.company_table = StockDetailTable()
        company_layout.addWidget(self.company_table)

        self.detail_tabs.addTab(self.company_info, "Company Info")

        # Add key statistics tab
        self.statistics = QWidget()
        statistics_layout = QVBoxLayout(self.statistics)

        # Statistics table
        self.statistics_table = StockDetailTable()
        statistics_layout.addWidget(self.statistics_table)

        self.detail_tabs.addTab(self.statistics, "Key Statistics")

        # Add tabs to details layout
        self.detail_layout.addWidget(self.detail_tabs)

        # Add stock details widget to the info layout (initially hidden)
        self.detail_section.setVisible(False)
        self.stock_info_layout.addWidget(self.detail_section)

        # Add info area to main layout
        main_layout.addWidget(self.stock_info_area)

        # Add status bar at the bottom
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("""
            QLabel {
                background-color: #041E42;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.status_bar)

        # Initialize state variables
        self.current_ticker = None

    def search_stock(self):
        """Search for a stock and display its details"""
        search_text = self.search_input.text().strip().upper()

        if not search_text:
            return

        self.status_bar.setText(f"Searching for {search_text}...")

        try:
            # Check if the symbol should have .NS suffix
            if not search_text.endswith('.NS') and not search_text.endswith('.BO'):
                ticker_symbol = f"{search_text}.NS"
            else:
                ticker_symbol = search_text

            # Try to fetch basic info to validate the symbol
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            # Check if info contains required fields
            if 'regularMarketPrice' not in info and 'currentPrice' not in info:
                # Try Mumbai exchange if NSE failed
                if ticker_symbol.endswith('.NS'):
                    ticker_symbol = ticker_symbol.replace('.NS', '.BO')
                    ticker = yf.Ticker(ticker_symbol)
                    info = ticker.info

                # Still no data, show error
                if 'regularMarketPrice' not in info and 'currentPrice' not in info:
                    self.status_bar.setText(f"No data found for {search_text}. Please check the symbol.")
                    QMessageBox.warning(self, "Stock Not Found",
                                        f"Could not find stock data for {search_text}. Please verify the symbol.")
                    return

            # Stock found, display details
            self.display_stock_details(ticker_symbol, info)

            # Clear search field and update status
            self.search_input.clear()
            self.status_bar.setText(f"Displaying data for {ticker_symbol}")

        except Exception as e:
            self.status_bar.setText(f"Error searching for stock: {str(e)}")
            QMessageBox.warning(self, "Search Error", f"Error while searching for {search_text}: {str(e)}")
            print(f"Search error: {str(e)}")

    def display_stock_details(self, ticker_symbol, info):
        """Display the details for the found stock"""
        try:
            # Save current ticker
            self.current_ticker = ticker_symbol

            # Hide empty state and show detail section
            self.empty_state.setVisible(False)
            self.detail_section.setVisible(True)

            # Update stock header
            company_name = info.get('longName', ticker_symbol)
            self.stock_title.setText(f"{company_name} ({ticker_symbol})")

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_updated.setText(f"Last Updated: {current_time}")

            # Update quick info cards
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))
            open_price = info.get('open', info.get('regularMarketOpen', 0))
            day_high = info.get('dayHigh', info.get('regularMarketDayHigh', 0))
            day_low = info.get('dayLow', info.get('regularMarketDayLow', 0))
            volume = info.get('volume', info.get('regularMarketVolume', 0))

            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0

            # Update cards
            self.price_card.update_value(f"₹{current_price:,.2f}")
            self.prev_close_card.update_value(f"₹{previous_close:,.2f}")
            self.open_card.update_value(f"₹{open_price:,.2f}")
            self.day_range_card.update_value(f"₹{day_low:,.2f} - ₹{day_high:,.2f}")
            self.volume_card.update_value(f"{volume:,}")
            self.change_card.update_value(f"₹{change:,.2f}", change, change_percent)

            # Update chart
            self.chart_widget.set_ticker(ticker_symbol)

            # Update historical data widget
            self.historical_widget.set_ticker(ticker_symbol)

            # Update company info
            self.update_company_info(info)

            # Update key statistics
            self.update_statistics(info)

            # Save company report to database
            from database import DatabaseConnection  # Import at the top of the file
            database_connection = DatabaseConnection()
            database_connection.add_company_report(
                ticker_symbol.replace('.NS', '').replace('.BO', ''),
                info
            )

        except Exception as e:
            self.status_bar.setText(f"Error displaying stock details: {str(e)}")
            print(f"Display error: {str(e)}")

    def update_company_info(self, info):
        """Update the company info table with data"""
        # Extract relevant company information
        company_data = {}

        if 'longName' in info:
            company_data['Company Name'] = info['longName']

        if 'sector' in info:
            company_data['Sector'] = info['sector']

        if 'industry' in info:
            company_data['Industry'] = info['industry']

        if 'fullTimeEmployees' in info:
            company_data['Employees'] = f"{info['fullTimeEmployees']:,}"

        if 'country' in info:
            company_data['Country'] = info['country']

        if 'city' in info:
            company_data['City'] = info['city']

        if 'website' in info:
            company_data['Website'] = info['website']

        if 'longBusinessSummary' in info:
            company_data['Business Summary'] = info['longBusinessSummary']

        # Update the table
        self.company_table.update_data(company_data)

    def update_statistics(self, info):
        """Update the key statistics table with data"""
        # Extract relevant financial statistics
        stats_data = {}

        # Market data
        if 'marketCap' in info:
            stats_data['Market Cap'] = f"₹{info['marketCap']:,.2f}"

        if 'enterpriseValue' in info:
            stats_data['Enterprise Value'] = f"₹{info['enterpriseValue']:,.2f}"

        # Share statistics
        if 'sharesOutstanding' in info:
            stats_data['Shares Outstanding'] = f"{info['sharesOutstanding']:,.0f}"

        if 'floatShares' in info:
            stats_data['Float'] = f"{info['floatShares']:,.0f}"

        if 'beta' in info:
            stats_data['Beta'] = f"{info['beta']:.2f}"

        # Price metrics
        if 'trailingPE' in info:
            stats_data['PE Ratio (TTM)'] = f"{info['trailingPE']:.2f}"

        if 'forwardPE' in info:
            stats_data['Forward PE'] = f"{info['forwardPE']:.2f}"

        if 'priceToBook' in info:
            stats_data['Price/Book'] = f"{info['priceToBook']:.2f}"

        # Dividends
        if 'dividendYield' in info and info['dividendYield'] is not None:
            stats_data['Dividend Yield'] = f"{info['dividendYield'] * 100:.2f}%"

        if 'dividendRate' in info and info['dividendRate'] is not None:
            stats_data['Dividend Rate'] = f"₹{info['dividendRate']:.2f}"

        # Financial metrics
        if 'returnOnEquity' in info and info['returnOnEquity'] is not None:
            stats_data['Return on Equity'] = f"{info['returnOnEquity'] * 100:.2f}%"

        if 'returnOnAssets' in info and info['returnOnAssets'] is not None:
            stats_data['Return on Assets'] = f"{info['returnOnAssets'] * 100:.2f}%"

        if 'profitMargins' in info and info['profitMargins'] is not None:
            stats_data['Profit Margin'] = f"{info['profitMargins'] * 100:.2f}%"

        if 'operatingMargins' in info and info['operatingMargins'] is not None:
            stats_data['Operating Margin'] = f"{info['operatingMargins'] * 100:.2f}%"

        # Trading info
        if 'fiftyTwoWeekHigh' in info:
            stats_data['52-Week High'] = f"₹{info['fiftyTwoWeekHigh']:,.2f}"

        if 'fiftyTwoWeekLow' in info:
            stats_data['52-Week Low'] = f"₹{info['fiftyTwoWeekLow']:,.2f}"

        if 'averageVolume' in info:
            stats_data['Average Volume'] = f"{info['averageVolume']:,}"

        # Update the table
        self.statistics_table.update_data(stats_data)

    def refresh_current_stock(self):
        """Refresh data for the currently displayed stock"""
        if not self.current_ticker:
            return

        try:
            self.status_bar.setText(f"Refreshing data for {self.current_ticker}...")

            # Fetch fresh data
            ticker = yf.Ticker(self.current_ticker)
            info = ticker.info

            # Update the display
            self.display_stock_details(self.current_ticker, info)

            self.status_bar.setText(f"Data refreshed for {self.current_ticker}")

        except Exception as e:
            self.status_bar.setText(f"Error refreshing data: {str(e)}")
            print(f"Refresh error: {str(e)}")


class ReportsWindow(QWidget):
    """Main ReportsWindow that integrates with the dashboard navigation"""
    switch_to_dashboard = pyqtSignal()

    def __init__(self, title="reports"):
        super().__init__()
        self.setWindowTitle(f"SARASFINTECH - {title}")

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create stock reports page
        self.stock_reports_page = StockReportsPage()

        # Connect signals
        self.stock_reports_page.switch_to_dashboard.connect(self.switch_to_dashboard)

        # Add to layout
        layout.addWidget(self.stock_reports_page)


# For testing the widget independently
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ReportsWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())