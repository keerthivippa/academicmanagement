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

TEACHER_DATA_FILE = os.path.join(DATA_DIR, "teacher_data.json")
STUDENT_DATA_FILE = os.path.join(DATA_DIR, "student_data.json")
CLASS_DATA_FILE = os.path.join(DATA_DIR, "class_data.json")
FEE_DATA_FILE = os.path.join(DATA_DIR, "fee_data.json")
EVENT_NOTICE_DATA_FILE = os.path.join(DATA_DIR, "event_notice_data.json")
ATTENDANCE_DATA_FILE = os.path.join(DATA_DIR, "attendance_data.json")
ASSIGNMENTS_DATA_FILE = os.path.join(DATA_DIR, "assignments_data.json")
PERFORMANCE_DATA_FILE = os.path.join(DATA_DIR, "performance_data.json")
TIMETABLE_DATA_FILE = os.path.join(DATA_DIR, "timetable_data.json")
MESSAGES_DATA_FILE = os.path.join(DATA_DIR, "messages_data.json")
RESOURCES_DATA_FILE = os.path.join(DATA_DIR, "resources_data.json")
LEAVE_DATA_FILE = os.path.join(DATA_DIR, "leave_data.json")


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

# Grade levels and sections
GRADE_LEVELS = ["Nursery", "LKG", "UKG"] + [f"Grade {i}" for i in range(1, 11)]
CLASS_SECTIONS = ["A", "B", "C", "D"]

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

# ==============================================================================
# SESSION STATE INITIALIZATION (Moved to top-level for immediate availability)
# ==============================================================================

# Initialize teachers data
if 'teachers' not in st.session_state:
    st.session_state.teachers = load_data(TEACHER_DATA_FILE)
    if not st.session_state.teachers:
        # Add a default admin if no teachers are found
        default_admin_id = str(uuid.uuid4())
        st.session_state.teachers[default_admin_id] = {
            "id": default_admin_id,
            "username": "admin",
            "password": hash_password("admin123"), # Default password
            "name": "Default Admin",
            "subject": "Administration",
            "email": "admin@school.com",
            "phone": "1234567890",
            "join_date": str(datetime.today().date()),
            "designation": "System Administrator",
            "resignation_date": None,
            "epf_number": "EPF001",
            "esi_number": "ESI001",
            "payroll": 50000.00,
            "is_admin": True
        }
        save_data(st.session_state.teachers, TEACHER_DATA_FILE)
        # Set a flag to show success message on login page
        st.session_state['default_admin_created'] = True 

# Initialize students data
if 'students' not in st.session_state:
    st.session_state.students = load_data(STUDENT_DATA_FILE)
    if not st.session_state.students:
        # Add some sample student data if the file is empty
        sample_students = {}
        for class_name in get_full_class_list():
            sample_students[class_name] = []
            num_students = 2 if class_name in ["Nursery", "LKG", "UKG"] else 3
            for i in range(1, num_students + 1):
                student_id_prefix = (GRADE_LEVELS.index(class_name.split(' ')[0] if ' ' in class_name else class_name) + 1) * 1000
                admission_no = f"ADM{student_id_prefix + i:04d}"
                sample_students[class_name].append({
                    "id": str(uuid.uuid4()), # Unique internal ID
                    "admission_no": admission_no,
                    "name": f"Student {i} {class_name}",
                    "roll_no": f"{i}",
                    "class": class_name,
                    "dob": "2010-01-01",
                    "date_of_joining": "2023-09-01",
                    "date_of_tc": None,
                    "adhar_number": f"1234567890{i:02d}",
                    "father_name": f"Father {i} {class_name}",
                    "mother_name": f"Mother {i} {class_name}",
                    "parent_email": f"parent{i}_{class_name.replace(' ', '_')}@example.com",
                    "parent_phone": f"98765432{i:02d}",
                    "address": f"{i} School Road, {class_name} City",
                    "emergency_contact": f"Emergency Contact {i} - 99988877{i:02d}",
                    "contact_number": f"91234567{i:02d}",
                    "blood_group": "O+",
                    "financial_status": "Paid",
                    "passport_photo_path": None
                })
            st.session_state.students = sample_students
            save_data(st.session_state.students, STUDENT_DATA_FILE)

# Initialize other data files with empty structures if they don't exist
data_files_to_initialize = {
    'attendance_data': ATTENDANCE_DATA_FILE,
    'assignments_data': ASSIGNMENTS_DATA_FILE,
    'timetable_data': TIMETABLE_DATA_FILE,
    'performance_data': PERFORMANCE_DATA_FILE,
    'messages_data': MESSAGES_DATA_FILE,
    'resources_data': RESOURCES_DATA_FILE,
    'leave_data': LEAVE_DATA_FILE,
    'class_data': CLASS_DATA_FILE,
    'fee_data': FEE_DATA_FILE,
    'event_notice_data': EVENT_NOTICE_DATA_FILE
}

for session_key, file_path in data_files_to_initialize.items():
    if session_key not in st.session_state:
        st.session_state[session_key] = load_data(file_path)
        if not st.session_state[session_key]: # If file was empty, initialize with empty dict
            st.session_state[session_key] = {}
            save_data(st.session_state[session_key], file_path)

# ======================
# SECURITY & AUTHENTICATION (Admin Specific)
# ======================

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_admin(username, password):
    """Authenticate admin credentials"""
    # Access teachers data from session state
    teachers = st.session_state.teachers
    for teacher_id, teacher in teachers.items():
        if teacher.get('username') == username and teacher.get('password') == hash_password(password) and teacher.get('is_admin', False):
            return teacher_id # Return the ID of the authenticated admin
    return None

def register_admin_page():
    """Display admin registration page and handle registration"""
    st.title("🏛️ School Management System - Admin Registration")
    st.info("Register a new Admin user. The first registered user automatically gets admin privileges.")

    # Access teachers data from session state
    teachers = st.session_state.teachers
    
    # Check if there are any existing admin users
    has_existing_admins = any(teacher.get('is_admin', False) for teacher in teachers.values())

    if has_existing_admins:
        st.warning("An admin user already exists. Additional registrations will not automatically grant admin privileges unless manually set later by an existing admin.")

    with st.form("admin_register_form"):
        new_username = st.text_input("Choose Admin Username*", help="This will be your login username.").strip()
        new_password = st.text_input("Choose Admin Password*", type="password")
        confirm_password = st.text_input("Confirm Password*", type="password")
        admin_name = st.text_input("Full Name (e.g., Admin Name)*").strip()
        admin_email = st.text_input("Email (Optional)").strip()
        admin_phone = st.text_input("Phone (Optional)").strip()
        admin_designation = st.text_input("Designation (e.g., Principal, Administrator)").strip()

        if st.form_submit_button("Register Admin"):
            if not all([new_username, new_password, confirm_password, admin_name, admin_designation]):
                st.error("Please fill all required fields (*)")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                if any(t.get('username') == new_username for t in teachers.values()):
                    st.error("Username already exists. Please choose a different one.")
                else:
                    new_id = str(uuid.uuid4()) # Generate unique ID for teacher
                    
                    # Grant admin privileges to the first registered user
                    is_admin_user = not has_existing_admins # True if no admins exist yet

                    st.session_state.teachers[new_id] = { # Update session state
                        "id": new_id,
                        "username": new_username,
                        "password": hash_password(new_password),
                        "name": admin_name,
                        "subject": "Administration", # Default subject for admin
                        "email": admin_email,
                        "phone": admin_phone,
                        "join_date": str(datetime.today().date()),
                        "designation": admin_designation, # New field
                        "resignation_date": None, # New field
                        "epf_number": "", # New field
                        "esi_number": "", # New field
                        "payroll": 0.0, # New field
                        "is_admin": is_admin_user
                    }
                    save_data(st.session_state.teachers, TEACHER_DATA_FILE) # Save updated data
                    st.success(f"Admin user '{admin_name}' registered successfully! You can now login.")
                    st.session_state['show_admin_login'] = True # After registration, show login
                    st.rerun()


