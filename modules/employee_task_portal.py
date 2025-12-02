import tkinter as tk
from tkinter import ttk, messagebox
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Firebase initialization
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("modules/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

TASKS_COLLECTION = "tasks"
EMPLOYEES_COLLECTION = "employees"


class EmployeeTaskPortal:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Task Portal")
        self.root.state("zoomed")  # Fullscreen with title bar
        self.root.configure(bg="#f4f6f8")

        self.employee_id = None
        self.tasks = []

        self.create_login_ui()

    # ---------------- LOGIN SCREEN ----------------
    def create_login_ui(self):
        self.login_frame = tk.Frame(self.root, bg="#f4f6f8")
        self.login_frame.pack(expand=True)

        title = tk.Label(
            self.login_frame,
            text="Employee Task Portal",
            font=("Arial", 28, "bold"),
            fg="#333",
            bg="#f4f6f8",
        )
        title.pack(pady=20)

        form_frame = tk.Frame(self.login_frame, bg="#f4f6f8")
        form_frame.pack(pady=20)

        tk.Label(
            form_frame, text="Enter Employee ID:", font=("Arial", 14), bg="#f4f6f8"
        ).grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.employee_id_entry = tk.Entry(
            form_frame, font=("Arial", 14), width=25, bd=2, relief="groove"
        )
        self.employee_id_entry.grid(row=0, column=1, padx=10, pady=10)

        login_btn = tk.Button(
            self.login_frame,
            text="Login",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5,
            command=self.login,
        )
        login_btn.pack(pady=10)

    def login(self):
        emp_id = self.employee_id_entry.get().strip()
        if not emp_id:
            messagebox.showerror("Error", "Please enter your Employee ID")
            return

        doc = db.collection(EMPLOYEES_COLLECTION).document(emp_id).get()
        if not doc.exists:
            messagebox.showerror("Error", "Employee ID not found")
            return

        self.employee_id = emp_id
        self.login_frame.destroy()
        self.create_dashboard_ui()

    # ---------------- DASHBOARD ----------------
    def create_dashboard_ui(self):
        self.dashboard_frame = tk.Frame(self.root, bg="#f4f6f8")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(self.dashboard_frame, bg="#2c3e50", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            sidebar,
            text=f"ID: {self.employee_id}",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 14, "bold"),
            pady=20,
        ).pack()

        tk.Label(
            sidebar, text="Filter by Status:", bg="#2c3e50", fg="white", font=("Arial", 12)
        ).pack(pady=(20, 5))

        self.filter_status = ttk.Combobox(
            sidebar,
            values=["All", "Pending", "In Progress", "Completed", "Incomplete"],
            state="readonly",
        )
        self.filter_status.set("All")
        self.filter_status.pack(padx=10, pady=5, fill="x")

        tk.Button(
            sidebar,
            text="Apply Filter",
            command=self.load_tasks,
            bg="#1abc9c",
            fg="white",
            font=("Arial", 12, "bold"),
        ).pack(pady=10, fill="x", padx=10)

        # Main Content
        content_frame = tk.Frame(self.dashboard_frame, bg="#f4f6f8")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.summary_label = tk.Label(
            content_frame,
            text="",
            font=("Arial", 12, "bold"),
            bg="#f4f6f8",
            fg="#333",
        )
        self.summary_label.pack(pady=10)

        style = ttk.Style()
        style.configure(
            "Treeview.Heading", font=("Arial", 12, "bold"), background="#ddd"
        )
        style.configure("Treeview", font=("Arial", 11), rowheight=28)

        self.tree = ttk.Treeview(
            content_frame,
            columns=("Task", "Priority", "Deadline", "Status"),
            show="headings",
        )
        for col in ["Task", "Priority", "Deadline", "Status"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=180)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.open_update_window)

        self.load_tasks()

    def load_tasks(self):
        selected_status = self.filter_status.get()
        self.tree.delete(*self.tree.get_children())
        self.tasks = []

        tasks_ref = db.collection(TASKS_COLLECTION).where(
            "assign_to", "==", self.employee_id
        ).stream()
        completed, pending, in_progress, incomplete = 0, 0, 0, 0

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

            self.tree.insert(
                "",
                "end",
                iid=task_id,
                values=(
                    task_data.get("task", ""),
                    task_data.get("priority", ""),
                    task_data.get("deadline", ""),
                    status,
                ),
            )
            self.tasks.append((task_id, task_data))

        summary_text = f"Total: {len(self.tasks)} | Pending: {pending} | In Progress: {in_progress} | Completed: {completed} | Incomplete: {incomplete}"
        self.summary_label.config(text=summary_text)

    def open_update_window(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        task_id = selected[0]
        task_data = next((td for tid, td in self.tasks if tid == task_id), None)
        if not task_data:
            return

        update_window = tk.Toplevel(self.root)
        update_window.title("Update Task Status")
        update_window.geometry("400x250")
        update_window.configure(bg="#f4f6f8")

        tk.Label(
            update_window, text="Task:", font=("Arial", 12, "bold"), bg="#f4f6f8"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        tk.Label(
            update_window, text=task_data.get("task", ""), font=("Arial", 12), bg="#f4f6f8"
        ).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        tk.Label(
            update_window, text="Update Status:", font=("Arial", 12), bg="#f4f6f8"
        ).grid(row=1, column=0, padx=10, pady=5, sticky="e")
        status_cb = ttk.Combobox(
            update_window,
            values=["Pending", "In Progress", "Completed", "Incomplete"],
            state="readonly",
        )
        status_cb.set(task_data.get("status", ""))
        status_cb.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(
            update_window, text="Remarks:", font=("Arial", 12), bg="#f4f6f8"
        ).grid(row=2, column=0, padx=10, pady=5, sticky="e")
        remarks_entry = tk.Entry(update_window, width=30, font=("Arial", 11))
        remarks_entry.grid(row=2, column=1, padx=10, pady=5)

        def update_task():
            new_status = status_cb.get()
            remark = remarks_entry.get()
            db.collection(TASKS_COLLECTION).document(task_id).update(
                {
                    "status": new_status,
                    "last_updated": datetime.utcnow().isoformat(),
                    "last_remark": remark,
                }
            )
            messagebox.showinfo("Success", "Task updated successfully!")
            update_window.destroy()
            self.load_tasks()

        tk.Button(
            update_window,
            text="Update",
            command=update_task,
            bg="#0099FF",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=5,
        ).grid(row=3, columnspan=2, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeTaskPortal(root)
    root.mainloop()
