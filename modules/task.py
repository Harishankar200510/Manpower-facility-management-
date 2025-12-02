
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from tkinter import messagebox
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import threading
import time
from datetime import datetime
import os
import logging

# Constants
TASKS_COLLECTION = "tasks"
EMPLOYEES_COLLECTION = "employees"
STATUS_PENDING = "Pending"
STATUS_INCOMPLETE = "Incomplete"
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate("modules/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
logging.basicConfig(level=logging.INFO)

def send_notification(employee_id, task_name):
    try:
        doc_ref = db.collection(EMPLOYEES_COLLECTION).document(employee_id)
        doc = doc_ref.get()
        if doc.exists:
            fcm_token = doc.to_dict().get("fcm_token")
            if fcm_token:
                headers = {
                    "Authorization": f"key={FCM_SERVER_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "to": fcm_token,
                    "notification": {
                        "title": "New Task Assigned",
                        "body": f"You have been assigned a new task: {task_name}"
                    }
                }
                response = requests.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers)
                logging.info(f"FCM Response: {response.json()}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")

def auto_expiry(stop_event):
    while not stop_event.is_set():
        try:
            tasks_ref = db.collection(TASKS_COLLECTION).where(filter=firestore.FieldFilter("status", "==", STATUS_PENDING)).stream()
            batch = db.batch()
            for task in tasks_ref:
                task_data = task.to_dict()
                if time.time() - task_data.get("timestamp", 0) >= 86400:
                    task_ref = db.collection(TASKS_COLLECTION).document(task.id)
                    batch.update(task_ref, {"status": STATUS_INCOMPLETE})
                    send_notification(task_data.get("assign_to", ""), f"Task {task_data.get('task', '')} marked as Incomplete")
            batch.commit()
        except Exception as e:
            logging.error(f"Error in auto-expiry thread: {e}")
        time.sleep(3600)

