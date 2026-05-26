import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl
from datetime import datetime, date
import os

def get_frame(parent, fc, utils, be, admin) -> ttk.Frame:
    frame = ttk.Frame(parent)
    
    # Title and Refresh row
    header = ttk.Frame(frame)
    header.pack(fill="x", pady=(0, 20))
    ttk.Label(header, text="Payments & Adjustments", style="Title.TLabel").pack(side="left")
    ttk.Button(header, text="🔄 Refresh Data", style="Primary.TButton", command=lambda: fc.clear_cache()).pack(side="right")

    notebook = ttk.Notebook(frame)
    notebook.pack(fill="both", expand=True)
    
    # Tab 1: Record Payment
    record_tab = ttk.Frame(notebook, padding=10)
    notebook.add(record_tab, text="💰 Record Payment")
    
    # Tab 2: Bulk Import Payments
    import_tab = ttk.Frame(notebook, padding=10)
    notebook.add(import_tab, text="📥 Bulk Import")
    
    # Tab 3: Payment Log
    log_tab = ttk.Frame(notebook, padding=10)
    notebook.add(log_tab, text="📜 Payment Log")
    
    # Tab 4: LPS Waiver
    waiver_tab = ttk.Frame(notebook, padding=10)
    notebook.add(waiver_tab, text="🏳️ LPS Waiver")
    
    # Tab 5: Credit Balance
    credit_tab = ttk.Frame(notebook, padding=10)
    notebook.add(credit_tab, text="🪙 Credit Balance")
    
    build_record_tab(record_tab, fc, utils, be, admin, frame)
    build_import_tab(import_tab, fc, utils, be, admin)
    build_log_tab(log_tab, fc, utils, be, admin)
    build_waiver_tab(waiver_tab, fc, utils, be, admin)
    build_credit_tab(credit_tab, fc, utils, be, admin)
    
    return frame

