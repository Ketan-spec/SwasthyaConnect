"""
SwasthyaConnect — UTM Virtual Machine Hypervisor Manager (Pseudo VM Interface)
================================================================================
Mimics the famous macOS UTM / Parallels Virtual Machine Manager interface.
Allows demonstration of SwasthyaConnect as a cross-platform, air-gapped edge
application running inside a virtualized Android 14 / Linux appliance on constrained
specifications (4 Cores, 4GB RAM).
"""

import sys
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QProgressBar, QTextEdit, QScrollArea, QDialog, QFormLayout,
    QSpinBox, QComboBox, QLineEdit, QStackedWidget, QSplitter,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QBrush, QPen


# Realistic Virtual Machine Profiles
DEFAULT_VM_PROFILES = [
    {
        "id": "android14",
        "name": "Android 14 (ARM64)",
        "subtitle": "Healthcare Mobile Kiosk Node",
        "icon": "🤖",
        "badge": "Android ART 14",
        "status": "Ready",
        "arch": "Apple Silicon ARM64 (hv_vm)",
        "cpu_cores": 4,
        "ram_mb": 4096,
        "storage_gb": 64,
        "display": "VirtIO-GPU (Metal 3, 1200x800 @ 60Hz)",
        "network": "VirtIO-Net (Bridged 192.168.64.4 Air-gapped)",
        "runtime": "Android Runtime (ART) / Python Mobile Edge",
        "ai_constraint": "Quantized CPU Offline Inference (NLLB-200 + Llama3)",
        "kernel": "Linux 6.6.21-android14-arm64 (android-build@google.com)"
    },
    {
        "id": "ubuntu22",
        "name": "Ubuntu 22.04 LTS",
        "subtitle": "SwasthyaEdge Laptop Client",
        "icon": "💻",
        "badge": "Linux 6.6 Edge",
        "status": "Ready",
        "arch": "x86_64 / ARM64 Universal",
        "cpu_cores": 4,
        "ram_mb": 6144,
        "storage_gb": 128,
        "display": "Wayland VirtIO-GPU (1440x900 @ 60Hz)",
        "network": "Shared NAT (192.168.64.12)",
        "runtime": "PySide6 / Ubuntu Desktop Client",
        "ai_constraint": "Constrained Laptop Edge CPU",
        "kernel": "Linux 6.6.0-42-generic #42-Ubuntu SMP"
    },
    {
        "id": "hospital_server",
        "name": "SwasthyaOS Hospital Node",
        "subtitle": "Air-Gapped Clinic Server Appliance",
        "icon": "🏥",
        "badge": "Enterprise Appliance",
        "status": "Ready",
        "arch": "x86_64 QEMU TCG",
        "cpu_cores": 8,
        "ram_mb": 8192,
        "storage_gb": 256,
        "display": "Headless / Remote VirtIO (1920x1080)",
        "network": "Isolated Hospital Intranet (10.0.4.1)",
        "runtime": "Swasthya Enterprise Core Server",
        "ai_constraint": "Local Dedicated Neural Server Node",
        "kernel": "Linux 6.1.0-swasthya-enterprise-amd64"
    }
]

# Global state of active VM profile
ACTIVE_VM_PROFILE = DEFAULT_VM_PROFILES[0].copy()


