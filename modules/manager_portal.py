import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("modules/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_employee_name_by_id(emp_id):
    try:
        doc = db.collection("employees").document(emp_id).get()
        if doc.exists:
            return doc.to_dict().get("Name", "Unknown")
        return "Unknown"
    except Exception as e:
        print(f"Error getting employee name: {e}")
        return "Unknown"

def show_attendance_ui(container):
    for widget in container.winfo_children():
        widget.destroy()

    def fetch_attendance():
        for i in tree.get_children():
            tree.delete(i)

        records = db.collection("attendance").stream()
        for record in records:
            data = record.to_dict()
            emp_id = data.get("employee_id", "Unknown")
            emp_name = get_employee_name_by_id(emp_id)
            timestamp = data.get("timestamp")
            status = data.get("status", "Unknown")
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(timestamp, datetime) else "Invalid"
            tree.insert("", "end", iid=record.id, values=(emp_id, emp_name, timestamp_str, status))

    def update_status():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected.")
            return

        record_id = selected[0]
        new_status = status_var.get()

        try:
            db.collection("attendance").document(record_id).update({"status": new_status})
            messagebox.showinfo("Success", "Status updated.")
            fetch_attendance()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update record: {e}")

    def delete_record():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected.")
            return

        record_id = selected[0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if confirm:
            try:
                db.collection("attendance").document(record_id).delete()
                messagebox.showinfo("Deleted", "Record deleted successfully.")
                fetch_attendance()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete record: {e}")

    def search_records(*_):
        query = search_var.get().lower()
        for item in tree.get_children():
            values = tree.item(item, "values")
            match = any(query in str(val).lower() for val in values)
            tree.item(item, tags=("match",) if match else ("hide",))
        tree.tag_configure("hide", foreground="white")
        tree.tag_configure("match", foreground="black")

    # Search bar
    search_frame = ttk.Frame(container)
    search_frame.pack(fill=X, pady=(0, 10))
    ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=5)
    search_var = ttk.StringVar()
    search_var.trace_add("write", search_records)
    ttk.Entry(search_frame, textvariable=search_var, width=30).pack(side=LEFT, padx=5)

    # Table
    global tree
    tree = ttk.Treeview(container, columns=("Employee ID", "Name", "Timestamp", "Status"), show="headings", height=18)
    for col in ("Employee ID", "Name", "Timestamp", "Status"):
        tree.heading(col, text=col)
        tree.column(col, width=200, anchor=W)
    tree.pack(fill=BOTH, expand=True, pady=5)

    # Status Dropdown
    global status_var
    status_var = ttk.StringVar(value="Present")
    status_dropdown = ttk.Combobox(container, textvariable=status_var, values=["Present", "Absent", "Late"], state="readonly")
    status_dropdown.pack(pady=10)

    # Action Buttons
    btn_frame = ttk.Frame(container)
    btn_frame.pack(pady=5)
    for text, cmd, style in [
        ("Update Status", update_status, "success-outline"),
        ("Delete Record", delete_record, "danger-outline"),
        ("Refresh", fetch_attendance, "info-outline")
    ]:
        ttk.Button(btn_frame, text=text, command=cmd, bootstyle=style, width=20).pack(side=LEFT, padx=10)

    fetch_attendance()