# ----------------------------------------------------
# TAB 1: Record Payment & Receipt Printing
# ----------------------------------------------------
def build_record_tab(tab, fc, utils, be, admin, main_frame):
    f = ttk.Frame(tab, padding=30)
    f.pack(fill="both", expand=True)
    
    # Left Form, Right Consumer Preview
    left_f = ttk.Frame(f)
    left_f.grid(row=0, column=0, sticky="n", padx=10)
    
    right_f = ttk.Frame(f, style="Card.TFrame", padding=25)
    right_f.grid(row=0, column=1, sticky="n", padx=20)
    ttk.Label(right_f, text="CONSUMER BALANCES", style="KPITitle.TLabel").pack(anchor="w", pady=(0, 15))
    
    ttk.Label(left_f, text="RECORD NEW PAYMENT", style="KPITitle.TLabel").pack(anchor="w", pady=(0, 20))
    
    form_f = ttk.Frame(left_f)
    form_f.pack(fill="x")
    
    # Form variables
    fields = {}
    debounce_id = [None]
    target_consumer = [None]
    
    # Grid form
    r = 0
    ttk.Label(form_f, text="CIN Number:*").grid(row=r, column=0, sticky="w", pady=4)
    cin_ent = ttk.Entry(form_f, width=22)
    cin_ent.grid(row=r, column=1, sticky="w", pady=4, padx=5)
    r += 1
    
    ttk.Label(form_f, text="Amount (₹):*").grid(row=r, column=0, sticky="w", pady=4)
    fields["amount"] = ttk.Entry(form_f, width=15)
    fields["amount"].grid(row=r, column=1, sticky="w", pady=4, padx=5)
    r += 1
    
    ttk.Label(form_f, text="Payment Mode:*").grid(row=r, column=0, sticky="w", pady=4)
    mode_var = tk.StringVar(value="Cash")
    mode_cb = ttk.Combobox(form_f, textvariable=mode_var, values=["Cash", "E-Mitra"], state="readonly", width=12)
    mode_cb.grid(row=r, column=1, sticky="w", pady=4, padx=5)
    r += 1
    
    ttk.Label(form_f, text="E-Mitra key:").grid(row=r, column=0, sticky="w", pady=4)
    emitra_ent = ttk.Entry(form_f, width=25, state="disabled")
    emitra_ent.grid(row=r, column=1, sticky="w", pady=4, padx=5)
    r += 1
    
    def on_mode_changed(event):
        if mode_var.get() == "E-Mitra":
            emitra_ent.config(state="normal")
        else:
            emitra_ent.delete(0, "end")
            emitra_ent.config(state="disabled")
            
    mode_cb.bind("<<ComboboxSelected>>", on_mode_changed)
    
    ttk.Label(form_f, text="Payment Date (DD-MM-YYYY):*").grid(row=r, column=0, sticky="w", pady=4)
    fields["pay_date"] = ttk.Entry(form_f, width=15)
    fields["pay_date"].grid(row=r, column=1, sticky="w", pady=4, padx=5)
    fields["pay_date"].insert(0, utils.today_str())
    r += 1
    
    ttk.Label(form_f, text="Cycle ID (Optional):").grid(row=r, column=0, sticky="w", pady=4)
    cycle_var = tk.StringVar()
    cycle_cb = ttk.Combobox(form_f, textvariable=cycle_var, state="readonly", width=18)
    cycle_cb.grid(row=r, column=1, sticky="w", pady=4, padx=5)
    r += 1
    
    def refresh_cycles():
        def fetch():
            return fc.list_billing_cycles(use_cache=True)
        def done(cycles):
            cycle_cb.config(values=[""] + [c["cycle_id"] for c in cycles])
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    refresh_cycles()
    
    ttk.Label(form_f, text="Remarks / Notes:").grid(row=r, column=0, sticky="w", pady=4)
    fields["notes"] = ttk.Entry(form_f, width=30)
    fields["notes"].grid(row=r, column=1, sticky="w", pady=4, padx=5)
    r += 1
    
    # Right panel consumer views
    c_name_lbl = ttk.Label(right_f, text="Name: —", font=("Segoe UI", 10, "bold"))
    c_name_lbl.pack(anchor="w", pady=2)
    
    c_out_lbl = ttk.Label(right_f, text="Outstanding: —", foreground="#c0392b", font=("Segoe UI", 9, "bold"))
    c_out_lbl.pack(anchor="w", pady=2)
    
    c_cred_lbl = ttk.Label(right_f, text="Credit Balance: —", foreground="#2a7a2a", font=("Segoe UI", 9, "bold"))
    c_cred_lbl.pack(anchor="w", pady=2)
    
    # LPS Preview Label
    lps_prev_lbl = ttk.Label(left_f, text="LPS Preview: —", font=("Segoe UI", 9, "italic"), foreground="orange")
    lps_prev_lbl.pack(anchor="w", pady=10)
    
    def update_lps_preview(*args):
        c = target_consumer[0]
        pay_date_str = fields["pay_date"].get().strip()
        cycle_id = cycle_var.get()
        amount_str = fields["amount"].get().strip()
        
        if not c or not pay_date_str or not cycle_id:
            lps_prev_lbl.config(text="LPS Preview: — (Select cycle and enter payment date)")
            return
            
        try:
            pay_d = utils.parse_date(pay_date_str)
            # Find cycle details
            def fetch():
                return fc.get_billing_cycle(cycle_id)
                
            def done(cycle_data):
                if not cycle_data:
                    return
                last_pay = utils.parse_date(cycle_data["last_payment_date"])
                
                # Check outstanding and calculate LPS
                out = float(c.get("outstanding_balance", 0.0))
                cred = float(c.get("credit_balance", 0.0))
                
                # Calculate LPS
                res = be.apply_lps(out, last_pay, pay_d, cred, out)
                l_amt = res["lps_amount"]
                l_type = res["lps_type"]
                
                if l_amt > 0:
                    lps_prev_lbl.config(text=f"LPS Warning: Delay applies LPS {l_type.upper()} = {utils.format_currency(l_amt)}", foreground="red")
                else:
                    lps_prev_lbl.config(text="LPS Preview: No delay penalty (Paid on-time)", foreground="#2a7a2a")
                    
            utils.run_in_thread(fetch, callback=done, widget=tab)
        except Exception:
            lps_prev_lbl.config(text="LPS Preview: — (date formatting error)")

    cycle_cb.bind("<<ComboboxSelected>>", update_lps_preview)
    fields["pay_date"].bind("<KeyRelease>", update_lps_preview)
    
    # Search-as-you-type consumer logic
    def perform_lookup():
        cin = cin_ent.get().strip()
        if not cin:
            c_name_lbl.config(text="Name: —")
            c_out_lbl.config(text="Outstanding: —")
            c_cred_lbl.config(text="Credit Balance: —")
            target_consumer[0] = None
            update_lps_preview()
            return
            
        def fetch():
            return fc.get_consumer(cin)
            
        def done(c):
            if c:
                target_consumer[0] = c
                c_name_lbl.config(text=f"Name: {c['name']}")
                c_out_lbl.config(text=f"Outstanding: {utils.format_currency(c.get('outstanding_balance', 0.0))}")
                c_cred_lbl.config(text=f"Credit Balance: {utils.format_currency(c.get('credit_balance', 0.0))}")
                update_lps_preview()
            else:
                c_name_lbl.config(text="Name: Not Found", foreground="red")
                c_out_lbl.config(text="Outstanding: —")
                c_cred_lbl.config(text="Credit Balance: —")
                target_consumer[0] = None
                update_lps_preview()
                
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    def on_cin_keypress(event):
        if debounce_id[0]:
            main_frame.after_cancel(debounce_id[0])
        debounce_id[0] = main_frame.after(350, perform_lookup)
        
    cin_ent.bind("<KeyRelease>", on_cin_keypress)
    
    def save_payment_action():
        c = target_consumer[0]
        if not c:
            messagebox.showerror("Error", "Please select a valid consumer profile.", parent=tab)
            return
            
        amt_str = fields["amount"].get().strip()
        p_date = fields["pay_date"].get().strip()
        mode = mode_var.get()
        key = emitra_ent.get().strip()
        cycle = cycle_var.get()
        notes = fields["notes"].get().strip()
        
        if not amt_str or not p_date:
            messagebox.showerror("Error", "Please fill required (*) fields.", parent=tab)
            return
        if mode == "E-Mitra" and not key:
            messagebox.showerror("Error", "E-Mitra transaction key is required for E-Mitra mode.", parent=tab)
            return
            
        try:
            amount = float(amt_str)
        except ValueError:
            messagebox.showerror("Error", "Payment amount must be a number.", parent=tab)
            return
            
        payload = {
            "cin_no": c["cin_no"],
            "amount": amount,
            "payment_mode": mode,
            "emitra_key": key if mode == "E-Mitra" else None,
            "payment_date": p_date,
            "entry_date": utils.today_str(),
            "cycle_id": cycle if cycle else None,
            "notes": notes if notes else "Manual payment"
        }
        
        def save():
            fc.clear_cache() # Invalidate cache on payment
            return fc.record_payment(payload, admin["name"])
            
        def done(payment_id):
            # Print Receipt Option Box
            confirm_print = messagebox.askyesno("Payment Recorded", f"Payment recorded successfully under Receipt: {payment_id}.\n\nDo you want to print the receipt PDF?", parent=tab)
            
            # Reset form fields
            cin_ent.delete(0, "end")
            fields["amount"].delete(0, "end")
            emitra_ent.delete(0, "end")
            emitra_ent.config(state="disabled")
            mode_var.set("Cash")
            fields["notes"].delete(0, "end")
            cycle_var.set("")
            
            c_name_lbl.config(text="Name: —")
            c_out_lbl.config(text="Outstanding: —")
            c_cred_lbl.config(text="Credit Balance: —")
            target_consumer[0] = None
            lps_prev_lbl.config(text="LPS Preview: —")
            
            if confirm_print:
                # Trigger printing in background
                def run_print():
                    p_doc = fc.list_payments({"cin_no": c["cin_no"]})[0] # get latest payment record
                    html_tmpl = utils.load_pdf_template("payment_receipt")
                    
                    html = html_tmpl.replace("{{receipt_number}}", p_doc.get("receipt_number", ""))\
                                    .replace("{{entry_date}}", p_doc.get("entry_date", ""))\
                                    .replace("{{cin_no}}", p_doc.get("cin_no", ""))\
                                    .replace("{{name}}", c["name"])\
                                    .replace("{{zone}}", str(c["zone"]))\
                                    .replace("{{category}}", c["category"])\
                                    .replace("{{address}}", c.get("address_area_location") or "")\
                                    .replace("{{payment_mode}}", p_doc.get("payment_mode", ""))\
                                    .replace("{{payment_date}}", p_doc.get("payment_date", ""))\
                                    .replace("{{cycle_period}}", p_doc.get("cycle_id") or "N/A")\
                                    .replace("{{emitra_key}}", p_doc.get("emitra_key") or "N/A")\
                                    .replace("{{notes}}", p_doc.get("notes") or "")\
                                    .replace("{{amount}}", utils.format_currency(p_doc.get("amount", 0.0)))\
                                    .replace("{{outstanding}}", utils.format_currency(max(0.0, float(c.get("outstanding_balance", 0.0)) - amount)))\
                                    .replace("{{credit}}", utils.format_currency(float(c.get("credit_balance", 0.0)) + max(0.0, amount - float(c.get("outstanding_balance", 0.0)))))\
                                    .replace("{{received_by}}", admin["name"])
                                    
                    pdf_bytes = utils.render_pdf_to_bytes(html)
                    temp_path = os.path.join(os.environ.get("TEMP", "."), f"receipt_{payment_id}.pdf")
                    with open(temp_path, "wb") as f_out:
                        f_out.write(pdf_bytes)
                    utils.open_pdf(temp_path)
                    
                utils.run_in_thread(run_print, widget=tab)
                
        def fail(err):
            messagebox.showerror("Error Saving Payment", f"Error:\n{err}", parent=tab)
            
        utils.run_in_thread(save, callback=done, error_callback=fail, widget=tab)

    ttk.Button(left_f, text="💰 Save & Record Payment", command=save_payment_action).pack(anchor="w", pady=10)

