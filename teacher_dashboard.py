import streamlit as st
import pandas as pd
import json
import os
import calendar
from datetime import datetime, timedelta
import uuid
from streamlit_option_menu import option_menu
import hashlib

# ======================
# DATA MANAGEMENT
# ======================

DATA_DIR = "data"
# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
# Ensure attachments directory exists within data directory
os.makedirs(os.path.join(DATA_DIR, "attachments"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "submissions"), exist_ok=True) # Ensure submissions directory exists
os.makedirs(os.path.join(DATA_DIR, "leave_attachments"), exist_ok=True) # Ensure leave attachments directory exists
os.makedirs(os.path.join(DATA_DIR, "school_essentials"), exist_ok=True) # Ensure school_essentials directory exists

TEACHER_DATA_FILE = os.path.join(DATA_DIR, "teacher_data.json")
ATTENDANCE_DATA_FILE = os.path.join(DATA_DIR, "attendance_data.json")
ASSIGNMENTS_DATA_FILE = os.path.join(DATA_DIR, "assignments_data.json")
TIMETABLE_DATA_FILE = os.path.join(DATA_DIR, "timetable_data.json")
PERFORMANCE_DATA_FILE = os.path.join(DATA_DIR, "performance_data.json")
MESSAGES_DATA_FILE = os.path.join(DATA_DIR, "messages_data.json")
RESOURCES_DATA_FILE = os.path.join(DATA_DIR, "resources_data.json")
LEAVE_DATA_FILE = os.path.join(DATA_DIR, "leave_data.json")
STUDENT_DATA_FILE = os.path.join(DATA_DIR, "student_data.json")
CLASS_DATA_FILE = os.path.join(DATA_DIR, "class_data.json") # Added for consistency, though not used extensively here
FEE_DATA_FILE = os.path.join(DATA_DIR, "fee_data.json") # Added for consistency
SCHOOL_ESSENTIALS_DATA_FILE = os.path.join(DATA_DIR, "school_essentials", "orders.json") # New file for school essentials orders


# Grade levels and sections
GRADE_LEVELS = ["Nursery", "LKG", "UKG"] + [f"Grade {i}" for i in range(1, 11)]
CLASS_SECTIONS = ["A", "B", "C", "D"]

# Common subjects for performance tracking and resources
COMMON_SUBJECTS = ["Mathematics", "Science", "English", "History", "Geography", "Computer Science", "Arts", "Physical Education", "Other"]


def get_full_class_list():
    """Generate complete list of classes with sections"""
    classes = []
    for grade in GRADE_LEVELS:
        if grade in ["Nursery", "LKG", "UKG"]:
            classes.append(grade)
        else:
            for section in CLASS_SECTIONS:
                classes.append(f"{grade}{section}")
    return classes

