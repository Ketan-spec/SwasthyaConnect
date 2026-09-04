"""
SwasthyaConnect — Blockchain Health Record Integrity Viewer
============================================================
Patient-facing UI showing their tamper-proof health record chain.
Allows live chain verification with a single click.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from src.blockchain.chain import (
    get_patient_blocks, verify_patient_chain, verify_chain,
    get_chain_stats, BLOCK_GENESIS
)


# ── Background verification worker ────────────────────────────────────────────

class VerifyWorker(QThread):
    """Runs chain verification in a background thread."""
    finished = pyqtSignal(bool, list)

    def __init__(self, patient_id=None):
        super().__init__()
        self.patient_id = patient_id

    def run(self):
        if self.patient_id:
            ok, errors = verify_patient_chain(self.patient_id)
        else:
            ok, errors = verify_chain()
        self.finished.emit(ok, errors)


# ── Event type display names & colors ─────────────────────────────────────────

EVENT_META = {
    "GENESIS":              ("🌐 Chain Origin",         "#64748b"),
    "MEDICAL_RECORD_ADDED": ("📋 Medical Record",       "#0ea5e9"),
    "PRESCRIPTION_ADDED":   ("💊 Prescription",         "#8b5cf6"),
    "TREATMENT_UPDATED":    ("🏥 Treatment Update",      "#f59e0b"),
    "REFERRAL_CREATED":     ("↗️ Referral",              "#ef4444"),
    "AI_SUMMARY_SAVED":     ("🤖 AI Summary",           "#10b981"),
    "AUTH_EVENT":           ("🔐 Auth Event",           "#94a3b8"),
    "RESOURCE_UPDATED":     ("🏗️ Resource Update",      "#f97316"),
    "APPOINTMENT_BOOKED":   ("📅 Appointment",          "#06b6d4"),
    "GRANT_REQUEST_CREATED": ("🏦 Hospital Grant Request", "#f59e0b"),
    "GOVT_GRANT_DISBURSED": ("🏛️ Govt Fund Disbursal",  "#10b981"),
}


class BlockchainViewerWidget(QWidget):
    """
    Full-page widget showing the patient's health record blockchain.
    Embedded in the Patient Dashboard sidebar navigation.
    """

    def __init__(self, patient_id: int):
        super().__init__()
        self.patient_id = patient_id
        self._build_ui()
        self.load_data()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: #f0f4f8;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────────
        title = QLabel("🔗 Health Record Integrity")
        title.setStyleSheet(
            "font-size: 26px; font-weight: 800; color: #0f172a;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "Every medical record, prescription, and treatment update is cryptographically sealed "
            "using SHA-256 blockchain. Tampering with any record breaks the chain and is instantly detectable."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 5px;")
        layout.addWidget(subtitle)

        # ── Status Banner ─────────────────────────────────────────────────────
        self.status_banner = QFrame()
        self.status_banner.setMinimumHeight(70)
        self._set_status_banner("checking")
        banner_layout = QHBoxLayout(self.status_banner)

        self.status_icon = QLabel("⏳")
        self.status_icon.setStyleSheet("font-size: 28px;")
        self.status_text = QLabel("Verifying chain integrity...")
        self.status_text.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: white;"
        )
        self.status_detail = QLabel("")
        self.status_detail.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8);")

        left = QVBoxLayout()
        left.addWidget(self.status_text)
        left.addWidget(self.status_detail)

        self.verify_btn = QPushButton("🔄 Verify Now")
        self.verify_btn.setFixedWidth(140)
        self.verify_btn.setStyleSheet(
            "background: rgba(255,255,255,0.25); color: white; border: 2px solid white; "
            "border-radius: 8px; padding: 8px 15px; font-weight: bold; font-size: 13px;"
        )
        self.verify_btn.clicked.connect(self.run_verification)

        banner_layout.addWidget(self.status_icon)
        banner_layout.addLayout(left)
        banner_layout.addStretch()
        banner_layout.addWidget(self.verify_btn)
        layout.addWidget(self.status_banner)

        # ── Stats Row ─────────────────────────────────────────────────────────
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(15)
        layout.addLayout(self.stats_layout)

        # ── Chain Table ───────────────────────────────────────────────────────
        chain_title = QLabel("📦 Your Health Record Blocks")
        chain_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1e293b; margin-top: 5px;"
        )
        layout.addWidget(chain_title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Block #", "Timestamp", "Event Type", "Details", "Block Hash", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #0f766e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:alternate { background-color: #f8fafc; }
            QTableWidget::item:selected { background-color: #e0f2fe; color: #0f172a; }
        """)
        layout.addWidget(self.table)

        # ── What This Means Section ────────────────────────────────────────────
        explain_card = QFrame()
        explain_card.setStyleSheet(
            "QFrame { background: white; border: 1px solid #e2e8f0; border-radius: 10px; }"
        )
        explain_layout = QVBoxLayout(explain_card)
        explain_layout.setContentsMargins(20, 15, 20, 15)

        exp_title = QLabel("🛡️ How Your Data Is Protected")
        exp_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #0f766e;")
        explain_layout.addWidget(exp_title)

        explain_points = [
            "Every health event (report upload, prescription, treatment) creates a tamper-proof block.",
            "Each block contains a SHA-256 hash of your data — changing even one character invalidates the block.",
            "Blocks are chained: each block stores the previous block's hash, creating an unbreakable sequence.",
            "If anyone modifies a past record, the chain verification will instantly detect it.",
            "Your data hash is stored — not your raw data — preserving privacy while guaranteeing integrity.",
        ]
        for pt in explain_points:
            lbl = QLabel(f"  ✅  {pt}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 13px; color: #475569; padding: 3px 0;")
            explain_layout.addWidget(lbl)

        layout.addWidget(explain_card)
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── Status banner styling ─────────────────────────────────────────────────

    def _set_status_banner(self, state: str):
        if state == "valid":
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);"
        elif state == "invalid":
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #ef4444);"
        else:  # checking
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e40af, stop:1 #3b82f6);"
        self.status_banner.setStyleSheet(
            f"QFrame {{ {style} border-radius: 12px; padding: 10px; }}"
        )

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_data(self):
        """Loads patient blockchain blocks into the table."""
        blocks = get_patient_blocks(self.patient_id, limit=200)

        # ── Stats cards ───────────────────────────────────────────────────────
        # Clear existing stats
        for i in reversed(range(self.stats_layout.count())):
            w = self.stats_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        event_counts = {}
        for b in blocks:
            rt = b.get("record_type", "")
            event_counts[rt] = event_counts.get(rt, 0) + 1

        stat_items = [
            ("Total Blocks", str(len(blocks)), "#0ea5e9"),
            ("Medical Records", str(event_counts.get("MEDICAL_RECORD_ADDED", 0)), "#8b5cf6"),
            ("Prescriptions", str(event_counts.get("PRESCRIPTION_ADDED", 0)), "#10b981"),
            ("Treatments", str(event_counts.get("TREATMENT_UPDATED", 0)), "#f59e0b"),
        ]
        for label, value, color in stat_items:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: white; border-radius: 8px; "
                f"border-left: 4px solid {color}; border: 1px solid #e2e8f0; }}"
            )
            card.setMinimumHeight(70)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            vl = QLabel(value)
            vl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {color};")
            tl = QLabel(label)
            tl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: bold;")
            cl.addWidget(vl)
            cl.addWidget(tl)
            self.stats_layout.addWidget(card)

        # ── Populate table ────────────────────────────────────────────────────
        self.table.setRowCount(len(blocks))
        for r, block in enumerate(blocks):
            rt = block.get("record_type", "")
            display_name, color = EVENT_META.get(rt, (rt, "#64748b"))

            # Block #
            idx_item = QTableWidgetItem(str(block.get("block_index", "")))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            idx_item.setFont(QFont("Courier", 10, QFont.Weight.Bold))
            self.table.setItem(r, 0, idx_item)

            # Timestamp (date only for brevity)
            ts = str(block.get("timestamp", ""))[:19]
            self.table.setItem(r, 1, QTableWidgetItem(ts))

            # Event Type (colored)
            type_item = QTableWidgetItem(display_name)
            type_item.setForeground(QColor(color))
            type_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            self.table.setItem(r, 2, type_item)

            # Extra details
            extra = block.get("extra_data") or "—"
            self.table.setItem(r, 3, QTableWidgetItem(str(extra)))

            # Block hash (truncated)
            bh = block.get("block_hash", "")
            hash_item = QTableWidgetItem(bh[:12] + "..." if bh else "—")
            hash_item.setFont(QFont("Courier", 9))
            hash_item.setForeground(QColor("#64748b"))
            hash_item.setToolTip(bh)  # full hash on hover
            self.table.setItem(r, 4, hash_item)

            # Verified status
            verified = block.get("verified", 1)
            status_item = QTableWidgetItem("✅ Intact" if verified else "❌ Error")
            status_item.setForeground(
                QColor("#059669") if verified else QColor("#dc2626")
            )
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 5, status_item)

        # Auto-run verification after loading
        self.run_verification()

    # ── Verification ──────────────────────────────────────────────────────────

    def run_verification(self):
        """Launches background verification thread."""
        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("Verifying...")
        self.status_text.setText("Verifying chain integrity...")
        self.status_icon.setText("⏳")
        self._set_status_banner("checking")

        self.worker = VerifyWorker(patient_id=self.patient_id)
        self.worker.finished.connect(self._on_verification_done)
        self.worker.start()

    def _on_verification_done(self, is_valid: bool, errors: list):
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("🔄 Verify Now")

        blocks = get_patient_blocks(self.patient_id, limit=1)
        block_count = len(get_patient_blocks(self.patient_id, limit=200))

        if is_valid:
            self._set_status_banner("valid")
            self.status_icon.setText("✅")
            self.status_text.setText("Chain Integrity: VERIFIED")
            self.status_detail.setText(
                f"{block_count} health record blocks — all hashes intact, no tampering detected."
            )
        else:
            self._set_status_banner("invalid")
            self.status_icon.setText("🚨")
            self.status_text.setText("Chain Integrity: COMPROMISED")
            self.status_detail.setText(
                f"{len(errors)} integrity error(s) detected. "
                f"Contact system administrator immediately."
            )