# ----------------------------------------------------
# TAB 2: Bulk Import Payments
# ----------------------------------------------------
def build_import_tab(tab, fc, utils, be, admin):
    ttk.Label(tab, text="Bulk Import Payments Log via Excel", style="Header.TLabel", foreground="#1a3a6b").pack(anchor="w", pady=(0, 10))
    ttk.Label(tab, text="Upload payment transactions sheet matching headers: cin_no, amount, payment_mode, emitra_key, payment_date, notes").pack(anchor="w", pady=(0, 15))
    
    def download_tmpl():
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], title="Save Payments Template")
        if path:
            xlsx_bytes = utils.get_excel_template_payments()
            with open(path, "wb") as f:
                f.write(xlsx_bytes)
            messagebox.showinfo("Success", "Template saved successfully.", parent=tab)
            
    ttk.Button(tab, text="📥 Download Payments Template", command=download_tmpl).pack(anchor="w", pady=5)
    
    # Import
    imp_f = ttk.LabelFrame(tab, text="Execute Import", padding=15)
    imp_f.pack(fill="x", pady=15)
    
    file_path = tk.StringVar()
    ttk.Label(imp_f, text="Select spreadsheet file:").grid(row=0, column=0, sticky="w")
    ttk.Entry(imp_f, textvariable=file_path, width=50, state="readonly").grid(row=0, column=1, padx=10)
    
    def browse():
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")], title="Select Payments Spreadsheet")
        if path:
            file_path.set(path)
            
    ttk.Button(imp_f, text="📂 Browse...", command=browse).grid(row=0, column=2)
    
    def run_import():
        path = file_path.get()
        if not path:
            return
            
        def run():
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            
            headers = [str(c).strip() for c in rows[0]]
            data_list = []
            
            for r_idx, row in enumerate(rows[1:]):
                if not row or not any(row):
                    continue
                payload = {}
                for idx, h in enumerate(headers):
                    payload[h] = row[idx]
                    
                if not payload.get("cin_no") or payload.get("amount") is None:
                    continue
                    
                payload["amount"] = float(payload["amount"])
                payload["entry_date"] = utils.today_str()
                payload["payment_date"] = str(payload.get("payment_date") or utils.today_str())
                
                data_list.append(payload)
                
            res = fc.bulk_record_payments(data_list, admin["name"])
            return res
            
        def done(res):
            success = res["success"]
            errors = res["errors"]
            msg = f"Bulk payments entered successfully!\n\nImported records: {success}"
            if errors:
                msg += f"\nFailed transactions: {len(errors)}"
                messagebox.showwarning("Warning", msg, parent=tab)
            else:
                messagebox.showinfo("Success", msg, parent=tab)
            file_path.set("")
            
        def fail(err):
            messagebox.showerror("Error", f"Failed running bulk payments import:\n{err}", parent=tab)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=tab)

    ttk.Button(imp_f, text="🚀 Import Payments Log", command=run_import).grid(row=1, column=1, sticky="w", pady=15)

