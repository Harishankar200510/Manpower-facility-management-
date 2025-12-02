import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys

# --- User Setup ---
USERS = {
    "admin": {"password": "admin123", "script": "modules/employee_management.py"},
    "employee": {"password": "emp123", "script": "modules/employee_portal_integrated.py"}
}


def open_login_window():
    # Use ttkbootstrap Window for consistency with other modules
    root = ttk.Window(themename="flatly")
    root.title("Employee Management System - Login")
    root.geometry("700x420")
    root.resizable(False, False)

    # Left sidebar (visual parity with other modules)
    sidebar = ttk.Frame(root, padding=12)
    sidebar.pack(side=LEFT, fill=Y)

    ttk.Label(sidebar, text="Welcome", font=("Segoe UI", 16, "bold")).pack(pady=(6, 12))
    ttk.Label(sidebar, text="Sign in to continue", font=("Segoe UI", 10)).pack(pady=(0, 20))
    ttk.Separator(sidebar, orient=VERTICAL).pack(fill=X, pady=(10, 10))

    # Right main area: login form
    main = ttk.Frame(root, padding=20)
    main.pack(side=RIGHT, fill=BOTH, expand=True)

    ttk.Label(main, text="Login Portal", font=("Segoe UI", 20, "bold")).pack(pady=(6, 18))

    # Username
    username_var = tk.StringVar()
    ttk.Label(main, text="Username", font=("Segoe UI", 10)).pack(anchor=W, padx=6)
    username_entry = ttk.Entry(main, textvariable=username_var, width=40)
    username_entry.pack(pady=(4, 8))

    # Password
    password_var = tk.StringVar()
    ttk.Label(main, text="Password", font=("Segoe UI", 10)).pack(anchor=W, padx=6)
    password_entry = ttk.Entry(main, textvariable=password_var, show="*", width=40)
    password_entry.pack(pady=(4, 8))

    # Show password
    show_password_var = tk.BooleanVar(value=False)

    def toggle_show():
        password_entry.configure(show="" if show_password_var.get() else "*")

    ttk.Checkbutton(main, text="Show Password", variable=show_password_var, bootstyle="secondary", command=toggle_show).pack(anchor=W, padx=4)

    # Spacer
    ttk.Label(main, text="").pack(pady=6)

    # Login function
    def login(event=None):
        username = username_var.get().strip()
        password = password_var.get().strip()
        if username in USERS and USERS[username]["password"] == password:
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            script_path = USERS[username]["script"]
            # Close login window and open target script
            try:
                root.destroy()
            except Exception:
                pass
            try:
                # Launch the target module with the same Python interpreter
                subprocess.Popen([sys.executable, script_path, "--fullscreen"])
            except Exception as e:
                messagebox.showerror("Error", f"Unable to open {script_path}\n{e}")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    # Buttons
    btn_frame = ttk.Frame(main)
    btn_frame.pack(pady=(10, 4))

    login_btn = ttk.Button(btn_frame, text="Login", width=18, bootstyle="success", command=login)
    login_btn.pack(side=LEFT, padx=8)

    quit_btn = ttk.Button(btn_frame, text="Quit", width=10, bootstyle="danger-outline", command=lambda: root.destroy())
    quit_btn.pack(side=LEFT, padx=8)

    # Key bindings
    root.bind('<Return>', login)
    root.bind('<Escape>', lambda e: root.destroy())

    # Start event loop with graceful KeyboardInterrupt handling
    try:
        root.mainloop()
    except KeyboardInterrupt:
        try:
            root.destroy()
        except Exception:
            pass
        sys.exit(0)


if __name__ == '__main__':
    open_login_window()
