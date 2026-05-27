import tkinter as tk
from tkinter import ttk, messagebox
import random
import string

def get_frame(parent, fc, utils, be, admin) -> ttk.Frame:
    frame = ttk.Frame(parent)
    
    # Title and Refresh row
    header = ttk.Frame(frame)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
    ttk.Label(header, text="Meter Reader Management", style="Title.TLabel").pack(side="left")
    ttk.Button(header, text="🔄 Refresh Readers", style="Primary.TButton", command=lambda: load_readers(use_cache=False)).pack(side="right")

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    content = ttk.Frame(frame)
    content.grid(row=1, column=0, sticky="nsew")

    # Grid layout: Left 45% List, Right 55% Editor
    content.grid_columnconfigure(0, weight=4)
    content.grid_columnconfigure(1, weight=5)
    content.grid_rowconfigure(0, weight=1)
    
    left_panel = ttk.Frame(content, padding=10)
    left_panel.grid(row=0, column=0, sticky="nsew")
    
    right_panel = ttk.Frame(content, style="Card.TFrame", padding=20)
    right_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)
    
    # Left Panel Elements
    ttk.Label(left_panel, text="Field Meter Readers", style="Header.TLabel", foreground="#1a3a6b").pack(anchor="w", pady=(0, 5))
    
    active_filter_var = tk.BooleanVar(value=False)
    filter_cb = ttk.Checkbutton(left_panel, text="Active Profiles Only", variable=active_filter_var, command=lambda: load_readers())
    filter_cb.pack(anchor="w", pady=5)
    
    tree_frame = ttk.Frame(left_panel)
    tree_frame.pack(fill="both", expand=True)
    
    tree = ttk.Treeview(tree_frame, columns=("employee_id", "role", "name", "zone", "status"), show="headings")
    tree.heading("employee_id", text="Emp ID")
    tree.heading("role", text="Role")
    tree.heading("name", text="Name")
    tree.heading("zone", text="Zone")
    tree.heading("status", text="Status")
    tree.column("employee_id", width=80, anchor="center")
    tree.column("role", width=70, anchor="center")
    tree.column("name", width=150, anchor="w")
    tree.column("zone", width=50, anchor="center")
    tree.column("status", width=70, anchor="center")
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Local cache of loaded readers
    readers_list = []
    current_selected_uid = [None]
    
    # Editor fields
    fields = {}
    
    def load_readers(use_cache=True):
        for item in tree.get_children():
            tree.delete(item)
            
        def fetch():
            return fc.list_meter_readers(active_filter_var.get(), use_cache=use_cache)
            
        def done(readers):
            nonlocal readers_list
            readers_list = readers
            for r in readers:
                status = "Active" if r.get("is_active", True) else "Inactive"
                zone = str(r.get("zone")) if r.get("zone") is not None else "All"
                tree.insert("", "end", values=(r["employee_id"], r.get("role", "Reader"), r["name"], zone, status), iid=r["uid"])
            clear_editor()
            
        utils.run_in_thread(fetch, callback=done, widget=frame)
        
    def clear_editor():
        current_selected_uid[0] = None
        for ent in fields.values():
            if not isinstance(ent, tk.BooleanVar):
                if isinstance(ent, ttk.Entry):
                    ent.delete(0, "end")
                elif isinstance(ent, ttk.Combobox):
                    ent.set("")
        # Disable editor inputs except New
        set_editor_state("disabled")
        deactivate_btn.config(state="disabled")
        reset_pwd_btn.config(state="disabled")
        
    def set_editor_state(state):
        for ent in fields.values():
            ent.config(state=state)
        save_btn.config(state=state)
        
    def on_tree_select(event):
        sel = tree.selection()
        if not sel:
            return
        uid = sel[0]
        current_selected_uid[0] = uid
        
        # Find reader details
        reader = next((r for r in readers_list if r["uid"] == uid), None)
        if not reader:
            return
            
        set_editor_state("normal")
        
        fields["name"].delete(0, "end")
        fields["name"].insert(0, reader["name"])
        
        fields["employee_id"].delete(0, "end")
        fields["employee_id"].insert(0, reader["employee_id"])
        
        fields["phone_number"].delete(0, "end")
        fields["phone_number"].insert(0, reader.get("phone_number", ""))
        
        fields["designation"].delete(0, "end")
        fields["designation"].insert(0, reader.get("designation", ""))
        
        fields["address"].delete(0, "end")
        fields["address"].insert(0, reader.get("address", ""))
        
        zone_val = str(reader["zone"]) if reader.get("zone") is not None else ""
        fields["zone"].set(zone_val)

        fields["role"].set(reader.get("role", "Reader"))
        
        # Configure buttons status
        deactivate_btn.config(state="normal")
        reset_pwd_btn.config(state="normal")
        
        is_active = reader.get("is_active", True)
        deactivate_btn.config(text="🔒 Deactivate" if is_active else "🔓 Reactivate")
        
    tree.bind("<<TreeviewSelect>>", on_tree_select)
    
    # Build Editor Interface
    ttk.Label(right_panel, text="READER PROFILE EDITOR", style="KPITitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
    row_idx = 1
    ttk.Label(right_panel, text="Name:*").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["name"] = ttk.Entry(right_panel, width=30)
    fields["name"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    ttk.Label(right_panel, text="Employee ID:*").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["employee_id"] = ttk.Entry(right_panel, width=20)
    fields["employee_id"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    ttk.Label(right_panel, text="Phone Number:").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["phone_number"] = ttk.Entry(right_panel, width=20)
    fields["phone_number"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    ttk.Label(right_panel, text="Designation:").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["designation"] = ttk.Entry(right_panel, width=25)
    fields["designation"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    ttk.Label(right_panel, text="Address:").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["address"] = ttk.Entry(right_panel, width=35)
    fields["address"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    ttk.Label(right_panel, text="Default Zone Filter:").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["zone"] = ttk.Combobox(right_panel, values=[""] + [str(z) for z in utils.ZONE_RANGE], state="readonly", width=8)
    fields["zone"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1

    ttk.Label(right_panel, text="System Role:*").grid(row=row_idx, column=0, sticky="w", pady=5)
    fields["role"] = ttk.Combobox(right_panel, values=utils.READER_ROLE_OPTIONS, state="readonly", width=15)
    fields["role"].grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    # Save edits action
    def save_edits():
        uid = current_selected_uid[0]
        if not uid:
            return
        name = fields["name"].get().strip()
        emp_id = fields["employee_id"].get().strip()
        if not name or not emp_id:
            messagebox.showerror("Error", "Required fields (*) cannot be empty.", parent=frame)
            return
            
        zone_str = fields["zone"].get()
        payload = {
            "name": name,
            "employee_id": emp_id,
            "phone_number": fields["phone_number"].get().strip() or None,
            "designation": fields["designation"].get().strip() or None,
            "address": fields["address"].get().strip() or None,
            "zone": int(zone_str) if zone_str else None,
            "role": fields["role"].get()
        }
        
        def save():
            fc.update_meter_reader(uid, payload, admin["name"])
            
        def done(res):
            messagebox.showinfo("Success", "Profile updated successfully.", parent=frame)
            load_readers()
            
        def fail(err):
            messagebox.showerror("Error", f"Failed saving edits:\n{err}", parent=frame)
            
        utils.run_in_thread(save, callback=done, error_callback=fail, widget=frame)
        
    save_btn = ttk.Button(right_panel, text="💾 Save Profile Edits", command=save_edits)
    save_btn.grid(row=row_idx, column=1, sticky="w", pady=10)
    row_idx += 1
    
    # Other actions panel
    ttk.Separator(right_panel, orient="horizontal").grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=15)
    row_idx += 1
    
    def toggle_status():
        uid = current_selected_uid[0]
        if not uid:
            return
        reader = next((r for r in readers_list if r["uid"] == uid), None)
        if not reader:
            return
        active = reader.get("is_active", True)
        action_str = "deactivate" if active else "reactivate"
        confirm = messagebox.askyesno("Confirm Toggle", f"Are you sure you want to {action_str} {reader['name']}?", parent=frame)
        if not confirm:
            return
            
        def run():
            if active:
                fc.deactivate_meter_reader(uid, admin["name"])
            else:
                fc.reactivate_meter_reader(uid, admin["name"])
                
        def done(res):
            messagebox.showinfo("Success", f"Reader profile {action_str}d successfully.", parent=frame)
            load_readers()
            
        def fail(err):
            messagebox.showerror("Error", f"Action failed:\n{err}", parent=frame)
            
        utils.run_in_thread(run, callback=done, error_callback=fail, widget=frame)

    deactivate_btn = ttk.Button(right_panel, text="🔒 Deactivate", command=toggle_status)
    deactivate_btn.grid(row=row_idx, column=0, sticky="w", pady=5)
    
    def reset_password_action():
        uid = current_selected_uid[0]
        if not uid:
            return
        reader = next((r for r in readers_list if r["uid"] == uid), None)
        
        pwd_win = tk.Toplevel(frame)
        pwd_win.title(f"Reset Password — {reader['name']}")
        pwd_win.geometry("300x180")
        pwd_win.resizable(False, False)
        pwd_win.grab_set()
        
        ttk.Label(pwd_win, text="Enter New Password:").pack(pady=10)
        pwd_ent = ttk.Entry(pwd_win, show="*", width=25)
        pwd_ent.pack(pady=2)
        pwd_ent.focus()
        
        def save():
            pwd = pwd_ent.get().strip()
            if len(pwd) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters.", parent=pwd_win)
                return
            
            def run():
                fc.reset_meter_reader_password(uid, pwd, admin["name"])
                
            def done(res):
                messagebox.showinfo("Success", "Password reset successful.", parent=frame)
                pwd_win.destroy()
                
            def fail(err):
                messagebox.showerror("Error", f"Reset failed:\n{err}", parent=pwd_win)
                
            utils.run_in_thread(run, callback=done, error_callback=fail, widget=pwd_win)
            
        ttk.Button(pwd_win, text="Reset Password", command=save).pack(pady=15)
        
    reset_pwd_btn = ttk.Button(right_panel, text="🔑 Reset Password", command=reset_password_action)
    reset_pwd_btn.grid(row=row_idx, column=1, sticky="w", pady=5)
    row_idx += 1
    
    # New reader dialog button
    def open_new_reader_dialog():
        dlg = tk.Toplevel(frame)
        dlg.title("Register New Meter Reader")
        dlg.geometry("420x450")
        dlg.grab_set()
        
        ttk.Label(dlg, text="New Reader Registration", font=("Segoe UI", 12, "bold"), foreground="#1a3a6b").pack(pady=15)
        f_dlg = ttk.Frame(dlg, padding=10)
        f_dlg.pack(fill="both", expand=True)
        
        d_fields = {}
        
        # Form
        r = 0
        ttk.Label(f_dlg, text="Name:*").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["name"] = ttk.Entry(f_dlg, width=25)
        d_fields["name"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1
        
        ttk.Label(f_dlg, text="Employee ID:*").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["emp_id"] = ttk.Entry(f_dlg, width=15)
        d_fields["emp_id"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1
        
        ttk.Label(f_dlg, text="Username (Email prefix):*").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["username"] = ttk.Entry(f_dlg, width=20)
        d_fields["username"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1
        
        # Generate password initially
        pwd_chars = string.ascii_letters + string.digits + "!@#$"
        gen_pwd = "".join(random.choice(pwd_chars) for _ in range(10))
        
        ttk.Label(f_dlg, text="Temporary Password:*").grid(row=r, column=0, sticky="w", pady=4)
        pass_f = ttk.Frame(f_dlg)
        pass_f.grid(row=r, column=1, sticky="w", pady=4)
        d_fields["password"] = ttk.Entry(pass_f, width=15)
        d_fields["password"].pack(side="left")
        d_fields["password"].insert(0, gen_pwd)
        
        def copy_pwd():
            frame.clipboard_clear()
            frame.clipboard_append(d_fields["password"].get())
            messagebox.showinfo("Clipboard", "Password copied to clipboard!", parent=dlg)
            
        ttk.Button(pass_f, text="📋 Copy", command=copy_pwd, width=6).pack(side="left", padx=5)
        r += 1
        
        ttk.Label(f_dlg, text="Phone Number:").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["phone"] = ttk.Entry(f_dlg, width=20)
        d_fields["phone"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1
        
        ttk.Label(f_dlg, text="Designation:").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["desig"] = ttk.Entry(f_dlg, width=20)
        d_fields["desig"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1
        
        ttk.Label(f_dlg, text="Address:").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["addr"] = ttk.Entry(f_dlg, width=30)
        d_fields["addr"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1
        
        ttk.Label(f_dlg, text="Default Zone Filter:").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["zone"] = ttk.Combobox(f_dlg, values=[""] + [str(z) for z in utils.ZONE_RANGE], state="readonly", width=8)
        d_fields["zone"].grid(row=r, column=1, sticky="w", pady=4)
        r += 1

        ttk.Label(f_dlg, text="System Role:*").grid(row=r, column=0, sticky="w", pady=4)
        d_fields["role"] = ttk.Combobox(f_dlg, values=utils.READER_ROLE_OPTIONS, state="readonly", width=15)
        d_fields["role"].grid(row=r, column=1, sticky="w", pady=4)
        d_fields["role"].set("Reader")
        r += 1
        
        def save():
            name = d_fields["name"].get().strip()
            emp_id = d_fields["emp_id"].get().strip()
            usr = d_fields["username"].get().strip()
            pwd = d_fields["password"].get().strip()
            
            if not name or not emp_id or not usr or not pwd:
                messagebox.showerror("Error", "Required fields (*) cannot be empty.", parent=dlg)
                return
                
            zone_val = d_fields["zone"].get()
            payload = {
                "name": name,
                "employee_id": emp_id,
                "username": usr,
                "password": pwd,
                "phone_number": d_fields["phone"].get().strip() or None,
                "designation": d_fields["desig"].get().strip() or None,
                "address": d_fields["addr"].get().strip() or None,
                "zone": int(zone_val) if zone_val else None,
                "role": d_fields["role"].get()
            }
            
            def run():
                return fc.create_meter_reader(payload, admin["name"])
                
            def success(uid_res):
                messagebox.showinfo("Success", f"User registered successfully. Auth UID:\n{uid_res}", parent=dlg)
                dlg.destroy()
                load_readers()
                
            def fail(err):
                messagebox.showerror("Registration Error", f"Failed saving user to Firebase:\n{err}", parent=dlg)
                
            utils.run_in_thread(run, callback=success, error_callback=fail, widget=dlg)
            
        ttk.Button(f_dlg, text="🚀 Save User Profile", command=save).grid(row=r, column=1, sticky="w", pady=15)
        
    ttk.Button(left_panel, text="➕ Register New Reader", command=open_new_reader_dialog).pack(pady=10)
    
    # Load initial list
    load_readers()
    
    return frame
