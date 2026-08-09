from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from src.blockchain import get_chain, verify_chain

class BlockchainViewerWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Health Record Integrity (Blockchain)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        header_layout.addWidget(title)

        verify_btn = QPushButton("Verify Chain Integrity")
        verify_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold;")
        verify_btn.clicked.connect(self.verify_chain_action)
        header_layout.addWidget(verify_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(header_layout)

        # Instructions
        desc = QLabel("All medical records are secured using cryptographic hashing to ensure no tampering occurs. Raw data is never stored here.")
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Index", "Timestamp", "Event", "Type", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        try:
            chain = get_chain()
            self.table.setRowCount(len(chain))
            
            # Reversing to show latest first
            for r, block in enumerate(reversed(chain)):
                self.table.setItem(r, 0, QTableWidgetItem(str(block.get('index', ''))))
                
                # Format timestamp
                ts = block.get('timestamp', '')
                if 'T' in ts:
                    ts = ts.replace('T', ' ')[:19]
                self.table.setItem(r, 1, QTableWidgetItem(ts))
                
                self.table.setItem(r, 2, QTableWidgetItem(str(block.get('event_type', ''))))
                self.table.setItem(r, 3, QTableWidgetItem(str(block.get('record_type', ''))))
                
                status_item = QTableWidgetItem("Secured 🔒")
                status_item.setForeground(Qt.GlobalColor.darkGreen)
                self.table.setItem(r, 4, status_item)
                
        except Exception as e:
            print(f"Error loading blockchain data: {e}")

    def verify_chain_action(self):
        is_valid = verify_chain()
        if is_valid:
            QMessageBox.information(self, "Chain Integrity", "✅ Blockchain integrity is fully intact. No records have been tampered with.")
        else:
            QMessageBox.critical(self, "Chain Integrity Compromised", "❌ WARNING: Blockchain integrity check failed! Records may have been tampered with.")