class VMSpecsDialog(QDialog):
    """Configuration Modal allowing user to tweak simulated hardware specs."""
    specs_updated = pyqtSignal(dict)

    def __init__(self, current_profile, parent=None):
        super().__init__(parent)
        self.profile = current_profile.copy()
        self.setWindowTitle(f"Hardware Configuration — {self.profile['name']}")
        self.resize(520, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e24;
                color: #f3f4f6;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
            }
            QComboBox, QSpinBox, QLineEdit {
                background-color: #2b2b36;
                border: 1px solid #3e3e4e;
                border-radius: 6px;
                padding: 6px 10px;
                color: white;
                font-size: 13px;
            }
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0062cc;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(f"⚙️ Virtual Hardware Specs: {self.profile['name']}")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #60a5fa;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # CPU Cores
        self.cpu_spin = QSpinBox()
        self.cpu_spin.setRange(1, 16)
        self.cpu_spin.setValue(self.profile["cpu_cores"])
        form.addRow("Virtual CPU Cores (vCPUs):", self.cpu_spin)

        # RAM
        self.ram_combo = QComboBox()
        self.ram_combo.addItems(["2048 MB (2 GB - Ultra-Low Spec)", "4096 MB (4 GB - Standard Mobile Kiosk)", "6144 MB (6 GB)", "8192 MB (8 GB)"])
        for i in range(self.ram_combo.count()):
            if str(self.profile["ram_mb"]) in self.ram_combo.itemText(i):
                self.ram_combo.setCurrentIndex(i)
                break
        form.addRow("Allocated Memory (RAM):", self.ram_combo)

        # Architecture
        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["Apple Silicon ARM64 (hv_vm Native)", "x86_64 (QEMU Emulation)", "ARMv8-A Android Kiosk"])
        form.addRow("Hypervisor Engine / Arch:", self.arch_combo)

        # Disk
        self.disk_combo = QComboBox()
        self.disk_combo.addItems(["32 GB NVMe", "64 GB NVMe", "128 GB NVMe", "256 GB NVMe"])
        form.addRow("Virtual Disk Size:", self.disk_combo)

        # GPU
        self.gpu_combo = QComboBox()
        self.gpu_combo.addItems(["VirtIO-GPU (Metal 3 Accelerated)", "VirtIO-RAMFB (Software Fallback)"])
        form.addRow("Display Controller:", self.gpu_combo)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #3e3e4e; color: white;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Specifications")
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def save(self):
        self.profile["cpu_cores"] = self.cpu_spin.value()
        ram_text = self.ram_combo.currentText()
        if "2048" in ram_text:
            self.profile["ram_mb"] = 2048
        elif "4096" in ram_text:
            self.profile["ram_mb"] = 4096
        elif "6144" in ram_text:
            self.profile["ram_mb"] = 6144
        elif "8192" in ram_text:
            self.profile["ram_mb"] = 8192

        self.profile["arch"] = self.arch_combo.currentText()
        self.specs_updated.emit(self.profile)
        self.accept()


