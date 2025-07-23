# LeaveTrack  

**LeaveTrack** is a Police Leave Management System built using **Python (Django)** and **MySQL**.  
It helps police departments digitize and streamline leave requests, approvals, and tracking with a simple, user-friendly interface.  

---

## 🚀 Features  

✅ **Role-based Access**  
- Officers can apply for leave  
- Approving officers can approve/reject requests  
- Admin can manage the entire system  

✅ **Leave Management**  
- Apply, approve, reject, and view leave history  
- Leave balance tracking & rules validation (prefix/suffix logic as per Kerala Service Rules)  

✅ **Additional Functionalities**  
- Upload in-service course details (Kerala, National, International)  
- Email notifications for leave approvals/rejections  
- Pastel green-themed UI for a clean, modern look  

✅ **Technology Stack**  
- **Backend:** Python (Django)  
- **Frontend:** HTML, CSS, Bootstrap, JavaScript  
- **Database:** MySQL  
- **Version Control:** Git & GitHub  

---

## 🛠 Installation  

Follow these steps to run **LeaveTrack** locally:  

```bash
# Clone the repository
git clone https://github.com/unnimayatk/LeaveTrack.git

# Go into the project folder
cd LeaveTrack

# Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate   # For Windows
source venv/bin/activate # For Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Run the development server
python manage.py runserver