def admin_login_or_register_page():
    """Display options for admin login or registration"""
    st.title("🏛️ School Management System - Admin Portal")

    if 'show_admin_login' not in st.session_state:
        st.session_state['show_admin_login'] = True # Default to showing login first

    # Display default admin creation message if flag is set
    if st.session_state.get('default_admin_created', False):
        st.success("Default admin user 'admin' with password 'admin123' has been created. Please log in.")
        del st.session_state['default_admin_created'] # Clear the flag after displaying

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login as Admin", key="login_option_btn"):
            st.session_state['show_admin_login'] = True
    with col2:
        if st.button("Register as Admin", key="register_option_btn"):
            st.session_state['show_admin_login'] = False

    st.markdown("---") # Separator

    if st.session_state['show_admin_login']:
        st.subheader("Admin Login")
        with st.form("admin_login_form"):
            username = st.text_input("Admin Username")
            password = st.text_input("Admin Password", type="password")

            if st.form_submit_button("Login"):
                admin_id = authenticate_admin(username, password)
                if admin_id:
                    st.session_state['admin_logged_in'] = True
                    st.session_state['admin_id'] = admin_id
                    st.rerun()
                else:
                    st.error("Invalid admin username or password. Ensure you have registered an admin account.")
    else:
        register_admin_page()


# ======================
# MANAGEMENT MODULE FUNCTIONS
# ======================

def display_overview_dashboard():
    """Display overview of institution performance"""
    st.header("📊 Institution Performance Overview")

    teachers = st.session_state.teachers
    students_by_class = st.session_state.students # This is a dict of lists, not a flat list
    attendance_data = st.session_state.attendance_data
    assignments_data = st.session_state.assignments_data
    fee_data = st.session_state.fee_data

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Teachers", len(teachers))
    with col2:
        total_students = sum(len(students) for students in students_by_class.values()) if students_by_class else 0
        st.metric("Total Students", total_students)
    with col3:
        total_classes = len(get_full_class_list())
        st.metric("Total Classes", total_classes)

    st.subheader("Key Performance Indicators")

    # Attendance Rate (simple average for demonstration)
    if attendance_data:
        total_present = 0
        total_records = 0
        for teacher_attn_key, teacher_attn_value in attendance_data.items(): # Iterate over items to get key and value
            if isinstance(teacher_attn_value, dict): # Ensure it's a dict before calling .values()
                for date_attn_key, date_attn_value in teacher_attn_value.items():
                    if isinstance(date_attn_value, dict): # Ensure it's a dict
                        for class_attn_key, class_attn_value in date_attn_value.items():
                            if isinstance(class_attn_value, dict): # Ensure it's a dict
                                total_present += list(class_attn_value.values()).count("Present")
                                total_records += len(class_attn_value)
                            else:
                                st.warning(f"Unexpected data type for class_attn_value at {teacher_attn_key}/{date_attn_key}/{class_attn_key}: {type(class_attn_value)}")
                    else:
                        st.warning(f"Unexpected data type for date_attn_value at {teacher_attn_key}/{date_attn_key}: {type(date_attn_value)}")
            else:
                st.warning(f"Unexpected data type for teacher_attn_value at {teacher_attn_key}: {type(teacher_attn_value)}")

        overall_attendance_rate = (total_present / total_records * 100) if total_records > 0 else 0
        st.metric("Overall Attendance Rate", f"{overall_attendance_rate:.1f}%")
    else:
        st.info("No attendance data available for analytics.")

    # Assignment Completion Rate (simple average)
    if assignments_data:
        total_assignments = 0
        total_submissions = 0
        for teacher_assignments in assignments_data.values():
            for assignment in teacher_assignments:
                total_assignments += 1
                total_submissions += len(assignment.get('submissions', []))

        completion_rate = (total_submissions / total_assignments * 100) if total_assignments > 0 else 0
        st.metric("Overall Assignment Completion Rate", f"{completion_rate:.1f}%")
    else:
        st.info("No assignment data available for analytics.")

    # Fee Collection Status
    if fee_data:
        total_expected_fees = sum(fee.get('amount_due', 0.0) for fee in fee_data.values())
        total_collected_fees = sum(fee.get('amount_paid', 0.0) for fee in fee_data.values())
        collection_percentage = (total_collected_fees / total_expected_fees * 100) if total_expected_fees > 0 else 0
        st.metric("Fee Collection Percentage", f"{collection_percentage:.1f}%")
    else:
        st.info("No fee data available for analytics.")

    st.subheader("Student Distribution by Class")
    student_counts = {cls: len(students) for cls, students in students_by_class.items()}
    if student_counts:
        df_students = pd.DataFrame(student_counts.items(), columns=['Class', 'Number of Students'])
        st.bar_chart(df_students.set_index('Class'))
    else:
        st.info("No student data available to display distribution.")

