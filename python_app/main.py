import sys
import os
import hashlib
import json
import time
from datetime import datetime, date
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QDialog, QLineEdit, QMessageBox, QFrame,
    QGridLayout, QStatusBar, QSpacerItem, QSizePolicy, QGroupBox, QFormLayout
)
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from PySide6.QtCore import Qt, QTimer, Slot

# Import configurations & client
import firebase_config
import firebase_client as fc
import utils
import billing_engine as be

CREDENTIALS_FILE = "admin_credentials.json"

def _load_fonts(app: QApplication) -> None:
    """Load JetBrains Mono from bundled TTF files in assets/fonts/."""
    for weight in ["Regular", "Bold", "Medium", "Italic", "BoldItalic"]:
        path = f"assets/fonts/JetBrainsMono-{weight}.ttf"
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)
    app.setFont(QFont("JetBrains Mono", 10))

def _load_stylesheet(app: QApplication) -> None:
    """Load QSS from assets/style.qss."""
    try:
        with open("assets/style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Authenticate")
        self.setFixedSize(400, 350); self.failed_attempts = 0; self.lockout_until = 0; self.admin_name = ""
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("login_dialog")
        layout = QVBoxLayout(self); layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("RAJASTHAN JAL BOARD"); title.setAlignment(Qt.AlignCenter); title.setStyleSheet("font-size: 18px; font-weight: bold")
        layout.addWidget(title)

        self.u_input = QLineEdit(); self.u_input.setPlaceholderText("Username")
        self.p_input = QLineEdit(); self.p_input.setPlaceholderText("Password"); self.p_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.u_input); layout.addWidget(self.p_input)

        self.msg_lbl = QLabel(""); self.msg_lbl.setStyleSheet("color: red"); layout.addWidget(self.msg_lbl)

        btn = QPushButton("AUTHENTICATE"); btn.clicked.connect(self.attempt_login); layout.addWidget(btn)

        self.timer = QTimer(); self.timer.timeout.connect(self.update_lockout); self.timer.start(1000)

    def update_lockout(self):
        if self.lockout_until > time.time():
            self.msg_lbl.setText(f"Lockout: {int(self.lockout_until - time.time())}s remaining")
        elif self.failed_attempts >= 5: self.msg_lbl.setText("")

    def attempt_login(self):
        if time.time() < self.lockout_until: return
        u, p = self.u_input.text().strip(), self.p_input.text()
        if not os.path.exists(CREDENTIALS_FILE): return self.show_setup()
        with open(CREDENTIALS_FILE, "r") as f: creds = json.load(f)
        if u == creds["username"] and hashlib.sha256(p.encode()).hexdigest() == creds["password_hash"]:
            self.admin_name = creds["name"]; self.accept()
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= 5: self.lockout_until = time.time() + 30
            self.msg_lbl.setText(f"Invalid. Attempt {self.failed_attempts}/5")

    def show_setup(self):
        dlg = QDialog(self); dlg.setWindowTitle("Setup Admin"); lay = QVBoxLayout(dlg)
        f = QFormLayout(); name = QLineEdit("Admin"); user = QLineEdit("admin"); pwd = QLineEdit(); pwd.setEchoMode(QLineEdit.Password)
        f.addRow("Name:", name); f.addRow("User:", user); f.addRow("Pass:", pwd); lay.addLayout(f)
        btn = QPushButton("Create"); lay.addWidget(btn)
        def save():
            if not name.text() or not user.text() or not pwd.text(): return
            with open(CREDENTIALS_FILE, "w") as f_out: json.dump({"name": name.text(), "username": user.text(), "password_hash": hashlib.sha256(pwd.text().encode()).hexdigest()}, f_out)
            QMessageBox.information(dlg, "Success", "Account created."); dlg.accept()
        btn.clicked.connect(save); dlg.exec()

