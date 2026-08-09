from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt
from src.blockchain import get_chain, verify_chain

DEVELOPER_PASSWORD = "KetanDev"

class DeveloperBlockchainPanel(QDialog):
    """
    Developer-access blockchain audit panel.
    Shows all blockchain transactions from all users (patient, doctor, hospital, govt).
    Access requires a developer password.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 Developer — Blockchain Audit Panel")
        self.resize(1100, 700)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; }
            QLabel { color: #e2e8f0; }
            QTableWidget {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                gridline-color: #334155;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #1e3a5f;
                color: #93c5fd;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::alternate-row {
                background-color: #1e293b;
            }
            QLineEdit {
                background-color: #1e293b;
                color: white;
                border: 1px solid #334155;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #1d4ed8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("🔗 Swasthya Connect — Blockchain Audit Ledger")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #60a5fa;")
        layout.addWidget(title)

        subtitle = QLabel("All transactions are cryptographically hashed. No raw patient data is stored. For developer audit only.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(subtitle)

        # Stats bar
        self.stats_label = QLabel("Loading...")
        self.stats_label.setStyleSheet(
            "font-size: 13px; color: #34d399; background: #064e3b; "
            "padding: 10px; border-radius: 6px; font-family: monospace;"
        )
        layout.addWidget(self.stats_label)

        # Filter toolbar
        toolbar = QHBoxLayout()
        filter_label = QLabel("Filter by Event:")
        filter_label.setStyleSheet("color: #94a3b8;")
        self.event_filter = QComboBox()
        self.event_filter.setStyleSheet(
            "background-color: #1e293b; color: white; border: 1px solid #334155; padding: 6px; border-radius: 5px;"
        )
        self.event_filter.addItems([
            "All Events", "GENESIS", "MEDICAL_REPORT_UPLOAD", "PRESCRIPTION_CREATED",
            "TREATMENT_STATUS_UPDATED", "PRESCRIPTION_UPDATED", "CONSENT_GRANTED",
            "CONSENT_REVOKED", "RECORD_VIEWED", "DOCTOR_LICENSE_VERIFIED"
        ])
        self.event_filter.currentTextChanged.connect(self.load_data)

        verify_btn = QPushButton("✅ Verify Chain Integrity")
        verify_btn.setStyleSheet("background-color: #059669; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        verify_btn.clicked.connect(self.verify_chain_action)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)

        close_btn = QPushButton("✖ Close")
        close_btn.setStyleSheet("background-color: #7f1d1d; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        close_btn.clicked.connect(self.close)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self.event_filter)
        toolbar.addStretch()
        toolbar.addWidget(verify_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(close_btn)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "Timestamp", "Event Type", "Record Type",
            "Record Hash (SHA-256)", "Actor Hash (SHA-256)",
            "Patient Hash (SHA-256)", "Nonce"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        chain = get_chain()
        event_filter = self.event_filter.currentText() if hasattr(self, 'event_filter') else "All Events"

        filtered = [b for b in chain if event_filter == "All Events" or b.get('event_type') == event_filter]

        # Stats
        event_counts = {}
        for block in chain:
            et = block.get('event_type', 'UNKNOWN')
            event_counts[et] = event_counts.get(et, 0) + 1

        stats_parts = [f"Total blocks: {len(chain)}"]
        for et, cnt in event_counts.items():
            stats_parts.append(f"{et}: {cnt}")
        self.stats_label.setText("  |  ".join(stats_parts))

        # Show reversed (newest first)
        self.table.setRowCount(len(filtered))
        for r, block in enumerate(reversed(filtered)):
            index_item = QTableWidgetItem(str(block.get('index', '')))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 0, index_item)

            ts = str(block.get('timestamp', ''))
            if 'T' in ts:
                ts = ts.replace('T', ' ')[:19]
            self.table.setItem(r, 1, QTableWidgetItem(ts))

            event_item = QTableWidgetItem(str(block.get('event_type', '')))
            event_type = block.get('event_type', '')
            if event_type == 'GENESIS':
                event_item.setForeground(Qt.GlobalColor.gray)
            elif 'UPLOAD' in event_type or 'CREATED' in event_type:
                event_item.setForeground(Qt.GlobalColor.cyan)
            elif 'UPDATED' in event_type:
                event_item.setForeground(Qt.GlobalColor.yellow)
            elif 'GRANTED' in event_type or 'VERIFIED' in event_type:
                event_item.setForeground(Qt.GlobalColor.green)
            elif 'REVOKED' in event_type:
                event_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(r, 2, event_item)

            self.table.setItem(r, 3, QTableWidgetItem(str(block.get('record_type', ''))))
            self.table.setItem(r, 4, QTableWidgetItem(str(block.get('record_hash', ''))[:32] + '...'))
            self.table.setItem(r, 5, QTableWidgetItem(str(block.get('actor_hash', ''))[:32] + '...'))
            self.table.setItem(r, 6, QTableWidgetItem(str(block.get('patient_hash', ''))[:32] + '...'))
            self.table.setItem(r, 7, QTableWidgetItem(str(block.get('nonce', ''))))

    def verify_chain_action(self):
        is_valid = verify_chain()
        if is_valid:
            QMessageBox.information(
                self, "✅ Chain Valid",
                f"Blockchain integrity is INTACT.\nAll {len(get_chain())} blocks verified successfully.\nNo tampering detected."
            )
        else:
            QMessageBox.critical(
                self, "❌ Chain Compromised",
                "WARNING: Blockchain integrity check FAILED!\nOne or more blocks have been tampered with."
            )