def manage_students_admin():
    """Admin view for managing student records (add/edit/delete)"""
    st.header("🧑‍🎓 Student Management")

    # Access students data from session state
    student_data = st.session_state.students

    tab1, tab2 = st.tabs(["Add Student", "Manage Existing Students"])

    with tab1:
        st.subheader("Add New Student")
        with st.form("add_student_admin", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                # New fields for Student Management
                student_admission_no = st.text_input("Student Admission Number*", help="Unique admission number for the student.").strip()
                name = st.text_input("Full Name*", help="Full legal name of the student.").strip()
                roll_no = st.text_input("Roll No.", help="Student's roll number in class (optional).").strip()
                class_name = st.selectbox("Class*", get_full_class_list())
                dob = st.date_input("Date of Birth*", max_value=datetime.today().date())
                date_of_joining = st.date_input("Date of Joining*", max_value=datetime.today().date())
                date_of_tc = st.date_input("Date of TC (Optional)", value=None, help="Date of Transfer Certificate issuance, if applicable.")
                adhar_number = st.text_input("Aadhar Number (Optional)").strip()
                contact_number = st.text_input("Student's Contact Number (Optional)").strip()
            with col2:
                parent_name = st.text_input("Parent/Guardian Name*").strip()
                father_name = st.text_input("Father's Name*").strip() # New field
                mother_name = st.text_input("Mother's Name*").strip() # New field
                parent_email = st.text_input("Parent Email*").strip()
                parent_phone = st.text_input("Parent Phone*").strip()
                address = st.text_area("Address").strip()
                emergency_contact = st.text_input("Emergency Contact (Name & Number)*").strip()
                blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]) # New field
                financial_status = st.text_input("Financial Status (e.g., Paid, Scholarship, Partial)").strip() # New field
                passport_photo = st.file_uploader("Upload Passport Photo (Optional)", type=["jpg", "jpeg", "png"]) # New field

            if st.form_submit_button("Add Student"):
                required_fields = [student_admission_no, name, class_name, dob, date_of_joining, parent_name, father_name, mother_name, parent_email, parent_phone, emergency_contact]
                if not all(required_fields):
                    st.error("Please fill all required fields (*)")
                else:
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
                            "admission_no": student_admission_no, # New field
                            "name": name,
                            "roll_no": roll_no, # New field
                            "class": class_name,
                            "dob": str(dob),
                            "date_of_joining": str(date_of_joining), # New field
                            "date_of_tc": str(date_of_tc) if date_of_tc else None, # New field
                            "adhar_number": adhar_number, # New field
                            "parent_name": parent_name,
                            "father_name": father_name, # New field
                            "mother_name": mother_name, # New field
                            "parent_email": parent_email,
                            "parent_phone": parent_phone,
                            "address": address,
                            "emergency_contact": emergency_contact,
                            "contact_number": contact_number, # New field
                            "blood_group": blood_group, # New field
                            "financial_status": financial_status, # New field
                            "passport_photo_path": photo_path # New field
                        }
                        student_data[class_name].append(new_student_record)
                        save_data(student_data, STUDENT_DATA_FILE) # Save updated data
                        st.success(f"Student '{name}' (Admission No: {student_admission_no}) added successfully to {class_name}!")
                        st.rerun() # Rerun to refresh the data display

    with tab2:
        st.subheader("Manage Existing Students")
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
            key="edit_delete_student_admission_no"
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

            action = st.radio("Choose Action", ["Edit", "Delete"], key="student_action_radio")

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
                        # For photo, allow new upload or display current
                        current_photo_path = selected_student_obj.get('passport_photo_path')
                        if current_photo_path and os.path.exists(current_photo_path):
                            st.image(current_photo_path, caption="Current Passport Photo", width=150)
                            st.info("Upload a new photo to replace the current one.")
                        new_passport_photo = st.file_uploader("Upload New Passport Photo (Optional)", type=["jpg", "jpeg", "png"], key=f"edit_photo_{selected_student_obj['id']}")

                    if st.form_submit_button("Save Changes"):
                        # Update the student data in session state
                        student_data_to_update = next((s for s in student_data[selected_student_obj['class']] if s['id'] == selected_student_obj['id']), None)
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
                if st.button("Confirm Delete", key=f"confirm_delete_{selected_student_obj['id']}"):
                    # Find and remove the student from the correct class list
                    original_class = selected_student_obj['class']
                    st.session_state.students[original_class] = [
                        s for s in st.session_state.students[original_class]
                        if s['id'] != selected_student_obj['id']
                    ]
                    # If the class list becomes empty, remove the class entry
                    if not st.session_state.students[original_class]:
                        del st.session_state.students[original_class]

                    save_data(st.session_state.students, STUDENT_DATA_FILE) # Save updated data
                    st.success("Student deleted successfully!")
                    st.rerun()
        else:
            st.info("Please select a student by Admission Number to manage.")


