import sys
from PyQt6.QtWidgets import QApplication
from adminlogin import AdminLoginWindow

def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Start with login window
    login_window = AdminLoginWindow()
    login_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()