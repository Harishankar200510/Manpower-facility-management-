# 🚀 Manpower Facility Management System

A comprehensive **Employee Management & Task Allocation System** built with Python and Firebase. Streamline HR operations, attendance tracking, task management, and performance monitoring in real-time.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Firebase](https://img.shields.io/badge/Firebase-Cloud--Database-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Future Roadmap](#-future-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 👥 Admin Panel
- ✅ **Employee Management** - Add, edit, delete, search employees with validation
- ✅ **Role Management** - Predefined roles (Manager, Housekeeping, Supervisor, Machine Operator) + custom role creation
- ✅ **Employee Database** - Comprehensive profiles with bank details, contact info, and calendar-based DOB picker
- ✅ **Task Assignment** - Assign tasks with priority levels and deadlines
- ✅ **Salary Management** - Calculate and manage employee salaries with deductions
- ✅ **Manager Portal** - Team oversight and performance tracking
- ✅ **Reports & Analytics** - Detailed attendance, task, and performance reports

### 👤 Employee Portal
- ✅ **Attendance Marking** - One-time daily attendance marking with duplicate prevention
- ✅ **Task Dashboard** - View assigned tasks with real-time status tracking
- ✅ **Task Updates** - Update task status with remarks and confirmation
- ✅ **Auto-Refresh** - Tasks refresh every 15 seconds for real-time updates
- ✅ **Employee Profile** - View personal and work-related information

### 🔐 Core Features
- ✅ **Role-Based Authentication** - Separate admin and employee login
- ✅ **Real-Time Sync** - Firebase Firestore cloud database
- ✅ **Input Validation** - Field-level constraints (name, age, contact, IFSC, etc.)
- ✅ **Calendar Date Picker** - Interactive calendar with month/year navigation
- ✅ **Modern UI** - Dark theme with ttkbootstrap (flatly)
- ✅ **Graceful Logout** - Auto database disconnect and Flask server shutdown
- ✅ **Standalone Executable** - PyInstaller .exe for easy distribution

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Python Tkinter + ttkbootstrap |
| **Backend** | Flask REST API |
| **Database** | Firebase Firestore (Cloud NoSQL) |
| **Authentication** | Firebase Admin SDK |
| **Notifications** | Firebase Cloud Messaging (FCM) |
| **Deployment** | PyInstaller (Standalone .exe) |
| **Version Control** | Git & GitHub |

### Dependencies
```
ttkbootstrap==1.6.11          # Modern Tkinter themes
firebase-admin==6.0.0         # Firebase SDK
flask==2.3.0                  # REST API framework
tkcalendar==1.6.1             # Calendar widget
requests==2.31.0              # HTTP client
google-cloud-firestore==2.11.0  # Firestore client
```

---

## 📦 Installation

### Prerequisites
- **Python 3.8+** installed
- **Git** for version control
- **Firebase Project** with service account key

### Step 1: Clone Repository
```bash
git clone https://github.com/Harishankar200510/Manpower-facility-management-.git
cd "Manpower-facility-management-"
```

### Step 2: Create Virtual Environment
```bash
# On Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Firebase
1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Download your **serviceAccountKey.json** file
3. Place it in the `modules/` folder:
   ```
   modules/serviceAccountKey.json
   ```

### Step 5: Run the Application
```bash
# On Windows
.\.venv\Scripts\python.exe modules/main.py

# On macOS/Linux
python modules/main.py
```

---

## 🎮 Usage

### Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Employee | `employee` | `emp123` |

### Admin Workflow
1. **Login** with admin credentials
2. **Manage Employees** - Add/edit/delete employee records
3. **Assign Tasks** - Create and assign tasks to employees
4. **View Reports** - Monitor attendance and task completion
5. **Manage Salary** - Calculate and process employee salaries
6. **Logout** - Returns to login screen

### Employee Workflow
1. **Login** with employee credentials
2. **Mark Attendance** - One-time per day (duplicate prevention)
3. **View Tasks** - Auto-refreshing task list
4. **Update Tasks** - Change status and add remarks
5. **Profile** - View personal information
6. **Logout** - Disconnects database and returns to login

---

## 📁 Project Structure

```
firebase/
├── modules/
│   ├── main.py                          # Login entry point
│   ├── employee_management.py           # Admin dashboard
│   ├── employee_portal_integrated.py    # Employee portal
│   ├── task.py                          # Task management
│   ├── salary.py                        # Salary calculations
│   ├── manager_portal.py                # Manager dashboard
│   ├── reports.py                       # Reports & analytics
│   └── serviceAccountKey.json           # Firebase credentials (git-ignored)
├── .venv/                               # Virtual environment
├── .gitignore                           # Git ignore rules
├── requirements.txt                     # Python dependencies
├── build_exe.py                         # PyInstaller build script
├── README.md                            # Project documentation
└── .git/                                # Git repository

```

---

## 🚀 Building Standalone Executable

Convert the project into a single `.exe` file for easy distribution:

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Run Build Script
```bash
python build_exe.py
```

### Step 3: Find Executable
```
dist/EmployeeManagementSystem.exe
```

The `.exe` is ~300-400 MB and includes all dependencies. Share it with any Windows machine—no Python/venv required!

---

## 📊 Database Schema

### Collections in Firestore

#### `employees`
```json
{
  "id": "EMP001",
  "name": "John Doe",
  "contact": "9876543210",
  "age": 28,
  "gender": "Male",
  "role": "Manager",
  "dob": "1996-05-15",
  "bank_name": "HDFC Bank",
  "account_number": "12345678901234",
  "ifsc_code": "HDFC0001234"
}
```

#### `tasks`
```json
{
  "id": "TASK001",
  "name": "Complete Report",
  "assigned_to": "EMP001",
  "priority": "High",
  "deadline": "2025-12-20",
  "status": "In Progress",
  "remarks": "Nearing completion",
  "created_at": "2025-11-19"
}
```

#### `attendance`
```json
{
  "id": "ATT001",
  "employee_id": "EMP001",
  "date": "2025-11-19",
  "timestamp": "2025-11-19T09:30:00Z",
  "status": "Present"
}
```

---

## 🔄 API Endpoints (Flask)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/get_employees` | Fetch all employees |
| POST | `/add_employee` | Add new employee |
| PUT | `/update_employee/<id>` | Update employee |
| DELETE | `/delete_employee/<id>` | Delete employee |
| GET | `/get_tasks` | Fetch all tasks |
| POST | `/assign_task` | Create new task |
| PUT | `/update_task/<id>` | Update task status |
| GET | `/get_attendance` | Fetch attendance records |
| POST | `/mark_attendance` | Mark employee attendance |
| POST | `/shutdown` | Graceful Flask shutdown |

---

## 📈 Data Validation

Each input field has specific constraints:

| Field | Constraint | Example |
|-------|-----------|---------|
| **Name** | 2-50 letters | "John Doe" |
| **Contact** | 10 digits | "9876543210" |
| **Age** | 18-70 years | 28 |
| **Account Number** | 9-20 digits | "12345678901234" |
| **IFSC Code** | 11 uppercase alphanumeric | "HDFC0001234" |
| **Gender** | Dropdown: Male/Female | "Male" |
| **Role** | Predefined or custom | "Manager" |
| **Date of Birth** | Past date only | "1996-05-15" |

---

## 🎯 Key Features in Detail

### ✅ Duplicate Attendance Prevention
- Employees can mark attendance only **once per day**
- System prevents re-marking by checking `date` field in Firestore
- Next day, attendance can be marked again

### ✅ Real-Time Task Updates
- Tasks auto-refresh every 15 seconds
- Changes visible instantly across all sessions
- Manual refresh button always available

### ✅ Interactive Calendar Picker
- Click date field to open floating calendar
- Month/Year dropdown for quick navigation
- Validates past dates only (prevents future DOBs)

### ✅ Graceful Shutdown
- Logout disconnects Firebase database
- Flask server auto-stops on app close
- No lingering processes or Ctrl+C required

### ✅ Input Field Constraints
- Real-time validation as user types
- Field-specific error messages
- Pre-submission validation check

---

## 🔐 Security Features

- **Firebase Rules**: Secure database access via Firestore rules
- **.gitignore**: Prevents committing sensitive files (`serviceAccountKey.json`)
- **Input Validation**: Sanitize user inputs to prevent injection attacks
- **Session Management**: Auto-logout with database disconnection

---

## 🚀 Future Roadmap

### Phase 1: Advanced Features
- 📧 Email notifications for task assignments
- 📱 SMS alerts for critical updates
- 📊 Dashboard analytics with charts/graphs
- 🔔 Push notifications via FCM
- 📱 Mobile app (React Native / Flutter)

### Phase 2: Performance & Scalability
- 🗄️ Database caching layer (Redis)
- ⚡ API response pagination
- 📦 Bulk import/export (CSV, Excel)
- ☁️ Cloud deployment (AWS, GCP, Azure)

### Phase 3: Advanced HR Features
- 🏆 Performance rating system
- 💰 Dynamic bonus/incentive calculation
- 📅 Leave management (vacation, sick leave)
- 🎓 Employee training records
- 👨‍💼 Org chart & hierarchy visualization

### Phase 4: Security & Compliance
- 🔐 Two-factor authentication (2FA)
- 📋 Audit logs for compliance
- 🔒 End-to-end encryption
- 📜 GDPR compliance
- 🛡️ Fine-grained role-based access (RBAC)

### Phase 5: Integration & Automation
- 🔗 Third-party integrations (Payroll, ERP)
- 🤖 Automated workflows (auto-escalate overdue tasks)
- 📊 BI integration (Power BI, Tableau)
- ⏰ Scheduled background jobs
- 🔔 Configurable alert rules

### Phase 6: User Experience
- 🌐 Web dashboard (React/Vue.js)
- 🎨 Theme customization
- 🌍 Multi-language support (English, Hindi)
- ♿ Accessibility (WCAG compliance)
- 📱 Mobile-responsive web UI

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/YourFeature`)
3. **Commit** your changes (`git commit -m 'Add YourFeature'`)
4. **Push** to the branch (`git push origin feature/YourFeature`)
5. **Submit** a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Test your changes before submitting
- Update README.md if adding features

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links & Resources

- **GitHub Repository**: https://github.com/Harishankar200510/Manpower-facility-management-
- **Firebase Documentation**: https://firebase.google.com/docs
- **ttkbootstrap GitHub**: https://github.com/israel-dryer/ttkbootstrap
- **Flask Documentation**: https://flask.palletsprojects.com/

---

## 👨‍💻 Author

**Harishankar**
- GitHub: [@Harishankar200510](https://github.com/Harishankar200510)
- LinkedIn: [Connect](www.linkedin.com/in/hari-shankar-488419356)

---

## 💬 Support & Feedback

Found a bug or have a suggestion? Please:
- Open an [Issue](https://github.com/Harishankar200510/Manpower-facility-management-/issues)
- Submit a [Pull Request](https://github.com/Harishankar200510/Manpower-facility-management-/pulls)
- Contact via LinkedIn

---

## 📊 Project Stats

- **Lines of Code**: 2000+
- **Modules**: 7
- **Database Collections**: 5
- **API Endpoints**: 15+
- **Validation Rules**: 30+
- **Development Time**: 3+ months

---

**⭐ If you find this project helpful, please consider giving it a star on GitHub!**

```
