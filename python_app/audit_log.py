import sys
import openpyxl
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox, QDialog,
    QLineEdit, QComboBox, QFileDialog, QTextEdit, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot

def get_widget(parent, fc, utils, be, admin_ctx) -> QWidget:
    return AuditLogWidget(parent, fc, utils, be, admin_ctx)

class AuditLogWidget(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.be = be; self.admin_ctx = admin_ctx
        self.logs_cache = {}; self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)
        header = QHBoxLayout(); title = QLabel("SECURITY AUDIT TIMELINE"); title.setObjectName("page_title"); header.addWidget(title)
        refresh_btn = QPushButton("🔄 Refresh Logs"); refresh_btn.clicked.connect(self.refresh_logs); header.addWidget(refresh_btn, 0, Qt.AlignRight); layout.addLayout(header)

        f_group = QGroupBox("Filters"); f_lay = QHBoxLayout(f_group)
        self.f_from = QLineEdit(self.utils.today_str()); self.f_to = QLineEdit(self.utils.today_str())
        self.f_action = QComboBox(); self.f_action.addItems(["All", "CREATE_CONSUMER", "UPDATE_CONSUMER", "DEACTIVATE_CONSUMER", "REACTIVATE_CONSUMER", "CREATE_BILLING_CYCLE", "CLOSE_BILLING_CYCLE", "ADMIN_UPDATE_READING", "APPROVE_CORRECTION_QUERY", "REJECT_CORRECTION_QUERY", "RECORD_PAYMENT", "LPS_WAIVER", "ADD_CUSTOM_ADJUSTMENT", "RECORD_METER_REPLACEMENT", "UPDATE_CHARGES_CONFIG", "CREATE_METER_READER", "UPDATE_METER_READER", "DEACTIVATE_METER_READER", "RESET_METER_READER_PASSWORD"])
        self.f_admin = QLineEdit()
        for l, w in [("From:", self.f_from), ("To:", self.f_to), ("Action:", self.f_action), ("Admin:", self.f_admin)]: f_lay.addWidget(QLabel(l)); f_lay.addWidget(w)
        load_btn = QPushButton("🔄 Load / Refresh"); load_btn.clicked.connect(self.refresh_logs); f_lay.addWidget(load_btn)
        exp_btn = QPushButton("📤 Export Excel"); exp_btn.clicked.connect(self.export_excel); f_lay.addWidget(exp_btn)
        layout.addWidget(f_group)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Action Type", "Performed By", "Target Doc", "Old Value", "New Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive); self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers); self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.doubleClicked.connect(self.on_row_double); layout.addWidget(self.table)

    def refresh_logs(self):
        filters = {"date_from": self.f_from.text().strip(), "date_to": self.f_to.text().strip(), "performed_by": self.f_admin.text().strip()}
        if self.f_action.currentText() != "All": filters["action_type"] = self.f_action.currentText()
        def fetch(): self.fc.clear_cache(); return self.fc.get_audit_log(filters)
        def done(logs):
            self.table.setRowCount(0); self.logs_cache = {l["log_id"]: l for l in logs}
            for l in logs:
                row = self.table.rowCount(); self.table.insertRow(row)
                ts = l.get("timestamp"); ts_str = self.utils.format_date(ts)
                items = [ts_str, l["action_type"], l.get("performed_by_name", ""), l.get("target_document", ""), str(l.get("old_value"))[:60], str(l.get("new_value"))[:60]]
                for i, v in enumerate(items):
                    item = QTableWidgetItem(str(v)); item.setData(Qt.UserRole, l["log_id"]); self.table.setItem(row, i, item)
        self.utils.run_in_thread(fetch, callback=done)

    def on_row_double(self, index):
        log_id = self.table.item(index.row(), 0).data(Qt.UserRole)
        l = self.logs_cache.get(log_id)
        if not l: return
        dlg = QDialog(self); dlg.setWindowTitle(f"Log Detail - {log_id}"); dlg.resize(800, 600); lay = QVBoxLayout(dlg)
        h = QHBoxLayout(); lay.addLayout(h)
        for title, val in [("PREVIOUS STATE", l.get("old_value")), ("NEW STATE", l.get("new_value"))]:
            v = QVBoxLayout(); v.addWidget(QLabel(title)); t = QTextEdit(); t.setReadOnly(True); t.setFont("JetBrains Mono")
            t.setPlainText(json.dumps(val, indent=2) if val is not None else "N/A"); v.addWidget(t); h.addLayout(v)
        dlg.exec()

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Audit Log", "AuditLog.xlsx", "Excel Files (*.xlsx)")
        if not path: return
        def run():
            wb = openpyxl.Workbook(); ws = wb.active; ws.append(["Timestamp", "Action", "Admin", "Target", "Old JSON", "New JSON"])
            for l in self.logs_cache.values():
                ws.append([str(l.get("timestamp")), l["action_type"], l.get("performed_by_name"), l.get("target_document"), json.dumps(l.get("old_value")), json.dumps(l.get("new_value"))])
            wb.save(path)
        self.utils.run_in_thread(run, callback=lambda _: QMessageBox.information(self, "Success", "Exported."))
