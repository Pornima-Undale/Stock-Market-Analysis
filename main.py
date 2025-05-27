import sys
from PyQt6.QtWidgets import QApplication
from login import LoginWindow
from signup import SignupWindow

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)  # Create QApplication instance
        self.login_window = LoginWindow()
        self.signup_window = SignupWindow()

        # Connect window switching signals
        self.login_window.switch_to_signup.connect(self.show_signup)
        self.signup_window.switch_to_login.connect(self.show_login)


        # Show login window initially
        self.login_window.show()

    def show_login(self):
        self.signup_window.hide()
        self.login_window.show()

    def show_signup(self):
        self.login_window.hide()
        self.signup_window.show()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == '__main__':
    app = App()
    app.run()