class MainWindow(QMainWindow):
    def __init__(self, fc, utils, be, admin_ctx):
        super().__init__()
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.setWindowTitle("Rajasthan Jal Board — Admin Console")
        self.setup_ui()

    def setup_ui(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        layout = QHBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        self.sidebar = QWidget(); self.sidebar.setObjectName("sidebar"); self.sidebar.setFixedWidth(200)
        layout.addWidget(self.sidebar)

        side_lay = QVBoxLayout(self.sidebar); side_lay.setContentsMargins(8, 8, 8, 8); side_lay.setSpacing(4)
        side_lay.addWidget(QLabel("Rajasthan Jal Board", styleSheet="font-weight: bold; font-size: 14px"))
        side_lay.addWidget(QLabel("Admin Console", styleSheet="font-size: 10px; color: #a09d96"))
        side_lay.addSpacing(8)

        self.stack = QStackedWidget(); layout.addWidget(self.stack, 1)

        nav_items = [("Dashboard", "🏠"), ("Consumers", "👥"), ("Meter Readers", "👷"), ("Billing Cycles", "💳"), ("Readings", "📖"), ("Payments", "💰"), ("Reports", "📊"), ("Charges Config", "⚙️"), ("Audit Log", "📋")]
        self.nav_btns = []
        for i, (name, icon) in enumerate(nav_items):
            btn = QPushButton(f"{icon} {name}"); btn.setObjectName("nav_item")
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            side_lay.addWidget(btn); self.nav_btns.append(btn)

        side_lay.addStretch(); logout_btn = QPushButton("🔒 Logout"); logout_btn.clicked.connect(self.close); side_lay.addWidget(logout_btn)

        # Add widgets to stack
        self.stack.addWidget(DashboardWidget(self.fc, self.utils, self.admin_ctx, self))
        import consumers, meter_readers, billing, readings, payments, reports, charges_config, audit_log
        for mod in [consumers, meter_readers, billing, readings, payments, reports, charges_config, audit_log]:
            self.stack.addWidget(mod.get_widget(self.stack, self.fc, self.utils, self.be, self.admin_ctx))

        self.switch_page(0)
        self.setStatusBar(QStatusBar()); self.statusBar().showMessage(f"Admin: {self.admin_ctx['name']}  |  {datetime.now().strftime('%d-%m-%Y')}")

    def switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setObjectName("nav_item_active" if i == idx else "nav_item")
            btn.setStyle(btn.style()) # Force style update

class DashboardWidget(QWidget):
    def __init__(self, fc, utils, admin_ctx, parent_window):
        super().__init__()
        self.fc = fc; self.utils = utils; self.admin_ctx = admin_ctx; self.parent_window = parent_window
        self.setup_ui()
        self.refresh_stats()
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh_stats); self.timer.start(300000)

    def setup_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(30, 30, 30, 30)
        title = QLabel("Dashboard Summary"); title.setObjectName("page_title"); layout.addWidget(title)

        self.grid = QGridLayout(); layout.addLayout(self.grid)
        self.kpi_cards = {}
        kpis = [("Active Consumers", 0, 0), ("Open Cycles", 0, 1), ("Pending Readings", 0, 2), ("Pending Queries", 1, 0), ("Total Outstanding", 1, 1), ("Collected Month", 1, 2)]
        for name, r, c in kpis:
            card = QFrame(); card.setObjectName("card"); slay = QVBoxLayout(card)
            slay.addWidget(QLabel(name.upper(), styleSheet="font-size: 10px; color: #6c6a64"))
            val = QLabel("..."); val.setStyleSheet("font-size: 24px; font-weight: bold"); slay.addWidget(val)
            self.grid.addWidget(card, r, c); self.kpi_cards[name] = val

        self.alert_box = QGroupBox("Action Required"); self.alert_box.setVisible(False); layout.addWidget(self.alert_box)
        alay = QHBoxLayout(self.alert_box); self.alert_lbl = QLabel(""); alay.addWidget(self.alert_lbl)
        go_btn = QPushButton("Go to Queries"); go_btn.clicked.connect(lambda: self.parent_window.switch_page(4)); alay.addWidget(go_btn)
        layout.addStretch()

    def refresh_stats(self):
        def done(s):
            self.kpi_cards["Active Consumers"].setText(str(s["consumers"]))
            self.kpi_cards["Open Cycles"].setText(str(s["cycles"]))
            self.kpi_cards["Pending Readings"].setText(str(s["pending_readings"]))
            self.kpi_cards["Pending Queries"].setText(str(s["pending_queries"]))
            self.kpi_cards["Total Outstanding"].setText(self.utils.format_currency(s["outstanding"]))
            self.kpi_cards["Collected Month"].setText(self.utils.format_currency(s["collected"]))
            self.alert_box.setVisible(s["pending_queries"] > 0)
            self.alert_lbl.setText(f"You have {s['pending_queries']} pending correction queries!")
        self.utils.run_in_thread(self.fc.get_dashboard_stats, callback=done)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    _load_fonts(app); _load_stylesheet(app)
    firebase_config.get_firebase_app()
    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        win = MainWindow(fc, utils, be, {"name": login.admin_name})
        win.showMaximized(); sys.exit(app.exec())
