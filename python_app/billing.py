import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import os

def get_frame(parent, fc, utils, be, admin) -> ttk.Frame:
    frame = ttk.Frame(parent)
    
    # Title and Refresh row
    header = ttk.Frame(frame)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
    ttk.Label(header, text="Billing Cycles", style="Title.TLabel").pack(side="left")
    ttk.Button(header, text="🔄 Refresh Cycles", style="Primary.TButton", command=lambda: build_active_tab(active_tab, fc, utils, be, admin, refresh=True)).pack(side="right")

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    notebook = ttk.Notebook(frame)
    notebook.grid(row=1, column=0, sticky="nsew")
    
    # Tab 1: Active Cycles
    active_tab = ttk.Frame(notebook, padding=10)
    notebook.add(active_tab, text="💳 Active Cycles")
    
    # Tab 2: Initiate New Cycle
    init_tab = ttk.Frame(notebook, padding=10)
    notebook.add(init_tab, text="➕ Initiate Cycle")
    
    # Tab 3: CSD Sheet Print
    print_tab = ttk.Frame(notebook, padding=10)
    notebook.add(print_tab, text="🖨️ Print CSD Sheets")
    
    # Tab 4: Past Cycles
    past_tab = ttk.Frame(notebook, padding=10)
    notebook.add(past_tab, text="📜 Past Cycles History")
    
    # Setup tabs
    build_active_tab(active_tab, fc, utils, be, admin)
    build_initiate_tab(init_tab, fc, utils, be, admin, notebook, active_tab, print_tab)
    build_print_tab(print_tab, fc, utils, be, admin)
    build_past_tab(past_tab, fc, utils, be, admin)
    
    return frame

