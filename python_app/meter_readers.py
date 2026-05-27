import sys
import random
import string
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QMessageBox, QDialog, QApplication, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot

def get_widget(parent, fc, utils, be, admin_ctx) -> QWidget:
    return MeterReadersWidget(parent, fc, utils, be, admin_ctx)

class MeterReadersWidget(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc
        self.utils = utils
        self.be = be
        self.admin_ctx = admin_ctx
        self.readers_list = []
        self.current_reader = None

        self.setup_ui()
        self.load_readers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QHBoxLayout()
        title_lbl = QLabel("METER READER MANAGEMENT")
        title_lbl.setObjectName("page_title")
        header.addWidget(title_lbl)

        refresh_btn = QPushButton("🔄 Refresh Readers")
        refresh_btn.clicked.connect(lambda: self.load_readers(use_cache=False))
        header.addWidget(refresh_btn, 0, Qt.AlignRight)
        layout.addLayout(header)

        content = QHBoxLayout()
        layout.addLayout(content)

        # Left Panel: List
        left_panel = QWidget()
        left_lay = QVBoxLayout(left_panel)

        filter_h = QHBoxLayout()
        self.active_only_chk = QCheckBox("Active Profiles Only")
        self.active_only_chk.stateChanged.connect(lambda: self.load_readers())
        filter_h.addWidget(self.active_only_chk)
        left_lay.addLayout(filter_h)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Emp ID", "Role", "Name", "Zone", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_lay.addWidget(self.table)

        new_btn = QPushButton("➕ Register New Reader")
        new_btn.clicked.connect(self.open_new_reader_dialog)
        left_lay.addWidget(new_btn)

        content.addWidget(left_panel, 4)

        # Right Panel: Editor
        self.editor_group = QGroupBox("READER PROFILE EDITOR")
        self.editor_lay = QFormLayout(self.editor_group)
        self.editor_lay.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.f_name = QLineEdit()
        self.f_emp_id = QLineEdit()
        self.f_phone = QLineEdit()
        self.f_desig = QLineEdit()
        self.f_addr = QLineEdit()
        self.f_zone = QComboBox()
        self.f_zone.addItems([""] + [str(z) for z in self.utils.ZONE_RANGE])
        self.f_role = QComboBox()
        self.f_role.addItems(self.utils.READER_ROLE_OPTIONS)

        self.editor_lay.addRow("Name:*", self.f_name)
        self.editor_lay.addRow("Employee ID:*", self.f_emp_id)
        self.editor_lay.addRow("Phone Number:", self.f_phone)
        self.editor_lay.addRow("Designation:", self.f_desig)
        self.editor_lay.addRow("Address:", self.f_addr)
        self.editor_lay.addRow("Zone Filter:", self.f_zone)
        self.editor_lay.addRow("System Role:*", self.f_role)

        self.save_btn = QPushButton("💾 Save Profile Edits")
        self.save_btn.clicked.connect(self.save_edits)
        self.editor_lay.addRow(self.save_btn)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        self.editor_lay.addRow(sep)

        self.status_btn = QPushButton("🔒 Deactivate")
        self.status_btn.clicked.connect(self.toggle_status)
        self.editor_lay.addRow(self.status_btn)

        self.reset_btn = QPushButton("🔑 Reset Password")
        self.reset_btn.clicked.connect(self.reset_password)
        self.editor_lay.addRow(self.reset_btn)

        content.addWidget(self.editor_group, 5)
        self.set_editor_enabled(False)

    def load_readers(self, use_cache=True):
        def fetch():
            return self.fc.list_meter_readers(self.active_only_chk.isChecked(), use_cache=use_cache)
        def done(readers):
            self.readers_list = readers
            self.table.setRowCount(0)
            for r in readers:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(r["employee_id"]))
                self.table.setItem(row, 1, QTableWidgetItem(r.get("role", "Reader")))
                self.table.setItem(row, 2, QTableWidgetItem(r["name"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(r.get("zone") if r.get("zone") is not None else "All")))
                self.table.setItem(row, 4, QTableWidgetItem("Active" if r.get("is_active", True) else "Inactive"))
                self.table.item(row, 0).setData(Qt.UserRole, r["uid"])
            self.set_editor_enabled(False)
        self.utils.run_in_thread(fetch, callback=done)

    def on_selection_changed(self):
        sel = self.table.selectedItems()
        if not sel: return
        uid = self.table.item(sel[0].row(), 0).data(Qt.UserRole)
        self.current_reader = next((r for r in self.readers_list if r["uid"] == uid), None)
        if self.current_reader:
            self.set_editor_enabled(True)
            self.f_name.setText(self.current_reader["name"])
            self.f_emp_id.setText(self.current_reader["employee_id"])
            self.f_phone.setText(self.current_reader.get("phone_number", ""))
            self.f_desig.setText(self.current_reader.get("designation", ""))
            self.f_addr.setText(self.current_reader.get("address", ""))
            self.f_zone.setCurrentText(str(self.current_reader.get("zone") if self.current_reader.get("zone") is not None else ""))
            self.f_role.setCurrentText(self.current_reader.get("role", "Reader"))
            is_active = self.current_reader.get("is_active", True)
            self.status_btn.setText("🔒 Deactivate" if is_active else "🔓 Reactivate")

    def set_editor_enabled(self, enabled):
        self.editor_group.setEnabled(enabled)

    def save_edits(self):
        if not self.current_reader: return
        payload = {
            "name": self.f_name.text().strip(),
            "employee_id": self.f_emp_id.text().strip(),
            "phone_number": self.f_phone.text().strip() or None,
            "designation": self.f_desig.text().strip() or None,
            "address": self.f_addr.text().strip() or None,
            "zone": int(self.f_zone.currentText()) if self.f_zone.currentText() else None,
            "role": self.f_role.currentText()
        }
        if not payload["name"] or not payload["employee_id"]:
            return QMessageBox.warning(self, "Error", "Required fields empty.")
            
        def run():
            self.fc.update_meter_reader(self.current_reader["uid"], payload, self.admin_ctx["name"])
        self.utils.run_in_thread(run, callback=lambda _: [QMessageBox.information(self, "Success", "Profile updated."), self.load_readers()])

    def toggle_status(self):
        if not self.current_reader: return
        active = self.current_reader.get("is_active", True)
        if QMessageBox.question(self, "Confirm", f"Sure to {'deactivate' if active else 'reactivate'}?") == QMessageBox.Yes:
            fn = self.fc.deactivate_meter_reader if active else self.fc.reactivate_meter_reader
            self.utils.run_in_thread(lambda: fn(self.current_reader["uid"], self.admin_ctx["name"]), callback=lambda _: self.load_readers())

    def reset_password(self):
        if not self.current_reader: return
        dlg = QDialog(self); dlg.setWindowTitle("Reset Password"); lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"Enter new password for {self.current_reader['name']}:"))
        pwd_input = QLineEdit(); pwd_input.setEchoMode(QLineEdit.Password); lay.addWidget(pwd_input)
        btn = QPushButton("Reset"); btn.clicked.connect(lambda: self.do_reset(dlg, pwd_input.text().strip())); lay.addWidget(btn)
        dlg.exec()

    def do_reset(self, dlg, pwd):
        if len(pwd) < 6: return QMessageBox.warning(dlg, "Error", "Min 6 chars.")
        self.utils.run_in_thread(lambda: self.fc.reset_meter_reader_password(self.current_reader["uid"], pwd, self.admin_ctx["name"]),
                                 callback=lambda _: [QMessageBox.information(self, "Success", "Reset done."), dlg.accept()])

    def open_new_reader_dialog(self):
        NewReaderDialog(self, self.fc, self.utils, self.admin_ctx, self.load_readers).exec()