def load_data(filename):
    """Load data from JSON file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                st.error(f"Error decoding JSON from {filename}. File might be corrupted or empty. Returning empty dict.")
                return {}
    return {}

def save_data(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# ======================
# SECURITY & AUTHENTICATION
# ======================

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """Authenticate user credentials"""
    teachers = load_data(TEACHER_DATA_FILE)
    for teacher in teachers.values():
        if teacher['username'] == username and teacher['password'] == hash_password(password):
            return teacher['id']
    return None

def register_teacher(username, password, name, subject):
    """Register a new teacher"""
    teachers = load_data(TEACHER_DATA_FILE)
    new_id = str(uuid.uuid4())  # Generate unique ID for teacher
    
    teachers[new_id] = {
        "id": new_id,
        "username": username,
        "password": hash_password(password),
        "name": name,
        "subject": subject,
        "email": "",
        "phone": "",
        "join_date": str(datetime.today().date()),
        "is_admin": False
    }
    save_data(teachers, TEACHER_DATA_FILE)

def login_page():
    """Display login page and handle authentication"""
    st.title("📚 School Management System - Teacher Portal")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            teacher_id = authenticate_user(username, password)
            if teacher_id:
                st.session_state['logged_in'] = True
                st.session_state['teacher_id'] = teacher_id
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    # Admin registration option (only if no teachers exist)
    teachers_data = load_data(TEACHER_DATA_FILE)
    if not teachers_data: # Only show registration if no teachers are registered
        with st.expander("New Teacher? Register Here"):
            with st.form("register_form"):
                new_username = st.text_input("Choose Username*")
                new_password = st.text_input("Choose Password*", type="password")
                teacher_name = st.text_input("Full Name*")
                teacher_subject = st.selectbox("Subject*", COMMON_SUBJECTS) # Using COMMON_SUBJECTS
                
                if st.form_submit_button("Register"):
                    if new_username and new_password and teacher_name and teacher_subject:
                        # Check if username already exists
                        if any(t.get('username') == new_username for t in teachers_data.values()):
                            st.error("Username already exists. Please choose a different one.")
                        else:
                            register_teacher(new_username, new_password, teacher_name, teacher_subject)
                            st.success("Registration successful! Please login.")
                            st.rerun()
                    else:
                        st.error("Please fill all required fields for registration.")

# ======================
# STUDENT MANAGEMENT FUNCTIONS
# ======================

def initialize_student_data():
    """Initialize sample student data with all new fields"""
    students = {}
    classes = get_full_class_list()
    
    for class_name in classes:
        students[class_name] = []
        num_students = 2 if class_name in ["Nursery", "LKG", "UKG"] else 3
        
        for i in range(1, num_students + 1):
            admission_no = f"ADM{GRADE_LEVELS.index(class_name.split(' ')[0] if ' ' in class_name else class_name) + 1}{i:03d}"
            # Default parent password for sample data
            default_parent_pwd = hash_password(f"parent{admission_no}") # Tie password to admission_no

            students[class_name].append({
                "id": str(uuid.uuid4()), # Unique internal ID
                "admission_no": admission_no,
                "name": f"Student {i} ({class_name})",
                "roll_no": f"{i}",
                "class": class_name,
                "dob": "2010-01-01",
                "date_of_joining": "2023-09-01",
                "date_of_tc": None,
                "adhar_number": f"1234567890{i:02d}",
                "father_name": f"Father {i} {class_name}",
                "mother_name": f"Mother {i} {class_name}",
                "parent_name": f"Parent {i}", # Kept for backward compatibility/simplicity
                "parent_email": f"parent{i}@example.com",
                "parent_phone": f"555-010{i}",
                "address": f"{i} Main Street, School City",
                "emergency_contact": f"Emergency Contact {i} - 555-911{i}",
                "contact_number": f"98765432{i:02d}",
                "blood_group": "O+",
                "financial_status": "Paid",
                "passport_photo_path": None,
                "parent_password": default_parent_pwd # Add hashed parent password
            })
    
    save_data(students, STUDENT_DATA_FILE)

def get_students_by_class(class_name):
    """Get students for a specific class"""
    student_data = load_data(STUDENT_DATA_FILE)
    return student_data.get(class_name, [])

# ======================
# SCHOOL ESSENTIALS FUNCTIONS
# ======================

def load_orders():
    """Load order data from JSON file"""
    return load_data(SCHOOL_ESSENTIALS_DATA_FILE)

def save_orders(orders):
    """Save order data to JSON file"""
    save_data(orders, SCHOOL_ESSENTIALS_DATA_FILE)

# ======================
# MAIN DASHBOARD
# ======================

def show():
    """Main teacher dashboard function"""
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_page()
        return
    
    teacher_id = st.session_state['teacher_id']
    teacher_data = load_data(TEACHER_DATA_FILE).get(str(teacher_id), {})
    
    st.title(f"👨‍🏫 Teacher Dashboard - {teacher_data.get('name', '')}")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    
    # Navigation menu
    selected = option_menu(
        None,
        ["Profile", "Attendance", "Assignments", "Timetable", "Student Management", 
         "Performance", "Communication", "Resources", "Leave", "Export Data", "School Essentials"],
        icons=['person', 'calendar-check', 'journal-text', 'calendar-range', 'people', 
               'graph-up', 'chat', 'folder', 'clock', 'download', 'bag'],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#e9ecef"},
            "nav-link-selected": {"background-color": "#0d6efd"},
        }
    )

    # Profile Section
    if selected == "Profile":
        st.header("👤 Teacher Profile")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
        
        with col2:
            st.write(f"**Name:** {teacher_data.get('name', '')}")
            st.write(f"**Subject:** {teacher_data.get('subject', '')}")
            st.write(f"**Email:** {teacher_data.get('email', '')}")
            st.write(f"**Phone:** {teacher_data.get('phone', '')}")
            st.write(f"**Joined:** {teacher_data.get('join_date', '')}")
            
            with st.expander("Update Profile"):
                with st.form("update_profile"):
                    new_email = st.text_input("Email", value=teacher_data.get('email', ''))
                    new_phone = st.text_input("Phone", value=teacher_data.get('phone', ''))
                    new_password = st.text_input("New Password (leave blank to keep current)", type="password")
                    submitted = st.form_submit_button("Update")
                    if submitted:
                        teacher_data['email'] = new_email
                        teacher_data['phone'] = new_phone
                        if new_password:
                            teacher_data['password'] = hash_password(new_password)
                        
                        all_data = load_data(TEACHER_DATA_FILE)
                        all_data[str(teacher_id)] = teacher_data
                        save_data(all_data, TEACHER_DATA_FILE)
                        st.success("Profile updated successfully")
                        st.rerun()

    # Attendance Section
    elif selected == "Attendance":
        st.header("📅 Attendance Tracking")
        
        # Date selection
        today = datetime.today()
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.selectbox("Year", range(today.year-1, today.year+2), index=1)
        with col2:
            month = st.selectbox("Month", list(calendar.month_name[1:]), index=today.month-1)
        with col3:
            day = st.selectbox("Day", range(1, 32), index=today.day-1)
        
        selected_date = f"{year}-{month}-{day}"
        selected_class = st.selectbox("Select Class", get_full_class_list())
        
        # Attendance form
        students = get_students_by_class(selected_class)
        attendance_data = load_data(ATTENDANCE_DATA_FILE).get(str(teacher_id), {})
        
        if selected_date not in attendance_data:
            attendance_data[selected_date] = {}
        if selected_class not in attendance_data[selected_date]:
            attendance_data[selected_date][selected_class] = {str(s['id']): "Present" for s in students}
        
        attendance_status = {}
        for student in students:
            current_status = attendance_data[selected_date][selected_class].get(str(student['id']), "Present")
            status = st.radio(
                f"{student.get('name', 'N/A')} (Adm No: {student.get('admission_no', 'N/A')})",
                ["Present", "Absent", "Late", "Excused"],
                index=["Present", "Absent", "Late", "Excused"].index(current_status),
                key=f"att_{student['id']}_{selected_date}",
                horizontal=True
            )
            attendance_status[str(student['id'])] = status
        
        if st.button("Save Attendance"):
            attendance_data[selected_date][selected_class] = attendance_status
            all_data = load_data(ATTENDANCE_DATA_FILE)
            all_data[str(teacher_id)] = attendance_data
            save_data(all_data, ATTENDANCE_DATA_FILE)
            st.success("Attendance saved successfully!")
            
            # Show summary
            present_count = list(attendance_status.values()).count("Present")
            absent_count = list(attendance_status.values()).count("Absent")
            st.metric("Present", present_count)
            st.metric("Absent", absent_count)

    # Student Management Section (UPDATED)
    elif selected == "Student Management":
        st.header("👥 Student Management")
        
        tab1, tab2, tab3 = st.tabs(["Add Student", "Manage Students", "Bulk Operations"])
        
        with tab1:
            with st.form("add_student", clear_on_submit=True):
                st.subheader("Add New Student")
                col1, col2 = st.columns(2)
                with col1:
                    student_admission_no = st.text_input("Student Admission Number*", help="Unique admission number for the student.").strip()
                    name = st.text_input("Full Name*", help="Full legal name of the student.").strip()
                    roll_no = st.text_input("Roll No.", help="Student's roll number in class (optional).").strip()
                    class_name = st.selectbox("Class*", get_full_class_list())
                    dob = st.date_input("Date of Birth*", max_value=datetime.today().date())
                    date_of_joining = st.date_input("Date of Joining*", max_value=datetime.today().date())
                    date_of_tc = st.date_input("Date of TC (Optional)", value=None, help="Date of Transfer Certificate issuance, if applicable.")
                with col2:
                    adhar_number = st.text_input("Aadhar Number (Optional)").strip()
                    father_name = st.text_input("Father's Name*").strip()
                    mother_name = st.text_input("Mother's Name*").strip()
                    parent_email = st.text_input("Parent Email*").strip()
                    parent_phone = st.text_input("Parent Phone*").strip()
                    address = st.text_area("Address").strip()
                    emergency_contact = st.text_input("Emergency Contact (Name & Number)*").strip()
                    contact_number = st.text_input("Student's Contact Number (Optional)").strip()
                    blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
                    financial_status = st.text_input("Financial Status (e.g., Paid, Scholarship, Partial)").strip()
                    passport_photo = st.file_uploader("Upload Passport Photo (Optional)", type=["jpg", "jpeg", "png"])
                
                if st.form_submit_button("Add Student"):
                    required_fields = [student_admission_no, name, class_name, dob, date_of_joining, father_name, mother_name, parent_email, parent_phone, emergency_contact]
                    if not all(required_fields):
                        st.error("Please fill all required fields (*)")
                    else:
                        student_data = load_data(STUDENT_DATA_FILE)
                        
                        # Check if admission number already exists globally
                        admission_exists = False
                        for cls_students in student_data.values():
                            if any(s.get('admission_no') == student_admission_no for s in cls_students):
                                admission_exists = True
                                break
                        
                        if admission_exists:
                            st.error(f"Student Admission Number '{student_admission_no}' already exists. Please use a unique admission number.")
                        else:
                            if class_name not in student_data:
                                student_data[class_name] = []

                            photo_path = None
                            if passport_photo:
                                photo_filename = f"student_photo_{student_admission_no}_{passport_photo.name}"
                                photo_save_path = os.path.join(DATA_DIR, "attachments", photo_filename)
                                try:
                                    with open(photo_save_path, "wb") as f:
                                        f.write(passport_photo.getbuffer())
                                    photo_path = photo_save_path
                                except Exception as e:
                                    st.error(f"Error saving photo: {e}")
                                    photo_path = None # Ensure photo_path is None on error

                            new_student_record = {
                                "id": str(uuid.uuid4()), # Unique internal ID
                                "admission_no": student_admission_no,
                                "name": name,
                                "roll_no": roll_no,
                                "class": class_name,
                                "dob": str(dob),
                                "date_of_joining": str(date_of_joining),
                                "date_of_tc": str(date_of_tc) if date_of_tc else None,
                                "adhar_number": adhar_number,
                                "father_name": father_name,
                                "mother_name": mother_name,
                                "parent_name": father_name, # Using father's name as primary parent name for now
                                "parent_email": parent_email,
                                "parent_phone": parent_phone,
                                "address": address,
                                "emergency_contact": emergency_contact,
                                "contact_number": contact_number,
                                "blood_group": blood_group,
                                "financial_status": financial_status,
                                "passport_photo_path": photo_path
                            }
                            student_data[class_name].append(new_student_record)
                            save_data(student_data, STUDENT_DATA_FILE)
                            st.success(f"Student '{name}' (Admission No: {student_admission_no}) added successfully to {class_name}!")
                            st.rerun()
        
        with tab2:
            st.subheader("Manage Existing Students")
            student_data = load_data(STUDENT_DATA_FILE)
            
            all_students_list = []
            for class_name_key, students_in_class in student_data.items():
                for student in students_in_class:
                    all_students_list.append({**student, "class_name_display": class_name_key})

            if not all_students_list:
                st.info("No student records available.")
                return

            df_students = pd.DataFrame(all_students_list)
            # Select columns to display in the main table
            display_columns = [
                "admission_no", "name", "roll_no", "class_name_display", "dob", "date_of_joining",
                "father_name", "mother_name", "parent_email", "parent_phone", "contact_number",
                "emergency_contact", "blood_group", "financial_status"
            ]
            st.dataframe(df_students[display_columns], use_container_width=True)

            st.subheader("Edit or Delete Student")
            
            # Use admission number for selection
            student_admission_numbers = [s['admission_no'] for s in all_students_list if 'admission_no' in s]
            student_to_manage_admission_no = st.selectbox(
                "Select Student by Admission Number to Edit/Delete",
                [""] + student_admission_numbers,
                key="edit_delete_student_admission_no_teacher" # Unique key for teacher module
            )

            selected_student_obj = None
            if student_to_manage_admission_no:
                for cls_students in student_data.values():
                    for s in cls_students:
                        if s.get('admission_no') == student_to_manage_admission_no:
                            selected_student_obj = s
                            break
                    if selected_student_obj:
                        break

            if selected_student_obj:
                st.write(f"**Selected Student:** {selected_student_obj['name']} (Admission No: {selected_student_obj['admission_no']}) in {selected_student_obj['class']}")

                action = st.radio("Choose Action", ["Edit", "Delete"], key="student_action_radio_teacher")

                if action == "Edit":
                    st.subheader(f"Edit Details for {selected_student_obj['name']}")
                    with st.form(f"edit_student_form_{selected_student_obj['id']}"):
                        col1_edit, col2_edit = st.columns(2)
                        with col1_edit:
                            new_name = st.text_input("Full Name", value=selected_student_obj.get('name', ''))
                            new_roll_no = st.text_input("Roll No.", value=selected_student_obj.get('roll_no', ''))
                            new_dob = st.date_input("Date of Birth", value=datetime.strptime(selected_student_obj['dob'], '%Y-%m-%d').date())
                            new_date_of_joining = st.date_input("Date of Joining", value=datetime.strptime(selected_student_obj.get('date_of_joining', str(datetime.today().date())), '%Y-%m-%d').date())
                            new_date_of_tc = st.date_input("Date of TC (Optional)", value=datetime.strptime(selected_student_obj['date_of_tc'], '%Y-%m-%d').date() if selected_student_obj.get('date_of_tc') else None)
                            new_adhar_number = st.text_input("Aadhar Number (Optional)", value=selected_student_obj.get('adhar_number', ''))
                            new_contact_number = st.text_input("Student's Contact Number (Optional)", value=selected_student_obj.get('contact_number', ''))
                        with col2_edit:
                            new_parent_name = st.text_input("Parent/Guardian Name", value=selected_student_obj.get('parent_name', ''))
                            new_father_name = st.text_input("Father's Name", value=selected_student_obj.get('father_name', ''))
                            new_mother_name = st.text_input("Mother's Name", value=selected_student_obj.get('mother_name', ''))
                            new_parent_email = st.text_input("Parent Email", value=selected_student_obj.get('parent_email', ''))
                            new_parent_phone = st.text_input("Parent Phone", value=selected_student_obj.get('parent_phone', ''))
                            new_address = st.text_area("Address", value=selected_student_obj.get('address', ''))
                            new_emergency_contact = st.text_input("Emergency Contact (Name & Number)", value=selected_student_obj.get('emergency_contact', ''))
                            new_blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"], index=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"].index(selected_student_obj.get('blood_group', 'Unknown')))
                            new_financial_status = st.text_input("Financial Status", value=selected_student_obj.get('financial_status', ''))
                            
                            current_photo_path = selected_student_obj.get('passport_photo_path')
                            if current_photo_path and os.path.exists(current_photo_path):
                                st.image(current_photo_path, caption="Current Passport Photo", width=150)
                                st.info("Upload a new photo to replace the current one.")
                            new_passport_photo = st.file_uploader("Upload New Passport Photo (Optional)", type=["jpg", "jpeg", "png"], key=f"edit_photo_{selected_student_obj['id']}_teacher")

                        if st.form_submit_button("Save Changes"):
                            # Update the specific student data in session state
                            student_data_to_update = None
                            for cls_students in student_data.values():
                                for s in cls_students:
                                    if s.get('id') == selected_student_obj['id']:
                                        student_data_to_update = s
                                        break
                                if student_data_to_update:
                                    break

                            if student_data_to_update:
                                student_data_to_update.update({
                                    "name": new_name,
                                    "roll_no": new_roll_no,
                                    "dob": str(new_dob),
                                    "date_of_joining": str(new_date_of_joining),
                                    "date_of_tc": str(new_date_of_tc) if new_date_of_tc else None,
                                    "adhar_number": new_adhar_number,
                                    "parent_name": new_parent_name,
                                    "father_name": new_father_name,
                                    "mother_name": new_mother_name,
                                    "parent_email": new_parent_email,
                                    "parent_phone": new_parent_phone,
                                    "address": new_address,
                                    "emergency_contact": new_emergency_contact,
                                    "contact_number": new_contact_number,
                                    "blood_group": new_blood_group,
                                    "financial_status": new_financial_status
                                })
                                if new_passport_photo:
                                    photo_filename = f"student_photo_{selected_student_obj['admission_no']}_{new_passport_photo.name}"
                                    photo_save_path = os.path.join(DATA_DIR, "attachments", photo_filename)
                                    try:
                                        with open(photo_save_path, "wb") as f:
                                            f.write(new_passport_photo.getbuffer())
                                        student_data_to_update["passport_photo_path"] = photo_save_path
                                    except Exception as e:
                                        st.error(f"Error saving new photo: {e}")

                                save_data(student_data, STUDENT_DATA_FILE) # Save updated data
                                st.success("Student details updated successfully!")
                                st.rerun()
                            else:
                                st.error("Error: Student not found in data for update.")

                elif action == "Delete":
                    st.warning(f"Are you sure you want to delete {selected_student_obj['name']} (Admission No: {selected_student_obj['admission_no']})?")
                    if st.button("Confirm Delete", key=f"confirm_delete_{selected_student_obj['id']}_teacher"):
                        # Find and remove the student from the correct class list
                        original_class = selected_student_obj['class']
                        if original_class in student_data:
                            student_data[original_class] = [
                                s for s in student_data[original_class]
                                if s['id'] != selected_student_obj['id']
                            ]
                            # If the class list becomes empty, remove the class entry
                            if not student_data[original_class]:
                                del student_data[original_class]

                        save_data(student_data, STUDENT_DATA_FILE) # Save updated data
                        st.success("Student deleted successfully!")
                        st.rerun()
            else:
                st.info("Please select a student by Admission Number to manage.")
        
        with tab3:
            st.subheader("Bulk Student Operations")
            
            with st.expander("Import Students from CSV"):
                uploaded_file = st.file_uploader("Choose CSV file", type="csv", key="bulk_import_students_teacher")
                if uploaded_file:
                    try:
                        df = pd.read_csv(uploaded_file)
                        st.write("Preview:")
                        st.dataframe(df.head())
                        
                        if st.button("Import Students", key="import_students_btn_teacher"):
                            student_data = load_data(STUDENT_DATA_FILE)
                            imported_count = 0
                            for _, row in df.iterrows():
                                class_name = row.get('class', 'Unknown Class')
                                if class_name not in student_data:
                                    student_data[class_name] = []
                                
                                admission_no = row.get('admission_no', str(uuid.uuid4()))
                                # Check for duplicate admission_no before adding
                                if any(s.get('admission_no') == admission_no for cls_students in student_data.values() for s in cls_students):
                                    st.warning(f"Skipping student with duplicate Admission No: {admission_no}")
                                    continue

                                photo_path = None # Bulk import doesn't handle photo files directly
                                if row.get('passport_photo_path') and os.path.exists(row['passport_photo_path']):
                                    photo_path = row['passport_photo_path'] # Assume path is valid if provided

                                student_data[class_name].append({
                                    "id": str(uuid.uuid4()),
                                    "admission_no": admission_no,
                                    "name": row.get('name', 'New Student'),
                                    "roll_no": str(row.get('roll_no', '')),
                                    "class": class_name,
                                    "dob": str(row.get('dob', '2000-01-01')),
                                    "date_of_joining": str(row.get('date_of_joining', '2023-01-01')),
                                    "date_of_tc": str(row.get('date_of_tc', None)) if pd.notna(row.get('date_of_tc')) else None,
                                    "adhar_number": str(row.get('adhar_number', '')),
                                    "father_name": row.get('father_name', 'N/A'),
                                    "mother_name": row.get('mother_name', 'N/A'),
                                    "parent_name": row.get('parent_name', row.get('father_name', 'N/A')), # Fallback
                                    "parent_email": row.get('parent_email', ''),
                                    "parent_phone": row.get('parent_phone', ''),
                                    "address": row.get('address', ''),
                                    "emergency_contact": row.get('emergency_contact', ''),
                                    "contact_number": str(row.get('contact_number', '')),
                                    "blood_group": row.get('blood_group', 'Unknown'),
                                    "financial_status": row.get('financial_status', 'N/A'),
                                    "passport_photo_path": photo_path
                                })
                                imported_count += 1
                            
                            save_data(student_data, STUDENT_DATA_FILE)
                            st.success(f"Imported {imported_count} students successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error reading or importing CSV file: {e}")
            
            with st.expander("Export Students to CSV"):
                if st.button("Generate Export File", key="export_students_btn_teacher"):
                    student_data = load_data(STUDENT_DATA_FILE)
                    all_students = []
                    for class_name, students in student_data.items():
                        for student in students:
                            all_students.append(student)
                    
                    if all_students:
                        df = pd.DataFrame(all_students)
                        # Ensure all columns are present, fill missing with None or empty string
                        expected_columns = [
                            "id", "admission_no", "name", "roll_no", "class", "dob",
                            "date_of_joining", "date_of_tc", "adhar_number", "father_name",
                            "mother_name", "parent_name", "parent_email", "parent_phone",
                            "address", "emergency_contact", "contact_number", "blood_group",
                            "financial_status", "passport_photo_path"
                        ]
                        for col in expected_columns:
                            if col not in df.columns:
                                df[col] = None # Or appropriate default value

                        csv = df[expected_columns].to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Students Data (CSV)",
                            csv,
                            "students_export.csv",
                            "text/csv"
                        )
                    else:
                        st.warning("No student data to export")

    # Timetable Section
    elif selected == "Timetable":
        st.header("📅 Class Timetable")
        
        tab1, tab2, tab3 = st.tabs(["View Timetable", "Edit Timetable", "Timetable Analytics"])
        
        with tab1:
            timetable_data = load_data(TIMETABLE_DATA_FILE).get(str(teacher_id), [])
            
            if not timetable_data:
                st.info("No timetable entries found")
            else:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                periods = range(1, 8)  # 7 periods per day
                
                # Create timetable grid
                timetable_grid = {day: {f"Period {period}": "" for period in periods} for day in days}
                
                for entry in timetable_data:
                    day = entry.get('day', 'N/A')
                    period = entry.get('period', 'N/A')
                    if day in timetable_grid and f"Period {period}" in timetable_grid[day]:
                        timetable_grid[day][f"Period {period}"] = f"{entry.get('subject', 'N/A')}\n{entry.get('class_name', 'N/A')}"
                
                # Display as dataframe with color coding
                df = pd.DataFrame(timetable_grid)
                st.dataframe(df.style.applymap(lambda x: 'background-color: #e6f3ff' if x else ''))
        
        with tab2:
            st.subheader("Edit Timetable")
            timetable_data = load_data(TIMETABLE_DATA_FILE).get(str(teacher_id), [])
            
            with st.form("timetable_entry"):
                col1, col2 = st.columns(2)
                with col1:
                    day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
                    period = st.number_input("Period", min_value=1, max_value=7, value=1)
                    subject = st.text_input("Subject", value=teacher_data.get('subject', ''))
                with col2:
                    class_name = st.selectbox("Class", get_full_class_list())
                    action = st.radio("Action", ["Add/Update", "Delete"])
                
                submitted = st.form_submit_button("Submit")
                if submitted:
                    entry = {
                        "day": day,
                        "period": period,
                        "subject": subject,
                        "class_name": class_name
                    }
                    
                    if action == "Add/Update":
                        # Remove existing entry for this day/period if exists
                        timetable_data = [e for e in timetable_data 
                                        if not (e.get('day') == day and e.get('period') == period)]
                        timetable_data.append(entry)
                        st.success("Timetable entry updated!")
                    else:
                        timetable_data = [e for e in timetable_data 
                                        if not (e.get('day') == day and e.get('period') == period 
                                               and e.get('class_name') == class_name)]
                        st.success("Timetable entry deleted!")
                    
                    all_data = load_data(TIMETABLE_DATA_FILE)
                    all_data[str(teacher_id)] = timetable_data
                    save_data(all_data, TIMETABLE_DATA_FILE)
                    st.rerun()
        
        with tab3:
            st.subheader("Timetable Analytics")
            timetable_data = load_data(TIMETABLE_DATA_FILE).get(str(teacher_id), [])
            
            if not timetable_data:
                st.info("No timetable data available")
            else:
                # Teaching hours per day
                df = pd.DataFrame(timetable_data)
                teaching_hours = df['day'].value_counts().sort_index()
                st.bar_chart(teaching_hours, use_container_width=True)
                # Class distribution
                class_dist = df['class_name'].value_counts()
                st.write("**Classes Taught:**")
                st.dataframe(class_dist)

    # Assignments Section (Updated)
    elif selected == "Assignments":
        st.header("📝 Assignments & Grading")
        tab1, tab2, tab3 = st.tabs(["Create Assignment", "Grade Submissions", "Assignment Analytics"])
        # Load assignments data
        assignments_data = load_data(ASSIGNMENTS_DATA_FILE).get(str(teacher_id), [])
        with tab1:
            with st.form("create_assignment", clear_on_submit=True):
                st.subheader("Create New Assignment")
                title = st.text_input("Assignment Title*")
                description = st.text_area("Description")
                due_date = st.date_input("Due Date*", min_value=datetime.today())
                assigned_class = st.selectbox("Assign to Class*", get_full_class_list())
                max_score = st.number_input("Maximum Score*", min_value=1, value=100)
                assignment_type = st.selectbox("Type", ["Homework", "Project", "Quiz", "Test"])
                if st.form_submit_button("Create Assignment"):
                    if not all([title, due_date, assigned_class, max_score]):
                        st.error("Please fill all required fields (*)")
                    else:
                        new_assignment = {
                            "id": str(uuid.uuid4()), # Use full UUID for assignments
                            "title": title,
                            "description": description,
                            "due_date": str(due_date),
                            "assigned_class": assigned_class,
                            "max_score": max_score,
                            "type": assignment_type,
                            "created_date": str(datetime.today().date()),
                            "submissions": []
                        }
                        assignments_data.append(new_assignment)
                        all_data = load_data(ASSIGNMENTS_DATA_FILE)
                        all_data[str(teacher_id)] = assignments_data
                        save_data(all_data, ASSIGNMENTS_DATA_FILE)
                        st.success("Assignment created successfully!")
                        st.rerun()
        with tab2:
            st.subheader("Grade Student Submissions")
            if not assignments_data:
                st.info("No assignments created yet")
            else:
                selected_assignment = st.selectbox(
                    "Select Assignment", assignments_data, format_func=lambda a: f"{a.get('title', 'Untitled')} - {a.get('assigned_class', 'N/A')} (Due: {a.get('due_date', 'N/A')})"
                )
                if not selected_assignment.get('submissions', []):
                    st.info("No submissions for this assignment yet")
                else:
                    for sub in selected_assignment['submissions']:
                        with st.expander(f"Submission by {sub.get('student_name', 'N/A')} (ID: {sub.get('student_id', 'N/A')})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Submitted on:** {sub.get('submission_date', 'N/A')}")
                                st.write(f"**Status:** {sub.get('status', 'Submitted')}")
                            with col2:
                                st.write(f"**Current Grade:** {sub.get('grade', 'Not graded')}/{selected_assignment.get('max_score', 'N/A')}")
                                st.write(f"**Late Submission:** {sub.get('late_days', 0)} days")
                            st.write("**Submission Content:**")
                            st.write(sub.get('submission_text', 'No content provided.'))
                            if sub.get('submission_file_path') and os.path.exists(sub['submission_file_path']):
                                try:
                                    with open(sub['submission_file_path'], "rb") as f:
                                        st.download_button(
                                            label="Download Submitted File",
                                            data=f.read(),
                                            file_name=os.path.basename(sub['submission_file_path']),
                                            mime="application/octet-stream", # Generic MIME type
                                            key=f"download_submission_{sub['id']}"
                                        )
                                except Exception as e:
                                    st.warning(f"Could not download submission file: {e}")
                            with st.form(f"grade_form_{sub.get('student_id', 'N/A')}_{selected_assignment.get('id', 'N/A')}"):
                                grade = st.number_input(
                                    "Grade", min_value=0, max_value=selected_assignment.get('max_score', 100), value=sub.get('grade', 0), key=f"grade_{sub.get('student_id', 'N/A')}_{selected_assignment.get('id', 'N/A')}"
                                )
                                feedback = st.text_area(
                                    "Feedback", value=sub.get('feedback', ""), height=150
                                )
                                status = st.selectbox(
                                    "Status", ["Submitted", "Graded", "Needs Revision"], index=["Submitted", "Graded", "Needs Revision"].index(sub.get('status', 'Submitted'))
                                )
                                submitted = st.form_submit_button("Submit Grade")
                                if submitted:
                                    # Update the specific submission object
                                    sub['grade'] = grade
                                    sub['feedback'] = feedback
                                    sub['status'] = status
                                    # Find the index of the selected assignment in the teacher's assignments_data
                                    # and update it to ensure changes are propagated
                                    assignment_found_and_updated = False
                                    for i, assign_item in enumerate(assignments_data):
                                        if assign_item['id'] == selected_assignment['id']:
                                            # Replace the entire assignment object with the updated one
                                            # This ensures all changes within 'submissions' are saved
                                            assignments_data[i] = selected_assignment
                                            assignment_found_and_updated = True
                                            break
                                    if assignment_found_and_updated:
                                        all_data = load_data(ASSIGNMENTS_DATA_FILE)
                                        all_data[str(teacher_id)] = assignments_data
                                        save_data(all_data, ASSIGNMENTS_DATA_FILE)
                                        st.success("Grade submitted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Error: Could not find or update assignment in data.")
        with tab3:
            st.subheader("Assignment Analytics")
            if not assignments_data:
                st.info("No assignment data available")
            else:
                # Calculate average grades per assignment
                assignment_stats = []
                for assignment in assignments_data:
                    if assignment.get('submissions'):
                        grades = [s.get('grade', 0) for s in assignment['submissions'] if 'grade' in s and s['grade'] is not None] # Filter out None grades
                        avg_grade = sum(grades) / len(grades) if grades else 0
                        # Get total students in assigned class for completion rate
                        students_in_class = get_students_by_class(assignment.get('assigned_class', ''))
                        total_students_in_class = len(students_in_class)
                        completion_rate = f"{len(assignment['submissions'])/total_students_in_class:.0%}" if total_students_in_class > 0 else "N/A"
                        assignment_stats.append({
                            "Assignment": assignment.get('title', 'N/A'),
                            "Class": assignment.get('assigned_class', 'N/A'),
                            "Due Date": assignment.get('due_date', 'N/A'),
                            "Submissions": len(assignment['submissions']),
                            "Avg Grade": f"{avg_grade:.1f}/{assignment.get('max_score', 'N/A')}",
                            "Completion": completion_rate
                        })
                if assignment_stats:
                    st.dataframe(pd.DataFrame(assignment_stats))
                # Grade distribution chart
                grades_data = []
                for assignment in assignments_data:
                    for sub in assignment.get('submissions', []):
                        if 'grade' in sub and sub['grade'] is not None: # Ensure grade is not None
                            grades_data.append({
                                "Assignment": assignment.get('title', 'N/A'),
                                "Grade": sub.get('grade', 0),
                                "Class": assignment.get('assigned_class', 'N/A')
                            })
                if grades_data:
                    grades_df = pd.DataFrame(grades_data)
                    st.bar_chart(grades_df.groupby('Assignment')['Grade'].mean())
                else:
                    st.info("No graded assignments yet")

    # Performance Section (Updated)
    elif selected == "Performance":
        st.header("📊 Student Performance Analytics")
        tab1, tab2, tab3 = st.tabs(["Record Performance", "Class Performance", "Individual Progress"])
        # Load performance data
        performance_data = load_data(PERFORMANCE_DATA_FILE).get(str(teacher_id), {})
        with tab1:
            st.subheader("Record Student Performance")
            # Select class and student
            all_classes = get_full_class_list()
            selected_class_for_perf = st.selectbox("Select Class", all_classes, key="perf_class_select")
            students_in_selected_class = get_students_by_class(selected_class_for_perf)
            student_options = {s['name']: s['id'] for s in students_in_selected_class}
            selected_student_name_for_perf = st.selectbox(
                "Select Student", [""] + list(student_options.keys()), key="perf_student_select"
            )
            selected_student_id_for_perf = student_options.get(selected_student_name_for_perf)
            if selected_student_id_for_perf:
                # Load existing performance for this student if any
                current_student_perf = None
                if selected_class_for_perf in performance_data:
                    for s_perf in performance_data[selected_class_for_perf]:
                        if s_perf.get('student_id') == selected_student_id_for_perf:
                            current_student_perf = s_perf
                            break
                
                with st.form("record_performance_form"):
                    subject_perf = st.selectbox("Subject", COMMON_SUBJECTS)
                    score = st.number_input("Score (out of 100)", min_value=0, max_value=100, value=current_student_perf.get('score', 0) if current_student_perf else 0)
                    feedback_perf = st.text_area("Feedback/Comments", value=current_student_perf.get('feedback', '') if current_student_perf else '')
                    
                    if st.form_submit_button("Save Performance"):
                        new_performance_entry = {
                            "student_id": selected_student_id_for_perf,
                            "student_name": selected_student_name_for_perf,
                            "class": selected_class_for_perf,
                            "subject": subject_perf,
                            "score": score,
                            "feedback": feedback_perf,
                            "date": str(datetime.today().date())
                        }
                        
                        if selected_class_for_perf not in performance_data:
                            performance_data[selected_class_for_perf] = []
                        
                        # Check if an entry for this student and subject already exists to update it
                        updated = False
                        for i, entry in enumerate(performance_data[selected_class_for_perf]):
                            if entry.get('student_id') == selected_student_id_for_perf and entry.get('subject') == subject_perf:
                                performance_data[selected_class_for_perf][i] = new_performance_entry
                                updated = True
                                break
                        
                        if not updated:
                            performance_data[selected_class_for_perf].append(new_performance_entry)
                        
                        all_data = load_data(PERFORMANCE_DATA_FILE)
                        all_data[str(teacher_id)] = performance_data
                        save_data(all_data, PERFORMANCE_DATA_FILE)
                        st.success("Performance recorded successfully!")
                        st.rerun()
            else:
                st.info("Please select a student to record performance.")
        
        with tab2:
            st.subheader("Class Performance Overview")
            selected_class_for_overview = st.selectbox("Select Class for Overview", all_classes, key="class_overview_select")
            if selected_class_for_overview in performance_data:
                class_perf_data = performance_data[selected_class_for_overview]
                if class_perf_data:
                    df_class_perf = pd.DataFrame(class_perf_data)
                    # Ensure all required columns are present before displaying or plotting
                    required_perf_cols = ['student_name', 'subject', 'score', 'date']
                    for col in required_perf_cols:
                        if col not in df_class_perf.columns:
                            df_class_perf[col] = None # Add missing column with None
                    st.dataframe(df_class_perf[required_perf_cols], use_container_width=True)
                    
                    # Average score per subject in class
                    avg_scores = df_class_perf.groupby('subject')['score'].mean().reset_index()
                    st.write("**Average Scores by Subject:**")
                    st.dataframe(avg_scores)
                    st.bar_chart(avg_scores.set_index('subject'))
                else:
                    st.info("No performance data for this class yet.")
            else:
                st.info("No performance data for this class yet.")
        
        with tab3:
            st.subheader("Individual Student Progress")
            selected_student_name_for_progress = st.selectbox(
                "Select Student for Progress", [""] + list(student_options.keys()), key="student_progress_select"
            )
            selected_student_id_for_progress = student_options.get(selected_student_name_for_progress)
            
            if selected_student_id_for_progress:
                student_progress_records = []
                for class_key, perf_list in performance_data.items():
                    for entry in perf_list:
                        if entry.get('student_id') == selected_student_id_for_progress:
                            student_progress_records.append(entry)
                
                if student_progress_records:
                    df_progress = pd.DataFrame(student_progress_records)
                    # Ensure all required columns are present before displaying or plotting
                    required_progress_cols = ['subject', 'score', 'date', 'feedback']
                    for col in required_progress_cols:
                        if col not in df_progress.columns:
                            df_progress[col] = None # Add missing column with None
                    st.write(f"**Progress for {selected_student_name_for_progress}:**")
                    st.dataframe(df_progress[required_progress_cols].sort_values(by='date', ascending=False), use_container_width=True)
                    
                    # Plot progress over time (if dates are consistent)
                    if 'date' in df_progress.columns:
                        df_progress['date'] = pd.to_datetime(df_progress['date'])
                        for subject in df_progress['subject'].unique():
                            subject_df = df_progress[df_progress['subject'] == subject].sort_values(by='date')
                            if not subject_df.empty: # Only plot if there's data for the subject
                                st.line_chart(subject_df.set_index('date')['score'], use_container_width=True)
                                st.caption(f"Score Trend for {subject}")
                    else:
                        st.warning("Date column not found for plotting progress.")
                else:
                    st.info("No performance records found for this student.")
            else:
                st.info("Please select a student to view their progress.")

    # Communication Section
    elif selected == "Communication":
        st.header("💬 Messages & Announcements")
        
        tab1, tab2 = st.tabs(["Send Message", "View Messages"])
        
        messages_data = load_data(MESSAGES_DATA_FILE).get(str(teacher_id), [])
        
        with tab1:
            with st.form("send_message", clear_on_submit=True):
                st.subheader("Send New Message")
                recipient_type = st.radio("Send to:", ["All Students", "Select Class", "Specific Student"])
                
                recipient_id = None
                if recipient_type == "Select Class":
                    selected_class = st.selectbox("Select Class", get_full_class_list(), key="msg_class_select")
                    recipient_id = f"class_{selected_class}"
                elif recipient_type == "Specific Student":
                    all_students_for_msg = []
                    student_data_msg = load_data(STUDENT_DATA_FILE)
                    for class_name_msg, students_in_class_msg in student_data_msg.items():
                        for student_msg in students_in_class_msg:
                            all_students_for_msg.append(student_msg)
                    
                    student_options_msg = {f"{s.get('name', 'N/A')} (Adm No: {s.get('admission_no', 'N/A')})": s['id'] for s in all_students_for_msg} # Added .get for safety
                    selected_student_display = st.selectbox(
                        "Select Student", [""] + list(student_options_msg.keys()), key="msg_student_select"
                    )
                    recipient_id = student_options_msg.get(selected_student_display)
                else: # All Students
                    recipient_id = "all_students"

                message_subject = st.text_input("Subject*")
                message_content = st.text_area("Message Content*", height=200)
                
                if st.form_submit_button("Send Message"):
                    if not message_subject or not message_content or not recipient_id:
                        st.error("Please fill all required fields and select a recipient.")
                    else:
                        new_message = {
                            "id": str(uuid.uuid4()),
                            "sender_id": teacher_id,
                            "sender_name": teacher_data.get('name', 'Teacher'),
                            "recipient_type": recipient_type,
                            "recipient_id": recipient_id,
                            "subject": message_subject,
                            "content": message_content,
                            "timestamp": str(datetime.now())
                        }
                        messages_data.append(new_message)
                        all_data = load_data(MESSAGES_DATA_FILE)
                        all_data[str(teacher_id)] = messages_data
                        save_data(all_data, MESSAGES_DATA_FILE)
                        st.success("Message sent successfully!")
                        st.rerun()

        with tab2:
            st.subheader("Sent Messages")
            if not messages_data:
                st.info("No messages sent yet.")
            else:
                for msg in sorted(messages_data, key=lambda x: x.get('timestamp', ''), reverse=True):
                    with st.expander(f"Subject: {msg.get('subject', 'No Subject')} | To: {msg.get('recipient_type', 'N/A').replace('class_', '')} | {msg.get('timestamp', 'N/A').split('.')[0]}"):
                        st.write(f"**From:** {msg.get('sender_name', 'N/A')}")
                        st.write(f"**Recipient:** {msg.get('recipient_type', 'N/A').replace('class_', 'Class: ')}")
                        st.write(f"**Content:** {msg.get('content', 'No content')}")

    # Resources Section
    elif selected == "Resources":
        st.header("📚 Learning Resources")
        
        tab1, tab2 = st.tabs(["Upload Resource", "View Resources"])
        
        resources_data = load_data(RESOURCES_DATA_FILE).get(str(teacher_id), [])
        
        with tab1:
            with st.form("upload_resource", clear_on_submit=True):
                st.subheader("Upload New Resource")
                title = st.text_input("Resource Title*")
                description = st.text_area("Description")
                class_name = st.selectbox("For Class*", get_full_class_list())
                subject = st.selectbox("Subject*", COMMON_SUBJECTS)
                uploaded_file = st.file_uploader("Upload File (PDF, DOCX, TXT, etc.)", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])
                
                if st.form_submit_button("Upload Resource"):
                    if not all([title, class_name, subject, uploaded_file]):
                        st.error("Please fill all required fields and upload a file.")
                    else:
                        file_path = os.path.join(DATA_DIR, "attachments", uploaded_file.name)
                        try:
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            new_resource = {
                                "id": str(uuid.uuid4()),
                                "title": title,
                                "description": description,
                                "class_name": class_name,
                                "subject": subject,
                                "uploaded_by": teacher_data.get('name', 'Teacher'),
                                "upload_date": str(datetime.today().date()),
                                "file_path": file_path
                            }
                            resources_data.append(new_resource)
                            all_data = load_data(RESOURCES_DATA_FILE)
                            all_data[str(teacher_id)] = resources_data
                            save_data(all_data, RESOURCES_DATA_FILE)
                            st.success("Resource uploaded successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving file: {e}")

        with tab2:
            st.subheader("Available Resources")
            if not resources_data:
                st.info("No resources uploaded yet.")
            else:
                for resource in sorted(resources_data, key=lambda x: x.get('upload_date', ''), reverse=True):
                    with st.expander(f"**{resource.get('title', 'No Title')}** - {resource.get('subject', 'N/A')} ({resource.get('class_name', 'N/A')})"):
                        st.write(f"**Description:** {resource.get('description', 'No description.')}")
                        st.write(f"**Uploaded by:** {resource.get('uploaded_by', 'N/A')} on {resource.get('upload_date', 'N/A')}")
                        if resource.get('file_path') and os.path.exists(resource['file_path']):
                            try:
                                with open(resource['file_path'], "rb") as f:
                                    st.download_button(
                                        label="Download Resource",
                                        data=f.read(),
                                        file_name=os.path.basename(resource['file_path']),
                                        mime="application/octet-stream",
                                        key=f"download_resource_{resource['id']}"
                                    )
                            except Exception as e:
                                st.warning(f"Could not download resource file: {e}")
                        
                        if st.button("Delete Resource", key=f"delete_resource_{resource['id']}"):
                            resources_data.remove(resource)
                            # Optionally delete the file from disk as well
                            if os.path.exists(resource['file_path']):
                                os.remove(resource['file_path'])
                            all_data = load_data(RESOURCES_DATA_FILE)
                            all_data[str(teacher_id)] = resources_data
                            save_data(all_data, RESOURCES_DATA_FILE)
                            st.success("Resource deleted successfully!")
                            st.rerun()

    # Leave Section
    elif selected == "Leave":
        st.header("Leave Application") # Changed from Japanese
        
        tab1, tab2 = st.tabs(["Apply", "Application History"]) # Changed from Japanese
        
        leave_data = load_data(LEAVE_DATA_FILE).get(str(teacher_id), [])
        
        with tab1:
            with st.form("apply_leave", clear_on_submit=True):
                st.subheader("Apply for Leave") # Changed from Japanese
                leave_type = st.selectbox("Leave Type", ["Sick Leave", "Casual Leave", "Bereavement Leave", "Other"]) # Changed from Japanese
                start_date = st.date_input("Start Date", min_value=datetime.today().date()) # Changed from Japanese
                end_date = st.date_input("End Date", min_value=start_date) # Changed from Japanese
                reason = st.text_area("Reason", help="Please provide a detailed reason for your leave.") # Changed from Japanese
                attachment = st.file_uploader("Attachment (e.g., medical certificate)", type=["pdf", "jpg", "png", "docx"]) # Changed from Japanese
                
                if st.form_submit_button("Submit Application"): # Changed from Japanese
                    if not reason:
                        st.error("Please enter a reason.") # Changed from Japanese
                    else:
                        attachment_path = None
                        if attachment:
                            attach_filename = f"leave_attachment_{uuid.uuid4()}_{attachment.name}"
                            attach_save_path = os.path.join(DATA_DIR, "leave_attachments", attach_filename)
                            try:
                                with open(attach_save_path, "wb") as f:
                                    f.write(attachment.getbuffer())
                                attachment_path = attach_save_path
                            except Exception as e:
                                st.error(f"Error saving attachment: {e}") # Changed from Japanese

                        new_leave_request = {
                            "id": str(uuid.uuid4()),
                            "teacher_id": teacher_id,
                            "teacher_name": teacher_data.get('name', 'N/A'),
                            "leave_type": leave_type,
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                            "reason": reason,
                            "attachment_path": attachment_path,
                            "status": "Pending", # Pending, Approved, Rejected
                            "request_date": str(datetime.today().date())
                        }
                        leave_data.append(new_leave_request)
                        all_data = load_data(LEAVE_DATA_FILE)
                        all_data[str(teacher_id)] = leave_data
                        save_data(all_data, LEAVE_DATA_FILE)
                        st.success("Leave application submitted successfully!") # Changed from Japanese
                        st.rerun()

        with tab2:
            st.subheader("Leave Application History") # Changed from Japanese
            if not leave_data:
                st.info("No application history found.") # Changed from Japanese
            else:
                for request in sorted(leave_data, key=lambda x: x.get('request_date', ''), reverse=True):
                    status_color = "orange"
                    if request.get('status') == "Approved":
                        status_color = "green"
                    elif request.get('status') == "Rejected":
                        status_color = "red"
                    
                    with st.expander(f"Type: {request.get('leave_type', 'N/A')} | {request.get('start_date', 'N/A')} - {request.get('end_date', 'N/A')} | Status: :{status_color}[{request.get('status', 'N/A')}]"): # Changed from Japanese
                        st.write(f"**Request Date:** {request.get('request_date', 'N/A')}") # Changed from Japanese
                        st.write(f"**Reason:** {request.get('reason', 'N/A')}") # Changed from Japanese
                        if request.get('attachment_path') and os.path.exists(request['attachment_path']):
                            try:
                                with open(request['attachment_path'], "rb") as f:
                                    st.download_button(
                                        label="Download Attachment", # Changed from Japanese
                                        data=f.read(),
                                        file_name=os.path.basename(request['attachment_path']),
                                        mime="application/octet-stream",
                                        key=f"download_leave_attach_{request['id']}"
                                    )
                            except Exception as e:
                                st.warning(f"Could not download attachment: {e}") # Changed from Japanese

    # Export Data Section
    elif selected == "Export Data":
        st.header("⬇️ Export Data") # Changed from Japanese
        st.write("You can export various data from the system in CSV format.") # Changed from Japanese
        
        export_option = st.selectbox(
            "Select data to export", # Changed from Japanese
            ["Teacher Data", "Student Data", "Attendance Data", "Assignment Data", "Timetable Data", "Performance Data", "Message Data", "Resource Data", "Leave Application Data"] # Changed from Japanese
        )
        
        if st.button("Generate Export File", key="generate_export_file"): # Changed from Japanese
            file_to_export = None
            export_filename = ""
            
            if export_option == "Teacher Data": # Changed from Japanese
                file_to_export = TEACHER_DATA_FILE
                export_filename = "teacher_data.json"
            elif export_option == "Student Data": # Changed from Japanese
                file_to_export = STUDENT_DATA_FILE
                export_filename = "student_data.json"
            elif export_option == "Attendance Data": # Changed from Japanese
                file_to_export = ATTENDANCE_DATA_FILE
                export_filename = "attendance_data.json"
            elif export_option == "Assignment Data": # Changed from Japanese
                file_to_export = ASSIGNMENTS_DATA_FILE
                export_filename = "assignments_data.json"
            elif export_option == "Timetable Data": # Changed from Japanese
                file_to_export = TIMETABLE_DATA_FILE
                export_filename = "timetable_data.json"
            elif export_option == "Performance Data": # Changed from Japanese
                file_to_export = PERFORMANCE_DATA_FILE
                export_filename = "performance_data.json"
            elif export_option == "Message Data": # Changed from Japanese
                file_to_export = MESSAGES_DATA_FILE
                export_filename = "messages_data.json"
            elif export_option == "Resource Data": # Changed from Japanese
                file_to_export = RESOURCES_DATA_FILE
                export_filename = "resources_data.json"
            elif export_option == "Leave Application Data": # Changed from Japanese
                file_to_export = LEAVE_DATA_FILE
                export_filename = "leave_data.json"

            if file_to_export and os.path.exists(file_to_export):
                data_to_export = load_data(file_to_export)
                # For teacher-specific data, export only the current teacher's data
                if export_option in ["Attendance Data", "Assignment Data", "Timetable Data", "Performance Data", "Message Data", "Resource Data", "Leave Application Data"]: # Changed from Japanese
                    data_to_export = data_to_export.get(str(teacher_id), {})
                
                # Convert complex structures to DataFrame for CSV export
                df_export = pd.DataFrame()
                if export_option == "Student Data": # Changed from Japanese
                    all_students_for_export = []
                    for class_name_export, students_in_class_export in data_to_export.items():
                        all_students_for_export.extend(students_in_class_export)
                    df_export = pd.DataFrame(all_students_for_export)
                elif export_option == "Teacher Data": # Changed from Japanese
                    df_export = pd.DataFrame([data_to_export]) # Wrap in list to make it a list of records
                elif export_option == "Attendance Data": # Changed from Japanese
                    records = []
                    for date, classes_data in data_to_export.items():
                        for class_name, attendance_records in classes_data.items():
                            for student_id, status in attendance_records.items():
                                # Assuming you can get student name from ID if needed, for simplicity using ID
                                student_name = next((s['name'] for s_list in load_data(STUDENT_DATA_FILE).values() for s in s_list if s['id'] == student_id), "Unknown Student")
                                records.append({"Date": date, "Class": class_name, "Student ID": student_id, "Student Name": student_name, "Status": status})
                    df_export = pd.DataFrame(records)
                elif export_option == "Assignment Data": # Changed from Japanese
                    records = []
                    for assignment in data_to_export:
                        for submission in assignment.get('submissions', []):
                            records.append({
                                "Assignment Title": assignment.get('title', 'N/A'),
                                "Assigned Class": assignment.get('assigned_class', 'N/A'),
                                "Due Date": assignment.get('due_date', 'N/A'),
                                "Student Name": submission.get('student_name', 'N/A'),
                                "Submission Date": submission.get('submission_date', 'N/A'),
                                "Grade": submission.get('grade', 'N/A'),
                                "Status": submission.get('status', 'N/A'),
                                "Feedback": submission.get('feedback', 'N/A')
                            })
                    df_export = pd.DataFrame(records)
                elif export_option == "Timetable Data": # Changed from Japanese
                    df_export = pd.DataFrame(data_to_export)
                elif export_option == "Performance Data": # Changed from Japanese
                    all_perf_records = []
                    for class_name_perf, perf_list in data_to_export.items():
                        all_perf_records.extend(perf_list)
                    df_export = pd.DataFrame(all_perf_records)
                elif export_option == "Message Data": # Changed from Japanese
                    df_export = pd.DataFrame(data_to_export)
                elif export_option == "Resource Data": # Changed from Japanese
                    df_export = pd.DataFrame(data_to_export)
                elif export_option == "Leave Application Data": # Changed from Japanese
                    df_export = pd.DataFrame(data_to_export)

                if not df_export.empty:
                    csv_export = df_export.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        f"Download {export_option} (.csv)", # Changed from Japanese
                        csv_export,
                        f"{export_option.replace(' ', '_').lower()}.csv",
                        "text/csv"
                    )
                else:
                    st.warning(f"No {export_option} data to export.") # Changed from Japanese
            else:
                st.error(f"{export_option} data file not found.") # Changed from Japanese
    
    # School Essentials Section
    elif selected == "School Essentials":
        st.header("🛍️ School Essentials")
        
        tab1, tab2 = st.tabs(["Purchase Items", "View Orders"]) # Removed "Update Delivery Status" tab
        
        with tab1:
            st.subheader("Purchase School Items")
            
            # Item selection
            item_type = st.selectbox("Select Item Type", ["School Uniform", "Pants", "Socks", "Shoes", "Other"])
            
            if item_type == "School Uniform":
                size = st.selectbox("Select Size", ["XS", "S", "M", "L", "XL", "XXL"])
                gender = st.radio("Gender", ["Male", "Female", "Unisex"])
                quantity = st.number_input("Quantity", min_value=1, value=1)
                price_per_item = 500 # Example price
                item_details = f"School Uniform - Size: {size}, Gender: {gender}"
            elif item_type == "Pants":
                size = st.selectbox("Select Size", ["24", "26", "28", "30", "32", "34", "36"])
                color = st.text_input("Color", value="Grey")
                quantity = st.number_input("Quantity", min_value=1, value=1)
                price_per_item = 300 # Example price
                item_details = f"Pants - Size: {size}, Color: {color}"
            elif item_type == "Socks":
                size = st.selectbox("Select Size", ["Small", "Medium", "Large"])
                color = st.text_input("Color", value="White")
                quantity = st.number_input("Quantity", min_value=1, value=1)
                price_per_item = 50 # Example price
                item_details = f"Socks - Size: {size}, Color: {color}"
            elif item_type == "Shoes":
                size = st.number_input("Select Shoe Size (UK)", min_value=1, max_value=12, value=6)
                style = st.selectbox("Style", ["Formal", "Sports"])
                quantity = st.number_input("Quantity", min_value=1, value=1)
                price_per_item = 700 # Example price
                item_details = f"Shoes - Size: {size}, Style: {style}"
            else: # Other
                custom_item_name = st.text_input("Item Name")
                custom_description = st.text_area("Description")
                quantity = st.number_input("Quantity", min_value=1, value=1)
                price_per_item = st.number_input("Price per item", min_value=0.0, value=100.0, step=0.1)
                item_details = f"{custom_item_name} - {custom_description}" if custom_item_name else "Other Item"

            total_price = quantity * price_per_item
            st.write(f"**Total Price: ₹{total_price:.2f}**")

            student_data_for_order = load_data(STUDENT_DATA_FILE)
            all_students_for_order_list = []
            for class_name_order, students_in_class_order in student_data_for_order.items():
                for student_order in students_in_class_order:
                    # Ensure 'admission_no' is present when constructing the display string
                    all_students_for_order_list.append(student_order)
            
            # Handle empty list of students to avoid error
            if not all_students_for_order_list:
                st.warning("No student records available to place an order. Please add students first in Student Management.")
                selected_student_id_for_order = None
            else:
                student_options_for_order = {f"{s.get('name', 'N/A')} (Adm No: {s.get('admission_no', 'N/A')})": s['id'] for s in all_students_for_order_list}
                selected_student_display_for_order = st.selectbox(
                    "Select Student for this Order", [""] + list(student_options_for_order.keys()), key="order_student_select"
                )
                selected_student_id_for_order = student_options_for_order.get(selected_student_display_for_order)

            if st.button("Place Order"):
                if not selected_student_id_for_order:
                    st.error("Please select a student for this order.")
                elif item_type == "Other" and not custom_item_name:
                    st.error("Please enter an item name for 'Other' type.")
                else:
                    orders = load_orders()
                    new_order = {
                        "order_id": str(uuid.uuid4()),
                        "student_id": selected_student_id_for_order,
                        "student_name": selected_student_display_for_order.split(" (")[0], # Extract name
                        "item_type": item_type,
                        "item_details": item_details,
                        "quantity": quantity,
                        "price_per_item": price_per_item,
                        "total_price": total_price,
                        "order_date": str(datetime.today().date()),
                        "delivery_status": "Pending", # Initial status
                        "teacher_id": teacher_id
                    }
                    if str(teacher_id) not in orders:
                        orders[str(teacher_id)] = []
                    orders[str(teacher_id)].append(new_order)
                    save_orders(orders)
                    st.success("Order placed successfully!")
                    st.rerun()

        with tab2:
            st.subheader("View All Orders")
            orders_data = load_orders().get(str(teacher_id), [])
            
            if not orders_data:
                st.info("No orders placed yet.")
            else:
                df_orders = pd.DataFrame(orders_data)
                df_orders_display = df_orders[[
                    "order_id", "student_name", "item_type", "item_details", 
                    "quantity", "total_price", "order_date", "delivery_status"
                ]]
                st.dataframe(df_orders_display, use_container_width=True)
