import sys
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QGroupBox, QFormLayout, QDialog, QLineEdit, QTextEdit, QDoubleSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QCheckBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, Slot

def get_widget(parent, fc, utils, be, admin_ctx) -> QWidget:
    return ChargesConfigWidget(parent, fc, utils, be, admin_ctx)

class ChargesConfigWidget(QWidget):
    def __init__(self, parent, fc, utils, be, admin_ctx):
        super().__init__(parent)
        self.fc = fc
        self.utils = utils
        self.be = be
        self.admin_ctx = admin_ctx
        self.active_rates = {}

        self.setup_ui()
        self.load_active_rates()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_lbl = QLabel("TARIFF & RATE CONFIGURATION")
        title_lbl.setObjectName("page_title") # For styling
        header_layout.addWidget(title_lbl)
        
        refresh_btn = QPushButton("🔄 Refresh Rates")
        refresh_btn.clicked.connect(self.load_active_rates)
        header_layout.addWidget(refresh_btn, 0, Qt.AlignRight)
        layout.addLayout(header_layout)

        # Meta Info Label
        self.meta_lbl = QLabel("Loading active configuration...")
        self.meta_lbl.setStyleSheet("font-style: italic; color: #6c6a64;")
        layout.addWidget(self.meta_lbl)

        # Main Rate Display Area (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        self.rates_layout = QVBoxLayout(scroll_content)
        self.rates_layout.setSpacing(15)
        
        # We'll populate this in populate_rates_display
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 4) # weight 4

        # Buttons Row
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("✏️ Edit Rates")
        edit_btn.clicked.connect(self.show_edit_dialog)
        
        annual_btn = QPushButton("📈 Apply Annual 10% Increment")
        annual_btn.clicked.connect(self.apply_annual_increment)
        
        history_btn = QPushButton("📜 View Change History")
        history_btn.clicked.connect(self.show_history_dialog)

        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(annual_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(history_btn)
        layout.addLayout(btn_layout)

        # Live Bill Test Widget
        test_group = QGroupBox("Live Bill Test (Sandbox)")
        test_layout = QHBoxLayout(test_group)
        
        # Inputs Column
        inputs_widget = QWidget()
        inputs_layout = QFormLayout(inputs_widget)
        inputs_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.test_supply_type = QComboBox()
        self.test_supply_type.addItems(self.utils.WATER_SUPPLY_TYPE_OPTIONS)
        self.test_supply_type.currentTextChanged.connect(self.toggle_test_sewerage_fields)
        
        self.test_has_sewer = QCheckBox("Has Sewer Connection")
        self.test_has_sewer.stateChanged.connect(self.toggle_test_sewerage_fields)

        self.test_sub_cat = QComboBox()
        self.test_sub_cat.addItems(self.utils.SEWERAGE_SUB_CATEGORY_OPTIONS)
        self.test_sub_cat.currentTextChanged.connect(self.toggle_test_sewerage_fields)
        
        self.test_num_rooms = QSpinBox()
        self.test_num_rooms.setRange(0, 1000)
        
        self.test_plot_area = QDoubleSpinBox()
        self.test_plot_area.setRange(0, 10000)
        self.test_plot_area.setDecimals(2)
        self.test_plot_area.setSuffix(" sqm")

        self.test_category = QComboBox()
        self.test_category.addItems(self.utils.CATEGORY_OPTIONS)
        
        self.test_meter_size = QComboBox()
        self.test_meter_size.addItems(self.utils.METER_SIZE_OPTIONS)
        
        self.test_consumption = QDoubleSpinBox()
        self.test_consumption.setRange(0, 9999)
        self.test_consumption.setValue(20.0)
        self.test_consumption.setSuffix(" KL")
        
        self.test_last_pay_date = QLineEdit(self.utils.today_str())
        self.test_pay_date = QLineEdit(self.utils.today_str())

        inputs_layout.addRow("Water Supply Type:", self.test_supply_type)
        inputs_layout.addRow(self.test_has_sewer)
        inputs_layout.addRow("Sewerage Sub-Category:", self.test_sub_cat)
        inputs_layout.addRow("Number of Rooms:", self.test_num_rooms)
        inputs_layout.addRow("Plot Area:", self.test_plot_area)
        inputs_layout.addRow("Consumer Category:", self.test_category)
        inputs_layout.addRow("Meter Size:", self.test_meter_size)
        inputs_layout.addRow("Consumption:", self.test_consumption)
        inputs_layout.addRow("Last Payment Date:", self.test_last_pay_date)
        inputs_layout.addRow("Current Payment Date:", self.test_pay_date)

        calc_btn = QPushButton("⚡ Calculate Simulation")
        calc_btn.clicked.connect(self.run_simulation)
        inputs_layout.addRow(calc_btn)

        test_layout.addWidget(inputs_widget, 1)

        # Output Column
        self.test_table = QTableWidget(0, 2)
        self.test_table.setHorizontalHeaderLabels(["Line Item", "Amount"])
        self.test_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        test_layout.addWidget(self.test_table, 1)

        layout.addWidget(test_group, 3) # weight 3
        
        self.toggle_test_sewerage_fields()

    def toggle_test_sewerage_fields(self):
        is_own = self.test_supply_type.currentText() == "Own Supply"
        has_sewer = self.test_has_sewer.isChecked()
        sub = self.test_sub_cat.currentText()
        
        # Logic: Sub-category visible only if Own Supply + Has Sewer
        self.test_sub_cat.setEnabled(is_own and has_sewer)
        
        # Rooms visible only if Own Supply + Has Sewer + Hotel or Other Industrial
        self.test_num_rooms.setEnabled(is_own and has_sewer and sub in ["Hotel", "Other Industrial/Commercial"])
        
        # Plot area visible only if Own Supply + Has Sewer + Domestic
        self.test_plot_area.setEnabled(is_own and has_sewer and sub == "Domestic (Own Supply)")

    def load_active_rates(self):
        self.utils.run_in_thread(self.fc.get_charges_config, callback=self.populate_rates_display)

    def populate_rates_display(self, rates):
        self.active_rates = rates
        # Clear previous layout
        while self.rates_layout.count():
            item = self.rates_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Meta info
        m_by = rates.get("last_updated_by", "System")
        m_at = rates.get("last_updated_at", "N/A")
        m_note = rates.get("last_change_note", "N/A")
        self.meta_lbl.setText(f"Last updated: {m_at} by {m_by} — Note: {m_note}")

        # Domestic
        dom_group = QGroupBox("Domestic (15mm–25mm) — Slabs")
        dom_lay = QFormLayout(dom_group)
        dom_lay.addRow("Slab 0-8 KL:", QLabel(f"₹{rates.get('domestic_slab_a_rate', 0):.2f}"))
        dom_lay.addRow("Slab 8-15 KL:", QLabel(f"₹{rates.get('domestic_slab_b_rate', 0):.2f}"))
        dom_lay.addRow("Slab 15-40 KL:", QLabel(f"₹{rates.get('domestic_slab_c_rate', 0):.2f}"))
        dom_lay.addRow("Slab Above 40 KL:", QLabel(f"₹{rates.get('domestic_slab_d_rate', 0):.2f}"))
        dom_lay.addRow("Rural Flat Rate:", QLabel(f"₹{rates.get('domestic_flat_rural', 0):.2f}"))
        self.rates_layout.addWidget(dom_group)

        # Non-Domestic
        nd_group = QGroupBox("Non-Domestic (15mm–25mm) — Slabs")
        nd_lay = QFormLayout(nd_group)
        nd_lay.addRow("Slab 0-15 KL:", QLabel(f"₹{rates.get('nondomestic_slab_a_rate', 0):.2f}"))
        nd_lay.addRow("Slab 15-40 KL:", QLabel(f"₹{rates.get('nondomestic_slab_b_rate', 0):.2f}"))
        nd_lay.addRow("Slab Above 40 KL:", QLabel(f"₹{rates.get('nondomestic_slab_c_rate', 0):.2f}"))
        self.rates_layout.addWidget(nd_group)

        # Industrial
        ind_group = QGroupBox("Industrial (15mm–25mm) — Slabs")
        ind_lay = QFormLayout(ind_group)
        ind_lay.addRow("Slab 0-15 KL:", QLabel(f"₹{rates.get('industrial_slab_a_rate', 0):.2f}"))
        ind_lay.addRow("Slab 15-40 KL:", QLabel(f"₹{rates.get('industrial_slab_b_rate', 0):.2f}"))
        ind_lay.addRow("Slab Above 40 KL:", QLabel(f"₹{rates.get('industrial_slab_c_rate', 0):.2f}"))
        self.rates_layout.addWidget(ind_group)

        # Bulk
        bulk_group = QGroupBox("Bulk Connections (>25mm)")
        bulk_lay = QFormLayout(bulk_group)
        bulk_lay.addRow("Bulk Dom Rate:", QLabel(f"₹{rates.get('bulk_domestic_rate', 0):.2f}/KL"))
        bulk_lay.addRow("Bulk Non-Dom Rate:", QLabel(f"₹{rates.get('bulk_nondomestic_rate', 0):.2f}/KL"))
        bulk_lay.addRow("Bulk Ind Rate:", QLabel(f"₹{rates.get('bulk_industrial_rate', 0):.2f}/KL"))
        self.rates_layout.addWidget(bulk_group)

        # General
        gen_group = QGroupBox("General Charges")
        gen_lay = QFormLayout(gen_group)
        gen_lay.addRow("Fixed Dom:", QLabel(f"₹{rates.get('fixed_charge_domestic', 0):.2f}"))
        gen_lay.addRow("Meter Svc 15mm:", QLabel(f"₹{rates.get('meter_svc_15mm', 0):.2f}"))
        self.rates_layout.addWidget(gen_group)

        # Sewerage - NEW
        sew_group = QGroupBox("Sewerage Charges")
        sew_lay = QVBoxLayout(sew_group)
        
        phed_sub = QGroupBox("PHED Supply (% of water charges)")
        phed_lay = QFormLayout(phed_sub)
        phed_lay.addRow("Sewerage Tax %:", QLabel(f"{rates.get('sewerage_phed_pct', 0):.1f}%"))
        phed_lay.addRow("STP Charge %:", QLabel(f"{rates.get('sewerage_stp_pct', 0):.1f}%"))
        sew_lay.addWidget(phed_sub)
        
        own_sub = QGroupBox("Own Supply — Flat Rates (₹/month)")
        own_lay = QFormLayout(own_sub)
        own_lay.addRow("Hotel (per room):", QLabel(f"₹{rates.get('sewerage_own_hotel_per_room', 0):.2f}"))
        own_lay.addRow("Restaurant:", QLabel(f"₹{rates.get('sewerage_own_restaurant', 0):.2f}"))
        own_lay.addRow("Cinema:", QLabel(f"₹{rates.get('sewerage_own_cinema', 0):.2f}"))
        own_lay.addRow("Car/Truck Service:", QLabel(f"₹{rates.get('sewerage_own_car_truck_service', 0):.2f}"))
        own_lay.addRow("Scooter Service:", QLabel(f"₹{rates.get('sewerage_own_scooter_service', 0):.2f}"))
        own_lay.addRow("Other Industrial:", QLabel(f"₹{rates.get('sewerage_own_other_industrial', 0):.2f}"))
        own_lay.addRow("Domestic — Base:", QLabel(f"₹{rates.get('sewerage_own_domestic_base', 0):.2f}"))
        own_lay.addRow("Domestic — per 100sqm:", QLabel(f"₹{rates.get('sewerage_own_domestic_per_100sqmtr', 0):.2f}"))
        own_lay.addRow("Domestic — Threshold:", QLabel(f"{rates.get('sewerage_own_domestic_plot_threshold', 0):.0f} sqm"))
        sew_lay.addWidget(own_sub)
        
        self.rates_layout.addWidget(sew_group)
        self.rates_layout.addStretch()

    def run_simulation(self):
        try:
            cons = self.test_consumption.value()
            last_pay = self.utils.parse_date(self.test_last_pay_date.text())
            curr_pay = self.utils.parse_date(self.test_pay_date.text())
            
            mock_consumer = {
                "category": self.test_category.currentText(),
                "meter_size": self.test_meter_size.currentText(),
                "water_supply_type": self.test_supply_type.currentText(),
                "has_sewer_connection": self.test_has_sewer.isChecked(),
                "sewerage_sub_category": self.test_sub_cat.currentText(),
                "num_rooms": self.test_num_rooms.value(),
                "plot_area_sqmtr": self.test_plot_area.value(),
                "consumer_status": "Active"
            }
            
            res = self.be.calculate_bill(
                consumption_kl=cons,
                consumer=mock_consumer,
                rates=self.active_rates,
                previous_outstanding=0.0,
                credit_balance=0.0,
                last_payment_date=last_pay,
                payment_date=curr_pay
            )
            
            self.test_table.setRowCount(0)
            items = [
                ("Water Charge", res['water_charge']),
                ("Fixed Charge", res['fixed_charge']),
                ("Meter Svc Charge", res['meter_service_charge']),
                ("Sewerage Tax", res['sewerage_tax']),
                ("STP Charge", res['stp_charge']),
                ("IDS Charge", res['ids_charge']),
                ("LPS Amount", res['lps_amount']),
                ("Total Amount", res['total_amount'])
            ]
            for row_idx, (name, val) in enumerate(items):
                self.test_table.insertRow(row_idx)
                self.test_table.setItem(row_idx, 0, QTableWidgetItem(name))
                self.test_table.setItem(row_idx, 1, QTableWidgetItem(self.utils.format_currency(val)))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Simulation failed: {str(e)}")

    def show_edit_dialog(self):
        dlg = EditRatesDialog(self, self.fc, self.utils, self.active_rates, self.admin_ctx)
        if dlg.exec():
            self.load_active_rates()

    def apply_annual_increment(self):
        confirm = QMessageBox.question(
            self, "Confirm Increment",
            "This will multiply all numeric water tariff rates by 1.10 representing the annual April increment.\n\n"
            "NOTE: Sewerage and STP rates are excluded from this increment.\n\n"
            "This cannot be undone. Proceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.utils.run_in_thread(
                self.fc.apply_annual_increment,
                self.admin_ctx["name"],
                callback=lambda _: (QMessageBox.information(self, "Success", "Annual increment applied."), self.load_active_rates())
            )

    def show_history_dialog(self):
        HistoryDialog(self, self.fc, self.utils).exec()

class EditRatesDialog(QDialog):
    def __init__(self, parent, fc, utils, current_rates, admin_ctx):
        super().__init__(parent)
        self.fc = fc
        self.utils = utils
        self.current_rates = current_rates
        self.admin_ctx = admin_ctx
        self.setWindowTitle("Edit Tariff Config & Rates")
        self.setMinimumSize(700, 800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form = QFormLayout(container)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.spinboxes = {}
        
        # Define fields to create
        groups = [
            ("Domestic Slabs", [
                ("domestic_slab_a_rate", "Slab 0-8 KL (₹/KL)"),
                ("domestic_slab_b_rate", "Slab 8-15 KL (₹/KL)"),
                ("domestic_slab_c_rate", "Slab 15-40 KL (₹/KL)"),
                ("domestic_slab_d_rate", "Slab Above 40 KL (₹/KL)"),
                ("domestic_flat_rural", "Rural Flat Rate (₹)"),
                ("domestic_min_15mm_avg_low", "Min 15mm Avg<=8 (₹)"),
                ("domestic_min_15mm_avg_high", "Min 15mm Avg>8 (₹)"),
            ]),
            ("Sewerage Charges", [
                ("sewerage_phed_pct", "PHED Sewerage Tax (%)"),
                ("sewerage_stp_pct", "STP Charge (%)"),
                ("sewerage_own_hotel_per_room", "Own: Hotel (₹/room)"),
                ("sewerage_own_restaurant", "Own: Restaurant (₹)"),
                ("sewerage_own_cinema", "Own: Cinema (₹)"),
                ("sewerage_own_car_truck_service", "Own: Car/Truck Svc (₹)"),
                ("sewerage_own_scooter_service", "Own: Scooter Svc (₹)"),
                ("sewerage_own_other_industrial", "Own: Other Ind/Comm (₹)"),
                ("sewerage_own_domestic_base", "Own: Domestic Base (₹)"),
                ("sewerage_own_domestic_per_100sqmtr", "Own: Dom per 100sqm (₹)"),
                ("sewerage_own_domestic_plot_threshold", "Own: Dom Threshold (sqm)"),
            ]),
            ("General Charges", [
                ("fixed_charge_domestic", "Fixed: Domestic (₹)"),
                ("meter_svc_15mm", "Meter Svc: 15mm (₹)"),
            ])
        ]
        
        for g_name, fields in groups:
            group_box = QGroupBox(g_name)
            g_lay = QFormLayout(group_box)
            for key, label in fields:
                sb = QDoubleSpinBox()
                sb.setRange(0, 9999999)
                sb.setDecimals(4)
                sb.setValue(float(self.current_rates.get(key, 0)))
                g_lay.addRow(label, sb)
                self.spinboxes[key] = sb
            form.addRow(group_box)
            
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Footer
        footer = QFormLayout()
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Required: Reason for change...")
        footer.addRow("Change Note <span style='color:#E8913A'>*</span>:", self.note_edit)
        layout.addLayout(footer)
        
        btn_box = QHBoxLayout()
        save_btn = QPushButton("💾 Save Changes")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

    def save(self):
        note = self.note_edit.text().strip()
        if not note:
            QMessageBox.warning(self, "Required", "Change note is mandatory.")
            return
            
        new_rates = dict(self.current_rates)
        diff_text = "<b>Review Changes:</b><br><br>"
        changes_found = False
        
        for k, sb in self.spinboxes.items():
            new_v = sb.value()
            old_v = float(self.current_rates.get(k, 0))
            if abs(new_v - old_v) > 0.00001:
                diff_text += f"• {k}: {old_v} ➔ {new_v}<br>"
                new_rates[k] = new_v
                changes_found = True
        
        if not changes_found:
            self.reject()
            return

        confirm = QMessageBox.question(self, "Confirm Changes", diff_text + "<br>Save these updates?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            def run():
                new_rates["last_change_note"] = note
                self.fc.update_charges_config(new_rates, self.admin_ctx["name"], note)

            self.utils.run_in_thread(run, callback=lambda _: self.accept(), error_callback=lambda e: QMessageBox.critical(self, "Error", str(e)))

class HistoryDialog(QDialog):
    def __init__(self, parent, fc, utils):
        super().__init__(parent)
        self.fc = fc
        self.utils = utils
        self.setWindowTitle("Charges Change History")
        self.resize(800, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Date", "Admin", "Note"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        self.utils.run_in_thread(self.fc.get_charges_config_history, callback=self.populate)

    def populate(self, history):
        self.table.setRowCount(0)
        for h in history:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(self.utils.format_date(h.get("changed_at"))))
            self.table.setItem(row, 1, QTableWidgetItem(h.get("changed_by", "Unknown")))
            self.table.setItem(row, 2, QTableWidgetItem(h.get("admin_note", "")))
