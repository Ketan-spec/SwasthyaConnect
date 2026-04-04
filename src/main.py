import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.database import initialize_database
from src.ui.login_window import LoginWindow

def main():
    # Initialize Database
    initialize_database()
    
    # Initialize App
    app = QApplication(sys.argv)
    
    # Show Login Window
    window = LoginWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