def manage_teachers_admin():
    """Admin view for managing teacher records (add/edit/delete)"""
    st.header("👨‍🏫 Teacher Management")

    # Access teachers data from session state
    teachers = st.session_state.teachers

    tab1, tab2 = st.tabs(["Add Teacher", "Manage Existing Teachers"])

    with tab1:
        st.subheader("Add New Teacher")
        with st.form("add_teacher_admin", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Choose Username*", help="This will be the teacher's login username.").strip()
                password = st.text_input("Choose Password*", type="password")
                teacher_name = st.text_input("Full Name*").strip()
                teacher_subject = st.selectbox("Subject*", ["Mathematics", "Science", "English", "History", "Geography", "Computer Science", "Arts", "Physical Education", "Other"])
                teacher_email = st.text_input("Email (Optional)").strip()
                teacher_phone = st.text_input("Phone (Optional)").strip()
            with col2:
                # New fields for Teacher Management
                designation = st.text_input("Designation*", help="e.g., Head of Department, Senior Teacher").strip()
                joining_date = st.date_input("Joining Date*", value=datetime.today().date())
                resignation_date = st.date_input("Resignation Date (Optional)", value=None, help="Set if the teacher has resigned.")
                epf_number = st.text_input("EPF Number (Optional)").strip()
                esi_number = st.text_input("ESI Number (Optional)").strip()
                payroll = st.number_input("Monthly Payroll (₹)", min_value=0.0, step=100.0, format="%.2f")
                # Monthly Attendance is derived from biometric system, not directly input here.
                # A placeholder or summary could be displayed elsewhere.
                is_admin_checkbox = st.checkbox("Grant Admin Privileges", help="Only grant to trusted personnel.")

            if st.form_submit_button("Add Teacher"):
                required_fields = [username, password, teacher_name, teacher_subject, designation, joining_date]
                if not all(required_fields):
                    st.error("Please fill all required fields (*)")
                else:
                    if any(t.get('username') == username for t in teachers.values()):
                        st.error("Username already exists. Please choose a different one.")
                    else:
                        new_id = str(uuid.uuid4()) # Generate unique ID for teacher
                        st.session_state.teachers[new_id] = { # Update session state
                            "id": new_id,
                            "username": username,
                            "password": hash_password(password),
                            "name": teacher_name,
                            "subject": teacher_subject,
                            "email": teacher_email,
                            "phone": teacher_phone,
                            "join_date": str(joining_date),
                            "designation": designation, # New field
                            "resignation_date": str(resignation_date) if resignation_date else None, # New field
                            "epf_number": epf_number, # New field
                            "esi_number": esi_number, # New field
                            "payroll": payroll, # New field
                            "is_admin": is_admin_checkbox
                        }
                        save_data(st.session_state.teachers, TEACHER_DATA_FILE) # Save updated data
                        st.success(f"Teacher '{teacher_name}' added successfully!")
                        st.rerun() # Rerun to refresh the data display

    with tab2:
        st.subheader("Manage Existing Teachers")
        teachers_list = list(teachers.values())

        if not teachers_list:
            st.info("No teacher records available.")
            return

        df_teachers = pd.DataFrame(teachers_list)
        # Don't display password hash and internal ID
        df_teachers_display = df_teachers.drop(columns=['password', 'id'], errors='ignore')
        st.dataframe(df_teachers_display, use_container_width=True)

        st.subheader("Edit or Delete Teacher")
        teacher_ids = [t['id'] for t in teachers_list]
        selected_teacher_id = st.selectbox("Select Teacher by ID", [""] + teacher_ids, key="edit_delete_teacher_id")

        if selected_teacher_id:
            current_teacher = teachers.get(selected_teacher_id)
            if current_teacher:
                st.write(f"**Selected Teacher:** {current_teacher['name']} ({current_teacher['username']})")

                action = st.radio("Choose Action", ["Edit", "Delete"], key="teacher_action_radio")

                if action == "Edit":
                    st.subheader(f"Edit Details for {current_teacher['name']}")
                    with st.form(f"edit_teacher_form_{selected_teacher_id}"):
                        col1_edit, col2_edit = st.columns(2)
                        with col1_edit:
                            new_name = st.text_input("Full Name", value=current_teacher.get('name', ''))
                            new_subject = st.selectbox("Subject", ["Mathematics", "Science", "English", "History", "Geography", "Computer Science", "Arts", "Physical Education", "Other"], index=["Mathematics", "Science", "English", "History", "Geography", "Computer Science", "Arts", "Physical Education", "Other"].index(current_teacher.get('subject', 'Other')))
                            new_email = st.text_input("Email", value=current_teacher.get('email', ''))
                            new_phone = st.text_input("Phone", value=current_teacher.get('phone', ''))
                            new_password_edit = st.text_input("New Password (leave blank to keep current)", type="password", key=f"new_pwd_edit_{selected_teacher_id}")
                        with col2_edit:
                            new_designation = st.text_input("Designation", value=current_teacher.get('designation', ''))
                            new_joining_date = st.date_input("Joining Date", value=datetime.strptime(current_teacher['join_date'], '%Y-%m-%d').date())
                            new_resignation_date = st.date_input("Resignation Date (Optional)", value=datetime.strptime(current_teacher['resignation_date'], '%Y-%m-%d').date() if current_teacher.get('resignation_date') else None)
                            new_epf_number = st.text_input("EPF Number", value=current_teacher.get('epf_number', ''))
                            new_esi_number = st.text_input("ESI Number", value=current_teacher.get('esi_number', ''))
                            new_payroll = st.number_input("Monthly Payroll (₹)", min_value=0.0, step=100.0, format="%.2f", value=float(current_teacher.get('payroll', 0.0)))
                            new_is_admin = st.checkbox("Admin Privileges", value=current_teacher.get('is_admin', False))

                        if st.form_submit_button("Save Changes"):
                            current_teacher['name'] = new_name
                            current_teacher['subject'] = new_subject
                            current_teacher['email'] = new_email
                            current_teacher['phone'] = new_phone
                            current_teacher['designation'] = new_designation # Update new field
                            current_teacher['join_date'] = str(new_joining_date) # Update new field
                            current_teacher['resignation_date'] = str(new_resignation_date) if new_resignation_date else None # Update new field
                            current_teacher['epf_number'] = new_epf_number # Update new field
                            current_teacher['esi_number'] = new_esi_number # Update new field
                            current_teacher['payroll'] = new_payroll # Update new field
                            current_teacher['is_admin'] = new_is_admin
                            if new_password_edit:
                                current_teacher['password'] = hash_password(new_password_edit)

                            st.session_state.teachers[selected_teacher_id] = current_teacher # Update session state
                            save_data(st.session_state.teachers, TEACHER_DATA_FILE) # Save updated data
                            st.success("Teacher details updated successfully!")
                            st.rerun()

                elif action == "Delete":
                    st.warning(f"Are you sure you want to delete {current_teacher['name']}?")
                    if st.button("Confirm Delete", key=f"confirm_delete_teacher_{selected_teacher_id}"):
                        del st.session_state.teachers[selected_teacher_id] # Update session state
                        save_data(st.session_state.teachers, TEACHER_DATA_FILE) # Save updated data
                        st.success("Teacher deleted successfully!")
                        st.rerun()
            else:
                st.warning("Teacher not found.")

# Removed manage_classes_scheduling() function as requested

def manage_fee_collection():
    """Manage fee collection and tracking"""
    st.header("💲 Fee Collection & Tracking")

    # Access data from session state
    student_data = st.session_state.students
    fee_data = st.session_state.fee_data

    tab1, tab2 = st.tabs(["Record Fee Payment", "View Fee Status"])

    with tab1:
        st.subheader("Record New Fee Payment")
        all_students_for_fee = []
        for class_name, students in student_data.items():
            for student in students:
                # Use 'admission_no' for display if available, fallback to 'id'
                student_identifier = student.get('admission_no', student.get('id', 'N/A'))
                all_students_for_fee.append({**student, "full_display_name": f"{student['name']} (Adm No: {student_identifier}) - {class_name}"})

        if not all_students_for_fee:
            st.info("No students found to record fees.")
            return

        selected_student_for_fee_display = st.selectbox(
            "Select Student",
            all_students_for_fee,
            format_func=lambda s: s['full_display_name'],
            key="fee_student_select"
        )

        if selected_student_for_fee_display:
            student_id_for_fee_record = selected_student_for_fee_display['id'] # Use the internal unique ID
            
            # Initialize fee record for student if not exists
            if str(student_id_for_fee_record) not in fee_data:
                fee_data[str(student_id_for_fee_record)] = {
                    "student_id": student_id_for_fee_record,
                    "student_admission_no": selected_student_for_fee_display.get('admission_no', 'N/A'),
                    "student_name": selected_student_for_fee_display.get('name', 'N/A'),
                    "class": selected_student_for_fee_display.get('class', 'N/A'),
                    "amount_due": 0.0, # Admin can set initial due amount
                    "amount_paid": 0.0,
                    "last_payment_date": "N/A",
                    "payment_history": []
                }

            current_fee_record = fee_data[str(student_id_for_fee_record)]
            st.write(f"**Fee Status for {current_fee_record.get('student_name', 'N/A')} ({current_fee_record.get('class', 'N/A')}):**")
            st.metric("Amount Due", f"₹{current_fee_record.get('amount_due', 0.0):.2f}")
            st.metric("Amount Paid", f"₹{current_fee_record.get('amount_paid', 0.0):.2f}")
            st.metric("Outstanding Balance", f"₹{current_fee_record.get('amount_due', 0.0) - current_fee_record.get('amount_paid', 0.0):.2f}")
            st.metric("Last Payment Date", current_fee_record.get('last_payment_date', 'N/A'))

            with st.form("record_payment_form", clear_on_submit=True):
                new_amount_due = st.number_input("Set/Update Total Amount Due", min_value=0.0, value=float(current_fee_record.get('amount_due', 0.0)), format="%.2f")
                payment_amount = st.number_input("Amount to Pay Now", min_value=0.0, value=0.0, format="%.2f")
                payment_date = st.date_input("Payment Date", value=datetime.today().date())
                payment_method = st.selectbox("Payment Method", ["Cash", "Online Transfer", "Cheque"])
                receipt_number = st.text_input("Receipt Number (Optional)").strip()

                if st.form_submit_button("Record Payment"):
                    current_fee_record['amount_due'] = new_amount_due
                    current_fee_record['amount_paid'] += payment_amount
                    current_fee_record['last_payment_date'] = str(payment_date)
                    current_fee_record['payment_history'].append({
                        "date": str(payment_date),
                        "amount": payment_amount,
                        "method": payment_method,
                        "receipt": receipt_number
                    })
                    st.session_state.fee_data[str(student_id_for_fee_record)] = current_fee_record # Update session state
                    save_data(st.session_state.fee_data, FEE_DATA_FILE) # Save updated data
                    st.success(f"Payment of ₹{payment_amount:.2f} recorded for {current_fee_record.get('student_name', 'N/A')}.")
                    st.rerun()

    with tab2:
        st.subheader("View Fee Status & History")
        fee_records_list = []
        for student_id_key, record in fee_data.items(): # student_id_key is the dict key (UUID string)
            fee_records_list.append({
                "Student ID": record.get('student_id', student_id_key), # Use .get() for robustness
                "Student Admission No": record.get('student_admission_no', 'N/A'),
                "Student Name": record.get('student_name', 'N/A'),
                "Class": record.get('class', 'N/A'),
                "Amount Due": record.get('amount_due', 0.0),
                "Amount Paid": record.get('amount_paid', 0.0),
                "Outstanding Balance": record.get('amount_due', 0.0) - record.get('amount_paid', 0.0),
                "Last Payment Date": record.get('last_payment_date', 'N/A')
            })

        if not fee_records_list:
            st.info("No fee records available.")
            return

        df_fees = pd.DataFrame(fee_records_list)
        st.dataframe(df_fees, use_container_width=True)

        st.subheader("Detailed Payment History")
        student_ids_with_fees = [str(record['Student ID']) for record in fee_records_list if 'Student ID' in record]
        selected_student_for_history_id = st.selectbox(
            "Select Student ID to View History",
            [""] + student_ids_with_fees,
            key="fee_history_student_select"
        )

        if selected_student_for_history_id:
            # Find the original record using the internal student_id
            history_record = fee_data.get(selected_student_for_history_id)
            if history_record and history_record.get('payment_history'):
                st.write(f"Payment History for {history_record.get('student_name', 'N/A')}:")
                df_history = pd.DataFrame(history_record['payment_history'])
                st.dataframe(df_history, use_container_width=True)
            else:
                st.info("No payment history for this student.")


def manage_events_notices():
    """Manage events and notices"""
    st.header("📢 Event & Notice Management")

    # Access data from session state
    event_notice_data = st.session_state.event_notice_data

    tab1, tab2 = st.tabs(["Create Event/Notice", "View/Manage Events & Notices"])

    with tab1:
        st.subheader("Create New Event or Notice")
        with st.form("create_event_notice", clear_on_submit=True):
            entry_type = st.radio("Type", ["Event", "Notice"], horizontal=True)
            title = st.text_input("Title*").strip()
            content = st.text_area("Content/Description*", height=150).strip()

            if entry_type == "Event":
                col1, col2 = st.columns(2)
                with col1:
                    event_date = st.date_input("Event Date*", min_value=datetime.today().date())
                with col2:
                    event_time = st.text_input("Event Time (e.g., 10:00 AM)", value="10:00 AM").strip()
                location = st.text_input("Location").strip()
                target_audience = st.multiselect("Target Audience", ["All", "Students", "Teachers", "Parents"] + get_full_class_list(), default="All")
            else: # Notice
                event_date = None # Not applicable
                event_time = None
                location = None
                target_audience = st.multiselect("Target Audience", ["All", "Students", "Teachers", "Parents"] + get_full_class_list(), default="All")
            
            attachment_file = st.file_uploader("Upload Attachment (Optional)", type=["pdf", "jpg", "png", "docx"])

            if st.form_submit_button("Publish"):
                if not all([title, content]):
                    st.error("Please fill all required fields (*)")
                elif entry_type == "Event" and not event_date:
                    st.error("Please specify an event date for events.")
                else:
                    new_id = str(uuid.uuid4())
                    
                    attachment_info = None
                    if attachment_file:
                        attachment_filename = f"{new_id}_{attachment_file.name}"
                        attachment_path = os.path.join(DATA_DIR, "attachments", attachment_filename)
                        try:
                            with open(attachment_path, "wb") as f:
                                f.write(attachment_file.getvalue())
                            attachment_info = {
                                "name": attachment_filename,
                                "path": attachment_path,
                                "type": attachment_file.type
                            }
                        except Exception as e:
                            st.error(f"Error saving attachment: {e}")
                            attachment_info = None

                    st.session_state.event_notice_data[new_id] = { # Update session state
                        "id": new_id,
                        "type": entry_type,
                        "title": title,
                        "content": content,
                        "publish_date": str(datetime.today().date()),
                        "event_date": str(event_date) if event_date else None,
                        "event_time": event_time,
                        "location": location,
                        "target_audience": target_audience,
                        "attachment": attachment_info
                    }
                    save_data(st.session_state.event_notice_data, EVENT_NOTICE_DATA_FILE) # Save updated data
                    st.success(f"{entry_type} '{title}' published successfully!")
                    st.rerun()

    with tab2:
        st.subheader("View & Manage Published Events/Notices")
        
        if not event_notice_data:
            st.info("No events or notices published yet.")
            return

        all_entries = list(event_notice_data.values())
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox("Filter by Type", ["All", "Event", "Notice"])
        with col2:
            filter_audience = st.selectbox("Filter by Target Audience", ["All", "Students", "Teachers", "Parents"] + get_full_class_list())

        filtered_entries = all_entries
        if filter_type != "All":
            filtered_entries = [e for e in filtered_entries if e.get('type') == filter_type]
        if filter_audience != "All":
            filtered_entries = [e for e in filtered_entries if filter_audience in e.get('target_audience', [])]

        if not filtered_entries:
            st.info("No entries match the filters.")
            return

        # Sort by date (events by event_date, notices by publish_date)
        filtered_entries.sort(key=lambda x: datetime.strptime(x.get('event_date', x.get('publish_date', '1900-01-01')), '%Y-%m-%d'), reverse=True)

        for entry in filtered_entries:
            with st.expander(f"{entry.get('type', 'Entry')}: {entry.get('title', 'Untitled')} (Published: {entry.get('publish_date', 'N/A')})"):
                st.write(f"**Type:** {entry.get('type', 'N/A')}")
                st.write(f"**Title:** {entry.get('title', 'N/A')}")
                st.write(f"**Content:** {entry.get('content', 'N/A')}")
                if entry.get('type') == "Event":
                    st.write(f"**Event Date:** {entry.get('event_date', 'N/A')}")
                    st.write(f"**Event Time:** {entry.get('event_time', 'N/A')}")
                    st.write(f"**Location:** {entry.get('location', 'N/A')}")
                st.write(f"**Target Audience:** {', '.join(entry.get('target_audience', ['N/A']))}")
                
                if entry.get('attachment'):
                    attachment_path = entry['attachment']['path']
                    if os.path.exists(attachment_path):
                        try:
                            with open(attachment_path, "rb") as file:
                                st.download_button(
                                    label=f"Download Attachment: {entry['attachment'].get('name', 'file')}",
                                    data=file.read(),
                                    file_name=entry['attachment'].get('name', 'download'),
                                    mime=entry['attachment'].get('type', 'application/octet-stream'),
                                    key=f"download_{entry['id']}"
                                )
                        except Exception as e:
                            st.warning(f"Could not read attachment file: {entry['attachment'].get('name', 'N/A')} ({e})")
                    else:
                        st.warning(f"Attachment file not found on server: {entry['attachment'].get('name', 'N/A')}")


                col1, col2 = st.columns(2)
                with col1:
                    # Edit functionality is complex for a form within an expander without full state management.
                    # For a full edit, you'd typically populate a new form or a modal.
                    st.button("Edit (Coming Soon)", key=f"edit_event_{entry['id']}", disabled=True)
                with col2:
                    if st.button("Delete", key=f"delete_event_{entry['id']}"):
                        del st.session_state.event_notice_data[entry['id']] # Update session state
                        save_data(st.session_state.event_notice_data, EVENT_NOTICE_DATA_FILE) # Save updated data
                        st.success(f"{entry.get('type', 'Entry')} '{entry.get('title', 'Untitled')}' deleted.")
                        st.rerun()

def generate_academic_reports():
    """Generate academic performance reports"""
    st.header("📈 Academic Performance Reports")

    st.subheader("Generate Reports by Class or Student")

    performance_data_all_teachers = st.session_state.performance_data
    if not performance_data_all_teachers:
        st.info("No performance data available from teachers to generate reports.")
        return

    # Consolidate performance data
    consolidated_performance = {}
    for teacher_id, classes_perf in performance_data_all_teachers.items():
        for class_name, students_perf in classes_perf.items():
            if class_name not in consolidated_performance:
                consolidated_performance[class_name] = []
            consolidated_performance[class_name].extend(students_perf)

    report_type = st.radio("Select Report Type", ["Class Performance Report", "Individual Student Report"])

    if report_type == "Class Performance Report":
        selected_class = st.selectbox("Select Class for Report", [""] + list(consolidated_performance.keys()))
        if selected_class and selected_class in consolidated_performance:
            st.subheader(f"Performance Report for {selected_class}")
            class_students_perf = consolidated_performance[selected_class]
            
            if class_students_perf:
                df_class_perf = pd.DataFrame(class_students_perf)
                
                # Expand subjects column for better reporting
                expanded_data = []
                for index, row in df_class_perf.iterrows():
                    student_id = row.get('student_id', 'N/A')
                    student_name = row.get('student_name', 'N/A')
                    overall_average = row.get('average', 0.0)
                    
                    if 'subjects' in row and row['subjects']:
                        for subject_perf in row['subjects']:
                            expanded_data.append({
                                "Student ID": student_id,
                                "Student Name": student_name,
                                "Subject": subject_perf.get('subject', 'N/A'),
                                "Subject Average": subject_perf.get('average', 0.0),
                                "Overall Average": overall_average
                            })
                    else:
                         expanded_data.append({
                                "Student ID": student_id,
                                "Student Name": student_name,
                                "Subject": "N/A",
                                "Subject Average": "N/A",
                                "Overall Average": overall_average
                            })
                
                if expanded_data:
                    df_report = pd.DataFrame(expanded_data)
                    st.dataframe(df_report, use_container_width=True)

                    csv = df_report.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Export to CSV",
                        data=csv,
                        file_name=f"{selected_class}_performance_report.csv",
                        mime="text/csv",
                    )
                else:
                    st.info(f"No detailed subject performance data for {selected_class}.")
            else:
                st.info(f"No performance data found for {selected_class}.")
        else:
            st.info("Please select a class to generate the report.")

    elif report_type == "Individual Student Report":
        all_students_for_report = []
        for class_name, students_perf in consolidated_performance.items():
            for student_perf in students_perf:
                all_students_for_report.append({
                    "id": student_perf.get('student_id', 'N/A'),
                    "name": student_perf.get('student_name', 'N/A'),
                    "class": class_name,
                    "avg": student_perf.get('average', 0.0),
                    "subjects": student_perf.get('subjects', [])
                })
        
        selected_student_for_report_display = st.selectbox(
            "Select Student for Report",
            [""] + [f"{s['name']} (ID: {s['id']}) - {s['class']}" for s in all_students_for_report]
        )

        if selected_student_for_report_display:
            # Find the actual student object
            selected_student_obj = next((s for s in all_students_for_report if f"{s['name']} (ID: {s['id']}) - {s['class']}" == selected_student_for_report_display), None)

            if selected_student_obj:
                st.subheader(f"Performance Report for {selected_student_obj.get('name', 'N/A')}")
                st.write(f"**Student ID:** {selected_student_obj.get('id', 'N/A')}")
                st.write(f"**Class:** {selected_student_obj.get('class', 'N/A')}")
                st.write(f"**Overall Average:** {selected_student_obj.get('avg', 0.0):.2f}%")

                if selected_student_obj.get('subjects'):
                    st.write("**Subject-wise Performance:**")
                    df_subject_perf = pd.DataFrame(selected_student_obj['subjects'])
                    st.dataframe(df_subject_perf, use_container_width=True)

                    csv = df_subject_perf.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Export Subject Performance to CSV",
                        data=csv,
                        file_name=f"{selected_student_obj.get('name', 'student')}_subject_performance.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("No subject-wise performance data available for this student.")
            else:
                st.error("Student not found for reporting.")
        else:
            st.info("Please select a student to generate the report.")

