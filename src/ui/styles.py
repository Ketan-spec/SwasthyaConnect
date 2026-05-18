# Modern Color Palettes
COLORS = {
    "primary": "#2563eb",       # Blue 600
    "primary_hover": "#1d4ed8", # Blue 700
    "secondary": "#64748b",     # Slate 500
    "success": "#10b981",       # Emerald 500
    "danger": "#ef4444",        # Red 500
    "warning": "#f59e0b",       # Amber 500
    "text_dark": "#0f172a",     # Slate 900
    "text_muted": "#475569",    # Slate 600
    "text_light": "#f8fafc",    # Slate 50
    "bg_main": "#f8fafc",       # Slate 50
    "bg_card": "#ffffff",       # White
    "border": "#e2e8f0",        # Slate 200
}

ROLE_THEMES = {
    "patient": {
        "primary": "#0d9488",   # Teal 600
        "primary_hover": "#0f766e",
        "bg_sidebar": "#0f172a", # Slate 900
        "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b)"
    },
    "doctor": {
        "primary": "#2563eb",   # Blue 600
        "bg_sidebar": "#1e3a8a", # Blue 900
        "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3a8a, stop:1 #1e40af)"
    },
    "hospital": {
        "primary": "#dc2626",   # Red 600
        "bg_sidebar": "#7f1d1d", # Red 900
        "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7f1d1d, stop:1 #991b1b)"
    },
    "govt": {
        "primary": "#475569",   # Slate 600
        "bg_sidebar": "#111827", # Gray 900
        "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #1f2937)"
    }
}

# Stylesheets
def get_sidebar_style(role):
    theme = ROLE_THEMES.get(role, ROLE_THEMES["patient"])
    return f"""
        QWidget#Sidebar {{
            background-color: {theme['bg_sidebar']};
            color: white;
            border-right: 1px solid rgba(0,0,0,0.15);
        }}
        QPushButton {{
            background-color: transparent;
            color: #cbd5e1;
            text-align: left;
            padding: 14px 24px;
            font-size: 15px;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            border: none;
            border-left: 4px solid transparent;
            margin: 2px 0px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.08);
            color: white;
        }}
        QPushButton:checked {{
            background-color: rgba(255, 255, 255, 0.15);
            color: white;
            border-left: 4px solid {theme['primary']};
            font-weight: 700;
        }}
        QLabel#SidebarTitle {{
            color: white;
            font-size: 20px;
            font-weight: 800;
            padding: 24px 20px;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            letter-spacing: 0.5px;
        }}
    """

CONTENT_STYLE = """
    * {
        font-family: 'Segoe UI', 'Inter', sans-serif;
        color: #1e293b;
    }
    QWidget#ContentArea {
        background-color: #f0f4f8; /* Soft blue-gray */
    }
    QFrame#Card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    QFrame#Card:hover {
        border: 1px solid #93c5fd;
    }
    QLabel#CardTitle {
        font-size: 15px;
        font-weight: 600;
        color: #64748b;
        padding-bottom: 2px;
    }
    QLabel#CardValue {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
    }
    QLabel#UserWelcome {
        font-size: 32px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 10px;
        letter-spacing: -0.5px;
    }
    QTableWidget {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        gridline-color: #f1f5f9;
        font-size: 14px;
        outline: none;
        selection-background-color: #f1f5f9;
        selection-color: #0f172a;
    }
    QTableWidget::item {
        padding: 12px;
        border-bottom: 1px solid #f1f5f9;
    }
    QHeaderView::section {
        background-color: #f8fafc;
        color: #475569;
        font-weight: 700;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #e2e8f0;
        text-align: left;
    }
    QScrollBar:vertical {
        border: none;
        background: #f1f5f9;
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #cbd5e1;
        min-height: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QPushButton {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #1d4ed8;
    }
    QPushButton:pressed {
        background-color: #1e40af;
    }
    QLineEdit, QComboBox, QTextEdit {
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 10px;
        font-size: 14px;
        background-color: #ffffff;
        color: #0f172a;
    }
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 2px solid #3b82f6;
    }
"""

LOGIN_STYLES = """
    QMainWindow {
        background-color: #f8fafc;
    }
    QWidget#CentralWidget {
         background-color: #f8fafc;
    }
    QFrame#AuthBox {
        background-color: white;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
    }
    QLabel {
        font-family: 'Segoe UI', 'Inter', sans-serif;
        color: #0f172a;
    }
    QLineEdit {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 14px;
        font-size: 15px;
        background-color: #f8fafc;
        color: #0f172a;
    }
    QLineEdit:focus {
        border: 2px solid #2563eb;
        background-color: #ffffff;
    }
    QPushButton#PrimaryBtn {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 14px;
        font-size: 16px;
        font-weight: 700;
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }
    QPushButton#PrimaryBtn:hover {
        background-color: #1d4ed8;
    }
    QComboBox {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px;
        font-size: 15px;
        background-color: #f8fafc;
    }
    QPushButton#SecondaryBtn {
        background-color: transparent;
        color: #2563eb;
        border: none;
        font-size: 15px;
        font-weight: 600;
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }
    QPushButton#SecondaryBtn:hover {
        color: #1d4ed8;
        background-color: #eff6ff;
        border-radius: 6px;
    }
    QLabel#Title {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 8px;
    }
"""
