import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl
import json
from datetime import datetime

def get_frame(parent, fc, utils, be, admin) -> ttk.Frame:
    frame = ttk.Frame(parent, padding=30)
    
    # Title and Refresh row
    header = ttk.Frame(frame)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 30))
    ttk.Label(header, text="SECURITY AUDIT TIMELINE", style="KPITitle.TLabel").pack(side="left")
    ttk.Button(header, text="🔄 Refresh Logs", style="Primary.TButton", command=lambda: refresh_logs()).pack(side="right")
    
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(2, weight=1)

    # Filters
    f_frame = ttk.Frame(frame, style="Card.TFrame", padding=15)
    f_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
    
    ttk.Label(f_frame, text="Date From:").pack(side="left", padx=3)
    from_ent = ttk.Entry(f_frame, width=10)
    from_ent.pack(side="left", padx=3)
    from_ent.insert(0, utils.today_str())
    
    ttk.Label(f_frame, text="Date To:").pack(side="left", padx=3)
    to_ent = ttk.Entry(f_frame, width=10)
    to_ent.pack(side="left", padx=3)
    to_ent.insert(0, utils.today_str())
    
    ttk.Label(f_frame, text="Action:").pack(side="left", padx=3)
    action_var = tk.StringVar(value="All")
    # Define common actions
    actions_options = ["All", "CREATE_CONSUMER", "UPDATE_CONSUMER", "DEACTIVATE_CONSUMER", "REACTIVATE_CONSUMER", "CREATE_BILLING_CYCLE", "CLOSE_BILLING_CYCLE", "ADMIN_UPDATE_READING", "APPROVE_CORRECTION_QUERY", "REJECT_CORRECTION_QUERY", "RECORD_PAYMENT", "LPS_WAIVER", "ADD_CUSTOM_ADJUSTMENT", "RECORD_METER_REPLACEMENT", "UPDATE_CHARGES_CONFIG", "CREATE_METER_READER", "UPDATE_METER_READER", "DEACTIVATE_METER_READER", "RESET_METER_READER_PASSWORD"]
    action_cb = ttk.Combobox(f_frame, textvariable=action_var, values=actions_options, width=18, state="readonly")
    action_cb.pack(side="left", padx=3)
    
    ttk.Label(f_frame, text="Admin:").pack(side="left", padx=3)
    admin_ent = ttk.Entry(f_frame, width=12)
    admin_ent.pack(side="left", padx=3)
    
    # Grid treeview
    tree_columns = ("timestamp", "action", "by", "target", "old_val", "new_val")
    tree_container = ttk.Frame(frame)
    tree_container.grid(row=2, column=0, sticky="nsew")

    tree = ttk.Treeview(tree_container, columns=tree_columns, show="headings")
    tree.heading("timestamp", text="Timestamp")
    tree.heading("action", text="Action Type")
    tree.heading("by", text="Performed By")
    tree.heading("target", text="Target Doc")
    tree.heading("old_val", text="Old Value (Truncated)")
    tree.heading("new_val", text="New Value (Truncated)")
    
    tree.column("timestamp", width=120, anchor="center")
    tree.column("action", width=150, anchor="center")
    tree.column("by", width=100)
    tree.column("target", width=150)
    tree.column("old_val", width=180)
    tree.column("new_val", width=180)
    
    scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    logs_cache = {}
    
    def refresh_logs():
        for r in tree.get_children():
            tree.delete(r)
            
        act_f = action_var.get()
        adm_f = admin_ent.get().strip()
        
        filters = {
            "date_from": from_ent.get().strip(),
            "date_to": to_ent.get().strip()
        }
        if act_f != "All":
            filters["action_type"] = act_f
        if adm_f:
            filters["performed_by"] = adm_f
            
        def fetch():
            fc.clear_cache() # Always fresh for audit
            return fc.get_audit_log(filters)
            
        def done(logs):
            for l in logs:
                logs_cache[l["log_id"]] = l
                # Truncate old/new values for table display
                old_trunc = str(l.get("old_value") or "")
                if len(old_trunc) > 50: old_trunc = old_trunc[:47] + "..."
                
                new_trunc = str(l.get("new_value") or "")
                if len(new_trunc) > 50: new_trunc = new_trunc[:47] + "..."
                
                # Format timestamp
                ts = l.get("timestamp")
                ts_str = "—"
                if ts:
                    try:
                        if hasattr(ts, "to_datetime"):
                            ts_str = ts.to_datetime().strftime("%d-%m-%Y %H:%M:%S")
                        elif isinstance(ts, datetime):
                            ts_str = ts.strftime("%d-%m-%Y %H:%M:%S")
                        else:
                            s = str(ts)
                            if "Z" in s:
                                s = s.replace("Z", "+00:00")
                            ts_str = datetime.fromisoformat(s).strftime("%d-%m-%Y %H:%M:%S")
                    except:
                        ts_str = str(ts)
                    
                tree.insert("", "end", values=(
                    ts_str,
                    l["action_type"],
                    l.get("performed_by_name"),
                    l.get("target_document"),
                    old_trunc,
                    new_trunc
                ), iid=l["log_id"])
                
        utils.run_in_thread(fetch, callback=done, widget=frame)

    ttk.Button(f_frame, text="🔄 Load / Refresh", command=refresh_logs).pack(side="left", padx=15)
    
    def export_excel():
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], title="Save Audit Log")
        if not path:
            return
        def run():
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Audit Log"
            ws.append(["Timestamp", "Action Type", "Performed By", "Target Document", "Old Value JSON", "New Value JSON"])
            for l_id, l in logs_cache.items():
                ts = l.get("timestamp")
                ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
                ws.append([
                    ts_str,
                    l["action_type"],
                    l.get("performed_by_name"),
                    l.get("target_document"),
                    json.dumps(l.get("old_value")),
                    json.dumps(l.get("new_value"))
                ])
            wb.save(path)
        def done(res): messagebox.showinfo("Success", "Spreadsheet saved.", parent=frame)
        utils.run_in_thread(run, callback=done, widget=frame)
        
    ttk.Button(f_frame, text="📤 Export Excel", command=export_excel).pack(side="right", padx=5)
    
    # Double click details popup
    def on_row_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        log_id = sel[0]
        l = logs_cache.get(log_id)
        if not l:
            return
            
        dlg = tk.Toplevel(frame)
        dlg.title(f"Log Inspection — {log_id}")
        dlg.geometry("800x600")
        dlg.configure(bg="#F9F7F2")
        dlg.grab_set()
        
        f = ttk.Frame(dlg, padding=30)
        f.pack(fill="both", expand=True)
        
        ttk.Label(f, text=f"AUDIT LOG: {log_id}", style="KPITitle.TLabel").pack(anchor="w", pady=(0, 5))
        ttk.Label(f, text=f"{l['action_type']} performed by {l.get('performed_by_name')}", style="Muted.TLabel").pack(anchor="w", pady=(0, 25))
        
        # Grid for old vs new textboxes
        text_f = ttk.Frame(f)
        text_f.pack(fill="both", expand=True)
        
        text_f.grid_columnconfigure(0, weight=1)
        text_f.grid_columnconfigure(1, weight=1)
        text_f.grid_rowconfigure(1, weight=1)
        
        ttk.Label(text_f, text="PREVIOUS STATE", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        old_txt = tk.Text(text_f, wrap="word", font=("JetBrains Mono", 10), bg="#FFFFFF", fg="#2D3436", relief="flat", padx=10, pady=10)
        old_txt.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=5)
        old_txt.insert("1.0", json.dumps(l.get("old_value"), indent=2) if l.get("old_value") is not None else "No previous record")
        old_txt.config(state="disabled")
        
        ttk.Label(text_f, text="NEW STATE", style="Muted.TLabel").grid(row=0, column=1, sticky="w", pady=(0, 10))
        new_txt = tk.Text(text_f, wrap="word", font=("JetBrains Mono", 10), bg="#FFFFFF", fg="#2D3436", relief="flat", padx=10, pady=10)
        new_txt.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=5)
        new_txt.insert("1.0", json.dumps(l.get("new_value"), indent=2) if l.get("new_value") is not None else "No new record")
        new_txt.config(state="disabled")
        
    tree.bind("<Double-1>", on_row_double_click)
    
    # Store handle
    frame.refresh_logs = refresh_logs
    
    return frame
