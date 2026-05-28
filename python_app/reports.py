import sys
import os
import openpyxl
import json
from datetime import datetime, date
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox,
    QFileDialog, QProgressBar, QLineEdit, QComboBox, QFrame, QScrollArea,
    QTextEdit
)
from PySide6.QtCore import Qt, Slot

def get_widget(parent, fc, utils, be, admin_ctx) -> QWidget:
    return ReportsWidget(parent, fc, utils, be, admin_ctx)

class ReportsWidget(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)
        header = QHBoxLayout(); title = QLabel("ANALYTICS & REPORTS"); title.setObjectName("page_title"); header.addWidget(title)
        refresh_btn = QPushButton("🔄 Refresh Cache"); refresh_btn.clicked.connect(self.fc.clear_cache); header.addWidget(refresh_btn, 0, Qt.AlignRight); layout.addLayout(header)

        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.tabs.addTab(ReaderActivityTab(self, self.fc, self.utils, self.be, self.admin_ctx), "👷 Reader Logs")
        self.tabs.addTab(BillingSummaryTab(self, self.fc, self.utils, self.be, self.admin_ctx), "📊 Billing Summary")
        self.tabs.addTab(ZoneCollectionTab(self, self.fc, self.utils, self.be, self.admin_ctx), "🗺️ Zone Collections")
        self.tabs.addTab(OutstandingTab(self, self.fc, self.utils, self.be, self.admin_ctx), "💰 Outstandings")
        self.tabs.addTab(SkippedTab(self, self.fc, self.utils, self.be, self.admin_ctx), "❌ Skippeds")
        self.tabs.addTab(LedgerStatementTab(self, self.fc, self.utils, self.be, self.admin_ctx), "📖 Ledger Statements")
        self.tabs.addTab(DatabaseBackupTab(self, self.fc, self.utils, self.be, self.admin_ctx), "💾 Database Backup")

class ReaderActivityTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); f_lay = QHBoxLayout()
        self.f_from = QLineEdit(self.utils.today_str()); self.f_to = QLineEdit(self.utils.today_str())
        self.f_reader = QComboBox(); self.f_zone = QComboBox(); self.f_zone.addItems(["All"] + [str(z) for z in self.utils.ZONE_RANGE])
        btn = QPushButton("🔍 Filter"); btn.clicked.connect(self.search)
        f_lay.addWidget(QLabel("From:")); f_lay.addWidget(self.f_from); f_lay.addWidget(QLabel("To:")); f_lay.addWidget(self.f_to)
        f_lay.addWidget(QLabel("Reader:")); f_lay.addWidget(self.f_reader); f_lay.addWidget(QLabel("Zone:")); f_lay.addWidget(self.f_zone)
        f_lay.addWidget(btn); f_lay.addStretch(); layout.addLayout(f_lay)
        self.table = QTableWidget(0, 9); self.table.setHorizontalHeaderLabels(["Reader", "Emp ID", "CIN", "Name", "Date", "Prev", "Curr", "Usage", "Status"])
        layout.addWidget(self.table)
        self.utils.run_in_thread(self.fc.list_meter_readers, callback=self.on_readers)
    def on_readers(self, rs):
        self.readers_map = {r["name"]: r["uid"] for r in rs}
        self.f_reader.clear(); self.f_reader.addItems(["All"] + list(self.readers_map.keys()))
    def search(self):
        r_uid = self.readers_map.get(self.f_reader.currentText()) if self.f_reader.currentText() != "All" else None
        z = int(self.f_zone.currentText()) if self.f_zone.currentText() != "All" else None
        def done(logs):
            self.table.setRowCount(0); self.cache = logs
            for l in logs:
                row = self.table.rowCount(); self.table.insertRow(row)
                items = [l.get("reader_name"), l.get("employee_id"), l.get("cin_no"), l.get("consumer_name"), l.get("reading_date"), f"{l.get('previous_reading',0):.2f}", f"{l.get('current_reading',0):.2f}", f"{l.get('consumption',0):.2f}", l.get("status")]
                for i, v in enumerate(items): self.table.setItem(row, i, QTableWidgetItem(str(v)))
        self.utils.run_in_thread(lambda: self.fc.get_meter_reader_activity(self.f_from.text(), self.f_to.text(), r_uid, z), callback=done)

class BillingSummaryTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); f_lay = QHBoxLayout(); self.f_cycle = QComboBox(); f_lay.addWidget(QLabel("Cycle:")); f_lay.addWidget(self.f_cycle)
        btn = QPushButton("📊 Run"); btn.clicked.connect(self.run); f_lay.addWidget(btn); f_lay.addStretch(); layout.addLayout(f_lay)
        self.kpi_lbl = QLabel("Billed: — | Collected: — | Deficit: —"); layout.addWidget(self.kpi_lbl)
        self.fig = Figure(figsize=(8, 4), facecolor="none"); self.canvas = FigureCanvas(self.fig); layout.addWidget(self.canvas)
        self.utils.run_in_thread(self.fc.list_billing_cycles, callback=lambda cs: [self.f_cycle.clear(), self.f_cycle.addItems([c["cycle_id"] for c in cs])])
    def run(self):
        cid = self.f_cycle.currentText()
        if not cid: return
        def fetch(): return self.fc.get_billing_summary(cid), self.fc.get_zone_collection_report(cid)
        def done(res):
            m, zd = res; self.kpi_lbl.setText(f"Billed: {self.utils.format_currency(m['total_billed'])} | Collected: {self.utils.format_currency(m['total_collected'])} | Deficit: {self.utils.format_currency(m['total_outstanding'])}")
            self.fig.clear(); ax = self.fig.add_subplot(111); zones = [str(z["zone"]) for z in zd]; billed = [z["billed_amount"] for z in zd]; coll = [z["collected_amount"] for z in zd]
            x = np.arange(len(zones)); w = 0.35; ax.bar(x - w/2, billed, w, label="Billed", color="#1e3a5f"); ax.bar(x + w/2, coll, w, label="Collected", color="#E8913A")
            ax.set_facecolor("none")
            ax.tick_params(colors="#1e3a5f") # Set to dark blue to match text on white-ish cards
            for s in ax.spines.values(): s.set_color("#334155")
            ax.set_xticks(x); ax.set_xticklabels(zones); ax.legend(); self.fig.tight_layout(); self.canvas.draw()
        self.utils.run_in_thread(fetch, callback=done)

class ZoneCollectionTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); self.f_cycle = QComboBox(); layout.addWidget(self.f_cycle)
        self.table = QTableWidget(0, 8); self.table.setHorizontalHeaderLabels(["Zone", "Total", "Read", "Cannot", "Pending", "Billed", "Collected", "Pct"])
        layout.addWidget(self.table); btn = QPushButton("Run"); btn.clicked.connect(self.run); layout.addWidget(btn)
        self.utils.run_in_thread(self.fc.list_billing_cycles, callback=lambda cs: self.f_cycle.addItems([c["cycle_id"] for c in cs]))
    def run(self):
        def done(zs):
            self.table.setRowCount(0)
            for z in zs:
                row = self.table.rowCount(); self.table.insertRow(row)
                items = [z["zone"], z["total_consumers"], z["read_consumers"], z["cannot_read_consumers"], z["pending_consumers"], self.utils.format_currency(z["billed_amount"]), self.utils.format_currency(z["collected_amount"]), f"{(z['collected_amount']/z['billed_amount']*100 if z['billed_amount']>0 else 0):.1f}%"]
                for i, v in enumerate(items): self.table.setItem(row, i, QTableWidgetItem(str(v)))
        self.utils.run_in_thread(lambda: self.fc.get_zone_collection_report(self.f_cycle.currentText()), callback=done)

class OutstandingTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["CIN", "Name", "Zone", "Category", "Outstanding", "Credit", "Status"])
        layout.addWidget(self.table); btn = QPushButton("Fetch Defaulters"); btn.clicked.connect(self.run); layout.addWidget(btn)
    def run(self): self.utils.run_in_thread(self.fc.get_outstanding_balance_report, callback=self.done)
    def done(self, cs):
        self.table.setRowCount(0)
        for c in cs:
            row = self.table.rowCount(); self.table.insertRow(row)
            items = [c["cin_no"], c["name"], c["zone"], c["category"], self.utils.format_currency(c["outstanding_balance"]), self.utils.format_currency(c["credit_balance"]), c["status"]]
            for i, v in enumerate(items): self.table.setItem(row, i, QTableWidgetItem(str(v)))

class SkippedTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); self.f_cycle = QComboBox(); layout.addWidget(self.f_cycle)
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["CIN", "Name", "Zone", "Reason", "Reader", "Date", "Notes"])
        layout.addWidget(self.table); btn = QPushButton("Query"); btn.clicked.connect(self.run); layout.addWidget(btn)
        self.utils.run_in_thread(self.fc.list_billing_cycles, callback=lambda cs: self.f_cycle.addItems([c["cycle_id"] for c in cs]))
    def run(self):
        def done(ds):
            self.table.setRowCount(0)
            for d in ds:
                row = self.table.rowCount(); self.table.insertRow(row)
                for i, v in enumerate([d["cin_no"], d["name"], d["zone"], d["reason"], d["reader_name"], d["reading_date"], d.get("notes","")]): self.table.setItem(row, i, QTableWidgetItem(str(v)))
        self.utils.run_in_thread(lambda: self.fc.get_skipped_readings_report(self.f_cycle.currentText()), callback=done)

class LedgerStatementTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); self.f_cin = QLineEdit(); layout.addWidget(QLabel("CIN:")); layout.addWidget(self.f_cin)
        btn = QPushButton("🖨️ Export PDF Ledger"); btn.clicked.connect(self.run); layout.addWidget(btn); layout.addStretch()
    def run(self):
        cin = self.f_cin.text().strip()
        if not cin: return
        def run_pdf():
            c = self.fc.get_consumer(cin)
            if not c: return
            html = self.utils.load_pdf_template("consumer_ledger").replace("{{cin_no}}", cin).replace("{{name}}", c["name"]) # simplified
            path = os.path.join(os.getcwd(), f"Ledger_{cin}.pdf")
            with open(path, "wb") as f: f.write(self.utils.render_pdf_to_bytes(html))
            return path
        self.utils.run_in_thread(run_pdf, callback=lambda p: self.utils.open_pdf(p) if p else QMessageBox.warning(self, "Error", "Not found."))

class DatabaseBackupTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); btn = QPushButton("💾 Run Full Backup"); btn.clicked.connect(self.run); layout.addWidget(btn); self.prog = QProgressBar(); self.prog.setVisible(False); layout.addWidget(self.prog); layout.addStretch()
    def run(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Backup", "Backup.xlsx", "Excel Files (*.xlsx)")
        if not path: return
        self.prog.setVisible(True); self.prog.setRange(0, 0)
        def done(data):
            wb = openpyxl.Workbook(); wb.remove(wb.active)
            for name, rows in data.items():
                ws = wb.create_sheet(title=name[:30])
                if rows: headers = list(rows[0].keys()); ws.append(headers); [ws.append([r.get(h) for h in headers]) for r in rows]
            wb.save(path); self.prog.setVisible(False); QMessageBox.information(self, "Success", "Backup saved.")
        self.utils.run_in_thread(self.fc.export_full_data_backup, callback=done)