def export_analytics():
    """Provides options to export data for analytics (CSV only for now)"""
    st.header("📤 Exportable Analytics")
    st.info("Select the data you wish to export as a CSV file.")

    export_option = st.selectbox(
        "Choose Data to Export",
        ["Select...", "Student Data", "Teacher Data", "Attendance Data", "Assignments Data", "Fee Data", "Timetable Data", "Performance Data", "Messages Data", "Resources Data", "Leave Data", "Events & Notices"]
    )

    if export_option == "Student Data":
        student_data = st.session_state.students
        all_students = []
        for class_name, students in student_data.items():
            for student in students:
                all_students.append(student)
        if all_students:
            df = pd.DataFrame(all_students)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Student Data (CSV)", csv, "students_data.csv", "text/csv")
        else:
            st.warning("No student data to export.")

    elif export_option == "Teacher Data":
        teachers = st.session_state.teachers
        if teachers:
            df = pd.DataFrame(list(teachers.values()))
            df = df.drop(columns=['password'], errors='ignore') # Exclude sensitive data
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Teacher Data (CSV)", csv, "teachers_data.csv", "text/csv")
        else:
            st.warning("No teacher data to export.")

    elif export_option == "Attendance Data":
        attendance_data = st.session_state.attendance_data
        all_attendance_records = []
        for teacher_id, teacher_attn in attendance_data.items():
            teacher_name = st.session_state.teachers.get(teacher_id, {}).get('name', f"Teacher {teacher_id}")
            for date_str, class_attn in teacher_attn.items():
                for class_name, student_statuses in class_attn.items():
                    for student_id, status in student_statuses.items():
                        all_attendance_records.append({
                            "Teacher ID": teacher_id,
                            "Teacher Name": teacher_name,
                            "Date": date_str,
                            "Class": class_name,
                            "Student ID": student_id,
                            "Status": status
                        })
        if all_attendance_records:
            df = pd.DataFrame(all_attendance_records)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Attendance Data (CSV)", csv, "attendance_data.csv", "text/csv")
        else:
            st.warning("No attendance data to export.")

    elif export_option == "Assignments Data":
        assignments_data = st.session_state.assignments_data
        all_assignments_records = []
        for teacher_id, assignments in assignments_data.items():
            teacher_name = st.session_state.teachers.get(teacher_id, {}).get('name', f"Teacher {teacher_id}")
            for assignment in assignments:
                for submission in assignment.get('submissions', []):
                    all_assignments_records.append({
                        "Assignment ID": assignment.get('id', 'N/A'),
                        "Title": assignment.get('title', 'N/A'),
                        "Assigned Class": assignment.get('assigned_class', 'N/A'),
                        "Due Date": assignment.get('due_date', 'N/A'),
                        "Max Score": assignment.get('max_score', 0),
                        "Type": assignment.get('type', 'N/A'),
                        "Teacher ID": teacher_id,
                        "Teacher Name": teacher_name,
                        "Student ID": submission.get('student_id', 'N/A'),
                        "Student Name": submission.get('student_name', 'N/A'),
                        "Submission Date": submission.get('submission_date', 'N/A'),
                        "Grade": submission.get('grade', 'N/A'),
                        "Feedback": submission.get('feedback', ''),
                        "Submission Status": submission.get('status', 'Submitted')
                    })
        if all_assignments_records:
            df = pd.DataFrame(all_assignments_records)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Assignments Data (CSV)", csv, "assignments_data.csv", "text/csv")
        else:
            st.warning("No assignment data to export.")
    
    elif export_option == "Fee Data":
        fee_data = st.session_state.fee_data
        fee_records_list = []
        for student_id_key, record in fee_data.items():
            fee_records_list.append({
                "Student ID": record.get('student_id', student_id_key),
                "Student Admission No": record.get('student_admission_no', 'N/A'),
                "Student Name": record.get('student_name', 'N/A'),
                "Class": record.get('class', 'N/A'),
                "Amount Due": record.get('amount_due', 0.0),
                "Amount Paid": record.get('amount_paid', 0.0),
                "Outstanding Balance": record.get('amount_due', 0.0) - record.get('amount_paid', 0.0),
                "Last Payment Date": record.get('last_payment_date', 'N/A')
            })
        if fee_records_list:
            df = pd.DataFrame(fee_records_list)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Fee Data (CSV)", csv, "fee_data.csv", "text/csv")
        else:
            st.warning("No fee data to export.")

    elif export_option == "Timetable Data":
        timetable_data_all_teachers = st.session_state.timetable_data
        all_timetable_entries = []
        for teacher_id, entries in timetable_data_all_teachers.items():
            teacher_name = st.session_state.teachers.get(teacher_id, {}).get('name', f"Teacher {teacher_id}")
            for entry in entries:
                all_timetable_entries.append({
                    "Teacher ID": teacher_id,
                    "Teacher Name": teacher_name,
                    "Day": entry.get('day', 'N/A'),
                    "Period": entry.get('period', 'N/A'),
                    "Subject": entry.get('subject', 'N/A'),
                    "Class": entry.get('class_name', 'N/A')
                })
        if all_timetable_entries:
            df = pd.DataFrame(all_timetable_entries)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Timetable Data (CSV)", csv, "timetable_data.csv", "text/csv")
        else:
            st.warning("No timetable data to export.")

    elif export_option == "Performance Data":
        performance_data_all_teachers = st.session_state.performance_data
        all_performance_records = []
        for teacher_id, classes_perf in performance_data_all_teachers.items():
            teacher_name = st.session_state.teachers.get(teacher_id, {}).get('name', f"Teacher {teacher_id}")
            for class_name, students_perf in classes_perf.items():
                for student_perf in students_perf:
                    record = {
                        "Teacher ID": teacher_id,
                        "Teacher Name": teacher_name,
                        "Class": class_name,
                        "Student ID": student_perf.get('student_id', 'N/A'),
                        "Student Name": student_perf.get('student_name', 'N/A'),
                        "Overall Average": student_perf.get('average', 0.0)
                    }
                    if 'subjects' in student_perf:
                        for subject_data in student_perf['subjects']:
                            record[f"Subject: {subject_data.get('subject', 'N/A')} Average"] = subject_data.get('average', 0.0)
                    all_performance_records.append(record)
        if all_performance_records:
            df = pd.DataFrame(all_performance_records)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Performance Data (CSV)", csv, "performance_data.csv", "text/csv")
        else:
            st.warning("No performance data to export.")
    
    elif export_option == "Messages Data":
        messages_data_all_teachers = st.session_state.messages_data
        all_messages_records = []
        for teacher_id, messages in messages_data_all_teachers.items():
            teacher_name = st.session_state.teachers.get(teacher_id, {}).get('name', f"Teacher {teacher_id}")
            for message in messages:
                all_messages_records.append({
                    "Message ID": message.get('id', 'N/A'),
                    "Teacher ID": teacher_id,
                    "Teacher Name": teacher_name,
                    "Date": message.get('date', 'N/A'),
                    "Time": message.get('time', 'N/A'),
                    "Subject": message.get('subject', 'N/A'),
                    "Student ID": message.get('student_id', 'N/A'),
                    "Student Name": message.get('student_name', 'N/A'),
                    "Class": message.get('class_name', 'N/A'),
                    "Parent Name": message.get('parent_name', 'N/A'),
                    "Parent Email": message.get('parent_email', 'N/A'),
                    "Parent Phone": message.get('parent_phone', 'N/A'),
                    "Type": message.get('type', 'N/A'),
                    "Urgency": message.get('urgency', 'N/A'),
                    "Content": message.get('content', 'N/A'),
                    "Requires Response": message.get('require_response', False),
                    "Status": message.get('status', 'N/A'),
                    "Attachment": message.get('attachment', {}).get('name', 'N/A')
                })
        if all_messages_records:
            df = pd.DataFrame(all_messages_records)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Messages Data (CSV)", csv, "messages_data.csv", "text/csv")
        else:
            st.warning("No messages data to export.")

    elif export_option == "Resources Data":
        resources_data_all_teachers = st.session_state.resources_data
        all_resources_records = []
        for teacher_id, resources in resources_data_all_teachers.items():
            teacher_name = st.session_state.teachers.get(teacher_id, {}).get('name', f"Teacher {teacher_id}")
            for resource in resources:
                all_resources_records.append({
                    "Resource ID": resource.get('id', 'N/A'),
                    "Title": resource.get('title', 'N/A'),
                    "Description": resource.get('description', 'N/A'),
                    "Type": resource.get('type', 'N/A'),
                    "Class Name": resource.get('class_name', 'N/A'),
                    "Tags": ", ".join(resource.get('tags', [])),
                    "Upload Date": resource.get('upload_date', 'N/A'),
                    "Upload Time": resource.get('upload_time', 'N/A'),
                    "File Name": resource.get('file_name', 'N/A'),
                    "File Type": resource.get('file_type', 'N/A'),
                    "File Size": resource.get('file_size', 0),
                    "Uploaded By Teacher ID": teacher_id,
                    "Uploaded By Teacher Name": teacher_name,
                    "Download Count": resource.get('download_count', 0)
                })
        if all_resources_records:
            df = pd.DataFrame(all_resources_records)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Resources Data (CSV)", csv, "resources_data.csv", "text/csv")
        else:
            st.warning("No resources data to export.")

    elif export_option == "Leave Data":
        leave_data_all_teachers = st.session_state.leave_data
        all_leave_records = []
        for teacher_id, leaves in leave_data_all_teachers.items():
            teacher_info = st.session_state.teachers.get(teacher_id, {})
            teacher_name = teacher_info.get('name', f"Teacher {teacher_id}")
            teacher_subject = teacher_info.get('subject', 'N/A')
            for leave in leaves:
                all_leave_records.append({
                    "Leave ID": leave.get('id', 'N/A'),
                    "Teacher ID": teacher_id,
                    "Teacher Name": teacher_name,
                    "Subject": teacher_subject,
                    "Start Date": leave.get('start_date', 'N/A'),
                    "End Date": leave.get('end_date', 'N/A'),
                    "Leave Days": leave.get('leave_days', 0),  # Safely get with default
                    "Type": leave.get('type', 'N/A'),
                    "Reason": leave.get('reason', 'N/A'),
                    "Status": leave.get('status', 'N/A'),
                    "Application Date": leave.get('application_date', 'N/A'),
                    "Applied By": leave.get('applied_by', 'N/A'),  # Safely get with default
                    "Supporting Docs": ", ".join(leave.get('supporting_docs', [])),
                    "Comments": leave.get('comments', '')
                })
        if all_leave_records:
            df = pd.DataFrame(all_leave_records)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Leave Data (CSV)", csv, "leave_data.csv", "text/csv")
        else:
            st.warning("No leave data to export.")
    
    elif export_option == "Events & Notices":
        event_notice_data = st.session_state.event_notice_data
        if event_notice_data:
            df = pd.DataFrame(list(event_notice_data.values()))
            # Flatten attachment info for CSV
            df['Attachment Name'] = df['attachment'].apply(lambda x: x.get('name', 'N/A') if x else 'N/A')
            df = df.drop(columns=['attachment'], errors='ignore')
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Events & Notices Data (CSV)", csv, "events_notices_data.csv", "text/csv")
        else:
            st.warning("No events or notices data to export.")