class VMLauncherWindow(QWidget):
    """
    UTM-style Virtual Machine Manager window.
    Acts as the entrypoint explaining cross-platform execution & local AI inference constraints.
    """
    def __init__(self, on_boot_complete_callback=None):
        super().__init__()
        self.on_boot_complete_callback = on_boot_complete_callback
        self.current_profile = DEFAULT_VM_PROFILES[0].copy()
        global ACTIVE_VM_PROFILE
        ACTIVE_VM_PROFILE = self.current_profile

        self.boot_timer = QTimer(self)
        self.boot_timer.timeout.connect(self._on_boot_step)
        self.boot_step = 0
        self.boot_lines = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("UTM — Virtual Machine Manager (macOS Edition)")
        self.resize(1120, 740)
        self.setMinimumSize(920, 600)
        
        # Authentic macOS dark metallic theme
        self.setStyleSheet("""
            QWidget#VMRoot {
                background-color: #1a1a20;
                color: #e5e7eb;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', sans-serif;
            }
            QFrame#Sidebar {
                background-color: #141419;
                border-right: 1px solid #282834;
            }
            QFrame#MainContent {
                background-color: #1a1a20;
            }
            QFrame#CardBox {
                background-color: #22222c;
                border-radius: 12px;
                border: 1px solid #2e2e3c;
            }
            QFrame#PreviewScreen {
                background-color: #0b0f19;
                border-radius: 12px;
                border: 2px solid #334155;
            }
            QPushButton#PrimaryLaunchBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007aff, stop:1 #0056b3);
                color: white;
                font-size: 15px;
                font-weight: 700;
                border-radius: 10px;
                padding: 12px 28px;
                border: 1px solid #3b82f6;
            }
            QPushButton#PrimaryLaunchBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a8cff, stop:1 #0066cc);
            }
            QPushButton#SecondaryBtn {
                background-color: #2b2b38;
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 14px;
                border: 1px solid #3e3e50;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #38384a;
                color: white;
            }
            QTextEdit#TerminalLogs {
                background-color: #0d1117;
                color: #38bdf8;
                font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px;
            }
            QLineEdit#SearchVM {
                background-color: #22222c;
                border: 1px solid #333344;
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-size: 12px;
            }
        """)
        self.setObjectName("VMRoot")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. Top macOS Window Toolbar ──
        toolbar = QFrame()
        toolbar.setFixedHeight(54)
        toolbar.setStyleSheet("background-color: #141419; border-bottom: 1px solid #282834;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(18, 0, 18, 0)

        # Traffic Lights (macOS buttons)
        traffic_lights = QHBoxLayout()
        traffic_lights.setSpacing(8)
        for color, action in [("#ff5f56", self.close), ("#ffbd2e", self.showMinimized), ("#27c93f", self._toggle_max)]:
            dot = QPushButton()
            dot.setFixedSize(13, 13)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 6px; border: none;")
            dot.clicked.connect(action)
            traffic_lights.addWidget(dot)
        tb_layout.addLayout(traffic_lights)

        tb_layout.addSpacing(20)

        # UTM App Icon & Title
        title_box = QHBoxLayout()
        utm_icon = QLabel("⚡")
        utm_icon.setStyleSheet("font-size: 18px;")
        app_name = QLabel("UTM Virtual Machine Manager")
        app_name.setStyleSheet("font-size: 14px; font-weight: 700; color: #f1f5f9;")
        ver_badge = QLabel("macOS HV_VM v4.5.3")
        ver_badge.setStyleSheet("font-size: 10px; color: #94a3b8; background: #22222c; padding: 2px 6px; border-radius: 4px;")
        title_box.addWidget(utm_icon)
        title_box.addWidget(app_name)
        title_box.addWidget(ver_badge)
        tb_layout.addLayout(title_box)

        tb_layout.addStretch()

        # Toolbar Actions
        new_vm_btn = QPushButton("➕ New VM")
        new_vm_btn.setObjectName("SecondaryBtn")
        new_vm_btn.clicked.connect(self._create_new_vm)
        tb_layout.addWidget(new_vm_btn)

        edit_btn = QPushButton("⚙️ Edit Specs")
        edit_btn.setObjectName("SecondaryBtn")
        edit_btn.clicked.connect(self._edit_specs)
        tb_layout.addWidget(edit_btn)

        quick_boot_btn = QPushButton("🚀 Direct Boot")
        quick_boot_btn.setObjectName("SecondaryBtn")
        quick_boot_btn.setToolTip("Skip boot sequence and launch SwasthyaConnect directly")
        quick_boot_btn.clicked.connect(self._direct_launch)
        tb_layout.addWidget(quick_boot_btn)

        main_layout.addWidget(toolbar)

        # ── 2. Split Body (Sidebar + Main Panel) ──
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(310)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 16, 14, 16)
        sb_layout.setSpacing(12)

        search_input = QLineEdit()
        search_input.setObjectName("SearchVM")
        search_input.setPlaceholderText("🔍 Search Virtual Machines...")
        sb_layout.addWidget(search_input)

        sb_header = QLabel("MY VIRTUAL MACHINES")
        sb_header.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; margin-top: 6px; letter-spacing: 0.5px;")
        sb_layout.addWidget(sb_header)

        # VM Items in Sidebar
        self.vm_buttons = {}
        for prof in DEFAULT_VM_PROFILES:
            btn = self._build_vm_card(prof)
            sb_layout.addWidget(btn)
            self.vm_buttons[prof["id"]] = btn

        sb_layout.addStretch()

        # Architecture & Hypervisor Info Pill
        hw_pill = QFrame()
        hw_pill.setStyleSheet("background-color: #1e1e26; border: 1px solid #2e2e3e; border-radius: 8px; padding: 10px;")
        pill_layout = QVBoxLayout(hw_pill)
        pill_layout.setContentsMargins(8, 8, 8, 8)
        pill_layout.setSpacing(4)
        h_title = QLabel("🖥️ Host Virtualization")
        h_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #38bdf8;")
        h_desc = QLabel("Apple Virtualization Framework (hv_vm)\nQEMU 8.2 • Low-latency Host Pass-through")
        h_desc.setStyleSheet("font-size: 10px; color: #94a3b8;")
        pill_layout.addWidget(h_title)
        pill_layout.addWidget(h_desc)
        sb_layout.addWidget(hw_pill)

        body_layout.addWidget(sidebar)

        # Main Content
        self.main_content = QFrame()
        self.main_content.setObjectName("MainContent")
        mc_layout = QVBoxLayout(self.main_content)
        mc_layout.setContentsMargins(28, 24, 28, 24)
        mc_layout.setSpacing(20)

        # ── Header Details of Selected VM ──
        vm_header = QHBoxLayout()
        self.vm_icon_lbl = QLabel(self.current_profile["icon"])
        self.vm_icon_lbl.setStyleSheet("font-size: 38px; padding: 8px; background: #232330; border-radius: 12px; border: 1px solid #333346;")
        
        vm_title_box = QVBoxLayout()
        self.vm_name_lbl = QLabel(self.current_profile["name"])
        self.vm_name_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: white;")
        self.vm_sub_lbl = QLabel(f"Sub-system: {self.current_profile['subtitle']} • {self.current_profile['arch']}")
        self.vm_sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        vm_title_box.addWidget(self.vm_name_lbl)
        vm_title_box.addWidget(self.vm_sub_lbl)

        vm_header.addWidget(self.vm_icon_lbl)
        vm_header.addSpacing(14)
        vm_header.addLayout(vm_title_box)
        vm_header.addStretch()

        # Status Tag
        self.status_tag = QLabel("🟢 Standby • Ready to Boot")
        self.status_tag.setStyleSheet("color: #34d399; background: rgba(16, 185, 129, 0.12); border: 1px solid #059669; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px;")
        vm_header.addWidget(self.status_tag)

        mc_layout.addLayout(vm_header)

        # ── Stacked Central Display: Specs View vs Boot Terminal View ──
        self.display_stack = QStackedWidget()

        # Page 0: Specifications & Screen Preview
        self.specs_page = self._build_specs_page()
        self.display_stack.addWidget(self.specs_page)

        # Page 1: Live Boot Sequence Console
        self.terminal_page = self._build_terminal_page()
        self.display_stack.addWidget(self.terminal_page)

        mc_layout.addWidget(self.display_stack, 1)

        # ── Footer Action Area ──
        footer = QHBoxLayout()
        footer.setSpacing(14)

        info_lbl = QLabel("💡 <b>Cross-Platform Edge Note:</b> SwasthyaConnect is virtualized in an emulated guest environment with local constrained RAM/vCPUs to verify offline stability.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        footer.addWidget(info_lbl, 1)

        self.start_vm_btn = QPushButton(f"▶ Start Virtual Machine")
        self.start_vm_btn.setObjectName("PrimaryLaunchBtn")
        self.start_vm_btn.clicked.connect(self._start_boot_sequence)
        footer.addWidget(self.start_vm_btn)

        mc_layout.addLayout(footer)

        body_layout.addWidget(self.main_content, 1)
        main_layout.addLayout(body_layout)

    def _toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _build_vm_card(self, profile):
        """Constructs a clickable VM entry for the sidebar."""
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 10px;
                text-align: left;
                padding: 10px 12px;
            }
            QPushButton:hover {
                background-color: #1e1e28;
                border: 1px solid #2e2e40;
            }
            QPushButton:checked {
                background-color: #232332;
                border: 1px solid #007aff;
            }
        """)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        icon = QLabel(profile["icon"])
        icon.setStyleSheet("font-size: 22px;")
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        name = QLabel(profile["name"])
        name.setStyleSheet("font-size: 13px; font-weight: 700; color: white;")
        meta = QLabel(f"{profile['cpu_cores']} vCPU • {profile['ram_mb']}MB RAM")
        meta.setStyleSheet("font-size: 11px; color: #94a3b8;")
        badge = QLabel(profile["badge"])
        badge.setStyleSheet("font-size: 9px; color: #38bdf8; font-weight: bold;")
        text_layout.addWidget(name)
        text_layout.addWidget(meta)
        text_layout.addWidget(badge)
        layout.addLayout(text_layout)

        if profile["id"] == self.current_profile["id"]:
            btn.setChecked(True)

        btn.clicked.connect(lambda: self._select_profile(profile))
        return btn

    def _select_profile(self, profile):
        self.current_profile = profile.copy()
        global ACTIVE_VM_PROFILE
        ACTIVE_VM_PROFILE = self.current_profile

        for pid, b in self.vm_buttons.items():
            b.setChecked(pid == profile["id"])

        self.vm_icon_lbl.setText(profile["icon"])
        self.vm_name_lbl.setText(profile["name"])
        self.vm_sub_lbl.setText(f"Sub-system: {profile['subtitle']} • {profile['arch']}")
        self.start_vm_btn.setText(f"▶ Start Virtual Machine")

        # Refresh specs view
        self._refresh_specs_labels()

    def _build_specs_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Left Column: Emulated Screen Preview
        preview_box = QFrame()
        preview_box.setObjectName("PreviewScreen")
        preview_box.setMinimumWidth(360)
        pv_layout = QVBoxLayout(preview_box)
        pv_layout.setContentsMargins(18, 18, 18, 18)
        pv_layout.setSpacing(12)

        pv_top = QHBoxLayout()
        os_badge = QLabel(f"🖥️ Virtual Display (1200x800 @ 60Hz)")
        os_badge.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        fps_lbl = QLabel("⚡ 60 FPS • Metal 3")
        fps_lbl.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
        pv_top.addWidget(os_badge)
        pv_top.addStretch()
        pv_top.addWidget(fps_lbl)
        pv_layout.addLayout(pv_top)

        pv_layout.addStretch()

        center_logo_box = QVBoxLayout()
        center_logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_icon = QLabel("🏥")
        c_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_icon.setStyleSheet("font-size: 52px;")
        c_title = QLabel("SwasthyaConnect")
        c_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_title.setStyleSheet("font-size: 20px; font-weight: 800; color: white;")
        c_sub = QLabel("Universal Cross-Platform Edge Runtime\nGuest OS Machine Ready to Boot")
        c_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_sub.setStyleSheet("font-size: 12px; color: #94a3b8;")
        center_logo_box.addWidget(c_icon)
        center_logo_box.addWidget(c_title)
        center_logo_box.addWidget(c_sub)
        pv_layout.addLayout(center_logo_box)

        pv_layout.addStretch()

        pv_bottom = QHBoxLayout()
        self.pv_status_lbl = QLabel("Guest OS: Standby (Press Start to Boot)")
        self.pv_status_lbl.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 600;")
        pv_bottom.addWidget(self.pv_status_lbl)
        pv_layout.addLayout(pv_bottom)

        layout.addWidget(preview_box, 1)

        # Right Column: Hardware & Spec Inspector
        specs_card = QFrame()
        specs_card.setObjectName("CardBox")
        sc_layout = QVBoxLayout(specs_card)
        sc_layout.setContentsMargins(20, 20, 20, 20)
        sc_layout.setSpacing(14)

        header_lbl = QLabel("📋 Virtual Hardware Allocation")
        header_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        sc_layout.addWidget(header_lbl)

        # Table-style entries
        self.spec_entries = {}
        specs_items = [
            ("🧠 vCPU Architecture", "arch"),
            ("⚡ Allocated Memory", "ram"),
            ("💾 Virtual Storage", "storage"),
            ("🖥️ Graphics Acceleration", "display"),
            ("🌐 Virtual Network", "network"),
            ("📱 Platform Environment", "runtime"),
            ("🤖 Local AI Constraint", "ai_constraint")
        ]

        for title, key in specs_items:
            row = QHBoxLayout()
            lbl = QLabel(title)
            lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
            val = QLabel("")
            val.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            val.setWordWrap(True)
            self.spec_entries[key] = val
            row.addWidget(lbl)
            row.addSpacing(10)
            row.addWidget(val, 1)
            sc_layout.addLayout(row)

        sc_layout.addStretch()

        config_btn = QPushButton("⚙️ Adjust Hardware Specs (vCPU / RAM)")
        config_btn.setObjectName("SecondaryBtn")
        config_btn.clicked.connect(self._edit_specs)
        sc_layout.addWidget(config_btn)

        layout.addWidget(specs_card, 1)

        self._refresh_specs_labels()
        return page

    def _refresh_specs_labels(self):
        p = self.current_profile
        if "arch" in self.spec_entries:
            self.spec_entries["arch"].setText(f"{p['cpu_cores']} Cores ({p['arch']})")
            self.spec_entries["ram"].setText(f"{p['ram_mb']} MB LPDDR5 (zRAM Swappable)")
            self.spec_entries["storage"].setText(f"{p['storage_gb']} GB NVMe (ext4 sparse image)")
            self.spec_entries["display"].setText(p["display"])
            self.spec_entries["network"].setText(p["network"])
            self.spec_entries["runtime"].setText(p["runtime"])
            self.spec_entries["ai_constraint"].setText(p["ai_constraint"])

    def _build_terminal_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        term_title = QLabel("💻 UTM Guest OS Boot Terminal & Hypervisor Kernel Logs")
        term_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
        self.kernel_tag = QLabel("hv_vm: Active")
        self.kernel_tag.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: bold;")
        top_row.addWidget(term_title)
        top_row.addStretch()
        top_row.addWidget(self.kernel_tag)
        layout.addLayout(top_row)

        self.terminal = QTextEdit()
        self.terminal.setObjectName("TerminalLogs")
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal, 1)

        self.boot_progress = QProgressBar()
        self.boot_progress.setStyleSheet("""
            QProgressBar {
                background-color: #22222c;
                border: 1px solid #3e3e50;
                border-radius: 6px;
                height: 12px;
                text-align: center;
                color: white;
                font-size: 10px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007aff, stop:1 #10b981);
                border-radius: 5px;
            }
        """)
        self.boot_progress.setValue(0)
        layout.addWidget(self.boot_progress)

        self.boot_status_lbl = QLabel("Initializing Apple Silicon Hypervisor...")
        self.boot_status_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")
        layout.addWidget(self.boot_status_lbl)

        return page

    def _start_boot_sequence(self):
        """Switches to the live terminal and streams realistic kernel boot logs."""
        self.display_stack.setCurrentIndex(1)
        self.terminal.clear()
        self.boot_progress.setValue(0)
        self.start_vm_btn.setEnabled(False)
        self.status_tag.setText("🟡 Booting Guest OS...")
        self.status_tag.setStyleSheet("color: #fbbf24; background: rgba(245, 158, 11, 0.12); border: 1px solid #d97706; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px;")

        p = self.current_profile
        self.boot_lines = [
            f"[  0.000000] Linux version {p['kernel']}",
            f"[  0.021400] QEMU 8.2.0 Virtual Machine Initialized (hv_vm accelerator active)",
            f"[  0.048200] CPU: {p['cpu_cores']} vCPUs online (Apple Silicon ARM64 pass-through)",
            f"[  0.104230] Memory: {p['ram_mb']}MB LPDDR5 Allocated, VirtIO Block device /dev/vda1 mounted",
            f"[  0.228940] VirtIO-GPU 3D Acceleration: Metal 3 shader backend initialized",
            f"[  0.340120] VirtIO-Net: Interface eth0 UP at 192.168.64.4 (Air-gapped local subnet)",
            f"[  0.490800] Starting Cross-Platform Container: {p['runtime']}",
            f"[  0.640100] Loading local offline AI weights into RAM ({p['ai_constraint']})...",
            f"[  0.780400] SHA-256 Blockchain Health Ledger Integrity: Verified 18 Blocks Intact 🟢",
            f"[  0.920000] Launching SwasthyaConnect Display Surface (1200x800 @ 60Hz)...",
            f"[  1.000000] Guest OS Boot Complete! Handing off execution to SwasthyaConnect..."
        ]
        self.boot_step = 0
        self.boot_timer.start(180)  # Stream line every 180ms for an ultra-smooth, fast ~2.0s boot sequence

    def _on_boot_step(self):
        if self.boot_step < len(self.boot_lines):
            line = self.boot_lines[self.boot_step]
            self.terminal.append(f"<span style='color: #38bdf8;'>{line}</span>")
            pct = int(((self.boot_step + 1) / len(self.boot_lines)) * 100)
            self.boot_progress.setValue(pct)
            self.boot_status_lbl.setText(f"Booting {self.current_profile['name']} ({pct}%)...")
            self.boot_step += 1
        else:
            self.boot_timer.stop()
            self.status_tag.setText("🟢 VM Running (Connected)")
            self.status_tag.setStyleSheet("color: #34d399; background: rgba(16, 185, 129, 0.12); border: 1px solid #059669; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px;")
            self.boot_status_lbl.setText("Virtual Machine Running! Launching SwasthyaConnect GUI...")
            # Trigger transition
            QTimer.singleShot(400, self._launch_app)

    def _launch_app(self):
        """Closes the launcher and hands off to the main SwasthyaConnect application."""
        self.hide()
        if self.on_boot_complete_callback:
            self.on_boot_complete_callback()

    def _direct_launch(self):
        """Bypasses boot animation for instant demonstration."""
        self._launch_app()

    def _edit_specs(self):
        dlg = VMSpecsDialog(self.current_profile, self)
        dlg.specs_updated.connect(self._on_specs_updated)
        dlg.exec()

    def _on_specs_updated(self, updated_profile):
        self.current_profile = updated_profile
        global ACTIVE_VM_PROFILE
        ACTIVE_VM_PROFILE = self.current_profile
        self._refresh_specs_labels()

    def _create_new_vm(self):
        dlg = VMSpecsDialog(self.current_profile, self)
        dlg.setWindowTitle("Create New Virtual Machine Profile")
        dlg.specs_updated.connect(self._on_specs_updated)
        dlg.exec()
