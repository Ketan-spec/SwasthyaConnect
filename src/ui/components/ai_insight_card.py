from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class AIInsightCard(QFrame):
    def __init__(self, main_text, category="Insight"):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #7c3aed);
                border-radius: 12px;
            }
            QLabel {
                color: white;
            }
        """)
        self.setFixedHeight(100)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        icon_label = QLabel("✨ Swasthya IQ")
        icon_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        cat_label = QLabel(category)
        cat_label.setStyleSheet("background-color: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; font-size: 10px;")
        
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(cat_label)
        layout.addLayout(header_layout)
        
        # Content
        content_label = QLabel(main_text)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("font-size: 13px; font-weight: 500; margin-top: 5px;")
        layout.addWidget(content_label)
