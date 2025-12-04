import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import threading
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import FieldFilter
from datetime import datetime
import os
import subprocess
import sys

# --- Initialize Firebase ---
cred = credentials.Certificate("modules/serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

TASKS_COLLECTION = "tasks"
EMPLOYEES_COLLECTION = "employees"


class EmployeePortalIntegrated:
    def __init__(self, root=None):
        # Use ttkbootstrap window for uniform UI
        self.root = root or ttk.Window(themename="flatly")
        self.root.title("Employee Portal - Attendance & Tasks")
        self.root.geometry("1200x700")

        self.employee_id = None
        self.employee_name = None
        self.tasks = []

        # Sidebar + container layout to match employee_management.py
        self.sidebar = ttk.Frame(self.root, padding=12)
        self.sidebar.pack(side=LEFT, fill=Y)

        ttk.Label(self.sidebar, text="Employee Portal", font=("Segoe UI", 13, "bold")).pack(pady=(0, 12))

        ttk.Button(self.sidebar, text="Attendance", width=20, bootstyle="secondary-outline", command=self.show_attendance_module).pack(pady=6)
        ttk.Button(self.sidebar, text="Tasks", width=20, bootstyle="secondary-outline", command=self.show_tasks_module).pack(pady=6)
        ttk.Separator(self.sidebar, orient=VERTICAL).pack(fill=X, pady=(10, 10))
        ttk.Button(self.sidebar, text="Logout", width=20, bootstyle="danger-outline", command=self.logout).pack(side=BOTTOM, pady=10)

        # Main container where panels will be loaded
        self.container = ttk.Frame(self.root, padding=(10, 10))
        self.container.pack(side=RIGHT, fill=BOTH, expand=True)

        # Prepare frames for animation-based switching
        self.attendance_frame = ttk.Frame(self.container)
        self.tasks_frame = ttk.Frame(self.container)

        # Start with login
        self.create_login_screen()

    def create_login_screen(self):
        # Clear container
        for w in self.container.winfo_children():
            w.destroy()

        login_frame = ttk.Frame(self.container, padding=30)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(login_frame, text="Employee Portal", font=("Segoe UI", 20, "bold")).pack(pady=(0, 10))
        ttk.Label(login_frame, text="Enter your Employee ID", font=("Segoe UI", 12)).pack(pady=(0, 8))

        self.login_id_entry = ttk.Entry(login_frame, width=30)
        self.login_id_entry.pack(pady=10)

        self.login_btn = ttk.Button(login_frame, text="Login", width=20, bootstyle="success", command=self.login)
        self.login_btn.pack(pady=8)

        self.login_status_label = ttk.Label(login_frame, text="", font=("Segoe UI", 10))
        self.login_status_label.pack(pady=(4,0))

        self.root.bind('<Return>', lambda e: self.login())
        self.root.bind('<Escape>', lambda e: self.root.quit())

    def login(self):
        emp_id = self.login_id_entry.get().strip()
        if not emp_id:
            messagebox.showerror("Error", "Please enter your Employee ID")
            return
        # run Firestore lookup in background thread to avoid blocking UI
        self.login_status_label.config(text="Checking employee ID...")
        self.login_btn.state(['disabled'])
        threading.Thread(target=self._login_worker, args=(emp_id,), daemon=True).start()

    def _login_worker(self, emp_id):
        error = None
        doc = None
        try:
            doc = db.collection(EMPLOYEES_COLLECTION).document(emp_id).get()
        except Exception as e:
            error = str(e)
        # schedule finish on main thread
        self.root.after(0, lambda: self._finish_login(emp_id, doc, error))

    def _finish_login(self, emp_id, doc, error):
        self.login_btn.state(['!disabled'])
        if error:
            self.login_status_label.config(text=f"Error: {error}")
            messagebox.showerror("Error", f"Failed to check employee ID:\n{error}")
            return
        if doc is None or not getattr(doc, 'exists', False):
            self.login_status_label.config(text="Employee ID not found")
            messagebox.showerror("Error", "Employee ID not found")
            return
        # success
        self.employee_id = emp_id
        emp_data = doc.to_dict()
        self.employee_name = emp_data.get("Name", "Employee")
        # remove login widgets
        for w in self.container.winfo_children():
            w.destroy()
        # create tasks frame and load tasks immediately before showing UI
        if not hasattr(self, 'tasks_frame') or not getattr(self.tasks_frame, 'winfo_exists', lambda: False)():
            self.tasks_frame = ttk.Frame(self.container)
        if not getattr(self.tasks_frame, 'winfo_ismapped', lambda: False)():
            self.create_tasks_tab(self.tasks_frame)
        # load tasks synchronously so they're ready instantly
        self.load_tasks()
        # show attendance module by default (tasks are pre-cached)
        self.show_attendance_module()
        # start auto-refresh timer for tasks
        self._schedule_auto_refresh()

    def _create_header(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill=X)
        ttk.Label(header, text=f"Welcome, {self.employee_name} (ID: {self.employee_id})", font=("Segoe UI", 14, "bold")).pack(side=LEFT, padx=8, pady=8)
        return header

    def animate_switch(self, from_frame, to_frame, duration=200):
        # Simple horizontal slide animation inside self.container
        container_w = self.container.winfo_width() or 1000
        steps = 10
        delay = int(duration / steps)

        # ensure frames exist
        if from_frame is not None:
            try:
                exists = from_frame.winfo_exists()
            except Exception:
                exists = False
            if not exists:
                from_frame = None

        try:
            to_frame.place(in_=self.container, x=container_w, y=0, relheight=1, relwidth=1)
        except Exception:
            # recreate to_frame if it's invalid
            to_frame = ttk.Frame(self.container)
            to_frame.place(in_=self.container, x=container_w, y=0, relheight=1, relwidth=1)

        def slide(step=0):
            if step > steps:
                if from_frame:
                    try:
                        from_frame.place_forget()
                    except Exception:
                        pass
                try:
                    to_frame.place(x=0, y=0, relheight=1, relwidth=1)
                except Exception:
                    pass
                return
            dx = int(container_w * (1 - step / steps))
            to_frame.place(x=dx, y=0, relheight=1, relwidth=1)
            self.root.after(delay, lambda: slide(step + 1))

        slide()

    def switch_tab(self, tab_name):
        if tab_name == "Attendance":
            self.animate_switch(self.tasks_frame, self.attendance_frame)
        else:
            self.animate_switch(self.attendance_frame, self.tasks_frame)
            self.load_tasks()

    def create_attendance_tab(self, parent):
        # parent is self.attendance_frame
        for w in parent.winfo_children():
            w.destroy()

        header = self._create_header(parent)

        body = ttk.Frame(parent)
        body.pack(fill=BOTH, expand=True, padx=12, pady=8)

        # Left controls panel
        left_ctrl = ttk.Frame(body, width=220)
        left_ctrl.pack(side=LEFT, fill=Y, padx=(0, 8))

        ttk.Label(left_ctrl, text="Attendance", font=("Segoe UI", 12, "bold")).pack(pady=(10, 6))
        ttk.Button(left_ctrl, text="Mark Attendance", bootstyle="success-outline", command=self.mark_attendance).pack(fill=X, pady=6, padx=6)
        ttk.Label(left_ctrl, text="", font=("Segoe UI", 10)).pack(pady=10)
        ttk.Button(left_ctrl, text="Refresh", bootstyle="info-outline", command=lambda: None).pack(fill=X, pady=6, padx=6)

        # Right panel: info card
        right = ttk.Frame(body)
        right.pack(side=LEFT, fill=BOTH, expand=True)

        info_card = ttk.Labelframe(right, text="Profile", padding=12)
        info_card.pack(fill=X, pady=(6, 12))

        ttk.Label(info_card, text=f"Name: {self.employee_name}", font=("Segoe UI", 11)).pack(anchor=W)
        ttk.Label(info_card, text=f"ID: {self.employee_id}", font=("Segoe UI", 11)).pack(anchor=W)
        ttk.Label(info_card, text=f"Date: {datetime.now().strftime('%A, %d %b %Y')}", font=("Segoe UI", 10)).pack(anchor=W, pady=(6,0))

        self.attendance_status_label = ttk.Label(right, text="", font=("Segoe UI", 10, "bold"))
        self.attendance_status_label.pack(pady=8)

    def mark_attendance(self):
        try:
            # Check if attendance already marked for today
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            existing = db.collection("attendance").where(
                filter=FieldFilter("employee_id", "==", self.employee_id)
            ).where(
                filter=FieldFilter("date", "==", today_date)
            ).stream()
            
            existing_list = list(existing)
            if existing_list:
                messagebox.showinfo(
                    "Attendance",
                    "Attendance already marked"
                )
                self.attendance_status_label.configure(text="⚠ Attendance already marked for today!")
                return
            
            confirm = messagebox.askyesno(
                "Confirm Attendance",
                f"Mark attendance for {self.employee_name}?"
            )
            if confirm:
                now = datetime.now()
                db.collection("attendance").add({
                    "employee_id": self.employee_id,
                    "employee_name": self.employee_name,
                    "timestamp": now,
                    "date": now.strftime("%Y-%m-%d"),
                    "status": "Present"
                })
                self.attendance_status_label.configure(text="✓ Attendance marked successfully!")
                messagebox.showinfo("Success", "Attendance marked successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark attendance: {str(e)}")

    def create_tasks_tab(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        header = self._create_header(parent)

        body = ttk.Frame(parent)
        body.pack(fill=BOTH, expand=True, padx=12, pady=8)

        # Left controls: moved from bottom to left side
        left_ctrl = ttk.Frame(body, width=220)
        left_ctrl.pack(side=LEFT, fill=Y, padx=(0, 8))

        ttk.Label(left_ctrl, text="Tasks", font=("Segoe UI", 12, "bold")).pack(pady=(10, 6))
        self.filter_status = ttk.Combobox(left_ctrl, values=["All", "Pending", "In Progress", "Completed", "Incomplete"], state="readonly")
        self.filter_status.set("All")
        self.filter_status.pack(fill=X, padx=6, pady=6)
        ttk.Button(left_ctrl, text="Apply Filter", bootstyle="info", command=self.load_tasks).pack(fill=X, padx=6, pady=6)

        ttk.Button(left_ctrl, text="Update Task", bootstyle="primary", command=self.update_selected_task).pack(fill=X, padx=6, pady=(20,6))
        ttk.Button(left_ctrl, text="Refresh", bootstyle="secondary", command=self.load_tasks).pack(fill=X, padx=6, pady=6)

        # Right: table + summary
        right = ttk.Frame(body)
        right.pack(side=LEFT, fill=BOTH, expand=True)

        self.summary_label = ttk.Label(right, text="", font=("Segoe UI", 10, "bold"))
        self.summary_label.pack(pady=6)

        columns = ("task", "priority", "deadline", "status")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=12)
        for col, heading in zip(columns, ["Task", "Priority", "Deadline", "Status"]):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=200, anchor=W)
        self.tree.pack(fill=BOTH, expand=True, padx=6, pady=6)
        self.tree.bind('<Double-1>', lambda e: self.open_update_window_from_tree())

    def load_tasks(self):
        # populate ttk.Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        selected_status = self.filter_status.get()
        self.tasks = []

        try:
            tasks_ref = db.collection(TASKS_COLLECTION).where("assign_to", "==", self.employee_id).stream()
            completed = pending = in_progress = incomplete = 0
            task_count = 0
            for task in tasks_ref:
                task_data = task.to_dict()
                task_id = task.id
                status = task_data.get("status", "")
                if selected_status != "All" and status != selected_status:
                    continue
                if status == "Completed":
                    completed += 1
                elif status == "Pending":
                    pending += 1
                elif status == "In Progress":
                    in_progress += 1
                elif status == "Incomplete":
                    incomplete += 1

                self.tasks.append((task_id, task_data))
                self.tree.insert("", "end", iid=task_id, values=(task_data.get("task", ""), task_data.get("priority", ""), task_data.get("deadline", ""), status))
                task_count += 1

            summary_text = f"Total: {task_count} | Pending: {pending} | In Progress: {in_progress} | Completed: {completed} | Incomplete: {incomplete}"
            self.summary_label.config(text=summary_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {str(e)}")

    def open_update_window(self, task_id, task_data):
        update_window = tk.Toplevel(self.root)
        update_window.title("Update Task Status")
        update_window.geometry("520x380")
        update_window.transient(self.root)
        update_window.grab_set()

        ttk.Label(update_window, text="Update Task Status", font=("Segoe UI", 14, "bold")).pack(pady=10)

        info = ttk.Labelframe(update_window, text="Task Info", padding=8)
        info.pack(fill=X, padx=10, pady=6)
        ttk.Label(info, text=task_data.get("task", "N/A"), font=("Segoe UI", 11)).pack(anchor=W)

        ttk.Label(update_window, text="Update Status:", font=("Segoe UI", 11)).pack(anchor=W, padx=10, pady=(6,2))
        status_cb = ttk.Combobox(update_window, values=["Pending", "In Progress", "Completed", "Incomplete"], state="readonly")
        status_cb.set(task_data.get("status", "Pending"))
        status_cb.pack(fill=X, padx=10)

        ttk.Label(update_window, text="Remarks:", font=("Segoe UI", 11)).pack(anchor=W, padx=10, pady=(6,2))
        remarks = tk.Text(update_window, height=8)
        remarks.pack(fill=BOTH, padx=10, pady=(0,6), expand=True)

        # Bottom frame for actions to ensure visibility
        action_frame = ttk.Frame(update_window)
        action_frame.pack(fill=X, padx=10, pady=8)

        status_msg = ttk.Label(action_frame, text="", font=("Segoe UI", 10))
        status_msg.pack(side=LEFT, padx=(0,10))

        def update_task():
            new_status = status_cb.get()
            remark = remarks.get("1.0", "end").strip()
            try:
                db.collection(TASKS_COLLECTION).document(task_id).update({
                    "status": new_status,
                    "last_updated": datetime.utcnow().isoformat(),
                    "last_remark": remark
                })
                status_msg.config(text="✓ Updated successfully")
                # Update tree immediately
                if task_id in [iid for iid, _ in self.tasks]:
                    self.tree.item(task_id, values=(task_data.get("task", ""), task_data.get("priority", ""), task_data.get("deadline", ""), new_status))
                messagebox.showinfo("Success", "Task updated successfully!")
                update_window.destroy()
                self.load_tasks()
            except Exception as e:
                status_msg.config(text="✗ Failed")
                messagebox.showerror("Error", f"Failed to update task: {str(e)}")

        # Confirm Update button at bottom right
        confirm_btn = ttk.Button(action_frame, text="Confirm Update", bootstyle="success", command=update_task)
        confirm_btn.pack(side=RIGHT)

        cancel_btn = ttk.Button(action_frame, text="Cancel", bootstyle="secondary", command=update_window.destroy)
        cancel_btn.pack(side=RIGHT, padx=(0, 6))

        # Bind Enter to confirm and Esc to cancel
        update_window.bind('<Return>', lambda e: confirm_btn.invoke())
        update_window.bind('<Escape>', lambda e: update_window.destroy())
        remarks.focus_set()

    def open_update_window_from_tree(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = sel[0]
        task_data = next((t for tid, t in self.tasks if tid == task_id), None)
        if task_data:
            self.open_update_window(task_id, task_data)

    def update_selected_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "No task selected")
            return
        self.open_update_window_from_tree()

    def show_attendance_module(self):
        # prepare frame if empty
        # recreate frame if it was destroyed
        if not hasattr(self, 'attendance_frame') or not getattr(self.attendance_frame, 'winfo_exists', lambda: False)():
            self.attendance_frame = ttk.Frame(self.container)
        if not getattr(self.attendance_frame, 'winfo_ismapped', lambda: False)():
            self.create_attendance_tab(self.attendance_frame)
        self.animate_switch(getattr(self, 'current_frame', None), self.attendance_frame)
        self.current_frame = self.attendance_frame

    def show_tasks_module(self):
        if not hasattr(self, 'tasks_frame') or not getattr(self.tasks_frame, 'winfo_exists', lambda: False)():
            self.tasks_frame = ttk.Frame(self.container)
        if not getattr(self.tasks_frame, 'winfo_ismapped', lambda: False)():
            self.create_tasks_tab(self.tasks_frame)
        self.animate_switch(getattr(self, 'current_frame', None), self.tasks_frame)
        self.current_frame = self.tasks_frame

    def logout(self):
        """Logout: disconnect Firebase and close the app window.

        Behavior:
        - Cancels auto-refresh timer
        - Deletes any initialized firebase apps to disconnect from Firestore.
        - Closes the tkinter window (triggers clean exit via daemon threads).
        """
        # Cancel auto-refresh timer
        try:
            if hasattr(self, 'refresh_timer'):
                try:
                    self.root.after_cancel(self.refresh_timer)
                except Exception:
                    pass
        except Exception:
            pass

        # Disconnect Firebase apps
        try:
            if hasattr(firebase_admin, '_apps') and firebase_admin._apps:
                for name, app_obj in list(firebase_admin._apps.items()):
                    try:
                        firebase_admin.delete_app(app_obj)
                    except Exception:
                        pass
        except Exception:
            pass

        # Close the GUI window
        # Attempt to shut down Flask server (if running) to free port
        try:
            try:
                requests.post('http://127.0.0.1:5000/shutdown', timeout=2)
            except Exception:
                pass
        except Exception:
            pass

        # Relaunch login (main.py) so user can sign in again
        try:
            script_path = os.path.join(os.path.dirname(__file__), "main.py")
            if os.path.exists(script_path):
                try:
                    subprocess.Popen([sys.executable, script_path])
                except Exception as e:
                    try:
                        messagebox.showwarning("Warning", f"Failed to reopen login window:\n{e}")
                    except Exception:
                        pass
        except Exception:
            pass

        # Close GUI and exit process
        try:
            try:
                self.root.quit()
            except Exception:
                try:
                    self.root.destroy()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            os._exit(0)
        except Exception:
            import atexit
            atexit._exithandlers.clear()
            sys.exit(0)

    def _schedule_auto_refresh(self):
        """Schedule periodic task refresh every 15 seconds."""
        try:
            # only refresh if on tasks tab and tree exists
            if hasattr(self, 'tree') and getattr(self, 'current_frame', None) == self.tasks_frame:
                self.load_tasks()
        except Exception:
            pass
        # reschedule in 15 seconds (1000 ms)
        self.refresh_timer = self.root.after(1000, self._schedule_auto_refresh)

    def _load_tasks_on_login(self):
        """Load employee tasks immediately after login (called from main thread)."""
        try:
            # ensure tasks frame is created and populated
            if not hasattr(self, 'tasks_frame') or not getattr(self.tasks_frame, 'winfo_exists', lambda: False)():
                self.tasks_frame = ttk.Frame(self.container)
            if not getattr(self.tasks_frame, 'winfo_ismapped', lambda: False)():
                self.create_tasks_tab(self.tasks_frame)
            # load tasks into the tree
            self.load_tasks()
        except Exception as e:
            print(f"Error loading tasks on login: {e}")


if __name__ == "__main__":
    app = EmployeePortalIntegrated()
    try:
        app.root.protocol("WM_DELETE_WINDOW", app.logout)
    except Exception:
        pass
    app.root.mainloop()