def manage_leave_applications():
    """Admin view for managing leave applications"""
    st.header("⏳ Manage Leave Applications")

    leave_data_all_teachers = st.session_state.leave_data
    all_leave_applications = []
    for teacher_id, leaves in leave_data_all_teachers.items():
        teacher_info = st.session_state.teachers.get(teacher_id, {})
        teacher_name = teacher_info.get('name', f"Teacher {teacher_id}")
        teacher_subject = teacher_info.get('subject', 'N/A')
        for leave in leaves:
            all_leave_applications.append({
                "Leave ID": leave.get('id', 'N/A'),
                "Teacher ID": teacher_id,
                "Teacher Name": teacher_name,
                "Subject": teacher_subject,
                "Start Date": leave.get('start_date', 'N/A'),
                "End Date": leave.get('end_date', 'N/A'),
                "Leave Days": leave.get('leave_days', 0), # Safely get with default
                "Type": leave.get('type', 'N/A'),
                "Reason": leave.get('reason', 'N/A'),
                "Status": leave.get('status', 'N/A'),
                "Application Date": leave.get('application_date', 'N/A'),
                "Applied By": leave.get('applied_by', 'N/A'), # Safely get with default
                "Supporting Docs": leave.get('supporting_docs', []),
                "Comments": leave.get('comments', '')
            })

    if not all_leave_applications:
        st.info("No leave applications to manage.")
        return

    df_leaves = pd.DataFrame(all_leave_applications)

    # Filter by status
    filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
    if filter_status != "All":
        df_leaves = df_leaves[df_leaves['Status'] == filter_status]

    if not df_leaves.empty:
        st.dataframe(df_leaves, use_container_width=True)

        st.subheader("Approve/Reject Leave Application")
        leave_ids = df_leaves['Leave ID'].tolist()
        selected_leave_id = st.selectbox("Select Leave ID to Manage", [""] + leave_ids)

        if selected_leave_id:
            selected_leave = next((l for l in all_leave_applications if l['Leave ID'] == selected_leave_id), None)

            if selected_leave:
                st.write(f"**Details for Leave ID:** {selected_leave.get('Leave ID', 'N/A')}")
                st.write(f"**Teacher:** {selected_leave.get('Teacher Name', 'N/A')} ({selected_leave.get('Subject', 'N/A')})")
                st.write(f"**Dates:** {selected_leave.get('Start Date', 'N/A')} to {selected_leave.get('End Date', 'N/A')} ({selected_leave.get('Leave Days', 0)} days)")
                st.write(f"**Type:** {selected_leave.get('Type', 'N/A')}")
                st.write(f"**Reason:** {selected_leave.get('Reason', 'N/A')}")
                st.write(f"**Current Status:** {selected_leave.get('Status', 'N/A')}")

                if selected_leave.get('Supporting Docs'):
                    st.write("**Supporting Documents:**")
                    for doc_name in selected_leave['Supporting Docs']:
                        # In a real app, you would provide a way to view/download these
                        st.write(f"- {doc_name} (File path not provided for download here)")

                with st.form(f"manage_leave_{selected_leave_id}"):
                    new_status = st.radio(
                        "Change Status to",
                        ["Pending", "Approved", "Rejected"],
                        index=["Pending", "Approved", "Rejected"].index(selected_leave.get('Status', 'Pending')),
                        horizontal=True
                    )
                    comments = st.text_area("Admin Comments", value=selected_leave.get('Comments', ''))

                    if st.form_submit_button("Update Leave Status"):
                        # Find the actual leave object in the loaded data and update it
                        found_and_updated = False
                        for teacher_id_key, teacher_leaves in st.session_state.leave_data.items(): # Access session state
                            for i, leave_obj in enumerate(teacher_leaves):
                                if leave_obj.get('id') == selected_leave_id:
                                    st.session_state.leave_data[teacher_id_key][i]['status'] = new_status # Update session state
                                    st.session_state.leave_data[teacher_id_key][i]['comments'] = comments # Update session state
                                    found_and_updated = True
                                    break
                            if found_and_updated:
                                break

                        if found_and_updated:
                            save_data(st.session_state.leave_data, LEAVE_DATA_FILE) # Save updated data
                            st.success(f"Leave application {selected_leave_id} updated to '{new_status}'.")
                            st.rerun()
                        else:
                            st.error("Error updating leave application.")
            else:
                st.warning("Selected leave application not found.")
    else:
        st.info("No leave applications matching the filters.")

