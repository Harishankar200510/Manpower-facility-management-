import customtkinter as ctk
from tkinter import messagebox
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- Initialize Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate("modules/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- Fetch Employee Details ---
def get_employee_details_by_id(emp_id):
    try:
        emp_id_str = str(emp_id).strip()
        doc_ref = db.collection("employees").document(emp_id_str)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"Error fetching employee details: {e}")
        return None

# --- Employee Portal ---
def employee_portal():
    def mark_attendance(event=None):
        emp_id = emp_id_entry.get().strip()
        employee = get_employee_details_by_id(emp_id)
        if not employee:
            messagebox.showerror("Error", f"Employee ID '{emp_id}' not found.")
            return

        # Display profile info in UI
        profile_label.configure(
            text=f"Name: {employee.get('Name', 'N/A')}\nRole: {employee.get('Role', 'N/A')}"
        )

        confirm = messagebox.askyesno("Confirm Attendance", f"Mark attendance for {employee.get('Name', 'N/A')}?")
        if confirm:
            now = datetime.datetime.now()
            db.collection("attendance").add({
                "employee_id": emp_id,
                "timestamp": now,
                "status": "Present"
            })
            messagebox.showinfo("Success", "Attendance marked!")
            emp_id_entry.delete(0, "end")
            profile_label.configure(text="")

    # --- UI Setup ---
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    emp_root = ctk.CTk()
    emp_root.title("Employee Attendance")

    # Fullscreen with title bar
    screen_width = emp_root.winfo_screenwidth()
    screen_height = emp_root.winfo_screenheight()
    emp_root.geometry(f"{screen_width}x{screen_height}+0+0")

    # Background gradient effect
    emp_root.configure(fg_color="#eef2f3")

    # Centered container (Card style)
    container = ctk.CTkFrame(
        emp_root,
        corner_radius=15,
        fg_color="white",
        width=500,
        height=350
    )
    container.place(relx=0.5, rely=0.5, anchor="center")

    # Title
    ctk.CTkLabel(
        container, text="Employee Attendance",
        font=ctk.CTkFont(size=26, weight="bold"),
        text_color="#2c3e50"
    ).pack(pady=(20, 15))

    # Employee ID entry
    ctk.CTkLabel(container, text="Enter your Employee ID:", font=ctk.CTkFont(size=16)).pack()
    emp_id_entry = ctk.CTkEntry(container, placeholder_text="Employee ID", width=300, height=40, corner_radius=8)
    emp_id_entry.pack(pady=10)

    # Profile display
    profile_label = ctk.CTkLabel(container, text="", font=ctk.CTkFont(size=14), text_color="#34495e")
    profile_label.pack(pady=5)

    # Mark Attendance Button
    ctk.CTkButton(
        container, text="Mark Attendance",
        width=200, height=40,
        corner_radius=8,
        font=ctk.CTkFont(size=16, weight="bold"),
        command=mark_attendance
    ).pack(pady=20)

    # Keyboard shortcuts
    emp_root.bind("<Return>", mark_attendance)
    emp_root.bind("<Escape>", lambda e: emp_root.destroy())

    emp_root.mainloop()

if __name__ == '__main__':
    employee_portal()
