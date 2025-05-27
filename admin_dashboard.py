from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFrame, QFileDialog, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import sys
from datetime import datetime
import pandas as pd
from database_manager import DatabaseManager


class AdminDashboard(QMainWindow):
    # Signal to send logout event to login window
    logout_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Initialize database connection
        self.db_manager = DatabaseManager.get_instance()

        self.init_ui()
        self.populate_user_table()
        self.populate_admin_reports_table()

    def init_ui(self):
        # Set window properties
        self.setWindowTitle('SARASFINTECH - Admin Dashboard')
        self.setMinimumSize(1550, 1000)
        self.setStyleSheet("""
            # ... (keep your existing stylesheet)
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #ddd;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background: #041E42;
                color: white;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Create header with title and logout button
        header_layout = QHBoxLayout()

        title_label = QLabel('Admin Dashboard')
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #041E42;
        """)

        logout_button = QPushButton('Logout')
        logout_button.setObjectName('logoutBtn')
        logout_button.clicked.connect(self.handle_logout)
        logout_button.setFixedWidth(120)

        # Add current admin and time
        current_time = QLabel(f"Last Login: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        current_time.setStyleSheet("color: #555; font-size: 12px;")

        admin_info = QLabel("Admin: Administrator")
        admin_info.setStyleSheet("color: #555; font-size: 12px;")

        time_layout = QVBoxLayout()
        time_layout.addWidget(admin_info)
        time_layout.addWidget(current_time)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addLayout(time_layout)
        header_layout.addWidget(logout_button)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # User Management Tab
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)

        # Add controls section for user management
        user_controls_layout = QHBoxLayout()

        # Add search input
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("Search users...")
        self.user_search.textChanged.connect(self.filter_users)

        # Add refresh button
        user_refresh_button = QPushButton("Refresh")
        user_refresh_button.clicked.connect(self.populate_user_table)
        user_refresh_button.setFixedWidth(120)

        # Add export button
        user_export_button = QPushButton("Export Excel")
        user_export_button.setObjectName('exportBtn')
        user_export_button.clicked.connect(self.export_to_excel)
        user_export_button.setFixedWidth(120)

        # Add controls to layout
        user_controls_layout.addWidget(self.user_search)
        user_controls_layout.addWidget(user_refresh_button)
        user_controls_layout.addWidget(user_export_button)

        # Create users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)  # Only show ID, username, email
        self.users_table.setHorizontalHeaderLabels([
            "User ID", "Username", "Email"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Add widgets to user tab layout
        user_layout.addLayout(user_controls_layout)
        user_layout.addWidget(self.users_table)

        # Admin Reports Tab
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(reports_tab)

        # Add controls section for admin reports
        reports_controls_layout = QHBoxLayout()

        # Add search input for reports
        self.reports_search = QLineEdit()
        self.reports_search.setPlaceholderText("Search reports...")
        self.reports_search.textChanged.connect(self.filter_admin_reports)

        # Add refresh button for reports
        reports_refresh_button = QPushButton("Refresh")
        reports_refresh_button.clicked.connect(self.populate_admin_reports_table)
        reports_refresh_button.setFixedWidth(120)

        # Add export button for reports
        reports_export_button = QPushButton("Export Excel")
        reports_export_button.setObjectName('exportBtn')
        reports_export_button.clicked.connect(self.export_admin_reports_to_excel)
        reports_export_button.setFixedWidth(120)

        # Add controls to reports layout
        reports_controls_layout.addWidget(self.reports_search)
        reports_controls_layout.addWidget(reports_refresh_button)
        reports_controls_layout.addWidget(reports_export_button)

        # Create admin reports table
        self.admin_reports_table = QTableWidget()
        self.admin_reports_table.setColumnCount(5)  # report_id, user_id, username, email, report_date
        self.admin_reports_table.setHorizontalHeaderLabels([
            "Report ID", "User ID", "Username", "Email", "Report Date"
        ])
        self.admin_reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.admin_reports_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.admin_reports_table.setAlternatingRowColors(True)
        self.admin_reports_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Add widgets to reports tab layout
        reports_layout.addLayout(reports_controls_layout)
        reports_layout.addWidget(self.admin_reports_table)

        # Add tabs to tab widget
        self.tab_widget.addTab(user_tab, "User Management")
        self.tab_widget.addTab(reports_tab, "Admin Reports")

        # Add tab widget to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tab_widget)

        # Remove these duplicate lines at the end
        # main_layout.addLayout(header_layout)
        # main_layout.addWidget(user_frame)

    def handle_logout(self):
        """Handle logout button click"""
        reply = QMessageBox.question(
            self, 'Confirm Logout',
            'Are you sure you want to logout?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Close database connection
            if hasattr(self, 'db_manager'):
                self.db_manager.close()

            # Emit logout signal to show login window
            self.logout_signal.emit()
            self.close()

    def populate_user_table(self):
        """Fetch and display user data from the database"""
        try:
            # Clear the table
            self.users_table.setRowCount(0)

            # Fetch data from database
            query = "SELECT user_id, user_name, email FROM user"
            success, error = self.db_manager.execute_query(query)

            if not success:
                QMessageBox.warning(self, "Database Error", f"Failed to fetch user data: {error}")
                return

            # Get user data
            users = self.db_manager.fetchall()

            # Populate table
            for i, user in enumerate(users):
                self.users_table.insertRow(i)

                # Add user ID
                id_item = QTableWidgetItem(str(user['user_id']))
                self.users_table.setItem(i, 0, id_item)

                # Add username
                username_item = QTableWidgetItem(user['user_name'])
                self.users_table.setItem(i, 1, username_item)

                # Add email
                email_item = QTableWidgetItem(user['email'])
                self.users_table.setItem(i, 2, email_item)

            # Show success message
            if len(users) > 0:
                self.statusBar().showMessage(f"Loaded {len(users)} users", 3000)
            else:
                self.statusBar().showMessage("No users found", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def filter_users(self):
        """Filter users based on search input"""
        search_text = self.user_search.text().lower()

        # Show/hide rows based on search
        for row in range(self.users_table.rowCount()):
            match_found = False

            # Check username and email
            username = self.users_table.item(row, 1).text().lower()
            email = self.users_table.item(row, 2).text().lower()

            if search_text in username or search_text in email:
                match_found = True

            # Show/hide row
            self.users_table.setRowHidden(row, not match_found)

    def export_to_excel(self):
        """Export user data to Excel file"""
        try:
            # Get data from the table
            data = []
            headers = []

            # Get headers
            for col in range(self.users_table.columnCount()):
                headers.append(self.users_table.horizontalHeaderItem(col).text())

            # Get data from all visible rows
            for row in range(self.users_table.rowCount()):
                if not self.users_table.isRowHidden(row):
                    row_data = []
                    for col in range(self.users_table.columnCount()):
                        item = self.users_table.item(row, col)
                        if item:
                            row_data.append(item.text())
                        else:
                            row_data.append("")
                    data.append(row_data)

            # Create DataFrame
            df = pd.DataFrame(data, columns=headers)

            # Ask user for save location - modified to work with PyQt6
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                "user_data.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )

            if file_path:
                # Make sure it has the correct extension
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'

                # Export to Excel
                df.to_excel(file_path, index=False)

                # Show success message
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data successfully exported to {file_path}"
                )

                # Show in status bar
                self.statusBar().showMessage(f"Data exported to {file_path}", 5000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export: {str(e)}"
            )

    def populate_admin_reports_table(self):
        """Fetch and display admin reports data from the database"""
        try:
            # First, insert all current user data into admin_reports
            insert_query = """
            INSERT INTO admin_reports (user_id, user_name, email)
            SELECT user_id, user_name, email FROM user
            WHERE NOT EXISTS (
                SELECT 1 FROM admin_reports ar 
                WHERE ar.user_id = user.user_id
            )
            """
            success, error = self.db_manager.execute_query(insert_query, commit=True)

            if not success:
                QMessageBox.warning(self, "Database Error", f"Failed to generate reports: {error}")
                return

            # Clear the table
            self.admin_reports_table.setRowCount(0)

            # Fetch data from database
            query = "SELECT report_id, user_id, user_name, email, report_date FROM admin_reports ORDER BY report_date DESC"
            success, error = self.db_manager.execute_query(query)

            if not success:
                QMessageBox.warning(self, "Database Error", f"Failed to fetch admin reports: {error}")
                return

            # Get admin reports data
            reports = self.db_manager.fetchall()

            # Populate table
            for i, report in enumerate(reports):
                self.admin_reports_table.insertRow(i)

                # Add report ID
                report_id_item = QTableWidgetItem(str(report['report_id']))
                self.admin_reports_table.setItem(i, 0, report_id_item)

                # Add user ID
                user_id_item = QTableWidgetItem(str(report['user_id']))
                self.admin_reports_table.setItem(i, 1, user_id_item)

                # Add username
                username_item = QTableWidgetItem(report['user_name'])
                self.admin_reports_table.setItem(i, 2, username_item)

                # Add email
                email_item = QTableWidgetItem(report['email'])
                self.admin_reports_table.setItem(i, 3, email_item)

                # Add report date
                date_item = QTableWidgetItem(report['report_date'].strftime('%Y-%m-%d %H:%M:%S'))
                self.admin_reports_table.setItem(i, 4, date_item)

            # Show success message
            if len(reports) > 0:
                self.statusBar().showMessage(f"Loaded {len(reports)} admin reports", 3000)
            else:
                self.statusBar().showMessage("No admin reports found", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def filter_admin_reports(self):
        """Filter admin reports based on search input"""
        search_text = self.reports_search.text().lower()

        # Show/hide rows based on search
        for row in range(self.admin_reports_table.rowCount()):
            match_found = False

            # Check username and email
            username = self.admin_reports_table.item(row, 2).text().lower()
            email = self.admin_reports_table.item(row, 3).text().lower()

            if search_text in username or search_text in email:
                match_found = True

            # Show/hide row
            self.admin_reports_table.setRowHidden(row, not match_found)

    def export_admin_reports_to_excel(self):
        """Export admin reports to Excel file"""
        try:
            # Get data from the table
            data = []
            headers = []

            # Get headers
            for col in range(self.admin_reports_table.columnCount()):
                headers.append(self.admin_reports_table.horizontalHeaderItem(col).text())

            # Get data from all visible rows
            for row in range(self.admin_reports_table.rowCount()):
                if not self.admin_reports_table.isRowHidden(row):
                    row_data = []
                    for col in range(self.admin_reports_table.columnCount()):
                        item = self.admin_reports_table.item(row, col)
                        if item:
                            row_data.append(item.text())
                        else:
                            row_data.append("")
                    data.append(row_data)

            # Create DataFrame
            df = pd.DataFrame(data, columns=headers)

            # Ask user for save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                "admin_reports.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )

            if file_path:
                # Make sure it has the correct extension
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'

                # Export to Excel
                df.to_excel(file_path, index=False)

                # Show success message
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data successfully exported to {file_path}"
                )

                # Show in status bar
                self.statusBar().showMessage(f"Admin reports exported to {file_path}", 5000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during export: {str(e)}"
            )