# ======================
# MAIN MANAGEMENT DASHBOARD
# ======================

def show():
    """Main function for the admin/management dashboard"""
    # Check if admin is logged in, if not, show login/register page
    if 'admin_logged_in' not in st.session_state or not st.session_state['admin_logged_in']:
        admin_login_or_register_page()
        return

    admin_id = st.session_state['admin_id']
    admin_data = st.session_state.teachers.get(str(admin_id), {}) # Access teachers from session state

    st.title(f"🏢 School Management System - Admin Dashboard")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    st.sidebar.markdown(f"**Welcome, {admin_data.get('name', 'Admin')}!**")

    selected = option_menu(
        None,
        ["Dashboard", "Student Management", "Teacher Management",
         "Fee Collection", "Events & Notices", "Academic Reports", "Leave Management", "Export Data"],
        icons=['house-door', 'people', 'person-badge', 'currency-dollar',
               'bell', 'bar-chart', 'clipboard-check', 'download'],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#e9ecef"},
            "nav-link-selected": {"background-color": "#28a745"}, # Admin theme green
        }
    )

    if selected == "Dashboard":
        display_overview_dashboard()
    elif selected == "Student Management":
        manage_students_admin()
    elif selected == "Teacher Management":
        manage_teachers_admin()
    # Removed "Class & Timetable" section
    elif selected == "Fee Collection":
        manage_fee_collection()
    elif selected == "Events & Notices":
        manage_events_notices()
    elif selected == "Academic Reports":
        generate_academic_reports()
    elif selected == "Leave Management":
        manage_leave_applications()
    elif selected == "Export Data":
        export_analytics()