# ----------------------------------------------------
# TAB 1: Active Cycles
# ----------------------------------------------------
def build_active_tab(tab, fc, utils, be, admin, refresh=False):
    for w in tab.winfo_children():
        w.destroy()

    if refresh:
        fc.clear_cache("open_cycles")

    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(1, weight=1)

    ttk.Label(tab, text="Open Billing Cycles", style="Header.TLabel", foreground=utils.UI_COLORS["primary"]).grid(row=0, column=0, sticky="w", pady=(0, 10))
    
    tree_columns = ("cycle_id", "zones", "start_date", "end_date", "last_pay", "progress", "skipped")
    tree = ttk.Treeview(tab, columns=tree_columns, show="headings", height=6)
    tree.heading("cycle_id", text="Cycle ID")
    tree.heading("zones", text="Zones")
    tree.heading("start_date", text="Start Date")
    tree.heading("end_date", text="End Date")
    tree.heading("last_pay", text="Last Pay By")
    tree.heading("progress", text="Progress (Read/Total)")
    tree.heading("skipped", text="Skipped")
    
    tree.column("cycle_id", width=120, anchor="center")
    tree.column("zones", width=100, anchor="w")
    tree.column("start_date", width=80, anchor="center")
    tree.column("end_date", width=80, anchor="center")
    tree.column("last_pay", width=80, anchor="center")
    tree.column("progress", width=140, anchor="center")
    tree.column("skipped", width=70, anchor="center")
    
    tree_container = ttk.Frame(tab)
    tree_container.grid(row=1, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree_container.grid_columnconfigure(0, weight=1)
    tree_container.grid_rowconfigure(0, weight=1)
    
    cycles_list = []
    
    def load_active():
        for r in tree.get_children():
            tree.delete(r)
            
        def fetch():
            cycles = fc.get_open_cycles()
            rows = []
            for c in cycles:
                # Calculate progress metrics
                c_id = c["cycle_id"]
                zones = c["zones"]
                
                # Fetch readings for this cycle
                readings = fc.get_readings_for_cycle(c_id)
                finalized_count = len([r for r in readings if r.get("status") == "finalized"])
                skipped_count = len([r for r in readings if r.get("status") == "skipped"])
                
                # Compute total consumers in these zones
                tot_c = sum(c.get("consumer_count_per_zone", {}).values())
                
                rows.append({
                    "cycle": c,
                    "finalized": finalized_count,
                    "skipped": skipped_count,
                    "total": tot_c
                })
            return rows
            
        def done(rows):
            nonlocal cycles_list
            cycles_list = rows
            for row in rows:
                c = row["cycle"]
                prog_str = f"{row['finalized']} of {row['total']} consumers"
                tree.insert("", "end", values=(
                    c["cycle_id"],
                    str(c["zones"]),
                    c["start_date"],
                    c["end_date"],
                    c["last_payment_date"],
                    prog_str,
                    row["skipped"]
                ), iid=c["cycle_id"])
                
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    # Actions on selection
    action_frame = ttk.Frame(tab, padding=10)
    action_frame.grid(row=2, column=0, sticky="ew", pady=10)
    
    def close_cycle_action():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Please select an active cycle from the list to close.", parent=tab)
            return
            
        cycle_id = sel[0]
        c_item = next((row for row in cycles_list if row["cycle"]["cycle_id"] == cycle_id), None)
        if not c_item:
            return
            
        # Gather metrics for checklist popup
        pending_c = max(0, c_item["total"] - (c_item["finalized"] + c_item["skipped"]))
        
        # Calculate totals
        def fetch_financials():
            summary = fc.get_billing_summary(cycle_id)
            return summary
            
        def on_financials(summary):
            # Show Checklist dialog
            checklist = tk.Toplevel(tab)
            checklist.title(f"Billing Cycle Close Checklist — {cycle_id}")
            checklist.geometry("450x320")
            checklist.grab_set()
            
            ttk.Label(checklist, text=f"Verify Status for Cycle: {cycle_id}", font=("Segoe UI", 12, "bold"), foreground="#1a3a6b").pack(pady=10)
            
            f = ttk.Frame(checklist, padding=15)
            f.pack(fill="both", expand=True)
            
            # Displays
            ttk.Label(f, text=f"• Pending Readings: {pending_c}", font=("Segoe UI", 10, "bold") if pending_c > 0 else ("Segoe UI", 10)).pack(anchor="w", pady=2)
            ttk.Label(f, text=f"• Skipped / Cannot Read: {c_item['skipped']}", font=("Segoe UI", 10)).pack(anchor="w", pady=2)
            ttk.Label(f, text=f"• Total Billed Amount: {utils.format_currency(summary['total_billed'])}", font=("Segoe UI", 10)).pack(anchor="w", pady=2)
            ttk.Label(f, text=f"• Total Collected Amount: {utils.format_currency(summary['total_collected'])}", font=("Segoe UI", 10)).pack(anchor="w", pady=2)
            ttk.Label(f, text=f"• Net Outstanding Balance: {utils.format_currency(summary['total_outstanding'])}", font=("Segoe UI", 10, "bold") if summary['total_outstanding'] > 0 else ("Segoe UI", 10)).pack(anchor="w", pady=2)
            
            warning_txt = ""
            if pending_c > 0:
                warning_txt = "⚠️ WARNING: Closing this cycle will lock the cycle despite pending readings. Unfinished zones will be freed."
                
            warn_lbl = ttk.Label(f, text=warning_txt, foreground="orange", font=("Segoe UI", 9, "bold"), wrap=380)
            warn_lbl.pack(pady=10)
            
            def confirm_close():
                confirm = messagebox.askyesno("Confirm Close", "Are you sure you want to permanently close this billing cycle?", parent=checklist)
                if not confirm:
                    return
                    
                def close():
                    fc.close_billing_cycle(cycle_id, admin["name"])
                    
                def closed(res):
                    messagebox.showinfo("Success", f"Billing cycle {cycle_id} closed successfully.", parent=tab)
                    checklist.destroy()
                    load_active()
                    # Trigger callbacks on other tabs
                    if hasattr(tab, "on_cycles_changed"):
                        tab.on_cycles_changed()
                        
                def fail(err):
                    messagebox.showerror("Error", f"Failed closing cycle:\n{err}", parent=checklist)
                    
                utils.run_in_thread(close, callback=closed, error_callback=fail, widget=checklist)
                
            ttk.Button(checklist, text="🔒 Complete and Close Cycle", command=confirm_close).pack(pady=15)
            
        utils.run_in_thread(fetch_financials, callback=on_financials, widget=tab)

    ttk.Button(action_frame, text="🔒 Close Selected Cycle", command=close_cycle_action).pack(side="left")
    
    # Store refresh handle
    tab.refresh_active = load_active
    load_active()

# ----------------------------------------------------
# TAB 2: Initiate New Cycle
# ----------------------------------------------------
def build_initiate_tab(tab, fc, utils, be, admin, notebook, active_tab, print_tab):
    f = ttk.Frame(tab, padding=30)
    f.pack(fill="both", expand=True)
    
    ttk.Label(f, text="INITIATE NEW BILLING CYCLE", style="KPITitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 25))
    
    # Zone selector Frame
    ttk.Label(f, text="Select Zone(s)*", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="nw", pady=5)
    zone_frame = ttk.Frame(f, style="Card.TFrame", padding=15)
    zone_frame.grid(row=1, column=1, sticky="w", pady=5)
    
    zone_vars = {}
    zone_checkboxes = {}
    
    # Grid: 4 rows x 5 columns = 20 checkboxes
    for z in utils.ZONE_RANGE:
        var = tk.BooleanVar(value=False)
        r = (z - 1) // 5
        c = (z - 1) % 5
        chk = ttk.Checkbutton(zone_frame, text=f"Zone {z}", variable=var)
        chk.grid(row=r, column=c, sticky="w", padx=8, pady=3)
        zone_vars[z] = var
        zone_checkboxes[z] = chk
        
    # Date fields
    ttk.Label(f, text="Start Date (DD-MM-YYYY):*").grid(row=2, column=0, sticky="w", pady=5)
    start_ent = ttk.Entry(f, width=15)
    start_ent.grid(row=2, column=1, sticky="w", pady=5)
    start_ent.insert(0, utils.today_str())
    
    ttk.Label(f, text="End Date (DD-MM-YYYY):*").grid(row=3, column=0, sticky="w", pady=5)
    end_ent = ttk.Entry(f, width=15)
    end_ent.grid(row=3, column=1, sticky="w", pady=5)
    
    # Grace Period radio
    ttk.Label(f, text="Grace Period:*").grid(row=4, column=0, sticky="w", pady=5)
    grace_var = tk.IntVar(value=1)
    grace_f = ttk.Frame(f)
    grace_f.grid(row=4, column=1, sticky="w", pady=5)
    ttk.Radiobutton(grace_f, text="1 Month", variable=grace_var, value=1).pack(side="left", padx=5)
    ttk.Radiobutton(grace_f, text="2 Months", variable=grace_var, value=2).pack(side="left", padx=5)
    
    # Preview Frame
    prev_frame = ttk.Frame(f, style="Card.TFrame", padding=20)
    prev_frame.grid(row=5, column=1, sticky="w", pady=25)
    ttk.Label(prev_frame, text="LIVE CYCLE PREVIEW", style="KPITitle.TLabel").pack(anchor="w", pady=(0, 10))
    
    c_count_lbl = ttk.Label(prev_frame, text="Consumers selected: 0", font=("Segoe UI", 9, "bold"))
    c_count_lbl.pack(anchor="w")
    
    pay_date_lbl = ttk.Label(prev_frame, text="Last Payment Date: —", font=("Segoe UI", 11, "bold"), foreground="#1a3a6b")
    pay_date_lbl.pack(anchor="w", pady=5)
    
    def refresh_locked_zones():
        # Get active cycle zones and disable checkbuttons
        def fetch():
            return fc.get_open_cycle_zones()
            
        def done(active_zones):
            for z, chk in zone_checkboxes.items():
                if z in active_zones:
                    chk.config(state="disabled", text=f"Z{z} (Active)")
                    zone_vars[z].set(False)
                else:
                    chk.config(state="normal", text=f"Zone {z}")
            update_preview()
            
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    def update_preview(*args):
        # Update consumer count
        sel_zones = [z for z, var in zone_vars.items() if var.get()]
        
        def count():
            tot = 0
            for z in sel_zones:
                tot += len(fc.list_consumers({"zone": z, "is_active": True}))
            return tot
            
        def done(tot):
            c_count_lbl.config(text=f"Consumers selected: {tot}")
            
        if sel_zones:
            utils.run_in_thread(count, callback=done, widget=tab)
        else:
            c_count_lbl.config(text="Consumers selected: 0")
            
        # Update calculated last payment date
        end_d_str = end_ent.get().strip()
        g_months = grace_var.get()
        
        try:
            end_d = utils.parse_date(end_d_str)
            last_pay_d = utils.add_months(end_d, g_months)
            pay_date_lbl.config(text=f"Last Payment Date: {utils.format_date(last_pay_d)}")
        except Exception:
            pay_date_lbl.config(text="Last Payment Date: — (enter valid end date)")
            
    # Bind preview triggers
    end_ent.bind("<KeyRelease>", update_preview)
    grace_var.trace_add("write", update_preview)
    for var in zone_vars.values():
        var.trace_add("write", update_preview)
        
    def initiate_cycle():
        zones = [z for z, var in zone_vars.items() if var.get()]
        start_d = start_ent.get().strip()
        end_d = end_ent.get().strip()
        grace = grace_var.get()
        
        if not zones:
            messagebox.showerror("Error", "Please select at least one zone.", parent=tab)
            return
        if not start_d or not end_d:
            messagebox.showerror("Error", "Please fill start and end dates.", parent=tab)
            return
            
        try:
            d_start = utils.parse_date(start_d)
            d_end = utils.parse_date(end_d)
            if d_end <= d_start:
                messagebox.showerror("Error", "End date must be after start date.", parent=tab)
                return
        except Exception:
            messagebox.showerror("Error", "Invalid date formatting.", parent=tab)
            return
            
        last_pay = utils.add_months(d_end, grace)
        last_pay_str = utils.format_date(last_pay)
        
        confirm_text = f"Cycle Details Summary:\n\n" \
                       f"• Zones: {zones}\n" \
                       f"• Period: {start_d} to {end_d}\n" \
                       f"• Grace Months: {grace}\n" \
                       f"• Calculated Last Pay Date: {last_pay_str}\n\n" \
                       f"Confirm initiating this cycle?"
                       
        confirm = messagebox.askyesno("Confirm Cycle Initiation", confirm_text, parent=tab)
        if not confirm:
            return
            
        payload = {
            "zones": zones,
            "start_date": start_d,
            "end_date": end_d,
            "last_payment_date": last_pay_str,
            "grace_period_months": grace
        }
        
        def run():
            return fc.create_billing_cycle(payload, admin["name"])
            
        def done(cycle_id):
            messagebox.showinfo("Success", f"Billing Cycle {cycle_id} initiated successfully.", parent=tab)
            # Clear fields
            for var in zone_vars.values():
                var.set(False)
            end_ent.delete(0, "end")
            
            # Refresh layouts
            refresh_locked_zones()
            active_tab.refresh_active()
            build_print_tab(print_tab, fc, utils, be, admin)
            
            notebook.select(0)
            
        def fail(err):
            messagebox.showerror("Initiation Failed", f"Error:\n{err}", parent=tab)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=tab)

    ttk.Button(f, text="💳 INITIATE BILLING CYCLE", command=initiate_cycle, style="Primary.TButton").grid(row=6, column=1, sticky="w", pady=10)
    
    # Store refresh
    tab.on_cycles_changed = refresh_locked_zones
    refresh_locked_zones()

# ----------------------------------------------------
# TAB 3: CSD Sheet Print
# ----------------------------------------------------
def build_print_tab(tab, fc, utils, be, admin):
    for w in tab.winfo_children():
        w.destroy()
        
    ttk.Label(tab, text="Generate CSD Field Sheets PDF", style="Header.TLabel", foreground="#1a3a6b").pack(anchor="w", pady=(0, 10))
    ttk.Label(tab, text="Generate printouts of Consumer Static Data with blank fields for manual reading recording.").pack(anchor="w", pady=(0, 15))
    
    f = ttk.Frame(tab, padding=10)
    f.pack(fill="x")
    
    # Active Cycles combo
    ttk.Label(f, text="Select Active Cycle:").grid(row=0, column=0, sticky="w", pady=5)
    cycle_var = tk.StringVar()
    cycle_cb = ttk.Combobox(f, textvariable=cycle_var, state="readonly", width=25)
    cycle_cb.grid(row=0, column=1, sticky="w", pady=5, padx=10)
    
    # Zone selector Frame
    ttk.Label(f, text="Select Zone:").grid(row=1, column=0, sticky="w", pady=5)
    zone_var = tk.StringVar()
    zone_cb = ttk.Combobox(f, textvariable=zone_var, state="readonly", width=10)
    zone_cb.grid(row=1, column=1, sticky="w", pady=5, padx=10)
    
    prog_bar = ttk.Progressbar(f, orient="horizontal", mode="determinate", length=300)
    status_lbl = ttk.Label(f, text="", font=("Segoe UI", 9, "italic"))
    
    def on_cycle_selected(event):
        c_id = cycle_var.get()
        if not c_id:
            return
            
        def fetch():
            return fc.get_billing_cycle(c_id)
            
        def done(cycle_data):
            if cycle_data:
                zones = cycle_data.get("zones", [])
                zone_cb.config(values=[str(z) for z in zones])
                if zones:
                    zone_cb.set(str(zones[0]))
            update_print_preview()
            
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    cycle_cb.bind("<<ComboboxSelected>>", on_cycle_selected)
    
    def update_print_preview(*args):
        c_id = cycle_var.get()
        z = zone_var.get()
        if not c_id or not z:
            status_lbl.config(text="Select cycle and zone to preview.")
            return
            
        def count():
            return len(fc.list_consumers({"zone": int(z), "is_active": True}))
            
        def done(tot):
            status_lbl.config(text=f"Ready to print {tot} consumer records for Zone {z}.")
            
        utils.run_in_thread(count, callback=done, widget=tab)
        
    zone_cb.bind("<<ComboboxSelected>>", update_print_preview)
    
    # Load cycles initially
    def load_active_cycles():
        def fetch():
            return fc.get_open_cycles()
            
        def done(cycles):
            cycle_cb.config(values=[c["cycle_id"] for c in cycles])
            if cycles:
                cycle_cb.set(cycles[0]["cycle_id"])
                on_cycle_selected(None)
                
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    load_active_cycles()
    
    # PDF generation logic
    def generate_pdf(save_as_path=None):
        c_id = cycle_var.get()
        z = zone_var.get()
        if not c_id or not z:
            messagebox.showerror("Error", "Please select a cycle and zone.", parent=tab)
            return
            
        prog_bar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        prog_bar["value"] = 10
        status_lbl.config(text="Fetching consumer data...")
        
        def run():
            cycle_data = fc.get_billing_cycle(c_id)
            consumers = fc.list_consumers({"zone": int(z), "is_active": True})
            
            prog_bar["value"] = 40
            status_lbl.config(text=f"Loaded {len(consumers)} profiles. Rendering templates...")
            
            # Load template
            html_tmpl = utils.load_pdf_template("csd_sheet")
            
            combined_html = ""
            for idx, c in enumerate(consumers):
                c_rows = ""
                for k, v in c.get("custom_attributes", {}).items():
                    c_rows += f"<tr><td class='label'>{k}</td><td class='value' colspan='3'>{v}</td></tr>"
                    
                html = html_tmpl.replace("{{cin_no}}", c["cin_no"])\
                                .replace("{{name}}", c["name"])\
                                .replace("{{zone}}", str(c["zone"]))\
                                .replace("{{category}}", c["category"])\
                                .replace("{{meter_size}}", c["meter_size"])\
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
                                
                if idx < len(consumers) - 1:
                    # Append page break
                    html = html.replace("</body>", "<div style='page-break-after: always;'></div></body>")
                    
                combined_html += html
                
            prog_bar["value"] = 80
            status_lbl.config(text="Compiling PDF via WeasyPrint...")
            
            pdf_bytes = utils.render_pdf_to_bytes(combined_html)
            
            output_path = save_as_path
            if not output_path:
                output_path = os.path.join(os.environ.get("TEMP", "."), f"csd_zone_{z}_{c_id}.pdf")
                
            with open(output_path, "wb") as f_out:
                f_out.write(pdf_bytes)
                
            prog_bar["value"] = 100
            return output_path
            
        def done(pdf_path):
            prog_bar.grid_remove()
            status_lbl.config(text="PDF Generated successfully.")
            utils.open_pdf(pdf_path)
            
        def fail(err):
            prog_bar.grid_remove()
            status_lbl.config(text="Generation failed.")
            messagebox.showerror("Error", f"Failed generating PDF sheet:\n{err}", parent=tab)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=tab)

    ttk.Button(f, text="🖨️ Generate & Open PDF", command=lambda: generate_pdf()).grid(row=2, column=1, sticky="w", pady=15, padx=10)
    
    def save_as_action():
        c_id = cycle_var.get()
        z = zone_var.get()
        if not c_id or not z:
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="Save CSD Sheets PDF")
        if path:
            generate_pdf(path)
            
    ttk.Button(f, text="💾 Save CSD PDF As...", command=save_as_action).grid(row=2, column=2, sticky="w", pady=15)
    
    status_lbl.grid(row=4, column=0, columnspan=3, sticky="w", pady=5)