# ----------------------------------------------------
# TAB 3: Payment Log Explorer
# ----------------------------------------------------
def build_log_tab(tab, fc, utils, be, admin):
    f_frame = ttk.Frame(tab, padding=5)
    f_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(f_frame, text="CIN No:").pack(side="left", padx=5)
    cin_ent = ttk.Entry(f_frame, width=12)
    cin_ent.pack(side="left", padx=5)
    
    ttk.Label(f_frame, text="Mode:").pack(side="left", padx=5)
    mode_var = tk.StringVar(value="All")
    mode_cb = ttk.Combobox(f_frame, textvariable=mode_var, values=["All", "Cash", "E-Mitra"], state="readonly", width=8)
    mode_cb.pack(side="left", padx=5)
    
    tree_columns = ("receipt", "date", "cin_no", "mode", "key", "amount", "by")
    tree = ttk.Treeview(tab, columns=tree_columns, show="headings")
    tree.heading("receipt", text="Receipt No")
    tree.heading("date", text="Date")
    tree.heading("cin_no", text="CIN")
    tree.heading("mode", text="Mode")
    tree.heading("key", text="E-Mitra Key")
    tree.heading("amount", text="Amount")
    tree.heading("by", text="Admin")
    
    tree.column("receipt", width=140, anchor="center")
    tree.column("date", width=90, anchor="center")
    tree.column("cin_no", width=100, anchor="center")
    tree.column("mode", width=80, anchor="center")
    tree.column("key", width=100, anchor="center")
    tree.column("amount", width=100, anchor="e")
    tree.column("by", width=100)
    
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="top", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    payments_cache = {}
    
    def perform_search():
        for r in tree.get_children():
            tree.delete(r)
            
        cin = cin_ent.get().strip()
        mode = mode_var.get()
        
        filters = {}
        if cin:
            filters["cin_no"] = cin
        if mode != "All":
            filters["mode"] = mode
            
        def fetch():
            return fc.list_payments(filters)
            
        def done(payments):
            for idx, p in enumerate(payments):
                receipt_key = p.get("receipt_number") or p.get("payment_id") or f"payment_{idx}"
                payments_cache[receipt_key] = p
                tree.insert("", "end", values=(
                    p.get("receipt_number"),
                    p.get("payment_date"),
                    p.get("cin_no"),
                    p.get("payment_mode"),
                    p.get("emitra_key") or "—",
                    utils.format_currency(p.get("amount", 0.0)),
                    p.get("received_by", "")
                ), iid=receipt_key)
                
        utils.run_in_thread(fetch, callback=done, widget=tab)

    ttk.Button(f_frame, text="🔍 Filter Payments", command=perform_search).pack(side="left", padx=15)
    
    # Double-click details with Reprint Receipt option
    def on_row_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        rec_no = sel[0]
        p = payments_cache.get(rec_no)
        if not p:
            return
            
        dlg = tk.Toplevel(tab)
        dlg.title(f"Receipt Details — {rec_no}")
        dlg.geometry("400x320")
        dlg.grab_set()
        
        f = ttk.Frame(dlg, padding=15)
        f.pack(fill="both", expand=True)
        
        ttk.Label(f, text="Payment Details", font=("Segoe UI", 12, "bold"), foreground="#1a3a6b").pack(anchor="w")
        
        c = fc.get_consumer(p["cin_no"])
        
        details = f"• Receipt No  : {rec_no}\n" \
                  f"• CIN Number  : {p['cin_no']}\n" \
                  f"• Consumer    : {c['name'] if c else 'Unknown'}\n" \
                  f"• Amount Paid : {utils.format_currency(p.get('amount'))}\n" \
                  f"• Payment Mode: {p.get('payment_mode')}\n" \
                  f"• Payment Date: {p.get('payment_date')}\n" \
                  f"• Entry Date  : {p.get('entry_date')}\n" \
                  f"• Received By : {p.get('received_by')}\n" \
                  f"• Remarks     : {p.get('notes', 'None')}"
                  
        ttk.Label(f, text=details, font=("Segoe UI", 10), justify="left").pack(anchor="w", pady=10)
        
        def reprint_receipt():
            html_tmpl = utils.load_pdf_template("payment_receipt")
            
            html = html_tmpl.replace("{{receipt_number}}", p.get("receipt_number", ""))\
                            .replace("{{entry_date}}", p.get("entry_date", ""))\
                            .replace("{{cin_no}}", p.get("cin_no", ""))\
                            .replace("{{name}}", c["name"] if c else "Unknown")\
                            .replace("{{zone}}", str(c["zone"] if c else "—"))\
                            .replace("{{category}}", c["category"] if c else "—")\
                            .replace("{{address}}", c.get("address_area_location") if c else "")\
                            .replace("{{payment_mode}}", p.get("payment_mode", ""))\
                            .replace("{{payment_date}}", p.get("payment_date", ""))\
                            .replace("{{cycle_period}}", p.get("cycle_id") or "N/A")\
                            .replace("{{emitra_key}}", p.get("emitra_key") or "N/A")\
                            .replace("{{notes}}", p.get("notes") or "")\
                            .replace("{{amount}}", utils.format_currency(p.get("amount", 0.0)))\
                            .replace("{{outstanding}}", utils.format_currency(c.get("outstanding_balance", 0.0) if c else 0.0))\
                            .replace("{{credit}}", utils.format_currency(c.get("credit_balance", 0.0) if c else 0.0))\
                            .replace("{{received_by}}", p.get("received_by", ""))
                            
            pdf_bytes = utils.render_pdf_to_bytes(html)
            temp_path = os.path.join(os.environ.get("TEMP", "."), f"receipt_reprint_{rec_no}.pdf")
            with open(temp_path, "wb") as f_out:
                f_out.write(pdf_bytes)
            utils.open_pdf(temp_path)
            
        ttk.Button(f, text="🖨️ Reprint PDF Receipt", command=reprint_receipt).pack(anchor="e")
        
    tree.bind("<Double-1>", on_row_double_click)
    perform_search()

