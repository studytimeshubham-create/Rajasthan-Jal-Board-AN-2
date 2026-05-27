import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def get_frame(parent, fc, utils, be, admin) -> ttk.Frame:
    frame = ttk.Frame(parent, padding=30)
    
    # Title and Refresh row
    header = ttk.Frame(frame)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 30))
    ttk.Label(header, text="TARIFF & RATE CONFIGURATION", style="KPITitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Button(header, text="🔄 Refresh Rates", style="Primary.TButton", command=lambda: load_active_rates()).grid(row=0, column=1, sticky="e")
    header.grid_columnconfigure(0, weight=1)

    # Grid layout: Top Rate Explorer, Bottom Sandbox Test Widget
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=4) # Rates view
    frame.grid_rowconfigure(2, weight=3) # Sandbox test
    
    # Use standard Frame for outer containers and Card.TFrame for inner card
    rates_view_panel = ttk.Frame(frame, padding=20)
    rates_view_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    
    sandbox_panel = ttk.Frame(frame, padding=20)
    sandbox_panel.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
    
    active_rates = [None] # Local rates cache
    
    # ----------------------------------------------------
    # Rate Explorer Panel
    # ----------------------------------------------------
    rates_text_frame = ttk.Frame(rates_view_panel, style="Card.TFrame", padding=15)
    rates_text_frame.grid(row=0, column=0, sticky="nsew")
    rates_view_panel.grid_columnconfigure(0, weight=1)
    rates_view_panel.grid_rowconfigure(0, weight=1)
    
    # Use Text widget for rich structured layout of rates
    rates_text = tk.Text(rates_text_frame, font=("Segoe UI", 9), wrap="word", relief="flat", bg="#fafafa", state="disabled")
    scrollbar = ttk.Scrollbar(rates_text_frame, orient="vertical", command=rates_text.yview)
    rates_text.configure(yscrollcommand=scrollbar.set)
    rates_text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    rates_text_frame.grid_columnconfigure(0, weight=1)
    rates_text_frame.grid_rowconfigure(0, weight=1)
    
    meta_lbl = ttk.Label(rates_view_panel, text="Loading active configuration...", font=("Segoe UI", 9, "italic"), foreground="#555")
    meta_lbl.grid(row=1, column=0, sticky="w", pady=5)
    
    def populate_rates_display(rates):
        rates_text.config(state="normal")
        rates_text.delete("1.0", "end")
        
        # Helper to format groups
        def print_title(title):
            rates_text.insert("end", f"\n{title.upper()}\n", "title")
            
        def print_rate(name, val):
            rates_text.insert("end", f"  {name:<35} : {val}\n")
            
        rates_text.tag_config("title", font=("Public Sans", 11, "bold"), foreground="#1a3a6b")
        
        print_title("Domestic (15mm–25mm) Slabs")
        print_rate("Slab 0-8 KL (Domestic)", f"₹{rates.get('domestic_slab_a_rate', 7.00):.2f} / KL")
        print_rate("Slab 8-15 KL (Domestic)", f"₹{rates.get('domestic_slab_b_rate', 9.00):.2f} / KL")
        print_rate("Slab 15-40 KL (Domestic)", f"₹{rates.get('domestic_slab_c_rate', 18.00):.2f} / KL")
        print_rate("Slab Above 40 KL (Domestic)", f"₹{rates.get('domestic_slab_d_rate', 22.00):.2f} / KL")
        print_rate("Rural Fixed Flat Rate", f"₹{rates.get('domestic_flat_rural', 110.00):.2f}")
        print_rate("Minimum (Avg <= 8 KL)", f"₹{rates.get('domestic_min_15mm_avg_low', 88.00):.2f}")
        print_rate("Minimum (Avg > 8 KL)", f"₹{rates.get('domestic_min_15mm_avg_high', 220.00):.2f}")
        print_rate("Minimum (20mm size)", f"₹{rates.get('domestic_min_20mm', 880.00):.2f}")
        print_rate("Minimum (25mm size)", f"₹{rates.get('domestic_min_25mm', 2200.00):.2f}")
        
        print_title("Non-Domestic (15mm–25mm) Slabs")
        print_rate("Slab 0-15 KL (Non-Dom)", f"₹{rates.get('nondomestic_slab_a_rate', 40.00):.2f} / KL")
        print_rate("Slab 15-40 KL (Non-Dom)", f"₹{rates.get('nondomestic_slab_b_rate', 73.00):.2f} / KL")
        print_rate("Slab Above 40 KL (Non-Dom)", f"₹{rates.get('nondomestic_slab_c_rate', 97.00):.2f} / KL")
        print_rate("Minimum (15mm size)", f"₹{rates.get('nondomestic_min_15mm', 880.00):.2f}")
        print_rate("Minimum (20mm size)", f"₹{rates.get('nondomestic_min_20mm', 2200.00):.2f}")
        print_rate("Minimum (25mm size)", f"₹{rates.get('nondomestic_min_25mm', 3520.00):.2f}")
        
        print_title("Industrial (15mm–25mm) Slabs")
        print_rate("Slab 0-15 KL (Industrial)", f"₹{rates.get('industrial_slab_a_rate', 154.00):.2f} / KL")
        print_rate("Slab 15-40 KL (Industrial)", f"₹{rates.get('industrial_slab_b_rate', 198.00):.2f} / KL")
        print_rate("Slab Above 40 KL (Industrial)", f"₹{rates.get('industrial_slab_c_rate', 220.00):.2f} / KL")
        print_rate("Minimum (15mm size)", f"₹{rates.get('industrial_min_15mm', 2200.00):.2f}")
        print_rate("Minimum (20mm size)", f"₹{rates.get('industrial_min_20mm', 3960.00):.2f}")
        print_rate("Minimum (25mm size)", f"₹{rates.get('industrial_min_25mm', 6160.00):.2f}")
        
        print_title("General Rates (15mm–25mm Only)")
        print_rate("Fixed Charge (Domestic)", f"₹{rates.get('fixed_charge_domestic', 27.50):.2f} / month")
        print_rate("Fixed Charge (Non-Dom)", f"₹{rates.get('fixed_charge_nondomestic', 55.00):.2f} / month")
        print_rate("Fixed Charge (Industrial)", f"₹{rates.get('fixed_charge_industrial', 110.00):.2f} / month")
        print_rate("Meter Service (15mm)", f"₹{rates.get('meter_svc_15mm', 22.00):.2f} / month")
        print_rate("Meter Service (20mm)", f"₹{rates.get('meter_svc_20mm', 55.00):.2f} / month")
        print_rate("Meter Service (25mm)", f"₹{rates.get('meter_svc_25mm', 110.00):.2f} / month")

        print_title("Sewerage & STP Charges")
        print_rate("PHED Sewerage Rate (%)", f"{rates.get('sewerage_phed_supply_rate_pct', 20.0):.1f} %")
        print_rate("Own Supply Hotel (per room)", f"₹{rates.get('sewerage_own_hotel_per_room', 31.25):.2f}")
        print_rate("Own Supply Restaurant (fixed)", f"₹{rates.get('sewerage_own_restaurant', 200.00):.2f}")
        print_rate("Own Supply Cinema (fixed)", f"₹{rates.get('sewerage_own_cinema', 400.00):.2f}")
        print_rate("Own Supply Car Svc (fixed)", f"₹{rates.get('sewerage_own_car_service', 200.00):.2f}")
        print_rate("Own Supply Scooter Svc (fixed)", f"₹{rates.get('sewerage_own_scooter_service', 62.50):.2f}")
        print_rate("Own Supply Other Ind (per room)", f"₹{rates.get('sewerage_own_other_ind_comm_per_room', 12.50):.2f}")
        print_rate("Own Supply Domestic (fixed)", f"₹{rates.get('sewerage_own_domestic', 12.50):.2f}")
        print_rate("Own Supply Large Plot (per 100sqm)", f"₹{rates.get('sewerage_own_house_large_per_100sqm', 6.25):.2f}")
        print_rate("STP Charge Rate (%)", f"{rates.get('stp_charge_rate_pct', 13.0):.1f} %")
        
        print_title("Bulk Connections (>25mm)")
        print_rate("Bulk Water (Domestic)", f"₹{rates.get('bulk_domestic_rate', 25.00):.2f} / KL")
        print_rate("Bulk Water (Non-Dom)", f"₹{rates.get('bulk_nondomestic_rate', 97.00):.2f} / KL")
        print_rate("Bulk Water (Industrial)", f"₹{rates.get('bulk_industrial_rate', 220.00):.2f} / KL")
        for size in ("40mm", "50mm", "80mm", "100mm", "150mm"):
            print_rate(f"Bulk Minimum Domestic ({size})", f"₹{rates.get(f'bulk_min_dom_{size}', 0.00):.2f} / month")
            print_rate(f"Bulk Minimum Non-Dom ({size})", f"₹{rates.get(f'bulk_min_nondom_{size}', 0.00):.2f} / month")
            print_rate(f"Bulk Minimum Industrial ({size})", f"₹{rates.get(f'bulk_min_ind_{size}', 0.00):.2f} / month")
            print_rate(f"Bulk Fixed Domestic ({size})", f"₹{rates.get(f'bulk_fixed_dom_{size}', 0.00):.2f} / month")
            print_rate(f"Bulk Fixed Non-Dom ({size})", f"₹{rates.get(f'bulk_fixed_nondom_{size}', 0.00):.2f} / month")
            print_rate(f"Bulk Fixed Industrial ({size})", f"₹{rates.get(f'bulk_fixed_ind_{size}', 0.00):.2f} / month")
            print_rate(f"Bulk Meter Service ({size})", f"₹{rates.get(f'bulk_svc_{size}', 0.00):.2f} / month")
        
        rates_text.config(state="disabled")
        
        # Meta info
        m_by = rates.get("last_updated_by", "System Initialization")
        m_at = rates.get("last_updated_at", "N/A")
        if "T" in m_at:
            m_at = datetime.fromisoformat(m_at).strftime("%d-%m-%Y %H:%M")
        meta_lbl.config(text=f"Last updated: {m_at} by {m_by}")
        
    def load_active_rates():
        def fetch():
            return fc.get_charges_config()
            
        def done(rates):
            active_rates[0] = rates
            populate_rates_display(rates)
            
        utils.run_in_thread(fetch, callback=done, widget=frame)
        
    # Buttons frame
    btn_frame = ttk.Frame(rates_view_panel)
    btn_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    
    def edit_rates_action():
        if not active_rates[0]:
            return
            
        dlg = tk.Toplevel(frame)
        dlg.title("Edit Slabs Config & Rates")
        dlg.geometry("600x700")
        dlg.configure(bg="#F9F7F2")
        dlg.grab_set()
        
        # Scrollable form inside popups
        canvas = tk.Canvas(dlg, bg="#F9F7F2", highlightthickness=0)
        scrollbar = ttk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, padding=30)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        ttk.Label(scroll_frame, text="Modify System Slabs & Rates", font=("Segoe UI", 12, "bold"), foreground="#1a3a6b").pack(pady=10)
        
        # Gather all key entries dynamically
        entries = {}
        
        # We will list standard fields to edit
        editable_fields = [
            ("domestic_slab_a_rate", "Domestic Slab 0-8 (₹/KL)"),
            ("domestic_slab_b_rate", "Domestic Slab 8-15 (₹/KL)"),
            ("domestic_slab_c_rate", "Domestic Slab 15-40 (₹/KL)"),
            ("domestic_slab_d_rate", "Domestic Slab Above 40 (₹/KL)"),
            ("domestic_flat_rural", "Rural Fixed Flat Rate (₹)"),
            ("domestic_min_15mm_avg_low", "Domestic Min 15mm Avg <= 8 KL (₹)"),
            ("domestic_min_15mm_avg_high", "Domestic Min 15mm Avg > 8 KL (₹)"),
            ("domestic_min_20mm", "Domestic Min 20mm (₹)"),
            ("domestic_min_25mm", "Domestic Min 25mm (₹)"),
            
            ("nondomestic_slab_a_rate", "Non-Domestic Slab 0-15 (₹/KL)"),
            ("nondomestic_slab_b_rate", "Non-Domestic Slab 15-40 (₹/KL)"),
            ("nondomestic_slab_c_rate", "Non-Domestic Slab Above 40 (₹/KL)"),
            ("nondomestic_min_15mm", "Non-Domestic Min 15mm (₹)"),
            ("nondomestic_min_20mm", "Non-Domestic Min 20mm (₹)"),
            ("nondomestic_min_25mm", "Non-Domestic Min 25mm (₹)"),
            
            ("industrial_slab_a_rate", "Industrial Slab 0-15 (₹/KL)"),
            ("industrial_slab_b_rate", "Industrial Slab 15-40 (₹/KL)"),
            ("industrial_slab_c_rate", "Industrial Slab Above 40 (₹/KL)"),
            ("industrial_min_15mm", "Industrial Min 15mm (₹)"),
            ("industrial_min_20mm", "Industrial Min 20mm (₹)"),
            ("industrial_min_25mm", "Industrial Min 25mm (₹)"),
            
            ("fixed_charge_domestic", "Fixed Renovation - Dom (₹)"),
            ("fixed_charge_nondomestic", "Fixed Renovation - Non-Dom (₹)"),
            ("fixed_charge_industrial", "Fixed Renovation - Ind (₹)"),
            
            ("meter_svc_15mm", "Meter Service Charge 15mm (₹)"),
            ("meter_svc_20mm", "Meter Service Charge 20mm (₹)"),
            ("meter_svc_25mm", "Meter Service Charge 25mm (₹)"),
            
            ("bulk_domestic_rate", "Bulk Water Rate - Dom (₹/KL)"),
            ("bulk_nondomestic_rate", "Bulk Water Rate - Non-Dom (₹/KL)"),
            ("bulk_industrial_rate", "Bulk Water Rate - Ind (₹/KL)"),

            ("sewerage_phed_supply_rate_pct", "PHED Sewerage Rate (%)"),
            ("sewerage_own_hotel_per_room", "Own Supply Hotel (per room)"),
            ("sewerage_own_restaurant", "Own Supply Restaurant (fixed)"),
            ("sewerage_own_cinema", "Own Supply Cinema (fixed)"),
            ("sewerage_own_car_service", "Own Supply Car Svc (fixed)"),
            ("sewerage_own_scooter_service", "Own Supply Scooter Svc (fixed)"),
            ("sewerage_own_other_ind_comm_per_room", "Own Supply Other Ind (per room)"),
            ("sewerage_own_domestic", "Own Supply Domestic (fixed)"),
            ("sewerage_own_house_large_per_100sqm", "Own Supply Large Plot (per 100sqm)"),
            ("stp_charge_rate_pct", "STP Charge Rate (%)")
        ]

        for size in ("40mm", "50mm", "80mm", "100mm", "150mm"):
            editable_fields.extend([
                (f"bulk_min_dom_{size}", f"Bulk Min Dom {size} (₹)"),
                (f"bulk_min_nondom_{size}", f"Bulk Min Non-Dom {size} (₹)"),
                (f"bulk_min_ind_{size}", f"Bulk Min Ind {size} (₹)"),
                (f"bulk_fixed_dom_{size}", f"Bulk Fixed Dom {size} (₹)"),
                (f"bulk_fixed_nondom_{size}", f"Bulk Fixed Non-Dom {size} (₹)"),
                (f"bulk_fixed_ind_{size}", f"Bulk Fixed Ind {size} (₹)"),
                (f"bulk_svc_{size}", f"Bulk Meter Service {size} (₹)"),
            ])
        
        f_grid = ttk.Frame(scroll_frame)
        f_grid.pack(fill="x", pady=10)
        
        for idx, (key, label) in enumerate(editable_fields):
            ttk.Label(f_grid, text=f"{label}:").grid(row=idx, column=0, sticky="w", pady=4, padx=5)
            ent = ttk.Entry(f_grid, width=12)
            ent.grid(row=idx, column=1, sticky="w", pady=4, padx=5)
            ent.insert(0, str(active_rates[0].get(key, "")))
            entries[key] = ent
            
        # Change Note
        ttk.Label(scroll_frame, text="Required Change Note:*", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=5)
        note_text = tk.Text(scroll_frame, height=3, width=45, font=("Segoe UI", 9))
        note_text.pack(pady=5)
        
        def save():
            note = note_text.get("1.0", "end").strip()
            if not note:
                messagebox.showerror("Error", "Please enter a change note context detailing reasons for updates.", parent=dlg)
                return
                
            updated_rates = dict(active_rates[0])
            # Validate values
            diff_text = "Review Changes:\n\n"
            for k, ent in entries.items():
                val_str = ent.get().strip()
                try:
                    val = float(val_str)
                    old_v = float(active_rates[0].get(k, 0.0))
                    if val != old_v:
                        diff_text += f"• {k}: {old_v} ➔ {val}\n"
                    updated_rates[k] = val
                except ValueError:
                    messagebox.showerror("Validation Error", f"Field '{k}' contains an invalid number.", parent=dlg)
                    return
                    
            confirm = messagebox.askyesno("Confirm Changes", diff_text + "\nDo you want to save modifications?", parent=dlg)
            if not confirm:
                return
                
            def run():
                fc.update_charges_config(updated_rates, admin["name"], note)
                
            def done(res):
                messagebox.showinfo("Success", "System rates updated successfully.", parent=frame)
                dlg.destroy()
                load_active_rates()
                
            def fail(err):
                messagebox.showerror("Error", f"Failed updating config:\n{err}", parent=dlg)
                
            utils.run_in_thread(run, callback=done, error_callback=fail, widget=dlg)
            
        ttk.Button(scroll_frame, text="💾 Save Changes", command=save).pack(pady=15)

    ttk.Button(btn_frame, text="✏️ Edit Rates", command=edit_rates_action).pack(side="left", padx=5)
    
    def apply_increment_action():
        confirm = messagebox.askyesno(
            "Confirm Annual Increment", 
            "This will multiply ALL numeric pricing tiers by 1.10 representing the annual 10% April increment.\n\n"
            "This operation cannot be undone. Confirm?",
            parent=frame
        )
        if not confirm:
            return
            
        def run():
            fc.apply_annual_increment(admin["name"])
            
        def done(res):
            messagebox.showinfo("Success", "Annual tariff increment applied successfully.", parent=frame)
            load_active_rates()
            
        def fail(err):
            messagebox.showerror("Error", f"Operation failed:\n{err}", parent=frame)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=frame)
        
    ttk.Button(btn_frame, text="📈 Apply Annual 10% Increment", command=apply_increment_action).pack(side="left", padx=5)
    
    def view_history_action():
        hist_win = tk.Toplevel(frame)
        hist_win.title("Pricing Changes Audit History")
        hist_win.geometry("600x400")
        hist_win.grab_set()
        
        tree = ttk.Treeview(hist_win, columns=("date", "by", "note"), show="headings")
        tree.heading("date", text="Changed At")
        tree.heading("by", text="Changed By")
        tree.heading("note", text="Admin Note / Justification")
        tree.column("date", width=120)
        tree.column("by", width=100)
        tree.column("note", width=350)
        
        scrollbar = ttk.Scrollbar(hist_win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def fetch():
            return fc.get_charges_config_history()
            
        def done(history):
            for h in history:
                tree.insert("", "end", values=(
                    utils.format_date(h.get("changed_at")),
                    h.get("changed_by"),
                    h.get("admin_note", "")
                ))
                
        utils.run_in_thread(fetch, callback=done, widget=hist_win)
        
    ttk.Button(btn_frame, text="📜 View Change History", command=view_history_action).pack(side="right", padx=5)

    # ----------------------------------------------------
    # Sandbox Test Widget (Bottom Panel)
    # ----------------------------------------------------
    sandbox_frame = ttk.Frame(sandbox_panel, style="Card.TFrame", padding=20)
    sandbox_frame.grid(row=0, column=0, sticky="nsew")
    sandbox_panel.grid_columnconfigure(0, weight=1)
    sandbox_panel.grid_rowconfigure(0, weight=1)
    
    inputs_f = ttk.Frame(sandbox_frame)
    inputs_f.grid(row=0, column=0, sticky="nsw", padx=5, pady=5)
    
    output_f = ttk.Frame(sandbox_frame, padding=5)
    output_f.grid(row=0, column=1, sticky="nsew")
    sandbox_frame.grid_columnconfigure(1, weight=1)
    sandbox_frame.grid_rowconfigure(0, weight=1)
    
    # Inputs Setup
    r_idx = 0
    ttk.Label(inputs_f, text="Category:").grid(row=r_idx, column=0, sticky="w", pady=4)
    cat_cb = ttk.Combobox(inputs_f, values=utils.CATEGORY_OPTIONS, state="readonly", width=12)
    cat_cb.grid(row=r_idx, column=1, sticky="w", pady=4, padx=5)
    cat_cb.set("Domestic")
    r_idx += 1
    
    ttk.Label(inputs_f, text="Meter Size:").grid(row=r_idx, column=0, sticky="w", pady=4)
    size_cb = ttk.Combobox(inputs_f, values=utils.METER_SIZE_OPTIONS, state="readonly", width=12)
    size_cb.grid(row=r_idx, column=1, sticky="w", pady=4, padx=5)
    size_cb.set("15mm")
    r_idx += 1
    
    ttk.Label(inputs_f, text="Consumption (KL):").grid(row=r_idx, column=0, sticky="w", pady=4)
    cons_ent = ttk.Entry(inputs_f, width=10)
    cons_ent.grid(row=r_idx, column=1, sticky="w", pady=4, padx=5)
    cons_ent.insert(0, "20.0")
    r_idx += 1
    
    ttk.Label(inputs_f, text="Payment Delay (Days):").grid(row=r_idx, column=0, sticky="w", pady=4)
    delay_ent = ttk.Entry(inputs_f, width=10)
    delay_ent.grid(row=r_idx, column=1, sticky="w", pady=4, padx=5)
    delay_ent.insert(0, "0")
    r_idx += 1
    
    # Output display
    ttk.Label(output_f, text="Live Bill Breakdown Output:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
    breakdown_text = tk.Text(output_f, height=8, font=("Courier New", 9), state="disabled", bg="#fcfcfc")
    breakdown_text.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
    output_f.grid_rowconfigure(1, weight=1)
    output_f.grid_columnconfigure(0, weight=1)
    
    def run_bill_simulation():
        if not active_rates[0]:
            messagebox.showerror("Error", "Tariff config not loaded yet.", parent=frame)
            return
            
        cat = cat_cb.get()
        size = size_cb.get()
        cons_str = cons_ent.get().strip()
        delay_str = delay_ent.get().strip()
        
        try:
            cons = float(cons_str)
            delay = int(delay_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid inputs.", parent=frame)
            return
            
        # Mock consumer snapshot
        mock_consumer = {
            "category": cat,
            "meter_size": size,
            "consumer_status": "Active",
            "outstanding_balance": 100.0 if delay > 0 else 0.0,
            "credit_balance": 0.0,
            "sewerage_connection": "PHED Supply", # default for sandbox
            "sewerage_sub_category": "Domestic"
        }
        
        from datetime import timedelta
        # Setup LPS parameters
        last_pay = utils.parse_date(utils.today_str())
        pay_date = last_pay + timedelta(days=delay)
        
        # Calculate
        res = be.calculate_bill(
            consumption_kl=cons,
            consumer=mock_consumer,
            rates=active_rates[0],
            previous_outstanding=mock_consumer["outstanding_balance"],
            credit_balance=0.0,
            last_payment_date=last_pay,
            payment_date=pay_date
        )
        
        # Write to Output Text
        breakdown_text.config(state="normal")
        breakdown_text.delete("1.0", "end")
        
        breakdown_text.insert("end", f"Water Charges Calculated  : {utils.format_currency(res['water_charge'])}\n")
        if res.get("minimum_charge_applied"):
            breakdown_text.insert("end", f"   [Applied Minimum Charge: {utils.format_currency(res['minimum_charge_amount'])}]\n")
            
        breakdown_text.insert("end", f"Fixed Renovation Charge   : {utils.format_currency(res['fixed_charge'])}\n")
        breakdown_text.insert("end", f"Meter Service Charge      : {utils.format_currency(res['meter_service_charge'])}\n")
        breakdown_text.insert("end", f"Sewerage Tax Amount       : {utils.format_currency(res['sewerage_tax'])}\n")
        breakdown_text.insert("end", f"STP Charge Amount         : {utils.format_currency(res['stp_charge'])}\n")
        breakdown_text.insert("end", f"IDS Surcharge ({res['ids_rate_pct']}% Rate)  : {utils.format_currency(res['ids_charge'])}\n")
        breakdown_text.insert("end", f"Subtotal before LPS       : {utils.format_currency(res['subtotal_before_lps'])}\n")
        breakdown_text.insert("end", f"Late Payment Surcharge    : {utils.format_currency(res['lps_amount'])} (Type: {res['lps_type']})\n")
        breakdown_text.insert("end", f"Previous Outstanding      : {utils.format_currency(res['previous_outstanding'])}\n")
        breakdown_text.insert("end", f"Total Rounded Amount (Ceil): {utils.format_currency(res['total_amount'])}\n")
        
        if res.get("is_anomaly"):
            breakdown_text.insert("end", "\n[WARNING: Flags reading anomaly detection limit!]\n")
            
        breakdown_text.config(state="disabled")

    ttk.Button(inputs_f, text="⚡ Simulate Bill", command=run_bill_simulation).grid(row=r_idx, column=1, sticky="w", pady=10, padx=5)
    
    # Load initial active rates
    load_active_rates()
    
    return frame