# ----------------------------------------------------
# TAB 4: Past Cycles
# ----------------------------------------------------
def build_past_tab(tab, fc, utils, be, admin):
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(1, weight=1)

    ttk.Label(tab, text="Closed Billing Cycles History", style="Header.TLabel", foreground="#1a3a6b").grid(row=0, column=0, sticky="w", pady=(0, 10))
    
    tree_frame = ttk.Frame(tab)
    tree_frame.grid(row=1, column=0, sticky="nsew")
    
    tree_columns = ("cycle_id", "zones", "period", "last_pay", "closed_at")
    tree = ttk.Treeview(tree_frame, columns=tree_columns, show="headings")
    tree.heading("cycle_id", text="Cycle ID")
    tree.heading("zones", text="Zones")
    tree.heading("period", text="Billing Period")
    tree.heading("last_pay", text="Last Pay By")
    tree.heading("closed_at", text="Closed At")
    
    tree.column("cycle_id", width=120, anchor="center")
    tree.column("zones", width=100)
    tree.column("period", width=150, anchor="center")
    tree.column("last_pay", width=100, anchor="center")
    tree.column("closed_at", width=120, anchor="center")
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)
    
    # Detail summary below
    summary_f = ttk.LabelFrame(tab, text="Selected Cycle Summary Breakdown", padding=10)
    summary_f.grid(row=2, column=0, sticky="ew", pady=10)
    
    sum_lbl = ttk.Label(summary_f, text="Select a past cycle row above to view consolidated billing metrics.", font=("Segoe UI", 9, "italic"))
    sum_lbl.pack(anchor="w")
    
    cycles_cache = {}
    
    def load_past():
        for r in tree.get_children():
            tree.delete(r)
            
        def fetch():
            return fc.list_billing_cycles("closed")
            
        def done(cycles):
            for c in cycles:
                cycles_cache[c["cycle_id"]] = c
                tree.insert("", "end", values=(
                    c["cycle_id"],
                    str(c["zones"]),
                    f"{c['start_date']} to {c['end_date']}",
                    c["last_payment_date"],
                    utils.format_date(c.get("closed_at"))
                ), iid=c["cycle_id"])
                
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    def on_row_select(event):
        sel = tree.selection()
        if not sel:
            return
        c_id = sel[0]
        c = cycles_cache.get(c_id)
        if not c:
            return
            
        sum_lbl.config(text="Retrieving financial summaries...")
        
        def fetch():
            return fc.get_billing_summary(c_id)
            
        def done(summary):
            tot_c = sum(c.get("consumer_count_per_zone", {}).values())
            res_txt = f"• Total Billed Amount : {utils.format_currency(summary['total_billed'])}\n" \
                      f"• Total Payments In    : {utils.format_currency(summary['total_collected'])}\n" \
                      f"• Outstanding Deficit  : {utils.format_currency(summary['total_outstanding'])}\n" \
                      f"• Total Consumers Count: {tot_c} registered in zones {c['zones']}"
            sum_lbl.config(text=res_txt, font=("Courier New", 9))
            
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    tree.bind("<<TreeviewSelect>>", on_row_select)
    load_past()
