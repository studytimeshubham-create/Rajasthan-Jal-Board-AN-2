import sys
import os
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox,
    QDialog, QProgressBar, QListWidget, QLineEdit, QRadioButton, QButtonGroup,
    QFileDialog, QFrame, QAbstractItemView, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt, Slot, QTimer

def get_widget(parent, fc, utils, be, admin_ctx) -> QWidget:
    return BillingWidget(parent, fc, utils, be, admin_ctx)

class BillingWidget(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("BILLING CYCLES"); title.setObjectName("page_title")
        header.addWidget(title)
        refresh_btn = QPushButton("🔄 Refresh All")
        refresh_btn.clicked.connect(self.refresh_all); header.addWidget(refresh_btn, 0, Qt.AlignRight)
        layout.addLayout(header)

        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.active_tab = ActiveCyclesTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.init_tab = InitiateCycleTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.print_tab = PrintCSDTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.past_tab = PastCyclesTab(self, self.fc, self.utils, self.be, self.admin_ctx)

        self.tabs.addTab(self.active_tab, "💳 Active Cycles")
        self.tabs.addTab(self.init_tab, "➕ Initiate Cycle")
        self.tabs.addTab(self.print_tab, "🖨️ Print CSD Sheets")
        self.tabs.addTab(self.past_tab, "📜 Past Cycles History")

    def refresh_all(self):
        self.active_tab.load_active(); self.init_tab.refresh_locked_zones(); self.print_tab.load_active_cycles(); self.past_tab.load_past()

class ActiveCyclesTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx; self.cycles_list = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Cycle ID", "Zones", "Start", "End", "Last Pay", "Progress", "Skipped"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        close_btn = QPushButton("🔒 Close Selected Cycle"); close_btn.clicked.connect(self.close_cycle)
        layout.addWidget(close_btn, 0, Qt.AlignLeft)
        self.load_active()

    def load_active(self):
        def fetch():
            cycles = self.fc.get_open_cycles(); rows = []
            for c in cycles:
                readings = self.fc.get_readings_for_cycle(c["cycle_id"])
                finalized = len([r for r in readings if r.get("status") == "finalized"])
                skipped = len([r for r in readings if r.get("status") == "skipped"])
                total = sum(c.get("consumer_count_per_zone", {}).values())
                rows.append({"cycle": c, "finalized": finalized, "skipped": skipped, "total": total})
            return rows
        def done(rows):
            self.cycles_list = rows; self.table.setRowCount(0)
            for r in rows:
                c = r["cycle"]; row = self.table.rowCount(); self.table.insertRow(row)
                for i, v in enumerate([c["cycle_id"], str(c["zones"]), c["start_date"], c["end_date"], c["last_payment_date"], f"{r['finalized']} of {r['total']}", str(r["skipped"])]):
                    self.table.setItem(row, i, QTableWidgetItem(v))
        self.utils.run_in_thread(fetch, callback=done)

    def close_cycle(self):
        sel = self.table.selectedItems()
        if not sel: return QMessageBox.warning(self, "Error", "Select a cycle.")
        cid = self.table.item(sel[0].row(), 0).text()
        item = next(r for r in self.cycles_list if r["cycle"]["cycle_id"] == cid)
        def fetch_summary(): return self.fc.get_billing_summary(cid)
        def on_summary(summary):
            pending = max(0, item["total"] - (item["finalized"] + item["skipped"]))
            dlg = QDialog(self); dlg.setWindowTitle(f"Checklist - {cid}"); lay = QVBoxLayout(dlg)
            lay.addWidget(QLabel(f"<b>Verify Cycle: {cid}</b>"))
            lay.addWidget(QLabel(f"• Pending: {pending}"))
            lay.addWidget(QLabel(f"• Billed: {self.utils.format_currency(summary['total_billed'])}"))
            lay.addWidget(QLabel(f"• Collected: {self.utils.format_currency(summary['total_collected'])}"))
            lay.addWidget(QLabel(f"• Net Outstanding: {self.utils.format_currency(summary['total_outstanding'])}"))
            if pending > 0: lay.addWidget(QLabel("⚠️ WARNING: Unfinished zones will be freed.", styleSheet="color: orange"))
            btn = QPushButton("🔒 Confirm Close Cycle"); btn.clicked.connect(lambda: self.do_close(cid, dlg)); lay.addWidget(btn); dlg.exec()
        self.utils.run_in_thread(fetch_summary, callback=on_summary)

    def do_close(self, cid, dlg):
        if QMessageBox.question(dlg, "Confirm", "Permanently close cycle?") == QMessageBox.Yes:
            self.utils.run_in_thread(lambda: self.fc.close_billing_cycle(cid, self.admin_ctx["name"]),
                                     callback=lambda _: [QMessageBox.information(self, "Success", "Closed."), dlg.accept(), self.load_active()])

class InitiateCycleTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.zone_list = QListWidget(); self.zone_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for z in self.utils.ZONE_RANGE: self.zone_list.addItem(f"Zone {z}")
        self.zone_list.itemSelectionChanged.connect(self.update_preview)
        layout.addWidget(QLabel("<b>Select Zone(s):</b>")); layout.addWidget(self.zone_list)

        form = QGroupBox("Cycle Parameters"); flay = QFormLayout(form)
        self.f_start = QLineEdit(self.utils.today_str()); self.f_end = QLineEdit()
        self.f_end.setPlaceholderText("DD-MM-YYYY"); self.f_end.textChanged.connect(self.update_preview)
        flay.addRow("Start Date:", self.f_start); flay.addRow("End Date:", self.f_end)

        self.grace_group = QButtonGroup(self); r1 = QRadioButton("1 Month"); r2 = QRadioButton("2 Months")
        self.grace_group.addButton(r1, 1); self.grace_group.addButton(r2, 2); r1.setChecked(True)
        self.grace_group.buttonClicked.connect(self.update_preview)
        gh = QHBoxLayout(); gh.addWidget(r1); gh.addWidget(r2); flay.addRow("Grace Period:", gh); layout.addWidget(form)

        prev = QGroupBox("Live Preview"); play = QVBoxLayout(prev)
        self.l_count = QLabel("Consumers: 0"); self.l_pay = QLabel("Last Pay Date: —")
        self.l_pay.setStyleSheet("font-weight: bold; font-size: 14px; color: #1A3A6B")
        play.addWidget(self.l_count); play.addWidget(self.l_pay); layout.addWidget(prev)

        btn = QPushButton("💳 INITIATE BILLING CYCLE"); btn.clicked.connect(self.initiate); layout.addWidget(btn); self.refresh_locked_zones()

    def refresh_locked_zones(self):
        def fetch(): return self.fc.get_open_cycle_zones()
        def done(active):
            for i in range(self.zone_list.count()):
                item = self.zone_list.item(i); z = int(item.text().split()[-1])
                if z in active: item.setFlags(Qt.NoItemFlags); item.setForeground(Qt.gray); item.setText(f"Zone {z} (Active)")
                else: item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled); item.setForeground(Qt.black); item.setText(f"Zone {z}")
        self.utils.run_in_thread(fetch, callback=done)

    def update_preview(self):
        zones = [int(i.text().split()[1]) for i in self.zone_list.selectedItems() if "(Active)" not in i.text()]
        if zones: self.utils.run_in_thread(lambda: sum(len(self.fc.list_consumers({"zone": z, "is_active": True})) for z in zones), callback=lambda n: self.l_count.setText(f"Consumers: {n}"))
        else: self.l_count.setText("Consumers: 0")
        try:
            d = self.utils.parse_date(self.f_end.text())
            lp = self.utils.add_months(d, self.grace_group.checkedId())
            self.l_pay.setText(f"Last Pay Date: {self.utils.format_date(lp)}")
        except: self.l_pay.setText("Last Pay Date: —")

    def initiate(self):
        zones = [int(i.text().split()[1]) for i in self.zone_list.selectedItems() if "(Active)" not in i.text()]
        if not zones or not self.f_end.text(): return QMessageBox.warning(self, "Error", "Fill all fields.")
        try: lp_str = self.l_pay.text().split(": ")[1]
        except: return QMessageBox.warning(self, "Error", "Invalid date.")
        data = {"zones": zones, "start_date": self.f_start.text(), "end_date": self.f_end.text(), "last_payment_date": lp_str, "grace_period_months": self.grace_group.checkedId()}
        if QMessageBox.question(self, "Confirm", f"Initiate for {zones}?") == QMessageBox.Yes:
            self.utils.run_in_thread(lambda: self.fc.create_billing_cycle(data, self.admin_ctx["name"]),
                                     callback=lambda cid: [QMessageBox.information(self, "Success", f"Cycle {cid} started."), self.parent().parent().refresh_all()])

class PrintCSDTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.setup_ui(); self.load_active_cycles()

    def setup_ui(self):
        layout = QVBoxLayout(self); form = QFormLayout()
        self.f_cycle = QComboBox(); self.f_cycle.currentIndexChanged.connect(self.on_cycle_selected)
        self.f_zone = QComboBox(); self.f_zone.currentIndexChanged.connect(self.update_preview)
        form.addRow("Select Cycle:", self.f_cycle); form.addRow("Select Zone:", self.f_zone); layout.addLayout(form)
        self.l_status = QLabel(""); layout.addWidget(self.l_status)
        self.prog = QProgressBar(); self.prog.setVisible(False); layout.addWidget(self.prog)
        btn = QPushButton("🖨️ Generate PDF"); btn.clicked.connect(self.generate); layout.addWidget(btn); layout.addStretch()

    def load_active_cycles(self):
        self.utils.run_in_thread(self.fc.get_open_cycles, callback=lambda cs: [self.f_cycle.clear(), self.f_cycle.addItems([c["cycle_id"] for c in cs])])

    def on_cycle_selected(self):
        cid = self.f_cycle.currentText()
        if cid: self.utils.run_in_thread(lambda: self.fc.get_billing_cycle(cid), callback=lambda c: [self.f_zone.clear(), self.f_zone.addItems([str(z) for z in c["zones"]])])

    def update_preview(self):
        z = self.f_zone.currentText()
        if z: self.utils.run_in_thread(lambda: len(self.fc.list_consumers({"zone": int(z), "is_active": True})), callback=lambda n: self.l_status.setText(f"Ready for {n} consumers."))

    def generate(self):
        cid, z = self.f_cycle.currentText(), self.f_zone.currentText()
        if not cid or not z: return
        self.prog.setVisible(True); self.prog.setRange(0, 0)
        def run():
            cycle_data = self.fc.get_billing_cycle(cid)
            cons = self.fc.list_consumers({"zone": int(z), "is_active": True})
            tmpl = self.utils.load_pdf_template("csd_sheet"); combined = ""
            for i, c in enumerate(cons):
                c_rows = "".join([f"<tr><td>{k}</td><td colspan='3'>{v}</td></tr>" for k, v in c.get("custom_attributes", {}).items()])
                h = tmpl.replace("{{cin_no}}", c["cin_no"]).replace("{{name}}", c["name"]).replace("{{zone}}", str(c["zone"]))\
                        .replace("{{category}}", c["category"]).replace("{{meter_size}}", c["meter_size"])\
                        .replace("{{meter_serial_no}}", c.get("meter_serial_no") or "")\
                        .replace("{{contact_number}}", str(c.get("contact_number") or ""))\
                        .replace("{{aadhaar_phed_no}}", c.get("aadhaar_phed_no") or "")\
                        .replace("{{consumer_status}}", c.get("consumer_status", "Active"))\
                        .replace("{{last_reading}}", f"{c.get('last_reading', 0.0):.2f}")\
                        .replace("{{apl_bpl}}", c.get("apl_bpl", "APL"))\
                        .replace("{{address}}", c.get("address_area_location", ""))\
                        .replace("{{address_landmark}}", c.get("address_landmark", ""))\
                        .replace("{{address_pin_code}}", str(c.get("address_pin_code") or ""))\
                        .replace("{{address_latitude}}", str(c.get("address_latitude") or "0.00"))\
                        .replace("{{address_longitude}}", str(c.get("address_longitude") or "0.00"))\
                        .replace("{{print_date}}", datetime.now().strftime("%d-%m-%Y"))\
                        .replace("{{cycle_period}}", f"{cycle_data.get('start_date')} to {cycle_data.get('end_date')}")\
                        .replace("{{custom_attributes_rows}}", c_rows)
                if i < len(cons) - 1: h = h.replace("</body>", "<div style='page-break-after: always;'></div></body>")
                combined += h
            path = os.path.join(os.getcwd(), f"CSD_{cid}_Z{z}.pdf")
            with open(path, "wb") as f: f.write(self.utils.render_pdf_to_bytes(combined))
            return path
        self.utils.run_in_thread(run, callback=lambda p: [self.prog.setVisible(False), self.utils.open_pdf(p)])

class PastCyclesTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.setup_ui(); self.load_past()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Cycle ID", "Zones", "Period", "Last Pay", "Closed At"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.itemSelectionChanged.connect(self.on_select); layout.addWidget(self.table)
        self.info = QLabel("Select a cycle for summary."); layout.addWidget(self.info)

    def load_past(self):
        def fetch(): return self.fc.list_billing_cycles("closed")
        def done(cs):
            self.table.setRowCount(0)
            for c in cs:
                row = self.table.rowCount(); self.table.insertRow(row)
                for i, v in enumerate([c["cycle_id"], str(c["zones"]), f"{c['start_date']} to {c['end_date']}", c["last_payment_date"], self.utils.format_date(c.get("closed_at"))]):
                    self.table.setItem(row, i, QTableWidgetItem(v))
        self.utils.run_in_thread(fetch, callback=done)

    def on_select(self):
        sel = self.table.selectedItems()
        if sel:
            cid = self.table.item(sel[0].row(), 0).text()
            self.utils.run_in_thread(lambda: self.fc.get_billing_summary(cid), callback=lambda s: self.info.setText(f"Billed: {self.utils.format_currency(s['total_billed'])} | Collected: {self.utils.format_currency(s['total_collected'])}"))