def show_task_ui(container):
    stop_event = threading.Event()
    employee_dict = {}

    def refresh_employee_list():
        try:
            employees_ref = db.collection(EMPLOYEES_COLLECTION).stream()
            employee_dict.clear()
            for emp in employees_ref:
                employee_dict[emp.id] = emp.to_dict().get("Name", "")
            assign_to["values"] = list(employee_dict.values())
            assign_to.set("")
        except Exception as e:
            logging.error(f"Error fetching employees: {e}")
            messagebox.showerror("Error", f"Failed to fetch employees: {e}")

    def assign_task():
        task = task_name.get().strip()
        assign_to_name = assign_to.get().strip()
        prio = priority.get().strip()

        # Robustly obtain deadline date from DateEntry (tkcalendar vs ttkbootstrap wrappers)
        try:
            if hasattr(deadline, 'get_date'):
                deadline_val = deadline.get_date()
            elif hasattr(deadline, 'entry') and hasattr(deadline.entry, 'get_date'):
                deadline_val = deadline.entry.get_date()
            else:
                # fallback: try to parse text value
                raw = deadline.get() if hasattr(deadline, 'get') else str(deadline)
                deadline_val = datetime.strptime(raw, "%Y-%m-%d").date()
        except Exception as e:
            logging.error(f"Error reading deadline value: {e}")
            messagebox.showerror("Error", "Invalid deadline value. Please select a valid date.")
            return

        # Normalize to date
        try:
            if isinstance(deadline_val, datetime):
                deadline_val = deadline_val.date()
        except Exception:
            pass

        if not all([task, assign_to_name, prio]):
            messagebox.showwarning("Warning", "Please fill all fields.")
            return

        if deadline_val < datetime.today().date():
            messagebox.showwarning("Warning", "Deadline cannot be in the past.")
            return

        assign_to_id = next((eid for eid, name in employee_dict.items() if name == assign_to_name), None)
        if not assign_to_id:
            messagebox.showerror("Error", "Employee not found.")
            return

        task_data = {
            "task": task,
            "assign_to": assign_to_id,
            "priority": prio,
            "deadline": deadline_val.strftime("%Y-%m-%d"),
            "status": STATUS_PENDING,
            "timestamp": time.time()
        }

        logging.info(f"Assigning task: {task_data}")
        try:
            db.collection(TASKS_COLLECTION).add(task_data)
            messagebox.showinfo("Success", "Task assigned successfully!")
            # Send notification in background so UI doesn't block
            try:
                threading.Thread(target=send_notification, args=(assign_to_id, task), daemon=True).start()
            except Exception as e:
                logging.error(f"Failed to start notification thread: {e}")
            fetch_tasks()
        except Exception as e:
            logging.error(f"Error assigning task: {e}")
            messagebox.showerror("Error", f"Failed to assign task: {str(e)}")

    def fetch_tasks():
        try:
            query = search_var.get().lower()
            tasks_ref = db.collection(TASKS_COLLECTION).stream()
            tree.delete(*tree.get_children())

            columns = ["Task", "Assigned To", "Priority", "Deadline", "Status"]
            tree["columns"] = columns
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=150)

            for task in tasks_ref:
                data = task.to_dict()
                assigned_name = employee_dict.get(data.get("assign_to", ""), "Unknown")
                task_name_val = data.get("task", "").lower()

                if query and query not in task_name_val and query not in assigned_name.lower():
                    continue

                tree.insert("", "end", values=(
                    data.get("task", ""),
                    assigned_name,
                    data.get("priority", ""),
                    data.get("deadline", ""),
                    data.get("status", "")
                ))
        except Exception as e:
            logging.error(f"Error fetching tasks: {e}")
            messagebox.showerror("Error", f"Failed to fetch tasks: {e}")

    # Clear existing widgets
    for widget in container.winfo_children():
        widget.destroy()

    # Build Task UI
    form_frame = ttk.Labelframe(container, text="Assign Task", padding=15)
    form_frame.pack(fill=X, pady=10)

    task_name = ttk.Combobox(form_frame, values=["Cleaning", "Maintenance", "Security", "Logistics"], state="readonly")
    assign_to = ttk.Combobox(form_frame, state="readonly")
    priority = ttk.Combobox(form_frame, values=["High", "Medium", "Low"], state="readonly")
    deadline = DateEntry(form_frame)

    ttk.Label(form_frame, text="Task Name").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    task_name.grid(row=0, column=1, padx=5, pady=5)
    ttk.Label(form_frame, text="Assign To").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    assign_to.grid(row=0, column=3, padx=5, pady=5)
    ttk.Label(form_frame, text="Priority").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    priority.grid(row=1, column=1, padx=5, pady=5)
    ttk.Label(form_frame, text="Deadline").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    deadline.grid(row=1, column=3, padx=5, pady=5)

    ttk.Button(form_frame, text="Refresh Employees", command=refresh_employee_list, bootstyle="warning-outline").grid(row=0, column=4, padx=10)
    ttk.Button(form_frame, text="Assign Task", command=assign_task, bootstyle="success", width=20).grid(row=2, columnspan=5, pady=10)

    search_frame = ttk.Frame(container)
    search_frame.pack(fill=X, pady=(0, 10))
    search_var = ttk.StringVar()
    ttk.Entry(search_frame, textvariable=search_var, width=40).pack(side=LEFT, padx=5)
    ttk.Button(search_frame, text="Search", command=fetch_tasks, bootstyle="info-outline").pack(side=LEFT, padx=5)
    ttk.Button(search_frame, text="Refresh", command=fetch_tasks, bootstyle="primary-outline").pack(side=LEFT, padx=5)

    tree = ttk.Treeview(container, show="headings", height=18)
    tree.pack(fill=BOTH, expand=True)

    refresh_employee_list()
    fetch_tasks()
    threading.Thread(target=auto_expiry, args=(stop_event,), daemon=True).start()