class NewReaderDialog(QDialog):
    def __init__(self, parent, fc, utils, admin_ctx, success_cb):
        super().__init__(parent)
        self.fc = fc; self.utils = utils; self.admin_ctx = admin_ctx; self.success_cb = success_cb
        self.setWindowTitle("Register New Meter Reader")
        self.setup_ui()

    def setup_ui(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.f_name = QLineEdit(); self.f_emp_id = QLineEdit(); self.f_user = QLineEdit()
        pwd_chars = string.ascii_letters + string.digits + "!@#$"; self.gen_pwd = "".join(random.choice(pwd_chars) for _ in range(10))
        self.f_pwd = QLineEdit(self.gen_pwd)
        copy_btn = QPushButton("📋 Copy Password"); copy_btn.clicked.connect(lambda: [QApplication.clipboard().setText(self.f_pwd.text()), QMessageBox.information(self, "Copied", "Password copied!")])
        self.f_phone = QLineEdit(); self.f_desig = QLineEdit(); self.f_addr = QLineEdit()
        self.f_zone = QComboBox(); self.f_zone.addItems([""] + [str(z) for z in self.utils.ZONE_RANGE])
        self.f_role = QComboBox(); self.f_role.addItems(self.utils.READER_ROLE_OPTIONS); self.f_role.setCurrentText("Reader")
        for l, w in [("Name:*", self.f_name), ("Employee ID:*", self.f_emp_id), ("Username:*", self.f_user), ("Temp Pwd:*", self.f_pwd), ("", copy_btn), ("Phone:", self.f_phone), ("Designation:", self.f_desig), ("Address:", self.f_addr), ("Zone Filter:", self.f_zone), ("Role:*", self.f_role)]: form.addRow(l, w)
        lay.addLayout(form)
        save_btn = QPushButton("🚀 Save User Profile"); save_btn.clicked.connect(self.save); lay.addWidget(save_btn)

    def save(self):
        data = {"name": self.f_name.text().strip(), "employee_id": self.f_emp_id.text().strip(), "username": self.f_user.text().strip(), "password": self.f_pwd.text().strip(),
                "phone_number": self.f_phone.text().strip() or None, "designation": self.f_desig.text().strip() or None, "address": self.f_addr.text().strip() or None,
                "zone": int(self.f_zone.currentText()) if self.f_zone.currentText() else None, "role": self.f_role.currentText()}
        if not all([data["name"], data["employee_id"], data["username"], data["password"]]): return QMessageBox.warning(self, "Error", "Required fields empty.")
        self.utils.run_in_thread(lambda: self.fc.create_meter_reader(data, self.admin_ctx["name"]), callback=lambda uid: [QMessageBox.information(self, "Success", f"Registered: {uid}"), self.success_cb(), self.accept()])
