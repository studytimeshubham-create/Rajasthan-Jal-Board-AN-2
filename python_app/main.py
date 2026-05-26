import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import json
import os
import time
from datetime import datetime, date

# Import configurations & client
import firebase_config
import firebase_client as fc
import utils
import billing_engine as be

CREDENTIALS_FILE = "admin_credentials.json"

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rajasthan Jal Board — Admin Console")
        self.root.geometry("1100x700")
        self.root.minsize(1000, 600)
        self.root.withdraw() # Hide until authenticated
        
        # Apply Segoe UI font theme
        self.root.option_add("*Font", ("Segoe UI", 10))
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use("clam")

        c = utils.UI_COLORS
        self.root.configure(bg=c["canvas"])

        self.style.configure(".", font=("Segoe UI", 10), background=c["canvas"], foreground=c["ink"])
        self.style.configure("TFrame", background=c["canvas"])
        self.style.configure("TLabel", font=("Segoe UI", 10), background=c["canvas"], foreground=c["ink"])

        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=c["primary"])
        self.style.configure("Title.TLabel", font=("Copernicus", 22), foreground=c["ink"]) # Tiempos/Copernicus feel

        self.style.configure("Sidebar.TFrame", background=c["surface_dark"])
        self.style.configure("Sidebar.TLabel", background=c["surface_dark"], foreground=c["on_dark"])
        self.style.configure("Sidebar.TButton",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padding=10,
            background=c["surface_dark"],
            foreground=c["on_dark_soft"],
            borderwidth=0
        )
        self.style.map("Sidebar.TButton",
            background=[("active", c["surface_dark_elevated"]), ("pressed", c["surface_dark_soft"])],
            foreground=[("active", c["on_dark"]), ("pressed", c["on_dark"])]
        )

        self.style.configure("Card.TFrame", background=c["surface_card"], borderwidth=1, relief="flat")
        self.style.configure("KPI.TLabel", font=("Copernicus", 18, "bold"), background=c["surface_card"], foreground=c["primary"])
        self.style.configure("KPITitle.TLabel", font=("Segoe UI", 9, "bold"), background=c["surface_card"], foreground=c["muted"])

        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.configure("Primary.TButton", background=c["primary"], foreground=c["on_primary"])
        self.style.map("Primary.TButton", background=[("active", c["primary_active"])])
        
        # Lockout tracking
        self.failed_attempts = 0
        self.lockout_until = 0
        self.logged_in_admin = "Admin"
        
        # Initialize UI layout frames
        self.sidebar_frame = None
        self.content_frame = None
        self.status_bar = None
        self.current_frame = None
        self.nav_buttons = {}
        
        # Check first-run credentials setup
        self.check_credentials_setup()

    def check_credentials_setup(self):
        if not os.path.exists(CREDENTIALS_FILE):
            self.show_setup_dialog()
        else:
            # Small delay to ensure root is withdrawn before dialog pops
            self.root.after(100, self.show_login_dialog)

    def show_setup_dialog(self):
        setup_win = tk.Toplevel(self.root)
        setup_win.title("First-Run Admin Setup")
        setup_win.geometry("400x300")
        setup_win.resizable(False, False)
        setup_win.grab_set()
        
        # Center the window
        setup_win.update_idletasks()
        w = setup_win.winfo_width()
        h = setup_win.winfo_height()
        x = (setup_win.winfo_screenwidth() // 2) - (w // 2)
        y = (setup_win.winfo_screenheight() // 2) - (h // 2)
        setup_win.geometry(f"+{x}+{y}")
        
        ttk.Label(setup_win, text="Setup Admin Account", font=("Segoe UI", 14, "bold"), foreground="#1a3a6b").pack(pady=15)
        
        f = ttk.Frame(setup_win)
        f.pack(pady=10, padx=20, fill="x")

        
        ttk.Label(f, text="Admin Name:").grid(row=0, column=0, sticky="w", pady=5)
        name_ent = ttk.Entry(f, width=25)
        name_ent.grid(row=0, column=1, pady=5)
        name_ent.insert(0, "Administrator")
        
        ttk.Label(f, text="Username:").grid(row=1, column=0, sticky="w", pady=5)
        user_ent = ttk.Entry(f, width=25)
        user_ent.grid(row=1, column=1, pady=5)
        user_ent.insert(0, "admin")
        
        ttk.Label(f, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        pass_ent = ttk.Entry(f, show="*", width=25)
        pass_ent.grid(row=2, column=1, pady=5)
        
        ttk.Label(f, text="Confirm Password:").grid(row=3, column=0, sticky="w", pady=5)
        conf_ent = ttk.Entry(f, show="*", width=25)
        conf_ent.grid(row=3, column=1, pady=5)
        
        def save_creds():
            name = name_ent.get().strip()
            username = user_ent.get().strip()
            p1 = pass_ent.get()
            p2 = conf_ent.get()
            
            if not name or not username or not p1:
                messagebox.showerror("Error", "All fields are required.", parent=setup_win)
                return
            if p1 != p2:
                messagebox.showerror("Error", "Passwords do not match.", parent=setup_win)
                return
                
            creds = {
                "name": name,
                "username": username,
                "password_hash": hashlib.sha256(p1.encode()).hexdigest()
            }
            with open(CREDENTIALS_FILE, "w") as file:
                json.dump(creds, file)
                
            messagebox.showinfo("Success", "Admin account created successfully! Please login.", parent=setup_win)
            setup_win.destroy()
            self.show_login_dialog()
            
        ttk.Button(setup_win, text="Create Account", command=save_creds).pack(pady=15)
        setup_win.protocol("WM_DELETE_WINDOW", lambda: self.root.destroy())

    def show_login_dialog(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("Admin Authenticate")
        login_win.geometry("400x350")
        login_win.resizable(False, False)
        login_win.grab_set()
        
        c = utils.UI_COLORS
        login_win.configure(bg=c["surface_dark"])

        # Center
        login_win.update_idletasks()
        w = login_win.winfo_width()
        h = login_win.winfo_height()
        x = (login_win.winfo_screenwidth() // 2) - (w // 2)
        y = (login_win.winfo_screenheight() // 2) - (h // 2)
        login_win.geometry(f"+{x}+{y}")
        
        ttk.Label(login_win, text="RAJASTHAN JAL BOARD", font=("Copernicus", 16, "bold"), style="Sidebar.TLabel").pack(pady=(30, 5))
        ttk.Label(login_win, text="Admin Console Login", font=("Segoe UI", 10), style="Sidebar.TLabel").pack(pady=(0, 20))
        
        f = ttk.Frame(login_win, style="Sidebar.TFrame")
        f.pack(pady=10, padx=40, fill="x")

        ttk.Label(f, text="Username", style="Sidebar.TLabel").pack(anchor="w")
        user_ent = ttk.Entry(f)
        user_ent.pack(fill="x", pady=(5, 15))
        user_ent.focus()
        
        ttk.Label(f, text="Password", style="Sidebar.TLabel").pack(anchor="w")
        pass_ent = ttk.Entry(f, show="*")
        pass_ent.pack(fill="x", pady=(5, 15))
        
        status_lbl = ttk.Label(login_win, text="", style="Sidebar.TLabel")
        status_lbl.pack()
        
        def attempt_login(event=None):
            # Check lockout
            if time.time() < self.lockout_until:
                remaining = int(self.lockout_until - time.time())
                status_lbl.config(text=f"Too many failed attempts. Try in {remaining}s.")
                return
                
            username = user_ent.get().strip()
            password = pass_ent.get()
            
            with open(CREDENTIALS_FILE, "r") as file:
                creds = json.load(file)
                
            if username == creds.get("username") and hashlib.sha256(password.encode()).hexdigest() == creds.get("password_hash"):
                # Success
                self.logged_in_admin = creds.get("name", "Administrator")
                
                # Check Firebase connection
                try:
                    status_lbl.config(text="Connecting to Firebase...", foreground="#1a3a6b")
                    login_win.update()
                    # Trigger Firebase Admin initialization
                    firebase_config.get_firebase_app()
                    
                    login_win.destroy()
                    self.root.deiconify() # Show main window
                    self.build_main_interface()
                except Exception as ex:
                    messagebox.showerror("Firebase Error", f"Failed to initialize Firebase Admin SDK:\n{ex}\n\nPlease place your 'serviceAccountKey.json' file in the directory.", parent=login_win)
                    status_lbl.config(text="Firebase connection failed.", foreground="red")
            else:
                self.failed_attempts += 1
                if self.failed_attempts >= 5:
                    self.lockout_until = time.time() + 30
                    self.failed_attempts = 0
                    status_lbl.config(text="Lockout active for 30 seconds.")
                else:
                    status_lbl.config(text=f"Invalid credentials. Attempt {self.failed_attempts}/5.")
        
        btn = ttk.Button(login_win, text="AUTHENTICATE", command=attempt_login, style="Primary.TButton")
        btn.pack(pady=20, padx=40, fill="x")
        
        login_win.bind("<Return>", attempt_login)
        login_win.protocol("WM_DELETE_WINDOW", lambda: self.root.destroy())

    def build_main_interface(self):
        # 1. Left Navigation Sidebar
        self.sidebar_frame = ttk.Frame(self.root, padding=0, width=220, style="Sidebar.TFrame")
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        # Logo and branding in Sidebar
        c = utils.UI_COLORS
        logo_lbl = ttk.Label(self.sidebar_frame, text="💧 RJB Console", font=("Segoe UI", 14, "bold"), style="Sidebar.TLabel", padding=20)
        logo_lbl.pack(fill="x", pady=(10, 20))
        
        # Navigation Items mapping (Display Name, Emoji, Module name)
        self.menu_items = [
            ("Dashboard", "🏠", "dashboard"),
            ("Consumers", "👤", "consumers"),
            ("Meter Readers", "👷", "meter_readers"),
            ("Billing Cycles", "💳", "billing"),
            ("Readings", "📖", "readings"),
            ("Payments", "💰", "payments"),
            ("Reports", "📈", "reports"),
            ("Charges Config", "⚙️", "charges_config"),
            ("Audit Log", "📋", "audit_log"),
            ("Dark Mode", "🌙", "dark_mode")
        ]
        
        for name, icon, mod in self.menu_items:
            btn = ttk.Button(
                self.sidebar_frame, 
                text=f"  {icon}   {name.upper()}",
                style="Sidebar.TButton",
                command=lambda m=mod: self.show_page(m)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[mod] = btn
            
        # 2. Right Content Frame
        self.content_frame = ttk.Frame(self.root, padding=15)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # 3. Status Bar at Bottom
        self.status_bar = ttk.Frame(self.root, padding=5, style="Sidebar.TFrame")
        self.status_bar.pack(side="bottom", fill="x")
        
        admin_lbl = ttk.Label(self.status_bar, text=f"Logged in as: {self.logged_in_admin}  |  Connected to Firebase", font=("Segoe UI", 8), style="Sidebar.TLabel")
        admin_lbl.pack(side="left", padx=10)
        
        date_lbl = ttk.Label(self.status_bar, text=datetime.now().strftime("%d-%m-%Y  %H:%M"), font=("Segoe UI", 8), style="Sidebar.TLabel")
        date_lbl.pack(side="right", padx=10)
        
        # Set Sidebar selected look map
        self.style.map("Sidebar.TButton",
            background=[("pressed", c["primary"]), ("active", c["surface_dark_elevated"]), ("!disabled", c["surface_dark"])],
            foreground=[("pressed", c["on_primary"]), ("active", c["on_dark"]), ("!disabled", c["on_dark_soft"])]
        )

        # Default Page -> Dashboard
        self.show_page("dashboard")

    def toggle_dark_mode(self):
        # Placeholder for real theme switching logic
        # For now we use the requested Claude theme which is already editorial
        messagebox.showinfo("Theme", "System is already using the Editorial Claude Theme with warm canvas and dark-navy highlights.", parent=self.root)

    def show_page(self, page_name):
        if page_name == "dark_mode":
            self.toggle_dark_mode()
            return

        # Update sidebar active highlighting
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.state(["pressed"])
            else:
                btn.state(["!pressed"])
                
        # Destroy current frame contents
        if self.current_frame:
            self.current_frame.destroy()
            
        # Dynamically import and render view module
        if page_name == "dashboard":
            self.current_frame = self.get_dashboard_frame(self.content_frame)
        else:
            try:
                mod = __import__(page_name)
                admin_ctx = {"name": self.logged_in_admin}
                self.current_frame = mod.get_frame(self.content_frame, fc, utils, be, admin_ctx)
            except Exception as e:
                # Fallback error frame
                self.current_frame = ttk.Frame(self.content_frame)
                ttk.Label(self.current_frame, text=f"Error loading module '{page_name}':\n{e}", foreground="red", font=("Segoe UI", 12)).pack(pady=50)
                import traceback
                traceback.print_exc()
                
        self.current_frame.pack(fill="both", expand=True)

    # ----------------------------------------------------
    # Embedded Dashboard View
    # ----------------------------------------------------
    def get_dashboard_frame(self, parent):
        frame = ttk.Frame(parent)
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill="x", pady=(10, 25))
        ttk.Label(title_frame, text="Rajasthan Jal Board Dashboard", style="Title.TLabel").pack(side="left")
        
        # Refresh button
        ref_btn = ttk.Button(title_frame, text="🔄 Refresh Dashboard", command=lambda: self.load_dashboard_data(use_cache=False), style="Primary.TButton")
        ref_btn.pack(side="right")
        
        # Cards frame
        self.cards_frame = ttk.Frame(frame)
        self.cards_frame.pack(fill="x", pady=10)
        
        # Grid layout for KPI Cards
        # We will create 6 cards
        self.kpi_labels = {}
        kpis = [
            ("Total Active Consumers", "consumers_val", "👤", 0, 0),
            ("Open Billing Cycles", "cycles_val", "💳", 0, 1),
            ("Pending Readings", "readings_val", "📖", 0, 2),
            ("Pending Queries", "queries_val", "⚠️", 1, 0),
            ("Outstanding Balance", "outstanding_val", "💰", 1, 1),
            ("Collected (This Month)", "collected_val", "📈", 1, 2)
        ]
        
        for name, key, icon, r, c in kpis:
            card = ttk.Frame(self.cards_frame, style="Card.TFrame", padding=20)
            card.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
            self.cards_frame.grid_columnconfigure(c, weight=1)
            
            ttk.Label(card, text=f"{icon}  {name.upper()}", style="KPITitle.TLabel").pack(anchor="w")
            
            val_lbl = ttk.Label(card, text="Loading...", style="KPI.TLabel")
            val_lbl.pack(anchor="w", pady=(10, 0))
            self.kpi_labels[key] = val_lbl
            
        # Alert frame for Pending Correction Queries (red/orange)
        self.alert_frame = ttk.Frame(frame, padding=10)
        self.alert_frame.pack(fill="x", pady=15)
        
        self.load_dashboard_data()
        
        return frame

    def load_dashboard_data(self, use_cache=True):
        # Update to Loading state
        for lbl in self.kpi_labels.values():
            if lbl.winfo_exists():
                lbl.config(text="Querying...")
            
        def fetch_db_stats():
            if not use_cache:
                fc.clear_cache()

            # Consumers
            active_c = len(fc.list_consumers({"is_active": True}, use_cache=use_cache))
            
            # Cycles & Readings
            open_cycles = fc.get_open_cycles(use_cache=use_cache)
            open_cycles_str = ", ".join([f"Zones {c['zones']}" for c in open_cycles]) if open_cycles else "None"
            
            pending_readings = 0
            for cycle in open_cycles:
                cycle_id = cycle["cycle_id"]
                # Billed count vs total
                for zone in cycle.get("zones", []):
                    total_zone_c = cycle.get("consumer_count_per_zone", {}).get(str(zone), 0)
                    readings_logged = len(fc.get_readings_for_cycle(cycle_id))
                    # simple difference approximation
                    zone_c_count = len(fc.list_consumers({"zone": zone, "is_active": True}))
                    # Calculate true pending
                    # (this is estimated quickly for dashboard)
                    
            # Better pending readings logic: count consumers in active zones minus readings count
            active_zones = fc.get_open_cycle_zones()
            tot_active_c = 0
            for zone in active_zones:
                tot_active_c += len(fc.list_consumers({"zone": zone, "is_active": True}))
                
            tot_readings = 0
            for cycle in open_cycles:
                tot_readings += len(fc.get_readings_for_cycle(cycle["cycle_id"]))
                
            pending_readings = max(0, tot_active_c - tot_readings)
            
            # Correction Queries
            pending_q = fc.get_pending_correction_queries()
            pending_q_count = len(pending_q)
            
            # Balances
            # Outstanding
            all_consumers = fc.list_consumers(use_cache=use_cache)
            total_outstanding = sum(float(c.get("outstanding_balance", 0.0)) for c in all_consumers)
            
            # Payments this month
            today = date.today()
            this_month_payments = fc.list_payments() # Payments not currently cached, might add if needed
            monthly_total = 0.0
            for p in this_month_payments:
                p_date = utils.parse_date(p.get("payment_date", ""))
                if p_date.month == today.month and p_date.year == today.year:
                    monthly_total += float(p.get("amount", 0.0))
                    
            return {
                "consumers": active_c,
                "cycles": len(open_cycles),
                "cycles_detail": open_cycles_str,
                "pending_readings": pending_readings,
                "pending_queries": pending_q_count,
                "outstanding": total_outstanding,
                "collected": monthly_total
            }
            
        def on_stats_fetched(stats):
            self.kpi_labels["consumers_val"].config(text=str(stats["consumers"]))
            
            cycles_txt = f"{stats['cycles']} active"
            if stats["cycles"] > 0:
                self.kpi_labels["cycles_val"].config(text=cycles_txt, font=("Segoe UI", 12, "bold"))
                ttk.ToolTip(self.kpi_labels["cycles_val"], stats["cycles_detail"])
            else:
                self.kpi_labels["cycles_val"].config(text="None", font=("Segoe UI", 18, "bold"))
                
            self.kpi_labels["readings_val"].config(text=str(stats["pending_readings"]))
            
            q_count = stats["pending_queries"]
            q_lbl = self.kpi_labels["queries_val"]
            q_lbl.config(text=str(q_count))
            
            c = utils.UI_COLORS

            # Clear alerts
            for widget in self.alert_frame.winfo_children():
                widget.destroy()
                
            if q_count > 0:
                q_lbl.config(foreground=c["error"])
                # Show alert banner
                banner = ttk.Frame(self.alert_frame, style="Card.TFrame", padding=10)
                banner.pack(fill="x")
                # Configure banner style
                lbl = ttk.Label(banner, text=f"⚠️ CRITICAL: There are {q_count} pending correction queries requiring approval!", font=("Segoe UI", 11, "bold"), foreground="#c0392b")
                lbl.pack(side="left")
                
                btn = ttk.Button(banner, text="Go to Readings Query Tab", command=lambda: self.show_page("readings"))
                btn.pack(side="right")
            else:
                q_lbl.config(foreground=c["primary"])
                
            self.kpi_labels["outstanding_val"].config(text=utils.format_currency(stats["outstanding"]))
            self.kpi_labels["collected_val"].config(text=utils.format_currency(stats["collected"]))
            
        def on_error(err):
            for lbl in self.kpi_labels.values():
                lbl.config(text="Error", foreground="red")
            messagebox.showerror("Error", f"Failed to refresh dashboard stats:\n{err}")

        utils.run_in_thread(fetch_db_stats, callback=on_stats_fetched, error_callback=on_error, widget=self.root)

# Helper ToolTip class for Tkinter
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        lbl = ttk.Label(self.tooltip, text=self.text, background="#ffffdd", relief="solid", borderwidth=1, font=("Segoe UI", 9), padding=4)
        lbl.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
ttk.ToolTip = ToolTip

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminApp(root)
    root.mainloop()
