
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog

import csv
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("modules/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def fetch_data_from_firestore(collection_name):
    try:
        docs = db.collection(collection_name).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {str(e)}")
        return []

def show_reports_ui(container):
    for widget in container.winfo_children():
        widget.destroy()

    def generate_report():
        report_type = report_var.get()

        collections = {
            "Employee List": ("employees", ["id", "Name", "Role", "Contact", "Gender", "Age", "Date of Birth", "Bank Name", "Account Number", "IFSC Code"]),
            "Attendance": ("attendance", ["id", "employee_name", "date", "status"]),
            "Payroll": ("salary", ["id", "employee_name", "total_days", "wage_per_day", "total_salary"]),
            "Salary Deductions": ("salary", ["id", "employee_name", "total_wage", "canteen_deduction", "total_salary"]),
            "Shift Reports": ("shifts", ["id", "employee_name", "shift_time", "department"])
        }

        if report_type not in collections:
            messagebox.showerror("Error", "Please select a valid report type.")
            return

        collection, headers = collections[report_type]
        data = fetch_data_from_firestore(collection)

        tree.delete(*tree.get_children())
        tree["columns"] = headers
        tree["show"] = "headings"

        for col in headers:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=150)

        for record in data:
            row = [record.get(col, "") for col in headers]
            tree.insert("", "end", values=row)

    def export_to_csv():
        if not tree.get_children():
            messagebox.showwarning("Warning", "No data to export!")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        headers = [tree.heading(col)["text"] for col in tree["columns"]]
        data = [tree.item(row)["values"] for row in tree.get_children()]

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(data)

        messagebox.showinfo("Success", "Report exported successfully!")

    # UI
    ttk.Label(container, text="Select Report:", font=("Segoe UI", 11)).pack(pady=(0, 5))
    report_var = ttk.StringVar()
    report_dropdown = ttk.Combobox(container, textvariable=report_var, state="readonly",
                                   values=["Employee List", "Attendance", "Payroll", "Salary Deductions", "Shift Reports"])
    report_dropdown.pack(pady=5)

    btn_frame = ttk.Frame(container)
    btn_frame.pack(pady=10)
    for text, cmd, style in [
        ("Generate Report", generate_report, "success-outline"),
        ("Export to CSV", export_to_csv, "info-outline")
    ]:
        ttk.Button(btn_frame, text=text, command=cmd, bootstyle=style, width=20).pack(side=LEFT, padx=10)

    global tree
    tree = ttk.Treeview(container, show="headings", height=18)
    tree.pack(fill=BOTH, expand=True, pady=10)