# ----------------------------------------------------
# TAB 4: LPS Waiver Section
# ----------------------------------------------------
def build_waiver_tab(tab, fc, utils, be, admin):
    f = ttk.Frame(tab, padding=30)
    f.pack(fill="both", expand=True)
    
    ttk.Label(f, text="LATE PAYMENT SURCHARGE (LPS) WAIVER", style="KPITitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 25))

    grid = ttk.Frame(f)
    grid.grid(row=1, column=0, sticky="n", padx=10)
    
    c_snap = ttk.Frame(f, style="Card.TFrame", padding=25)
    c_snap.grid(row=1, column=1, sticky="n", padx=20)
    ttk.Label(c_snap, text="CONSUMER SNAPSHOT", style="KPITitle.TLabel").pack(anchor="w", pady=(0, 15))
    
    target_c = [None]
    
    # Search
    r = 0
    ttk.Label(grid, text="Search CIN:").grid(row=r, column=0, sticky="w", pady=5)
    cin_ent = ttk.Entry(grid, width=15)
    cin_ent.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    r += 1
    
    c_name_lbl = ttk.Label(c_snap, text="Name: —", font=("Segoe UI", 9, "bold"))
    c_name_lbl.pack(anchor="w", pady=2)
    c_out_lbl = ttk.Label(c_snap, text="Outstanding: —", foreground="#c0392b")
    c_out_lbl.pack(anchor="w", pady=2)
    
    def lookup():
        cin = cin_ent.get().strip()
        if not cin:
            return
        def fetch():
            return fc.get_consumer(cin)
        def done(c):
            if c:
                target_c[0] = c
                c_name_lbl.config(text=f"Name: {c['name']}")
                c_out_lbl.config(text=f"Outstanding Balance: {utils.format_currency(c['outstanding_balance'])}")
            else:
                target_c[0] = None
                c_name_lbl.config(text="Name: Not Found", foreground="red")
                c_out_lbl.config(text="Outstanding: —")
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    ttk.Button(grid, text="🔍 Search Profile", command=lookup).grid(row=0, column=2, padx=5)
    
    # Waiver inputs
    ttk.Label(grid, text="Waiver Type:").grid(row=r, column=0, sticky="w", pady=5)
    w_type_var = tk.StringVar(value="Full")
    w_type_cb = ttk.Combobox(grid, textvariable=w_type_var, values=["Full", "Partial"], state="readonly", width=10)
    w_type_cb.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    r += 1
    
    ttk.Label(grid, text="Waiver Amount (₹):").grid(row=r, column=0, sticky="w", pady=5)
    w_amt_ent = ttk.Entry(grid, width=12)
    w_amt_ent.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    r += 1
    
    def on_type_changed(event):
        if w_type_var.get() == "Full":
            w_amt_ent.delete(0, "end")
            w_amt_ent.config(state="disabled")
        else:
            w_amt_ent.config(state="normal")
            
    w_type_cb.bind("<<ComboboxSelected>>", on_type_changed)
    w_amt_ent.config(state="disabled") # default full
    
    ttk.Label(grid, text="Reason Note:*").grid(row=r, column=0, sticky="nw", pady=5)
    note_txt = tk.Text(grid, height=3, width=25, font=("Segoe UI", 9))
    note_txt.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    r += 1
    
    def apply_waiver_action():
        c = target_c[0]
        if not c:
            return
        w_type = w_type_var.get()
        reason = note_txt.get("1.0", "end").strip()
        
        if not reason:
            messagebox.showerror("Error", "Justification Reason Note is required for audit logs.", parent=tab)
            return
            
        out = float(c["outstanding_balance"])
        if w_type == "Full":
            w_amt = out
        else:
            try:
                w_amt = float(w_amt_ent.get().strip())
                if w_amt > out:
                    messagebox.showerror("Error", "Waiver cannot exceed outstanding balance.", parent=tab)
                    return
            except ValueError:
                messagebox.showerror("Error", "Waiver amount must be a number.", parent=tab)
                return
                
        confirm = messagebox.askyesno("Confirm Waiver", f"This will apply an LPS waiver of {utils.format_currency(w_amt)} to {c['name']}. Confirm?", parent=tab)
        if not confirm:
            return
            
        def run():
            fc.update_consumer_lps_waiver(c["cin_no"], w_amt, reason, admin["name"])
            
        def done(res):
            messagebox.showinfo("Waiver Applied", "Waiver applied successfully.", parent=tab)
            cin_ent.delete(0, "end")
            w_amt_ent.delete(0, "end")
            note_txt.delete("1.0", "end")
            
            c_name_lbl.config(text="Name: —")
            c_out_lbl.config(text="Outstanding: —")
            target_c[0] = None
            
        def fail(err):
            messagebox.showerror("Waiver Error", f"Error:\n{err}", parent=tab)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=tab)

    ttk.Button(grid, text="🏳️ Apply LPS Waiver", command=apply_waiver_action).grid(row=r, column=1, sticky="w", pady=15)

