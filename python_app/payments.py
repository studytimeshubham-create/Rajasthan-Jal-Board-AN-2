import sys
import os
import openpyxl
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QMessageBox, QFileDialog, QFrame, QAbstractItemView, QTextEdit
)
from PySide6.QtCore import Qt, Slot, QTimer

def get_widget(parent, fc, utils, be, admin_ctx) -> QWidget:
    return PaymentsWidget(parent, fc, utils, be, admin_ctx)

class PaymentsWidget(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)
        header = QHBoxLayout(); title = QLabel("PAYMENTS & ADJUSTMENTS"); title.setObjectName("page_title"); header.addWidget(title)
        refresh_btn = QPushButton("🔄 Refresh Data"); refresh_btn.clicked.connect(self.fc.clear_cache); header.addWidget(refresh_btn, 0, Qt.AlignRight); layout.addLayout(header)

        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.record_tab = RecordPaymentTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.import_tab = BulkImportPaymentsTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.log_tab = PaymentLogTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.waiver_tab = LPSWaiverTab(self, self.fc, self.utils, self.be, self.admin_ctx)
        self.credit_tab = CreditBalanceTab(self, self.fc, self.utils, self.be, self.admin_ctx)

        self.tabs.addTab(self.record_tab, "💰 Record Payment")
        self.tabs.addTab(self.import_tab, "📥 Bulk Import")
        self.tabs.addTab(self.log_tab, "📜 Payment Log")
        self.tabs.addTab(self.waiver_tab, "🏳️ LPS Waiver")
        self.tabs.addTab(self.credit_tab, "🪙 Credit Balance")

class RecordPaymentTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.debounce = QTimer(); self.debounce.setSingleShot(True); self.debounce.timeout.connect(self.lookup)
        self.target_c = None; self.setup_ui()

    def setup_ui(self):
        lay = QHBoxLayout(self); left = QVBoxLayout(); right = QVBoxLayout(); lay.addLayout(left, 1); lay.addLayout(right, 1)
        form = QGroupBox("Record New Payment"); flay = QFormLayout(form)
        self.f_cin = QLineEdit(); self.f_cin.textChanged.connect(lambda: self.debounce.start(300))
        self.f_amt = QLineEdit(); self.f_mode = QComboBox(); self.f_mode.addItems(["Cash", "E-Mitra"]); self.f_mode.currentTextChanged.connect(self.toggle_emitra)
        self.f_key = QLineEdit(); self.f_key.setEnabled(False); self.f_date = QLineEdit(self.utils.today_str())
        self.f_date.editingFinished.connect(self.update_lps); self.f_cycle = QComboBox(); self.f_cycle.currentTextChanged.connect(self.update_lps)
        self.f_notes = QLineEdit()
        for l, w in [("CIN:", self.f_cin), ("Amount:", self.f_amt), ("Mode:", self.f_mode), ("E-Mitra Key:", self.f_key), ("Date:", self.f_date), ("Cycle:", self.f_cycle), ("Notes:", self.f_notes)]: flay.addRow(l, w)
        left.addWidget(form); self.lps_lbl = QLabel("LPS Preview: —"); left.addWidget(self.lps_lbl)
        save_btn = QPushButton("💰 Save & Record Payment"); save_btn.clicked.connect(self.save); left.addWidget(save_btn); left.addStretch()
        snap = QGroupBox("Consumer Snapshot"); slay = QVBoxLayout(snap); self.l_name = QLabel("Name: —"); self.l_out = QLabel("Outstanding: —")
        slay.addWidget(self.l_name); slay.addWidget(self.l_out); slay.addStretch(); right.addWidget(snap)
        self.utils.run_in_thread(self.fc.list_billing_cycles, callback=lambda cs: [self.f_cycle.clear(), self.f_cycle.addItems([""] + [c["cycle_id"] for c in cs])])

    def toggle_emitra(self, m): self.f_key.setEnabled(m == "E-Mitra")
    def lookup(self): self.utils.run_in_thread(lambda: self.fc.get_consumer(self.f_cin.text().strip()), callback=self.on_found)
    def on_found(self, c):
        self.target_c = c
        if c: self.l_name.setText(f"Name: {c['name']}"); self.l_out.setText(f"Out: {self.utils.format_currency(c.get('outstanding_balance',0))}")
        else: self.l_name.setText("Name: Not Found")
        self.update_lps()
    def update_lps(self):
        if not self.target_c or not self.f_cycle.currentText(): return
        def fetch(): return self.fc.get_billing_cycle(self.f_cycle.currentText())
        def done(cycle):
            if not cycle: return
            res = self.be.apply_lps(float(self.f_amt.text() or 0), self.utils.parse_date(cycle["last_payment_date"]), self.utils.parse_date(self.f_date.text()),
                                    self.target_c.get("credit_balance",0), self.target_c.get("outstanding_balance",0))
            self.lps_lbl.setText(f"LPS: {self.utils.format_currency(res['lps_amount'])} ({res['lps_type']})")
        self.utils.run_in_thread(fetch, callback=done)

    def save(self):
        if not self.target_c: return
        try: amount = float(self.f_amt.text())
        except: return QMessageBox.warning(self, "Error", "Invalid amount.")
        p = {"cin_no": self.target_c["cin_no"], "amount": amount, "payment_mode": self.f_mode.currentText(), "emitra_key": self.f_key.text() if self.f_mode.currentText() == "E-Mitra" else None,
             "payment_date": self.f_date.text(), "entry_date": self.utils.today_str(), "cycle_id": self.f_cycle.currentText() or None, "notes": self.f_notes.text()}
        def run(): self.fc.clear_cache(); return self.fc.record_payment(p, self.admin_ctx["name"])
        def done(pid):
            if QMessageBox.question(self, "Success", f"Recorded: {pid}\nPrint receipt?") == QMessageBox.Yes: self.print_rcpt(pid, p, self.target_c)
            self.f_cin.clear(); self.f_amt.clear(); self.on_found(None)
        self.utils.run_in_thread(run, callback=done)

    def print_rcpt(self, pid, p, c):
        def run():
            tmpl = self.utils.load_pdf_template("payment_receipt")
            h = tmpl.replace("{{receipt_number}}", pid).replace("{{cin_no}}", c["cin_no"]).replace("{{name}}", c["name"])\
                    .replace("{{amount}}", self.utils.format_currency(p["amount"])).replace("{{payment_date}}", p["payment_date"])\
                    .replace("{{received_by}}", self.admin_ctx["name"])
            path = os.path.join(os.getcwd(), f"Receipt_{pid}.pdf")
            with open(path, "wb") as f: f.write(self.utils.render_pdf_to_bytes(h))
            return path
        self.utils.run_in_thread(run, callback=self.utils.open_pdf)

class BulkImportPaymentsTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.admin_ctx = admin_ctx; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); layout.addWidget(QLabel("<b>Bulk Import Payments (Excel)</b>"))
        self.path_edit = QLineEdit(); self.path_edit.setReadOnly(True)
        h = QHBoxLayout(); h.addWidget(self.path_edit); b = QPushButton("📂 Browse"); b.clicked.connect(self.browse); h.addWidget(b); layout.addLayout(h)
        import_b = QPushButton("🚀 Import"); import_b.clicked.connect(self.run_import); layout.addWidget(import_b); layout.addStretch()
    def browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Excel", "", "Excel Files (*.xlsx)")
        if p: self.path_edit.setText(p)
    def run_import(self):
        p = self.path_edit.text()
        if not p: return
        def run():
            ws = openpyxl.load_workbook(p, data_only=True).active; rows = list(ws.iter_rows(values_only=True)); headers = [str(h).strip() for h in rows[0]]
            data = []
            for r in rows[1:]:
                if not any(r): continue
                d = {headers[i]: r[i] for i in range(len(headers)) if i < len(r)}
                d["amount"] = float(d["amount"]); data.append(d)
            return self.fc.bulk_record_payments(data, self.admin_ctx["name"])
        self.utils.run_in_thread(run, callback=lambda res: QMessageBox.information(self, "Done", f"Imported {res['success']} payments."))

class PaymentLogTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["Receipt", "Date", "CIN", "Mode", "Key", "Amount", "Admin"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(self.table)
        self.refresh()
    def refresh(self): self.utils.run_in_thread(lambda: self.fc.list_payments({}), callback=self.done)
    def done(self, ps):
        self.table.setRowCount(0)
        for p in ps:
            row = self.table.rowCount(); self.table.insertRow(row)
            items = [p.get("receipt_number"), p.get("payment_date"), p.get("cin_no"), p.get("payment_mode"), p.get("emitra_key") or "—", self.utils.format_currency(p.get("amount",0)), p.get("received_by", "")]
            for i, v in enumerate(items): self.table.setItem(row, i, QTableWidgetItem(str(v)))

class LPSWaiverTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); layout.addWidget(QLabel("<b>LPS Waiver Tool</b>"))
        self.f_cin = QLineEdit(); self.f_amt = QLineEdit(); self.f_note = QTextEdit()
        lay = QFormLayout(); lay.addRow("CIN:", self.f_cin); lay.addRow("Waiver Amount:", self.f_amt); lay.addRow("Reason:", self.f_note); layout.addLayout(lay)
        btn = QPushButton("🏳️ Apply Waiver"); btn.clicked.connect(self.save); layout.addWidget(btn); layout.addStretch()
    def save(self):
        def run(): self.fc.update_consumer_lps_waiver(self.f_cin.text().strip(), float(self.f_amt.text()), self.f_note.toPlainText().strip(), self.admin_ctx["name"])
        self.utils.run_in_thread(run, callback=lambda _: QMessageBox.information(self, "Success", "Waiver applied."))

class CreditBalanceTab(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent); self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx; self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self); layout.addWidget(QLabel("<b>Credit Balance Adjustments</b>"))
        self.f_cin = QLineEdit(); self.f_amt = QLineEdit(); self.f_note = QTextEdit()
        lay = QFormLayout(); lay.addRow("CIN:", self.f_cin); lay.addRow("Adjustment Amount:", self.f_amt); lay.addRow("Reason:", self.f_note); layout.addLayout(lay)
        btn = QPushButton("🪙 Save Adjustment"); btn.clicked.connect(self.save); layout.addWidget(btn); layout.addStretch()
    def save(self):
        def run(): self.fc.add_custom_adjustment(self.f_cin.text().strip(), "waiver", float(self.f_amt.text()), self.f_note.toPlainText().strip(), self.admin_ctx["name"])
        self.utils.run_in_thread(run, callback=lambda _: QMessageBox.information(self, "Success", "Adjustment saved."))
