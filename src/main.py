import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.database import initialize_database
from src.ui.login_window import LoginWindow
from src.ui.vm_launcher import VMLauncherWindow

def main():
    # Initialize Database
    initialize_database()
    
    # Initialize App
    app = QApplication(sys.argv)
    
    # Check if direct launch was requested via CLI flags
    if "--direct" in sys.argv or "--no-vm" in sys.argv:
        window = LoginWindow()
        window.show()
    else:
        # Launch UTM Virtual Machine Manager Interface
        login_window = None
        
        def on_boot_complete():
            nonlocal login_window
            login_window = LoginWindow()
            login_window.show()
            
        launcher = VMLauncherWindow(on_boot_complete_callback=on_boot_complete)
        launcher.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
