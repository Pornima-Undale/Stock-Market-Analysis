# database.py
from database_manager import DatabaseManager
import json
import socket
from datetime import datetime


class DatabaseConnection:
    def __init__(self):
        """Initialize using the database manager singleton"""
        self.manager = DatabaseManager.get_instance()

    def add_to_watchlist(self, user_id, stock_symbol, notes=None):
        """Add a stock to user's watchlist"""
        try:
            query = """
            INSERT INTO watchlist (user_id, stock_symbol, notes)
            VALUES (%s, %s, %s)
            """
            success, error = self.manager.execute_query(query, (user_id, stock_symbol, notes), commit=True)

            if not success:
                if "Duplicate entry" in error:
                    return False, f"{stock_symbol} is already in your watchlist"
                return False, f"Database error: {error}"

            # Log the action
            self.log_access(user_id, None, "WATCHLIST_ADD", "SUCCESS",
                            details=f"Added {stock_symbol} to watchlist")

            return True, f"Added {stock_symbol} to watchlist"
        except Exception as e:
            print(f"❌ Error adding to watchlist: {e}")
            return False, f"Database error: {str(e)}"

    def log_access(self, user_id=None, admin_id=None, action_type="", status="", details=None):
        """
        Log access or actions for security and audit purposes
        """
        try:
            # Get IP address (simplified for local development)
            ip_address = socket.gethostbyname(socket.gethostname())

            query = """
            INSERT INTO access_logs 
            (user_id, admin_id, action_type, ip_address, status, details)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            params = (
                user_id, admin_id, action_type, ip_address, status,
                json.dumps(details) if details else None
            )

            success, error = self.manager.execute_query(query, params, commit=True)

            if not success:
                print(f"❌ Error logging access: {error}")
                return False

            return True
        except Exception as e:
            print(f"❌ Error logging access: {e}")
            return False

    def remove_from_watchlist(self, user_id, stock_symbol):
        """
        Remove a stock from user's watchlist
        """
        try:
            query = """
            DELETE FROM watchlist 
            WHERE user_id = %s AND stock_symbol = %s
            """
            success, error = self.manager.execute_query(query, (user_id, stock_symbol), commit=True)

            if not success:
                return False, f"Database error: {error}"

            if self.manager.cursor.rowcount > 0:
                # Log the action
                self.log_access(user_id, None, "WATCHLIST_REMOVE", "SUCCESS",
                                details=f"Removed {stock_symbol} from watchlist")
                return True, f"Removed {stock_symbol} from watchlist"
            else:
                return False, f"{stock_symbol} was not in your watchlist"

        except Exception as e:
            print(f"❌ Error removing from watchlist: {e}")
            return False, f"Database error: {str(e)}"

    def get_user_watchlist(self, user_id):
        """
        Get watchlist stocks for a specific user
        """
        try:
            query = """
            SELECT w.watchlist_id, w.stock_symbol, w.date_added, w.notes
            FROM watchlist w
            WHERE w.user_id = %s
            ORDER BY w.date_added DESC
            """
            success, error = self.manager.execute_query(query, (user_id,))

            if not success:
                print(f"❌ Error getting watchlist: {error}")
                return []

            return self.manager.fetchall()
        except Exception as e:
            print(f"❌ Error getting watchlist: {e}")
            return []

    def get_user_portfolio(self, user_id):
        """
        Get portfolio holdings for a specific user
        """
        try:
            query = """
            SELECT p.portfolio_id, p.stock_symbol, p.quantity, p.purchase_price, 
                   p.purchase_date, p.notes
            FROM portfolio p
            WHERE p.user_id = %s
            ORDER BY p.purchase_date DESC
            """
            success, error = self.manager.execute_query(query, (user_id,))

            if not success:
                print(f"❌ Error getting portfolio: {error}")
                return []

            return self.manager.fetchall()
        except Exception as e:
            print(f"❌ Error getting portfolio: {e}")
            return []

    def add_to_portfolio(self, user_id, stock_symbol, quantity, purchase_price, purchase_date, notes=None):
        """
        Add a stock to user's portfolio
        """
        try:
            query = """
            INSERT INTO portfolio (user_id, stock_symbol, quantity, purchase_price, purchase_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            success, error = self.manager.execute_query(
                query,
                (user_id, stock_symbol, quantity, purchase_price, purchase_date, notes),
                commit=True
            )

            if not success:
                return False, f"Database error: {error}"

            # Log the action
            self.log_access(user_id, None, "PORTFOLIO_ADD", "SUCCESS",
                            details=f"Added {quantity} shares of {stock_symbol} to portfolio")

            return True, f"Added {quantity} shares of {stock_symbol} to portfolio"
        except Exception as e:
            print(f"❌ Error adding to portfolio: {e}")
            return False, f"Database error: {str(e)}"

    def remove_from_portfolio(self, user_id, portfolio_id):
        """
        Remove a stock from user's portfolio
        """
        try:
            # First get the stock symbol for logging
            query = "SELECT stock_symbol FROM portfolio WHERE portfolio_id = %s AND user_id = %s"
            success, error = self.manager.execute_query(query, (portfolio_id, user_id))

            if not success:
                return False, f"Database error: {error}"

            result = self.manager.fetchone()

            if not result:
                return False, "Portfolio item not found or doesn't belong to you"

            stock_symbol = result['stock_symbol']

            # Delete the portfolio item
            delete_query = "DELETE FROM portfolio WHERE portfolio_id = %s AND user_id = %s"
            success, error = self.manager.execute_query(delete_query, (portfolio_id, user_id), commit=True)

            if not success:
                return False, f"Database error: {error}"

            # Log the action
            self.log_access(user_id, None, "PORTFOLIO_REMOVE", "SUCCESS",
                            details=f"Removed {stock_symbol} from portfolio")

            return True, f"Removed {stock_symbol} from portfolio"
        except Exception as e:
            print(f"❌ Error removing from portfolio: {e}")
            return False, f"Database error: {str(e)}"

    def get_user_analytics_preferences(self, user_id):
        """Get analytics preferences for a specific user"""
        try:
            query = """
            SELECT preference_id, stock_symbol, date_added
            FROM analytics_preferences
            WHERE user_id = %s
            ORDER BY date_added DESC
            """
            success, error = self.manager.execute_query(query, (user_id,))

            if not success:
                print(f"❌ Error getting analytics preferences: {error}")
                return []

            return self.manager.fetchall()
        except Exception as e:
            print(f"❌ Error getting analytics preferences: {e}")
            return []

    def add_analytics_preference(self, user_id, stock_symbol):
        """Add a stock to user's analytics preferences"""
        try:
            query = """
            INSERT INTO analytics_preferences (user_id, stock_symbol)
            VALUES (%s, %s)
            """
            success, error = self.manager.execute_query(query, (user_id, stock_symbol), commit=True)

            if not success:
                if "Duplicate entry" in error:
                    return False, f"{stock_symbol} is already in your analytics preferences"
                return False, f"Database error: {error}"

            # Log the action
            self.log_access(user_id, None, "ANALYTICS_ADD", "SUCCESS",
                            details=f"Added {stock_symbol} to analytics preferences")

            return True, f"Added {stock_symbol} to analytics"
        except Exception as e:
            print(f"❌ Error adding to analytics preferences: {e}")
            return False, f"Database error: {str(e)}"

    def remove_analytics_preference(self, user_id, preference_id):
        """Remove a stock from user's analytics preferences"""
        try:
            # First get the stock symbol for logging
            query = """
            SELECT stock_symbol FROM analytics_preferences 
            WHERE preference_id = %s AND user_id = %s
            """
            success, error = self.manager.execute_query(query, (preference_id, user_id))

            if not success:
                return False, f"Database error: {error}"

            result = self.manager.fetchone()
            if not result:
                return False, "Analytics preference not found or doesn't belong to you"

            stock_symbol = result['stock_symbol']

            # Delete the preference
            delete_query = """
            DELETE FROM analytics_preferences 
            WHERE preference_id = %s AND user_id = %s
            """
            success, error = self.manager.execute_query(delete_query,
                                                        (preference_id, user_id),
                                                        commit=True)

            if not success:
                return False, f"Database error: {error}"

            # Log the action
            self.log_access(user_id, None, "ANALYTICS_REMOVE", "SUCCESS",
                            details=f"Removed {stock_symbol} from analytics preferences")

            return True, f"Removed {stock_symbol} from analytics"
        except Exception as e:
            print(f"❌ Error removing from analytics preferences: {e}")
            return False, f"Database error: {str(e)}"

    def create_user(self, username, email, password):
        """
        Create a new user account

        Args:
            username (str): The username for the new account
            email (str): The email address for the new account
            password (str): The password for the new account

        Returns:
            tuple: (success, message)
        """
        try:
            # Check if username already exists
            check_username_query = "SELECT user_id FROM user WHERE user_name = %s"
            success, error = self.manager.execute_query(check_username_query, (username,))

            if not success:
                return False, f"Database error: {error}"

            if self.manager.fetchone():
                return False, "Username already exists. Please choose another username."

            # Check if email already exists
            check_email_query = "SELECT user_id FROM user WHERE email = %s"
            success, error = self.manager.execute_query(check_email_query, (email,))

            if not success:
                return False, f"Database error: {error}"

            if self.manager.fetchone():
                return False, "Email already registered. Please use a different email."

            # Insert new user
            insert_query = """
            INSERT INTO user (user_name, email, password, created_at, account_status)
            VALUES (%s, %s, %s, NOW(), 'active')
            """
            success, error = self.manager.execute_query(
                insert_query,
                (username, email, password),
                commit=True
            )

            if not success:
                return False, f"Database error: {error}"

            # Get the new user ID
            user_id = self.manager.cursor.lastrowid

            # Log the account creation
            self.log_access(user_id, None, "USER_REGISTRATION", "SUCCESS")

            return True, "Account created successfully"

        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False, f"Database error: {str(e)}"

    def verify_login(self, username, password):
        """
        Verify user login with proper password checking
        """
        try:
            # Find user by username
            query = "SELECT * FROM user WHERE user_name = %s"
            success, error = self.manager.execute_query(query, (username,))

            if not success:
                return False, f"Database error: {error}"

            user = self.manager.fetchone()

            if not user:
                self.log_access(None, None, "USER_LOGIN_ATTEMPT", "FAILED", details="User not found")
                return False, "Invalid username or password"

            # Using plain text for compatibility with your current system
            if user['password'] == password:
                # Update last login time
                query = "UPDATE user SET last_login = NOW() WHERE user_id = %s"
                self.manager.execute_query(query, (user['user_id'],), commit=True)

                # Log successful login
                self.log_access(user['user_id'], None, "USER_LOGIN", "SUCCESS")

                # Return user info (excluding password)
                user_info = dict(user)
                user_info.pop('password', None)
                return True, user_info
            else:
                # Log failed login attempt
                self.log_access(None, None, "USER_LOGIN_ATTEMPT", "FAILED",
                                details=f"Invalid password for user: {username}")
                return False, "Invalid username or password"

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False, f"Database error: {str(e)}"

    def add_company_report(self, ticker_symbol, info):
        """
        Add or update a company report with basic information
        """
        try:
            query = """
            INSERT INTO company_reports 
            (stock_symbol, company_name, current_price, market_cap, report_date)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
            company_name = VALUES(company_name),
            current_price = VALUES(current_price),
            market_cap = VALUES(market_cap),
            report_date = NOW()
            """

            # Extract values
            company_name = info.get('longName', ticker_symbol)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            market_cap = info.get('marketCap', 0)

            # Execute query
            success, error = self.manager.execute_query(
                query,
                (ticker_symbol, company_name, current_price, market_cap),
                commit=True
            )

            if not success:
                print(f"❌ Error adding company report: {error}")
                return False

            return True

        except Exception as e:
            print(f"❌ Error adding company report: {e}")
            return False

    def get_company_reports(self, limit=50):
        """
        Retrieve recent company reports
        """
        try:
            query = """
            SELECT stock_symbol, company_name, current_price, market_cap, report_date
            FROM company_reports
            ORDER BY report_date DESC
            LIMIT %s
            """

            success, error = self.manager.execute_query(query, (limit,))

            if not success:
                print(f"❌ Error getting company reports: {error}")
                return []

            return self.manager.fetchall()

        except Exception as e:
            print(f"❌ Error getting company reports: {e}")
            return []

    def get_company_report_by_symbol(self, stock_symbol):
        """
        Retrieve a specific company report by stock symbol
        """
        try:
            query = """
            SELECT * FROM company_reports
            WHERE stock_symbol = %s
            """

            success, error = self.manager.execute_query(query, (stock_symbol,))

            if not success:
                print(f"❌ Error getting company report: {error}")
                return None

            return self.manager.fetchone()

        except Exception as e:
            print(f"❌ Error getting company report: {e}")
            return None

    def save_stock_data(self, symbol, current_price, open_price, high_price, low_price, volume, change_percentage):
        """
        Simple method to save stock data to the database
        """
        try:
            query = """
            INSERT INTO stock 
            (symbol, current_price, open_price, high_price, low_price, volume, change_percentage, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            current_price = %s,
            open_price = %s,
            high_price = %s,
            low_price = %s,
            volume = %s,
            change_percentage = %s,
            last_updated = NOW()
            """

            # Prepare parameters
            params = (
                symbol, current_price, open_price, high_price, low_price, volume, change_percentage,
                # Duplicate values for UPDATE part
                current_price, open_price, high_price, low_price, volume, change_percentage
            )

            # Execute query
            success, error = self.manager.execute_query(query, params, commit=True)

            if not success:
                print(f"❌ Error saving stock data for {symbol}: {error}")
                return False

            return True

        except Exception as e:
            print(f"❌ Error in save_stock_data: {e}")
            return False

    def close(self):
        """
        Close connection via manager - mainly a no-op since manager handles connections
        """
        # We don't manually close connections when using the manager
        pass