
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import csv
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("modules/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_employee_names():
    try:
        docs = db.collection("employees").stream()
        names = [doc.to_dict().get("Name") for doc in docs]
        return names if names else ["No Employees Found"]
    except Exception as e:
        print(f"Error fetching employee names: {e}")
        return ["Error fetching names"]

def show_salary_ui(container):
    for widget in container.winfo_children():
        widget.destroy()

    def calculate_salary():
        try:
            days_worked = int(days_worked_entry.get())
            gender = gender_combo.get()
            canteen_deduction = float(canteen_entry.get()) if canteen_entry.get() else 0

            if gender not in ["Male", "Female"]:
                messagebox.showerror("Error", "Please select a valid gender.")
                return

            wage_per_day = 350 if gender == "Male" else 250
            gross_wage = days_worked * wage_per_day
            wage_deduction = gross_wage * 0.0075
            net_wage = gross_wage - wage_deduction
            total_salary = net_wage - canteen_deduction

            wage_label.config(text=f"{net_wage:.2f}")
            salary_label.config(text=f"{total_salary:.2f}")
            deduction_label.config(text=f"Wage Deduction (0.75%): {wage_deduction:.2f}")

            container.computed_wage = net_wage
            container.computed_salary = total_salary

        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for Days Worked and Deduction.")

    def save_salary():
        if not emp_combo.get():
            messagebox.showerror("Error", "Please select an employee.")
            return

        calculate_salary()

        data = {
            "employee_name": emp_combo.get(),
            "total_days": int(days_worked_entry.get()),
            "gender": gender_combo.get(),
            "wage_per_day": 350 if gender_combo.get() == "Male" else 250,
            "total_wage": container.computed_wage,
            "canteen_deduction": float(canteen_entry.get()) if canteen_entry.get() else 0,
            "total_salary": container.computed_salary
        }

        try:
            db.collection("salaries").add(data)
            messagebox.showinfo("Success", "Salary saved to Firebase successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save salary: {e}")

    def export_to_csv():
        try:
            docs = db.collection("salaries").stream()
            data = [doc.to_dict() for doc in docs]

            if not data:
                messagebox.showwarning("Warning", "No salary records found.")
                return

            with open("salary_records.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Employee Name", "Total Days", "Gender", "Wage/Day", "Total Wage", "Canteen Deduction", "Total Salary"])
                for d in data:
                    writer.writerow([
                        d.get("employee_name"),
                        d.get("total_days"),
                        d.get("gender"),
                        d.get("wage_per_day"),
                        d.get("total_wage"),
                        d.get("canteen_deduction"),
                        d.get("total_salary")
                    ])
            messagebox.showinfo("Exported", "Exported data to 'salary_records.csv'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def refresh_names():
        emp_combo["values"] = get_employee_names()

    frame = ttk.Frame(container, padding=20)
    frame.pack(fill=BOTH, expand=True)

    ttk.Label(frame, text="Employee Name:").grid(row=0, column=0, sticky=W, padx=10, pady=5)
    emp_combo = ttk.Combobox(frame, font=("Segoe UI", 11))
    emp_combo.grid(row=0, column=1, sticky=EW, padx=10, pady=5)
    refresh_names()

    ttk.Label(frame, text="Total Days Worked:").grid(row=1, column=0, sticky=W, padx=10, pady=5)
    days_worked_entry = ttk.Entry(frame)
    days_worked_entry.grid(row=1, column=1, sticky=EW, padx=10, pady=5)

    ttk.Label(frame, text="Gender:").grid(row=2, column=0, sticky=W, padx=10, pady=5)
    gender_combo = ttk.Combobox(frame, values=["Male", "Female"])
    gender_combo.grid(row=2, column=1, sticky=EW, padx=10, pady=5)

    ttk.Label(frame, text="Canteen Deduction:").grid(row=3, column=0, sticky=W, padx=10, pady=5)
    canteen_entry = ttk.Entry(frame)
    canteen_entry.grid(row=3, column=1, sticky=EW, padx=10, pady=5)

    deduction_label = ttk.Label(frame, text="Wage Deduction (0.75%): 0.00")
    deduction_label.grid(row=4, column=1, sticky=W, padx=10, pady=5)

    ttk.Label(frame, text="Total Wage:").grid(row=5, column=0, sticky=W, padx=10, pady=5)
    wage_label = ttk.Label(frame, text="0.00")
    wage_label.grid(row=5, column=1, sticky=EW, padx=10, pady=5)

    ttk.Label(frame, text="Total Salary (After Deductions):").grid(row=6, column=0, sticky=W, padx=10, pady=5)
    salary_label = ttk.Label(frame, text="0.00")
    salary_label.grid(row=6, column=1, sticky=EW, padx=10, pady=5)

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=7, column=0, columnspan=2, pady=20)

    for text, cmd, style in [
        ("Calculate", calculate_salary, "primary"),
        ("Save Salary", save_salary, "success"),
        ("Export CSV", export_to_csv, "info"),
        ("Refresh", refresh_names, "warning")
    ]:
        ttk.Button(btn_frame, text=text, command=cmd, bootstyle=style).pack(side=LEFT, padx=10)