# ======================
# INITIALIZATION
# ======================
def initialize_session_state_data():
    """
    Initializes all data files and loads them into st.session_state if not already present.
    Also adds a default admin if no teachers exist.
    """
    # Teachers data is initialized at the top-level of the script for immediate availability.
    # This function is now mainly for other data files if they weren't initialized.
    pass # No need to re-initialize teachers/students here

# ======================
# MAIN EXECUTION
# ======================
if __name__ == "__main__":
    st.set_page_config(
        page_title="Admin Dashboard",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
            .stButton button {
                width: 100%;
            }
            .stSelectbox, .stTextInput, .stTextArea, .stDateInput, .stFileUploader, .stNumberInput {
                margin-bottom: 1rem;
            }
            .stExpander {
                margin-bottom: 1rem;
                border: 1px solid #e1e4e8;
                border-radius: 0.5rem;
            }
            .stExpander .stMarkdown {
                padding: 1rem;
            }
            /* Admin specific primary color for selected menu item */
            div.st-emotion-cache-1jmveo1 > div { /* This targets the selected menu item in the sidebar */
                background-color: #28a745; /* Green for admin selected */
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: #F0F2F6;
                border-radius: 4px 4px 0px 0px;
                gap: 10px;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #28a745; /* Active tab green */
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

    show()
