import sys
import threading
import subprocess
import os
import requests
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import csv
from reportlab.pdfgen import canvas
import datetime
from manager_portal import show_attendance_ui
from task import show_task_ui
from salary import show_salary_ui
from reports import show_reports_ui

# --- Firebase Setup ---
cred = credentials.Certificate("modules/serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Flask App Setup ---
app = Flask(__name__)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400
    new_id = get_next_employee_id()
    data["id"] = new_id
    db.collection("employees").document(new_id).set(data)
    return jsonify({"message": "Employee added successfully!", "id": new_id})

@app.route('/get_employees', methods=['GET'])
def get_employees():
    employees_ref = db.collection("employees").stream()
    employees = [doc.to_dict() for doc in employees_ref]
    return jsonify(employees)

@app.route('/delete_employee/<emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    try:
        db.collection("employees").document(emp_id).delete()
        return jsonify({"message": f"Employee {emp_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_next_employee_id():
    employees_ref = db.collection("employees").stream()
    employee_ids = [int(doc.id) for doc in employees_ref if doc.id.isdigit()]
    return str(max(employee_ids) + 1) if employee_ids else "1"

def run_flask():
    app.run(debug=False, port=5000, use_reloader=False)


# --- Tkinter GUI with ttkbootstrap ---
class EmployeeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Management System")
        self.root.geometry("1200x700")
        self.fields = ["Name", "Role", "Contact", "Gender", "Age", "Date of Birth", "Bank Name", "Account Number", "IFSC Code"]
        self.entries = {}

        # Sidebar with navigation
        sidebar = ttk.Frame(root, padding=15)
        sidebar.pack(side=LEFT, fill=Y)
        ttk.Label(sidebar, text="Modules", font=("Segoe UI", 13, "bold")).pack(pady=(0, 15))

        self.module_buttons = {
            "Employee Management": self.show_employee_module,
            "Task": lambda: self.load_module(show_task_ui),
            "Salary": lambda: self.load_module(show_salary_ui),
            "Attendance": lambda: self.load_module(show_attendance_ui),
            "Reports": lambda: self.load_module(show_reports_ui),
            }


        for name, command in self.module_buttons.items():
            ttk.Button(sidebar, text=name, width=22, bootstyle="secondary-outline", command=command).pack(pady=7)

        ttk.Separator(sidebar, orient=VERTICAL).pack(fill=X, pady=(10, 10))
        ttk.Button(sidebar, text="Logout", width=22, bootstyle="danger-outline", command=self.logout).pack(side=BOTTOM, pady=10)

        # Container for dynamic modules
        self.container = ttk.Frame(root, padding=(10, 15))
        self.container.pack(side=RIGHT, fill=BOTH, expand=True)

        self.show_employee_module()

    # ------------------- Module Switchers -------------------
    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def load_module(self, module_function):
        self.clear_container()  # clears old widgets from the right pane
        module_function(self.container)  # loads the new module into the container


    def show_employee_module(self):
        self.clear_container()

        form_frame = ttk.Labelframe(self.container, text="Employee Details", padding=(15, 10))
        form_frame.pack(fill=X, pady=(0, 10))

        # Predefined roles
        self.predefined_roles = ["Manager", "Housekeeping", "Supervisor", "Machine Operator"]

        for idx, field in enumerate(self.fields):
            r, c = divmod(idx, 2)
            
            # Create label with constraints info
            constraint_text = self.get_field_constraint_text(field)
            label_text = field + ":" + (" " + constraint_text if constraint_text else "")
            ttk.Label(form_frame, text=label_text, font=("Segoe UI", 9)).grid(row=r, column=c*2, sticky=E, pady=8, padx=(5, 2))
            
            # Gender dropdown
            if field == "Gender":
                widget = ttk.Combobox(form_frame, values=["Male", "Female"], state="readonly")
            # Role dropdown with "Add new role" option
            elif field == "Role":
                role_frame = ttk.Frame(form_frame)
                role_frame.grid(row=r, column=c*2 + 1, padx=(2, 10), pady=8, sticky=W+E)
                
                # Combobox with predefined roles + "Add new role"
                role_values = self.predefined_roles + ["Add new role..."]
                self.role_combo = ttk.Combobox(role_frame, values=role_values, state="readonly", width=25)
                self.role_combo.pack(side=LEFT, fill=X, expand=True)
                self.role_combo.bind("<<ComboboxSelected>>", self.on_role_selected)
                
                widget = self.role_combo
                self.entries[field] = widget
                form_frame.columnconfigure(c*2 + 1, weight=1)
                continue
            # Date of Birth calendar picker
            elif field == "Date of Birth":
                date_frame = ttk.Frame(form_frame)
                date_frame.grid(row=r, column=c*2 + 1, padx=(2, 10), pady=8, sticky=W+E)
                
                # Entry field for date display
                date_entry = ttk.Entry(date_frame, width=20)
                date_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
                date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
                
                # Button to open calendar
                def open_calendar(entry_widget=date_entry):
                    self.open_calendar_popup(entry_widget)
                
                ttk.Button(date_frame, text="📅", width=3, command=open_calendar).pack(side=LEFT)
                
                form_frame.columnconfigure(c*2 + 1, weight=1)
                self.entries[field] = date_entry
                continue
            else:
                widget = ttk.Entry(form_frame)
                # Attach validation based on field type
                self.apply_field_validation(widget, field)
            
            widget.grid(row=r, column=c*2 + 1, padx=(2, 10), pady=8, sticky=W+E)
            form_frame.columnconfigure(c*2 + 1, weight=1)
            self.entries[field] = widget

        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(pady=(0, 15))
        for text, cmd, style in [
            ("Add", self.add_employee, "success-outline"),
            ("Refresh", self.fetch_employees, "info-outline"),
            ("Delete", self.delete_employee, "danger-outline"),
            ("Export CSV", self.export_csv, "secondary-outline"),
            ("Export PDF", self.export_pdf, "warning-outline")
        ]:
            ttk.Button(btn_frame, text=text, command=cmd, bootstyle=style, width=14).pack(side=LEFT, padx=7)

        search_frame = ttk.Frame(self.container)
        search_frame.pack(fill=X, pady=(5, 10))
        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=5)
        self.search_var = ttk.StringVar()
        self.search_var.trace_add("write", self.search_employees)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=LEFT, padx=5)

        self.tree = ttk.Treeview(self.container, columns=["ID"] + self.fields, show="headings", height=15)
        for col in ["ID"] + self.fields:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=W)
        self.tree.pack(fill=BOTH, expand=True)

        # Fetch employees after tree is created
        self.fetch_employees()

    def get_field_constraint_text(self, field):
        """Return constraint description for each field."""
        constraints = {
            "Name": "(2-50 letters)",
            "Contact": "(10 digits)",
            "Age": "(18-70)",
            "Account Number": "(digits only)",
            "IFSC Code": "(11 chars, A-Z0-9)"
        }
        return constraints.get(field, "")

    def apply_field_validation(self, entry_widget, field):
        """Apply validation rules to entry widgets based on field type."""
        if field == "Name":
            # Allow only letters and spaces, max 50 characters
            def validate_name(value):
                if len(value) > 50:
                    return False
                return all(c.isalpha() or c.isspace() for c in value)
            
            vcmd = (self.root.register(validate_name), '%S')
            entry_widget.configure(validate='key', validatecommand=vcmd)
        
        elif field == "Contact":
            # Allow only digits, exactly 10 characters
            def validate_contact(value):
                return len(value) <= 10 and value.isdigit()
            
            vcmd = (self.root.register(validate_contact), '%S')
            entry_widget.configure(validate='key', validatecommand=vcmd)
        
        elif field == "Age":
            # Allow only digits, validate range 18-70 with full field text
            def validate_age(value, action):
                # action: 1=insert, 0=delete, -1=focus
                if action == '-1':  # focusout
                    return True
                # For insertions, check the change
                if action == '1':
                    if not value.isdigit():
                        return False
                    if len(value) > 2:
                        return False
                return True
            
            vcmd = (self.root.register(validate_age), '%S', '%d')
            entry_widget.configure(validate='key', validatecommand=vcmd)
        
        elif field == "Account Number":
            # Allow only digits, max 20 characters
            def validate_account(value):
                return len(value) <= 20 and value.isdigit()
            
            vcmd = (self.root.register(validate_account), '%S')
            entry_widget.configure(validate='key', validatecommand=vcmd)
        
        elif field == "IFSC Code":
            # Allow uppercase letters and digits only, exactly 11 characters
            def validate_ifsc(value):
                if len(value) > 11:
                    return False
                return all(c.isupper() or c.isdigit() for c in value)
            
            vcmd = (self.root.register(validate_ifsc), '%S')
            entry_widget.configure(validate='key', validatecommand=vcmd)
        
        elif field == "Bank Name":
            # Allow letters, numbers, spaces, and common symbols
            def validate_bank(value):
                if len(value) > 100:
                    return False
                return all(c.isalnum() or c.isspace() or c in '-&().' for c in value)
            
            vcmd = (self.root.register(validate_bank), '%S')
            entry_widget.configure(validate='key', validatecommand=vcmd)

    def on_role_selected(self, event):
        """Handle role selection. If 'Add new role...' is selected, prompt for new role."""
        selected = self.role_combo.get()
        if selected == "Add new role...":
            # Prompt user to enter new role
            top = ttk.Toplevel(self.root)
            top.title("Add New Role")
            top.geometry("300x120")
            top.resizable(False, False)
            
            ttk.Label(top, text="Enter new role name:", font=("Segoe UI", 10)).pack(pady=(10, 5))
            new_role_entry = ttk.Entry(top, width=35)
            new_role_entry.pack(pady=5)
            new_role_entry.focus()
            
            def add_role():
                new_role = new_role_entry.get().strip()
                if new_role:
                    if new_role not in self.predefined_roles:
                        self.predefined_roles.append(new_role)
                        # Update the combobox values
                        updated_values = self.predefined_roles + ["Add new role..."]
                        self.role_combo['values'] = updated_values
                        self.role_combo.set(new_role)
                    else:
                        messagebox.showinfo("Info", f"{new_role} already exists!")
                    top.destroy()
                else:
                    messagebox.showwarning("Warning", "Please enter a role name!")
            
            ttk.Button(top, text="Add", command=add_role).pack(pady=5)
            new_role_entry.bind('<Return>', lambda e: add_role())

    def open_calendar_popup(self, date_entry):
        """Open a floating calendar card (no new window) and place it below the entry."""
        # Get current date from entry
        try:
            current_date = datetime.datetime.strptime(date_entry.get(), "%Y-%m-%d").date()
        except Exception:
            current_date = datetime.date.today()

        year = current_date.year
        month = current_date.month

        # Floating overlay frame
        overlay = ttk.Frame(self.root, relief="raised", borderwidth=1)

        # Position overlay just below the date_entry
        self.root.update_idletasks()
        ex = date_entry.winfo_rootx() - self.root.winfo_rootx()
        ey = date_entry.winfo_rooty() - self.root.winfo_rooty() + date_entry.winfo_height()
        overlay.place(x=ex, y=ey)

        # Close button
        ctrl_frame = ttk.Frame(overlay)
        ctrl_frame.pack(fill=X, padx=6, pady=(6, 0))
        ttk.Button(ctrl_frame, text="Close", bootstyle="secondary-outline", command=lambda: overlay.destroy()).pack(side=RIGHT)

        month_year_var = tk.StringVar(value=f"{datetime.date(year, month, 1).strftime('%B %Y')}")
        ttk.Label(overlay, textvariable=month_year_var, font=("Segoe UI", 11, "bold")).pack(pady=(6, 2))

        btn_frame = ttk.Frame(overlay)
        btn_frame.pack(pady=(0, 6))
        def change_month(delta):
            nonlocal year, month
            month += delta
            if month > 12:
                month = 1
                year += 1
            elif month < 1:
                month = 12
                year -= 1
            month_year_var.set(f"{datetime.date(year, month, 1).strftime('%B %Y')}")
            try:
                year_combo.set(str(year))
            except Exception:
                pass
            update_calendar()

        # Prev button
        ttk.Button(btn_frame, text="◀ Prev", width=8, command=lambda: change_month(-1)).pack(side=LEFT, padx=4)

        # Year selection combobox
        current_year = datetime.date.today().year
        # Provide a reasonable year range for DOB (1900..current_year)
        year_values = [str(y) for y in range(current_year, 1899, -1)]
        year_combo = ttk.Combobox(btn_frame, values=year_values, width=6, state="readonly")
        year_combo.set(str(year))
        year_combo.pack(side=LEFT, padx=(6, 6))
        def on_year_selected(e=None):
            nonlocal year
            try:
                sel = int(year_combo.get())
                year = sel
                month_year_var.set(f"{datetime.date(year, month, 1).strftime('%B %Y')}")
                update_calendar()
            except Exception:
                pass
        year_combo.bind('<<ComboboxSelected>>', on_year_selected)

        # Next button
        ttk.Button(btn_frame, text="Next ▶", width=8, command=lambda: change_month(1)).pack(side=LEFT, padx=4)

        cal_frame = ttk.Frame(overlay)
        cal_frame.pack(fill=BOTH, expand=True, padx=6, pady=6)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, day in enumerate(days):
            ttk.Label(cal_frame, text=day, font=("Segoe UI", 9, "bold")).grid(row=0, column=col, padx=2, pady=2)

        day_buttons = {}

        def update_calendar():
            # Clear previous buttons
            for btn in list(day_buttons.values()):
                btn.destroy()
            day_buttons.clear()

            # Get first day of month and number of days
            first_day = datetime.date(year, month, 1)
            last_day = (datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)) - datetime.timedelta(days=1)
            num_days = last_day.day

            start_pos = first_day.weekday()

            row = 1
            col = start_pos

            for day in range(1, num_days + 1):
                is_today = (year == current_date.year and month == current_date.month and day == current_date.day)

                btn = ttk.Button(cal_frame, text=str(day), width=3, command=lambda d=day: select_date(d))
                btn.grid(row=row, column=col, padx=2, pady=2)
                day_buttons[day] = btn
                if is_today:
                    btn.configure(style="info.TButton")

                col += 1
                if col > 6:
                    col = 0
                    row += 1

        def select_date(day):
            selected_date = datetime.date(year, month, day)
            date_entry.delete(0, 'end')
            date_entry.insert(0, selected_date.strftime('%Y-%m-%d'))
            overlay.destroy()

        update_calendar()

    def show_task_module(self):
        self.clear_container()
        ttk.Label(self.container, text="Task Module (To be implemented)", font=("Segoe UI", 14, "bold")).pack(pady=20)

    def show_salary_module(self):
        self.clear_container()
        ttk.Label(self.container, text="Salary Module (To be implemented)", font=("Segoe UI", 14, "bold")).pack(pady=20)

    def show_attendance_module(self):
        self.clear_container()
        ttk.Label(self.container, text="Attendance Module (To be implemented)", font=("Segoe UI", 14, "bold")).pack(pady=20)

    def show_reports_module(self):
        self.clear_container()
        ttk.Label(self.container, text="Reports Module (To be implemented)", font=("Segoe UI", 14, "bold")).pack(pady=20)

    # ------------------- Employee Module Functions -------------------
    def add_employee(self):
        data = {}
        for field in self.fields:
            widget = self.entries[field]
            data[field] = widget.get()
        
        # Validate all fields before submitting
        validation_errors = self.validate_employee_data(data)
        if validation_errors:
            messagebox.showerror("Validation Error", "Please fix the following:\n\n" + "\n".join(validation_errors))
            return
        
        response = requests.post("http://127.0.0.1:5000/add_employee", json=data)
        if response.status_code == 200:
            messagebox.showinfo("Success", "Employee added successfully!")
            self.fetch_employees()
            # Clear form
            for field in self.fields:
                if field == "Date of Birth":
                    self.entries[field].delete(0, 'end')
                    self.entries[field].insert(0, datetime.date.today().strftime('%Y-%m-%d'))
                else:
                    self.entries[field].delete(0, 'end') if hasattr(self.entries[field], 'delete') else None
        else:
            messagebox.showerror("Error", "Failed to add employee")

    def validate_employee_data(self, data):
        """Validate all employee data fields. Returns list of error messages."""
        errors = []
        
        # Name validation: 2-50 letters only
        name = data.get("Name", "").strip()
        if not name:
            errors.append("• Name is required")
        elif len(name) < 2 or len(name) > 50:
            errors.append("• Name must be 2-50 characters")
        elif not all(c.isalpha() or c.isspace() for c in name):
            errors.append("• Name must contain only letters and spaces")
        
        # Contact validation: exactly 10 digits
        contact = data.get("Contact", "").strip()
        if not contact:
            errors.append("• Contact is required")
        elif len(contact) != 10 or not contact.isdigit():
            errors.append("• Contact must be exactly 10 digits")
        
        # Gender validation
        gender = data.get("Gender", "").strip()
        if not gender:
            errors.append("• Gender must be selected")
        elif gender not in ["Male", "Female"]:
            errors.append("• Gender must be Male or Female")
        
        # Age validation: 18-70
        age = data.get("Age", "").strip()
        if not age:
            errors.append("• Age is required")
        elif not age.isdigit():
            errors.append("• Age must be a number")
        else:
            try:
                age_int = int(age)
                if age_int < 18 or age_int > 70:
                    errors.append("• Age must be between 18 and 70")
            except:
                errors.append("• Age must be a valid number")
        
        # Date of Birth validation
        dob = data.get("Date of Birth", "").strip()
        if not dob:
            errors.append("• Date of Birth is required")
        else:
            try:
                dob_date = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
                today = datetime.date.today()
                if dob_date >= today:
                    errors.append("• Date of Birth must be in the past")
            except:
                errors.append("• Date of Birth must be in YYYY-MM-DD format")
        
        # Role validation
        role = data.get("Role", "").strip()
        if not role:
            errors.append("• Role must be selected")
        
        # Bank Name validation
        bank = data.get("Bank Name", "").strip()
        if not bank:
            errors.append("• Bank Name is required")
        elif len(bank) > 100:
            errors.append("• Bank Name must be 100 characters or less")
        
        # Account Number validation: digits only
        account = data.get("Account Number", "").strip()
        if not account:
            errors.append("• Account Number is required")
        elif not account.isdigit():
            errors.append("• Account Number must contain only digits")
        elif len(account) < 9 or len(account) > 20:
            errors.append("• Account Number must be 9-20 digits")
        
        # IFSC Code validation: 11 characters, uppercase alphanumeric
        ifsc = data.get("IFSC Code", "").strip().upper()
        if not ifsc:
            errors.append("• IFSC Code is required")
        elif len(ifsc) != 11:
            errors.append("• IFSC Code must be exactly 11 characters")
        elif not all(c.isupper() or c.isdigit() for c in ifsc):
            errors.append("• IFSC Code must contain only letters and digits")
        
        return errors

    def fetch_employees(self):
        response = requests.get("http://127.0.0.1:5000/get_employees")
        if response.status_code == 200:
            self.all_employees = response.json()
            self.display_employees(self.all_employees)

    def display_employees(self, data):
        self.tree.delete(*self.tree.get_children())
        for emp in data:
            self.tree.insert("", END, values=[emp.get("id", "")] + [emp.get(f, "") for f in self.fields])

    def delete_employee(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No employee selected")
            return
        emp_id = self.tree.item(selected[0])['values'][0]
        response = requests.delete(f"http://127.0.0.1:5000/delete_employee/{emp_id}")
        if response.status_code == 200:
            messagebox.showinfo("Deleted", f"Employee {emp_id} deleted")
            self.fetch_employees()
        else:
            messagebox.showerror("Error", "Failed to delete employee")

    def export_csv(self):
        with open("employees.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id"] + self.fields)
            writer.writeheader()
            writer.writerows(self.all_employees)
        messagebox.showinfo("Exported", "Employee data exported to employees.csv")

    def export_pdf(self):
        c = canvas.Canvas("employees.pdf")
        c.setFont("Helvetica", 10)
        c.drawString(30, 820, f"Employee Report - {datetime.date.today().strftime('%Y-%m-%d')}")
        y = 800
        for emp in self.all_employees:
            line = f"ID: {emp.get('id')} | " + " | ".join(f"{f}: {emp.get(f, '')}" for f in self.fields)
            c.drawString(30, y, line)
            y -= 15
            if y < 40:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 800
        c.save()
        messagebox.showinfo("Exported", "Employee data exported to employees.pdf")

    def search_employees(self, *_):
        query = self.search_var.get().lower()
        filtered = [emp for emp in self.all_employees if any(query in str(val).lower() for val in emp.values())]
        self.display_employees(filtered)

    def logout(self):
        """Logout: disconnect Firebase and close the app window.

        Behavior:
        - Deletes any initialized firebase apps to disconnect from Firestore.
        - Closes the tkinter window (triggers clean exit via daemon threads).
        - Parent process (main.py) will handle relaunching the login window.
        """
        # 1) Disconnect Firebase apps
        try:
            if hasattr(firebase_admin, '_apps') and firebase_admin._apps:
                for name, app_obj in list(firebase_admin._apps.items()):
                    try:
                        firebase_admin.delete_app(app_obj)
                    except Exception:
                        pass
        except Exception:
            pass

        # 2) Close the GUI window (allows parent process to handle restart)
        try:
            self.root.destroy()
        except Exception:
            pass

# --- Run App ---
def open_employee_app():
    root = ttk.Window(themename="flatly")
    EmployeeApp(root)
    root.mainloop()
if __name__ == "__main__":
    # Start Flask API server only when running this module directly.
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    open_employee_app()