# ----------------------------------------------------
# TAB 5: Credit Balance adjustments
# ----------------------------------------------------
def build_credit_tab(tab, fc, utils, be, admin):
    ttk.Label(tab, text="Consumer Credit Balance Ledger Tools", style="Header.TLabel", foreground="#1a3a6b").pack(anchor="w", pady=(0, 10))
    
    f = ttk.Frame(tab, padding=10)
    f.pack(fill="both", expand=True)
    
    grid = ttk.Frame(f)
    grid.pack(side="left", fill="y", padx=5)
    
    right_f = ttk.Frame(f)
    right_f.pack(side="right", fill="both", expand=True, padx=15)
    
    target_c = [None]
    
    # Search Left
    r = 0
    ttk.Label(grid, text="Search CIN:").grid(row=r, column=0, sticky="w", pady=5)
    cin_ent = ttk.Entry(grid, width=15)
    cin_ent.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    
    c_name_lbl = ttk.Label(grid, text="Name: —", font=("Segoe UI", 9, "bold"))
    c_out_lbl = ttk.Label(grid, text="Outstanding: —")
    c_cred_lbl = ttk.Label(grid, text="Credit Balance: —", foreground="#2a7a2a")
    
    # Treeview for adjustments history on the right
    ttk.Label(right_f, text="Credit & Waiver Adjustments History", font=("Segoe UI", 9, "bold")).pack(anchor="w")
    hist_tree = ttk.Treeview(right_f, columns=("date", "type", "reason", "amount"), show="headings", height=8)
    hist_tree.heading("date", text="Date")
    hist_tree.heading("type", text="Type")
    hist_tree.heading("reason", text="Reason Note")
    hist_tree.heading("amount", text="Amount")
    hist_tree.column("date", width=110, anchor="center")
    hist_tree.column("type", width=90, anchor="center")
    hist_tree.column("reason", width=200)
    hist_tree.column("amount", width=90, anchor="e")
    hist_tree.pack(fill="both", expand=True, pady=5)
    
    def refresh_history(cin):
        for item in hist_tree.get_children():
            hist_tree.delete(item)
        def fetch():
            return fc.get_adjustments_for_consumer(cin)
        def done(adjs):
            for a in adjs:
                hist_tree.insert("", "end", values=(
                    utils.format_date(a.get("applied_at")),
                    a.get("type"),
                    a.get("reason_note"),
                    utils.format_currency(a.get("amount", 0.0))
                ))
        utils.run_in_thread(fetch, callback=done, widget=tab)

    def lookup():
        cin = cin_ent.get().strip()
        if not cin:
            return
        def fetch():
            return fc.get_consumer(cin)
        def done(c):
            if c:
                target_c[0] = c
                c_name_lbl.config(text=f"Name: {c['name']}")
                c_out_lbl.config(text=f"Outstanding: {utils.format_currency(c.get('outstanding_balance', 0.0))}")
                c_cred_lbl.config(text=f"Credit Balance: {utils.format_currency(c.get('credit_balance', 0.0))}")
                refresh_history(cin)
            else:
                target_c[0] = None
                c_name_lbl.config(text="Name: Not Found", foreground="red")
                c_out_lbl.config(text="Outstanding: —")
                c_cred_lbl.config(text="Credit Balance: —")
        utils.run_in_thread(fetch, callback=done, widget=tab)
        
    ttk.Button(grid, text="🔍 Search", command=lookup).grid(row=0, column=2, padx=5)
    r += 1
    
    # Display balances inside grid
    c_name_lbl.grid(row=r, column=1, sticky="w", pady=2)
    r += 1
    c_out_lbl.grid(row=r, column=1, sticky="w", pady=2)
    r += 1
    c_cred_lbl.grid(row=r, column=1, sticky="w", pady=2)
    r += 1
    
    # Inputs for Adjusting Credit
    ttk.Label(grid, text="Waiver Amount (₹):*").grid(row=r, column=0, sticky="w", pady=5)
    adj_ent = ttk.Entry(grid, width=12)
    adj_ent.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    r += 1
    
    ttk.Label(grid, text="Reason Note:*").grid(row=r, column=0, sticky="nw", pady=5)
    note_txt = tk.Text(grid, height=3, width=22, font=("Segoe UI", 9))
    note_txt.grid(row=r, column=1, sticky="w", pady=5, padx=5)
    r += 1
    
    def save_credit_adj():
        c = target_c[0]
        if not c:
            return
        amt_str = adj_ent.get().strip()
        reason = note_txt.get("1.0", "end").strip()
        
        if not amt_str or not reason:
            messagebox.showerror("Error", "Required fields (*) cannot be empty.", parent=tab)
            return
            
        try:
            amt = float(amt_str)
            if amt <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number.", parent=tab)
            return
            
        confirm = messagebox.askyesno("Confirm Adjustment", f"Apply credit adjustment waiver of {utils.format_currency(amt)} to {c['name']}?", parent=tab)
        if not confirm:
            return
            
        def run():
            # Add custom adjustment type waiver
            fc.add_custom_adjustment(
                cin_no=c["cin_no"],
                adj_type="waiver",
                amount=amt,
                reason_note=reason,
                admin_name=admin["name"]
            )
            
        def done(res):
            messagebox.showinfo("Success", "Credit balance adjustment logged successfully.", parent=tab)
            # Reset
            cin_ent.delete(0, "end")
            adj_ent.delete(0, "end")
            note_txt.delete("1.0", "end")
            
            c_name_lbl.config(text="Name: —")
            c_out_lbl.config(text="Outstanding: —")
            c_cred_lbl.config(text="Credit Balance: —")
            target_c[0] = None
            for item in hist_tree.get_children():
                hist_tree.delete(item)
                
        def fail(err):
            messagebox.showerror("Error Saving", f"Error:\n{err}", parent=tab)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=tab)

    ttk.Button(grid, text="🪙 Save Adjustment", command=save_credit_adj).grid(row=r, column=1, sticky="w", pady=15)
