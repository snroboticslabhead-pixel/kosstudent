from flask import render_template, request, jsonify, redirect, url_for, session, send_file
from functools import wraps
import json
import pandas as pd
from io import BytesIO
import bcrypt
import jwt
import requests
from datetime import datetime, timedelta
from database import db
from config import Config

# Import models
from models import Student, Task, Submission, Admin, Teacher, Campus, Grade, Notification, initialize_default_data

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('token')
        if not token or not verify_token(token):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'admin':
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))
        
        payload = verify_token(token)
        if not payload or payload.get('user_type') != 'teacher':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Utility Functions
def create_token(user_id, user_type):
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_student_id(campus, sequence):
    campus_prefix = {
        'Subhash Nagar': 'SUB',
        'Yamuna': 'YAM', 
        'I20': 'I20'
    }.get(campus, 'STD')
    return f"{campus_prefix}-{sequence:03d}"

def generate_teacher_id(campus, sequence):
    campus_prefix = {
        'Subhash Nagar': 'SUB',
        'Yamuna': 'YAM', 
        'I20': 'I20'
    }.get(campus, 'TCH')
    return f"{campus_prefix}-T{sequence:03d}"

def export_students_to_excel(students):
    # Create DataFrame with student data including passwords
    student_data = []
    for s in students:
        student_data.append({
            'studentID': s['studentID'],
            'name': s['name'],
            'campus': s['campus'],
            'grade': s['grade'],
            'section': s.get('section', ''),
            'password': '123456'  # Default password for all students
        })
    
    df = pd.DataFrame(student_data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Students', index=False)
        
        # Add a info sheet with instructions
        info_data = {
            'Information': [
                'This file contains student login credentials',
                'All students have default password: 123456',
                'Students should change their password after first login',
                'Keep this file secure and do not share publicly'
            ]
        }
        info_df = pd.DataFrame(info_data)
        info_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    output.seek(0)
    return output

def export_teachers_to_excel(teachers):
    # Create DataFrame with teacher data including passwords
    teacher_data = []
    for t in teachers:
        teacher_data.append({
            'teacherID': t['teacherID'],
            'name': t['name'],
            'email': t['email'],
            'campus': t['campus'],
            'password': '123456'  # Default password for all teachers
        })
    
    df = pd.DataFrame(teacher_data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Teachers', index=False)
        
        # Add a info sheet with instructions
        info_data = {
            'Information': [
                'This file contains teacher login credentials',
                'All teachers have default password: 123456',
                'Teachers should change their password after first login',
                'Keep this file secure and do not share publicly'
            ]
        }
        info_df = pd.DataFrame(info_data)
        info_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    output.seek(0)
    return output

def import_students_from_excel(file):
    try:
        df = pd.read_excel(file)
        students = []
        
        for idx, row in df.iterrows():
            student_id = generate_student_id(row['campus'], idx + 1)
            student = {
                'studentID': student_id,
                'name': row['name'],
                'campus': row['campus'],
                'grade': row['grade'],
                'section': row.get('section', 'LL'),
                'password': '123456'  # Default password
            }
            students.append(student)
        
        return students
    except Exception as e:
        print(f"Error importing Excel: {e}")
        return []

def get_student_progress_data(campus=None):
    """Get comprehensive student progress data for admin/teacher dashboard"""
    students = Student.get_all()
    tasks = Task.get_all()
    
    # Filter students by campus if provided
    if campus:
        students = [s for s in students if s['campus'] == campus]
    
    progress_data = {
        'campus_wise': {},
        'grade_wise': {},
        'task_wise': {},
        'section_wise': {},
        'overall_stats': {
            'total_students': len(students),
            'total_tasks': len(tasks),
            'total_submissions': 0,
            'completion_rate': 0
        }
    }
    
    # Campus-wise progress
    campuses = ['Subhash Nagar', 'Yamuna', 'I20']
    for campus_name in campuses:
        campus_students = [s for s in students if s['campus'] == campus_name]
        campus_tasks = []
        
        for task in tasks:
            campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
            if campus_name in campus_target:
                campus_tasks.append(task)
        
        total_possible_submissions = len(campus_students) * len(campus_tasks)
        actual_submissions = 0
        
        for student in campus_students:
            student_submissions = Submission.get_by_student(student['studentID'])
            actual_submissions += len(student_submissions)
        
        progress_data['campus_wise'][campus_name] = {
            'total_students': len(campus_students),
            'total_tasks': len(campus_tasks),
            'completed_submissions': actual_submissions,
            'completion_rate': round((actual_submissions / total_possible_submissions * 100), 2) if total_possible_submissions > 0 else 0
        }
    
    # Grade-wise progress
    grades = [f"{i}th Class" for i in range(1, 11)]
    for grade in grades:
        grade_students = [s for s in students if s['grade'] == grade]
        grade_tasks = []
        
        for task in tasks:
            grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
            if grade in grade_target:
                grade_tasks.append(task)
        
        total_possible_submissions = len(grade_students) * len(grade_tasks)
        actual_submissions = 0
        
        for student in grade_students:
            student_submissions = Submission.get_by_student(student['studentID'])
            actual_submissions += len(student_submissions)
        
        progress_data['grade_wise'][grade] = {
            'total_students': len(grade_students),
            'total_tasks': len(grade_tasks),
            'completed_submissions': actual_submissions,
            'completion_rate': round((actual_submissions / total_possible_submissions * 100), 2) if total_possible_submissions > 0 else 0
        }
    
    # Section-wise progress
    sections = [
        'LL', 'HH', 'DD', 'FF', 
        'Tata Boys', 'Tata Girls', 
        'Google Boys', 'Google Girls', 
        'Infosys Boys', 'Infosys Girls', 
        'Adobe', 'Adobe Boys', 'Adobe Girls',
        'Mahendra Boys', 'Mahendra Girls',
        'Verizon Boys', 'Verizon Girls', 
        'Microsoft Boys', 'Microsoft Girls'
    ]
    
    for section in sections:
        section_students = [s for s in students if s.get('section') == section]
        if section_students:  # Only include sections that have students
            total_possible_submissions = len(section_students) * len(tasks)
            actual_submissions = 0
            
            for student in section_students:
                student_submissions = Submission.get_by_student(student['studentID'])
                actual_submissions += len(student_submissions)
            
            progress_data['section_wise'][section] = {
                'total_students': len(section_students),
                'total_tasks': len(tasks),
                'completed_submissions': actual_submissions,
                'completion_rate': round((actual_submissions / total_possible_submissions * 100), 2) if total_possible_submissions > 0 else 0
            }
    
    # Task-wise progress
    for task in tasks:
        completions = Submission.get_task_completions(task['id'])
        total_students = 0
        
        campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
        grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
        
        for campus_name in campus_target:
            for grade in grade_target:
                students_count = len(Student.get_by_campus_grade(campus_name, grade))
                total_students += students_count
        
        progress_data['task_wise'][task['title']] = {
            'task_id': task['id'],
            'completed': len(completions),
            'total_students': total_students,
            'pending': total_students - len(completions),
            'completion_rate': round((len(completions) / total_students * 100), 2) if total_students > 0 else 0
        }
    
    # Overall stats
    total_submissions = sum([len(Submission.get_by_student(s['studentID'])) for s in students])
    total_possible_submissions = len(students) * len(tasks)
    
    progress_data['overall_stats']['total_submissions'] = total_submissions
    progress_data['overall_stats']['completion_rate'] = round((total_submissions / total_possible_submissions * 100), 2) if total_possible_submissions > 0 else 0
    
    return progress_data

# AI Code Validation Function using OpenRouter
def validate_student_code(student_code, task_description):
    """Validate student code using OpenRouter AI with detailed feedback"""
    try:
        user_prompt = f"""
Task Description: {task_description}
Student Code:
{student_code}
Please validate if the above code is correct, partially correct, or incorrect.
Provide detailed feedback on any errors, syntax issues, or missing requirements.

Respond with:
1. Validation status: "Correct", "Partially Correct", or "Incorrect"
2. Detailed feedback explaining the issues (if any)
3. Specific error messages (if applicable)

Format your response as:
Status: [Validation Status]
Feedback: [Detailed feedback]
Errors: [Specific error messages or "None"]
"""
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": """You are an expert code validation assistant. 
                    Your task is to validate student code against task requirements.
                    Provide detailed feedback on any issues found."""
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://taskboard.example.com",
            "X-Title": "TaskBoard"
        }
        
        response = requests.post(Config.OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        
        # Parse the response to extract status, feedback, and errors
        status = "Incorrect"
        feedback = "No feedback provided"
        errors = "None"
        
        for line in result.split('\n'):
            if line.startswith("Status:"):
                status = line.replace("Status:", "").strip()
            elif line.startswith("Feedback:"):
                feedback = line.replace("Feedback:", "").strip()
            elif line.startswith("Errors:"):
                errors = line.replace("Errors:", "").strip()
        
        return {
            "status": status,
            "feedback": feedback,
            "errors": errors
        }
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        return {
            "status": "Error",
            "feedback": f"Validation error: {str(e)}",
            "errors": "API error"
        }

# AI Code Generation Function using OpenRouter
def generate_code_with_ai(prompt, language="python"):
    """Generate code using OpenRouter AI"""
    try:
        system_prompt = f"""
You are an expert {language} programmer and educator. 
Generate clean, well-commented code that solves the user's request.
Focus on educational value and best practices.
Only provide the code without explanations unless specifically asked.
"""
        
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://taskboard.example.com",
            "X-Title": "TaskBoard"
        }
        
        response = requests.post(Config.OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        return result
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        return f"Error generating code: {str(e)}"

# AI Chat Function using OpenRouter
def chat_with_ai(messages):
    """Chat with OpenRouter AI"""
    try:
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": messages
        }
        
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://taskboard.example.com",
            "X-Title": "TaskBoard"
        }
        
        response = requests.post(Config.OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        return result
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        return f"Error: {str(e)}"

# Notification Routes
@login_required
def get_notifications():
    """Get notifications for current user"""
    try:
        token = session.get('token')
        payload = verify_token(token)
        user_type = payload.get('user_type')
        user_id = payload.get('user_id')
        
        # Get user-specific data for filtering
        campus = None
        grade = None
        
        if user_type == 'teacher':
            teacher = Teacher.find_by_id(user_id)
            if teacher:
                campus = teacher['campus']
        elif user_type == 'student':
            student = Student.find_by_id(user_id)
            if student:
                campus = student['campus']
                grade = student['grade']
        
        notifications = Notification.get_for_user(user_type, user_id, campus, grade)
        
        # Convert datetime to string for JSON serialization
        for notification in notifications:
            notification['id'] = str(notification['id'])
            if 'createdAt' in notification and isinstance(notification['createdAt'], datetime):
                notification['createdAt'] = notification['createdAt'].isoformat()
        
        return jsonify({
            'status': 'success',
            'notifications': notifications,
            'unread_count': Notification.get_unread_count(user_type, user_id, campus, grade)
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        token = session.get('token')
        payload = verify_token(token)
        user_type = payload.get('user_type')
        user_id = payload.get('user_id')
        
        # Get user-specific data for access control
        campus = None
        grade = None
        
        if user_type == 'teacher':
            teacher = Teacher.find_by_id(user_id)
            if teacher:
                campus = teacher['campus']
        elif user_type == 'student':
            student = Student.find_by_id(user_id)
            if student:
                campus = student['campus']
                grade = student['grade']
        
        result = Notification.mark_as_read(notification_id, user_type, user_id, campus, grade)
        
        if result:
            return jsonify({'status': 'success', 'message': 'Notification marked as read'})
        else:
            return jsonify({'status': 'error', 'message': 'Notification not found or access denied'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    try:
        token = session.get('token')
        payload = verify_token(token)
        user_type = payload.get('user_type')
        user_id = payload.get('user_id')
        
        # Get user-specific data for access control
        campus = None
        grade = None
        
        if user_type == 'teacher':
            teacher = Teacher.find_by_id(user_id)
            if teacher:
                campus = teacher['campus']
        elif user_type == 'student':
            student = Student.find_by_id(user_id)
            if student:
                campus = student['campus']
                grade = student['grade']
        
        result = Notification.mark_all_as_read(user_type, user_id, campus, grade)
        
        return jsonify({
            'status': 'success', 
            'message': 'All notifications marked as read'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Auth Routes
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if user_type == 'admin':
            admin = Admin.verify_password(username, password)
            if admin:
                token = create_token(admin['username'], 'admin')
                session['token'] = token
                session['user_type'] = 'admin'
                session['username'] = admin['username']
                return redirect(url_for('admin_dashboard'))
        elif user_type == 'teacher':
            teacher = Teacher.verify_password(username, password)
            if teacher:
                token = create_token(teacher['teacherID'], 'teacher')
                session['token'] = token
                session['user_type'] = 'teacher'
                session['teacher_id'] = teacher['teacherID']
                session['teacher_name'] = teacher['name']
                session['teacher_campus'] = teacher['campus']
                return redirect(url_for('teacher_dashboard'))
        else:
            student = Student.verify_password(username, password)
            if student:
                token = create_token(student['studentID'], 'student')
                session['token'] = token
                session['user_type'] = 'student'
                session['student_id'] = student['studentID']
                session['student_name'] = student['name']
                return redirect(url_for('student_dashboard'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin Routes
@admin_required
def admin_dashboard():
    progress_data = get_student_progress_data()
    
    # Get notifications for admin
    notifications = Notification.get_for_user('admin')
    unread_count = Notification.get_unread_count('admin')
    
    return render_template('admin_dashboard.html', 
                         progress_data=progress_data,
                         notifications=notifications[:5],  # Show only 5 recent
                         unread_count=unread_count)

@admin_required
def manage_students():
    students = Student.get_all()
    return render_template('manage_students.html', students=students)

@admin_required
def add_student():
    sections = [
        'LL', 'HH', 'DD', 'FF', 
        'Tata Boys', 'Tata Girls', 
        'Google Boys', 'Google Girls', 
        'Infosys Boys', 'Infosys Girls', 
        'Adobe', 'Adobe Boys', 'Adobe Girls',
        'Mahendra Boys', 'Mahendra Girls',
        'Verizon Boys', 'Verizon Girls', 
        'Microsoft Boys', 'Microsoft Girls'
    ]
    
    if request.method == 'POST':
        # Get the count of existing students to generate ID
        existing_students = Student.get_all()
        sequence = len(existing_students) + 1
        
        data = {
            'studentID': generate_student_id(request.form.get('campus'), sequence),
            'name': request.form.get('name'),
            'campus': request.form.get('campus'),
            'grade': request.form.get('grade'),
            'section': request.form.get('section'),
            'password': request.form.get('password', '123456')
        }
        
        result = Student.create(data)
        if result:
            # Get the created student to create notification
            student = Student.find_by_id(data['studentID'])
            if student:
                Notification.create_student_notification(student, "added")
            
            return redirect(url_for('manage_students'))
        else:
            return render_template('add_student.html', error='Failed to create student', sections=sections)
    
    return render_template('add_student.html', sections=sections)

@admin_required
def edit_student(student_id):
    student = Student.find_by_id(student_id)
    if not student:
        return redirect(url_for('manage_students'))
    
    sections = [
        'LL', 'HH', 'DD', 'FF', 
        'Tata Boys', 'Tata Girls', 
        'Google Boys', 'Google Girls', 
        'Infosys Boys', 'Infosys Girls', 
        'Adobe', 'Adobe Boys', 'Adobe Girls',
        'Mahendra Boys', 'Mahendra Girls',
        'Verizon Boys', 'Verizon Girls', 
        'Microsoft Boys', 'Microsoft Girls'
    ]
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'campus': request.form.get('campus'),
            'grade': request.form.get('grade'),
            'section': request.form.get('section')
        }
        
        # If password is provided, update it too
        password = request.form.get('password')
        if password:
            data['password'] = password
        
        result = Student.update(student_id, data)
        if result:
            # Create update notification
            Notification.create_student_notification(student, "updated")
            return redirect(url_for('manage_students'))
        else:
            return render_template('edit_student.html', student=student, error='Failed to update student', sections=sections)
    
    return render_template('edit_student.html', student=student, sections=sections)

@admin_required
def delete_student(student_id):
    student = Student.find_by_id(student_id)
    if student:
        Student.delete(student_id)
        # Create delete notification
        Notification.create_student_notification(student, "deleted")
    return redirect(url_for('manage_students'))

@admin_required
def upload_students():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('manage_students'))
        
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('manage_students'))
        
        if file and file.filename.endswith('.xlsx'):
            students_data = import_students_from_excel(file)
            success_count = 0
            for student_data in students_data:
                try:
                    Student.create(student_data)
                    success_count += 1
                    # Create notification for each student
                    student = Student.find_by_id(student_data['studentID'])
                    if student:
                        Notification.create_student_notification(student, "added")
                except Exception as e:
                    print(f"Error creating student: {e}")
            
            print(f"Successfully imported {success_count} students")
            return redirect(url_for('manage_students'))
    
    return redirect(url_for('manage_students'))

@admin_required
def export_students():
    students = Student.get_all()
    excel_file = export_students_to_excel(students)
    return send_file(excel_file, 
                    download_name='students_with_passwords.xlsx',
                    as_attachment=True)

@admin_required
def manage_teachers():
    teachers = Teacher.get_all()
    return render_template('manage_teachers.html', teachers=teachers)

@admin_required
def add_teacher():
    campuses = ['Subhash Nagar', 'Yamuna', 'I20']
    
    if request.method == 'POST':
        # Get the count of existing teachers for this campus to generate ID
        campus = request.form.get('campus')
        existing_teachers = Teacher.get_by_campus(campus)
        sequence = len(existing_teachers) + 1
        
        data = {
            'teacherID': generate_teacher_id(campus, sequence),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'campus': campus,
            'password': request.form.get('password', '123456'),
            'can_manage_students': request.form.get('can_manage_students') == 'on',
            'can_manage_tasks': request.form.get('can_manage_tasks') == 'on'
        }
        
        result = Teacher.create(data)
        if result:
            # Get the created teacher to create notification
            teacher = Teacher.find_by_id(data['teacherID'])
            if teacher:
                Notification.create_teacher_notification(teacher, "added")
            
            return redirect(url_for('manage_teachers'))
        else:
            return render_template('add_teacher.html', error='Failed to create teacher', campuses=campuses)
    
    return render_template('add_teacher.html', campuses=campuses)

@admin_required
def edit_teacher(teacher_id):
    teacher = Teacher.find_by_id(teacher_id)
    if not teacher:
        return redirect(url_for('manage_teachers'))
    
    campuses = ['Subhash Nagar', 'Yamuna', 'I20']
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'campus': request.form.get('campus'),
            'can_manage_students': request.form.get('can_manage_students'),
            'can_manage_tasks': request.form.get('can_manage_tasks')
        }
        
        # If password is provided, update it too
        password = request.form.get('password')
        if password:
            data['password'] = password
        
        result = Teacher.update(teacher_id, data)
        if result:
            # Create update notification
            Notification.create_teacher_notification(teacher, "updated")
            return redirect(url_for('manage_teachers'))
        else:
            return render_template('edit_teacher.html', teacher=teacher, error='Failed to update teacher', campuses=campuses)
    
    return render_template('edit_teacher.html', teacher=teacher, campuses=campuses)

@admin_required
def delete_teacher(teacher_id):
    teacher = Teacher.find_by_id(teacher_id)
    if teacher:
        Teacher.delete(teacher_id)
        # Create delete notification
        Notification.create_teacher_notification(teacher, "deleted")
    return redirect(url_for('manage_teachers'))

@admin_required
def export_teachers():
    teachers = Teacher.get_all()
    excel_file = export_teachers_to_excel(teachers)
    return send_file(excel_file, 
                    download_name='teachers_with_passwords.xlsx',
                    as_attachment=True)

@admin_required
def manage_tasks():
    tasks = Task.get_all()
    return render_template('manage_tasks.html', tasks=tasks)

@admin_required
def add_task():
    grades = [f"{i}th Class" for i in range(1, 11)]
    campuses = ['Subhash Nagar', 'Yamuna', 'I20']
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'language': request.form.get('language'),
            'campusTarget': request.form.getlist('campusTarget'),
            'gradeTarget': request.form.getlist('gradeTarget')
        }
        
        # Validate required fields
        if not data['title'] or not data['description'] or not data['language']:
            return render_template('add_task.html', error='All fields are required', 
                                 grades=grades, campuses=campuses)
        
        if not data['campusTarget'] or not data['gradeTarget']:
            return render_template('add_task.html', error='Please select at least one campus and grade', 
                                 grades=grades, campuses=campuses)
        
        result = Task.create(data)
        if result:
            # Get the created task to create notification
            task = Task.find_by_id(result)
            if task:
                Notification.create_task_notification(task, "created")
            
            return redirect(url_for('manage_tasks'))
        else:
            return render_template('add_task.html', error='Failed to create task', 
                                 grades=grades, campuses=campuses)
    
    return render_template('add_task.html', grades=grades, campuses=campuses)

@admin_required
def edit_task(task_id):
    task = Task.find_by_id(task_id)
    if not task:
        return redirect(url_for('manage_tasks'))
    
    grades = [f"{i}th Class" for i in range(1, 11)]
    campuses = ['Subhash Nagar', 'Yamuna', 'I20']
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'language': request.form.get('language'),
            'campusTarget': request.form.getlist('campusTarget'),
            'gradeTarget': request.form.getlist('gradeTarget')
        }
        
        # Validate required fields
        if not data['title'] or not data['description'] or not data['language']:
            return render_template('edit_task.html', error='All fields are required', 
                                 task=task, grades=grades, campuses=campuses)
        
        if not data['campusTarget'] or not data['gradeTarget']:
            return render_template('edit_task.html', error='Please select at least one campus and grade', 
                                 task=task, grades=grades, campuses=campuses)
        
        result = Task.update(task_id, data)
        if result:
            # Create update notification
            Notification.create_task_notification(task, "updated")
            return redirect(url_for('manage_tasks'))
        else:
            return render_template('edit_task.html', error='Failed to update task', 
                                 task=task, grades=grades, campuses=campuses)
    
    return render_template('edit_task.html', task=task, grades=grades, campuses=campuses)

@admin_required
def delete_task(task_id):
    task = Task.find_by_id(task_id)
    if task:
        Task.delete(task_id)
        # Create delete notification
        Notification.create_task_notification(task, "deleted")
    return redirect(url_for('manage_tasks'))

@admin_required
def analytics():
    progress_data = get_student_progress_data()
    return render_template('analytics.html', progress_data=progress_data)

@admin_required
def task_details(task_id):
    task = Task.find_by_id(task_id)
    if not task:
        return redirect(url_for('analytics'))
    
    # Get completed students
    completed_students = Submission.get_completed_students_for_task(task_id)
    
    # Get all students who should complete this task
    all_target_students = []
    campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
    grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
    
    for campus in campus_target:
        for grade in grade_target:
            students = Student.get_by_campus_grade(campus, grade)
            all_target_students.extend(students)
    
    # Find pending students
    completed_student_ids = [s['studentID'] for s in completed_students]
    pending_students = [s for s in all_target_students if s['studentID'] not in completed_student_ids]
    
    return render_template('task_details.html', 
                         task=task, 
                         completed_students=completed_students,
                         pending_students=pending_students)

@admin_required
def view_submission(task_id, student_id):
    task = Task.find_by_id(task_id)
    student = Student.find_by_id(student_id)
    
    if not task or not student:
        return redirect(url_for('analytics'))
    
    submission = Submission.find_by_student_task(student_id, task_id)
    
    if not submission:
        return redirect(url_for('task_details', task_id=task_id))
    
    return render_template('view_submission.html', 
                         task=task, 
                         student=student,
                         submission=submission)

# Teacher Routes
@teacher_required
def teacher_dashboard():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Get progress data for teacher's campus only
    progress_data = get_student_progress_data(campus=teacher['campus'])
    
    # Get notifications for teacher
    notifications = Notification.get_for_user('teacher', teacher_id, teacher['campus'])
    unread_count = Notification.get_unread_count('teacher', teacher_id, teacher['campus'])
    
    return render_template('teacher_dashboard.html', 
                         teacher=teacher, 
                         progress_data=progress_data,
                         notifications=notifications[:5],  # Show only 5 recent
                         unread_count=unread_count)

@teacher_required
def teacher_students():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Get students for teacher's campus only
    students = Student.get_all()
    campus_students = [s for s in students if s['campus'] == teacher['campus']]
    
    # Get tasks that target teacher's campus
    tasks = Task.get_all()
    campus_tasks = []
    for task in tasks:
        campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
        if teacher['campus'] in campus_target:
            campus_tasks.append(task)
    
    # Calculate task statistics for each student
    for student in campus_students:
        # Get all tasks assigned to this student (based on campus and grade)
        student_tasks = []
        for task in campus_tasks:
            grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
            if student['grade'] in grade_target:
                student_tasks.append(task)
        
        student['tasks_assigned'] = len(student_tasks)
        
        # Get submissions for this student
        submissions = Submission.get_by_student(student['studentID'])
        student['tasks_completed'] = len(submissions)
    
    return render_template('teacher_students.html', 
                         teacher=teacher, 
                         students=campus_students)

@teacher_required
def teacher_add_student():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Check if teacher has permission to manage students
    if not teacher.get('can_manage_students', False):
        return redirect(url_for('teacher_students'))
    
    sections = [
        'LL', 'HH', 'DD', 'FF', 
        'Tata Boys', 'Tata Girls', 
        'Google Boys', 'Google Girls', 
        'Infosys Boys', 'Infosys Girls', 
        'Adobe', 'Adobe Boys', 'Adobe Girls',
        'Mahendra Boys', 'Mahendra Girls',
        'Verizon Boys', 'Verizon Girls', 
        'Microsoft Boys', 'Microsoft Girls'
    ]
    
    if request.method == 'POST':
        # Get the count of existing students for this campus to generate ID
        campus = teacher['campus']  # Use teacher's campus
        existing_students = Student.get_all()
        campus_students = [s for s in existing_students if s['campus'] == campus]
        sequence = len(campus_students) + 1
        
        data = {
            'studentID': generate_student_id(campus, sequence),
            'name': request.form.get('name'),
            'campus': campus,  # Force to teacher's campus
            'grade': request.form.get('grade'),
            'section': request.form.get('section'),
            'password': request.form.get('password', '123456')
        }
        
        result = Student.create(data)
        if result:
            # Get the created student to create notification
            student = Student.find_by_id(data['studentID'])
            if student:
                Notification.create_student_notification(student, "added")
            
            return redirect(url_for('teacher_students'))
        else:
            return render_template('teacher_add_student.html', error='Failed to create student', sections=sections, teacher=teacher)
    
    return render_template('teacher_add_student.html', sections=sections, teacher=teacher)

@teacher_required
def teacher_edit_student(student_id):
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Check if teacher has permission to manage students
    if not teacher.get('can_manage_students', False):
        return redirect(url_for('teacher_students'))
    
    student = Student.find_by_id(student_id)
    if not student:
        return redirect(url_for('teacher_students'))
    
    # Ensure student belongs to teacher's campus
    if student['campus'] != teacher['campus']:
        return redirect(url_for('teacher_students'))
    
    sections = [
        'LL', 'HH', 'DD', 'FF', 
        'Tata Boys', 'Tata Girls', 
        'Google Boys', 'Google Girls', 
        'Infosys Boys', 'Infosys Girls', 
        'Adobe', 'Adobe Boys', 'Adobe Girls',
        'Mahendra Boys', 'Mahendra Girls',
        'Verizon Boys', 'Verizon Girls', 
        'Microsoft Boys', 'Microsoft Girls'
    ]
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'grade': request.form.get('grade'),
            'section': request.form.get('section')
        }
        
        # If password is provided, update it too
        password = request.form.get('password')
        if password:
            data['password'] = password
        
        result = Student.update(student_id, data)
        if result:
            # Create update notification
            Notification.create_student_notification(student, "updated")
            return redirect(url_for('teacher_students'))
        else:
            return render_template('teacher_edit_student.html', student=student, error='Failed to update student', sections=sections, teacher=teacher)
    
    return render_template('teacher_edit_student.html', student=student, sections=sections, teacher=teacher)

@teacher_required
def teacher_delete_student(student_id):
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Check if teacher has permission to manage students
    if not teacher.get('can_manage_students', False):
        return redirect(url_for('teacher_students'))
    
    student = Student.find_by_id(student_id)
    if student:
        # Ensure student belongs to teacher's campus
        if student['campus'] == teacher['campus']:
            Student.delete(student_id)
            # Create delete notification
            Notification.create_student_notification(student, "deleted")
    
    return redirect(url_for('teacher_students'))

@teacher_required
def teacher_export_students():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('teacher_students'))
    
    # Get students for teacher's campus only
    students = Student.get_all()
    campus_students = [s for s in students if s['campus'] == teacher['campus']]
    
    excel_file = export_students_to_excel(campus_students)
    return send_file(excel_file, 
                    download_name=f'students_{teacher["campus"]}.xlsx',
                    as_attachment=True)

@teacher_required
def teacher_tasks():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Get tasks that target teacher's campus
    tasks = Task.get_all()
    campus_tasks = []
    for task in tasks:
        campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
        if teacher['campus'] in campus_target:
            campus_tasks.append(task)
    
    # Calculate statistics for each task
    for task in campus_tasks:
        # Get all students who should complete this task from teacher's campus
        all_target_students = []
        grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
        for grade in grade_target:
            students = Student.get_by_campus_grade(teacher['campus'], grade)
            all_target_students.extend(students)
        
        task['students_assigned'] = len(all_target_students)
        
        # Get completed submissions for this task
        completions = Submission.get_task_completions(task['id'])
        
        # Filter to only include students from teacher's campus
        completed_students = []
        for completion in completions:
            student = Student.find_by_id(completion['studentId'])
            if student and student['campus'] == teacher['campus']:
                completed_students.append(student)
        
        task['completions'] = len(completed_students)
        
        # Calculate completion rate
        if task['students_assigned'] > 0:
            task['completion_rate'] = (task['completions'] / task['students_assigned']) * 100
        else:
            task['completion_rate'] = 0
    
    return render_template('teacher_tasks.html', 
                         teacher=teacher, 
                         tasks=campus_tasks)

@teacher_required
def teacher_add_task():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Check if teacher has permission to manage tasks
    if not teacher.get('can_manage_tasks', False):
        return redirect(url_for('teacher_tasks'))
    
    grades = [f"{i}th Class" for i in range(1, 11)]
    # Only show teacher's campus
    campuses = [teacher['campus']]
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'language': request.form.get('language'),
            'campusTarget': [teacher['campus']],  # Force to teacher's campus
            'gradeTarget': request.form.getlist('gradeTarget')
        }
        
        # Validate required fields
        if not data['title'] or not data['description'] or not data['language']:
            return render_template('teacher_add_task.html', error='All fields are required', 
                                 grades=grades, campuses=campuses, teacher=teacher)
        
        if not data['gradeTarget']:
            return render_template('teacher_add_task.html', error='Please select at least one grade', 
                                 grades=grades, campuses=campuses, teacher=teacher)
        
        result = Task.create(data)
        if result:
            # Get the created task to create notification
            task = Task.find_by_id(result)
            if task:
                Notification.create_task_notification(task, "created")
            
            return redirect(url_for('teacher_tasks'))
        else:
            return render_template('teacher_add_task.html', error='Failed to create task', 
                                 grades=grades, campuses=campuses, teacher=teacher)
    
    return render_template('teacher_add_task.html', grades=grades, campuses=campuses, teacher=teacher)

@teacher_required
def teacher_edit_task(task_id):
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Check if teacher has permission to manage tasks
    if not teacher.get('can_manage_tasks', False):
        return redirect(url_for('teacher_tasks'))
    
    task = Task.find_by_id(task_id)
    if not task:
        return redirect(url_for('teacher_tasks'))
    
    # Check if task is for teacher's campus
    campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
    if teacher['campus'] not in campus_target:
        return redirect(url_for('teacher_tasks'))
    
    grades = [f"{i}th Class" for i in range(1, 11)]
    # Only show teacher's campus
    campuses = [teacher['campus']]
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'language': request.form.get('language'),
            'campusTarget': [teacher['campus']],  # Force to teacher's campus
            'gradeTarget': request.form.getlist('gradeTarget')
        }
        
        # Validate required fields
        if not data['title'] or not data['description'] or not data['language']:
            return render_template('teacher_edit_task.html', error='All fields are required', 
                                 task=task, grades=grades, campuses=campuses, teacher=teacher)
        
        if not data['gradeTarget']:
            return render_template('teacher_edit_task.html', error='Please select at least one grade', 
                                 task=task, grades=grades, campuses=campuses, teacher=teacher)
        
        result = Task.update(task_id, data)
        if result:
            # Create update notification
            Notification.create_task_notification(task, "updated")
            return redirect(url_for('teacher_tasks'))
        else:
            return render_template('teacher_edit_task.html', error='Failed to update task', 
                                 task=task, grades=grades, campuses=campuses, teacher=teacher)
    
    return render_template('teacher_edit_task.html', task=task, grades=grades, campuses=campuses, teacher=teacher)

@teacher_required
def teacher_delete_task(task_id):
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    # Check if teacher has permission to manage tasks
    if not teacher.get('can_manage_tasks', False):
        return redirect(url_for('teacher_tasks'))
    
    task = Task.find_by_id(task_id)
    if task:
        # Check if task is for teacher's campus
        campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
        if teacher['campus'] in campus_target:
            Task.delete(task_id)
            # Create delete notification
            Notification.create_task_notification(task, "deleted")
    
    return redirect(url_for('teacher_tasks'))

@teacher_required
def teacher_task_details(task_id):
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    task = Task.find_by_id(task_id)
    if not task:
        return redirect(url_for('teacher_tasks'))
    
    # Check if task is for teacher's campus
    campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
    if teacher['campus'] not in campus_target:
        return redirect(url_for('teacher_tasks'))
    
    # Get completed students for this task
    completed_students = Submission.get_completed_students_for_task(task_id)
    
    # Filter to only include students from teacher's campus
    completed_students = [s for s in completed_students if s['campus'] == teacher['campus']]
    
    # Get all students who should complete this task from teacher's campus
    all_target_students = []
    grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
    for grade in grade_target:
        students = Student.get_by_campus_grade(teacher['campus'], grade)
        all_target_students.extend(students)
    
    # Find pending students
    completed_student_ids = [s['studentID'] for s in completed_students]
    pending_students = [s for s in all_target_students if s['studentID'] not in completed_student_ids]
    
    return render_template('teacher_task_details.html', 
                         teacher=teacher,
                         task=task, 
                         completed_students=completed_students,
                         pending_students=pending_students)

@teacher_required
def teacher_view_submission(task_id, student_id):
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'teacher':
        return redirect(url_for('logout'))
    
    teacher_id = payload.get('user_id')
    teacher = Teacher.find_by_id(teacher_id)
    
    if not teacher:
        return redirect(url_for('logout'))
    
    task = Task.find_by_id(task_id)
    student = Student.find_by_id(student_id)
    
    if not task or not student:
        return redirect(url_for('teacher_tasks'))
    
    # Check if student is from teacher's campus
    if student['campus'] != teacher['campus']:
        return redirect(url_for('teacher_tasks'))
    
    submission = Submission.find_by_student_task(student_id, task_id)
    
    if not submission:
        return redirect(url_for('teacher_task_details', task_id=task_id))
    
    return render_template('teacher_view_submission.html', 
                         teacher=teacher,
                         task=task, 
                         student=student,
                         submission=submission)

# Student Routes
@login_required
def student_dashboard():
    token = session.get('token')
    payload = verify_token(token)
    
    if payload.get('user_type') != 'student':
        return redirect(url_for('logout'))
    
    student_id = payload.get('user_id')
    student = Student.find_by_id(student_id)
    
    if not student:
        return redirect(url_for('logout'))
    
    # Get assigned tasks
    tasks = Task.get_for_student(student['campus'], student['grade'])
    
    # Get submission status
    task_status = []
    for task in tasks:
        submission = Submission.find_by_student_task(student_id, task['id'])
        task_status.append({
            'task': {
                'id': task['id'],
                'title': task['title'],
                'language': task['language'],
                'description': task.get('description', '')
            },
            'completed': submission is not None,
            'completed_date': submission.get('submittedAt') if submission else None
        })
    
    # Get notifications for student
    notifications = Notification.get_for_user('student', student_id, student['campus'], student['grade'])
    unread_count = Notification.get_unread_count('student', student_id, student['campus'], student['grade'])
    
    return render_template('student_dashboard.html',
                         student=student,
                         task_status=task_status,
                         notifications=notifications[:5],  # Show only 5 recent
                         unread_count=unread_count)

@login_required
def web_editor():
    task_id = request.args.get('task_id')
    if not task_id:
        return redirect(url_for('student_dashboard'))
    
    task = Task.find_by_id(task_id)
    
    if not task:
        return redirect(url_for('student_dashboard'))
    
    # Get student submission if exists
    token = session.get('token')
    payload = verify_token(token)
    student_id = payload.get('user_id')
    
    submission = Submission.find_by_student_task(student_id, task_id)
    
    return render_template('web_editor.html', task=task, submission=submission)

# Practice Editor Route (Available to all roles)
@login_required
def practice_editor():
    token = session.get('token')
    payload = verify_token(token)
    
    # Allow all roles to access practice editor
    if payload.get('user_type') not in ['admin', 'teacher', 'student']:
        return redirect(url_for('logout'))
    
    return render_template('practice_editor.html', current_language='arduino')

# Code Validation Route
@login_required
def validate_code():
    """Validate student code against task requirements using OpenRouter AI"""
    try:
        data = request.get_json()
        task_id = data.get("task_id")
        code = data.get("code")
        
        if not task_id or not code:
            return jsonify({"status": "error", "message": "Task ID and code are required"})
        
        # Get task from database
        task = Task.find_by_id(task_id)
        if not task:
            return jsonify({"status": "error", "message": "Task not found"})
        
        # Validate code using AI
        validation_result = validate_student_code(code, task.get('description', ''))
        
        # Determine if submit button should be enabled
        submit_enabled = validation_result.get("status") == "Correct"
        
        return jsonify({
            "status": "success",
            "validation_result": validation_result.get("status"),
            "feedback": validation_result.get("feedback"),
            "errors": validation_result.get("errors"),
            "submit_enabled": submit_enabled,
            "message": validation_result.get("feedback")
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# AI Code Simulation Route
@login_required
def simulate_code_execution():
    """Simulate code execution using OpenRouter AI"""
    try:
        data = request.get_json()
        code = data.get("code", "")
        language = data.get("language", "arduino")
        task_id = data.get("task_id", "")
        
        if not code:
            return jsonify({"status": "error", "output": "No code provided"}), 400
        
        # Prepare the prompt for AI
        if language == "arduino":
            system_prompt = """
You are an Arduino compiler and interpreter. Analyze the following Arduino code and provide feedback on any errors, warnings, or issues. 
If the code is correct, simulate the output that would be printed to the serial monitor.

Provide your response in the following format:
If there are errors:
ERROR: [error message]
If there are no errors:
SUCCESS: [simulated output]

Do not provide corrected code. Only provide the error message or the simulated output.
"""
        else:  # python
            system_prompt = """
You are a Python interpreter. Analyze the following Python code and provide feedback on any errors, warnings, or issues. 
If the code is correct, simulate the output that would be printed to the console.

Provide your response in the following format:
If there are errors:
ERROR: [error message]
If there are no errors:
SUCCESS: [simulated output]

Do not provide corrected code. Only provide the error message or the simulated output.
"""
        
        user_prompt = f"Code:\n{code}"
        
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://taskboard.example.com",
            "X-Title": "TaskBoard"
        }
        
        response = requests.post(Config.OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        
        # Check if the result starts with "ERROR" or "SUCCESS"
        if result.startswith("ERROR:"):
            return jsonify({"status": "error", "output": result[6:].strip()})
        elif result.startswith("SUCCESS:"):
            return jsonify({"status": "success", "output": result[8:].strip()})
        else:
            # If the AI didn't follow the format, return the whole result as output
            return jsonify({"status": "error", "output": "Unexpected response from AI: " + result})
    
    except Exception as e:
        return jsonify({"status": "error", "output": f"Simulation failed: {str(e)}"})

# AI Code Generation Route
@login_required
def generate_code():
    """Generate code using OpenRouter AI"""
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        language = data.get("language", "python")
        
        if not prompt:
            return jsonify({"status": "error", "message": "Prompt is required"})
        
        # Generate code using AI
        generated_code = generate_code_with_ai(prompt, language)
        
        return jsonify({
            "status": "success",
            "code": generated_code,
            "message": "Code generated successfully"
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# AI Chat Route
@login_required
def ai_chat():
    """Chat with OpenRouter AI"""
    try:
        data = request.get_json()
        messages = data.get("messages")
        
        if not messages or not isinstance(messages, list):
            return jsonify({"status": "error", "message": "Valid messages array is required"})
        
        # Chat with AI
        response = chat_with_ai(messages)
        
        return jsonify({
            "status": "success",
            "response": response,
            "message": "AI response received"
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Submit Task Route
@login_required
def submit_task():
    try:
        data = request.get_json()
        task_id = data.get("task_id")
        code = data.get("code")
        output = data.get("output")
        
        if not task_id or not code:
            return jsonify({"status": "error", "message": "Task ID and code are required"})
        
        token = session.get('token')
        payload = verify_token(token)
        user_type = payload.get('user_type')
        
        if user_type == 'student':
            user_id = payload.get('user_id')
        else:
            return jsonify({"status": "error", "message": "Only students can submit tasks"})
        
        submission_data = {
            'studentId': user_id,
            'taskId': task_id,
            'code': code,
            'output': output
        }
        
        result = Submission.create(submission_data)
        if result:
            # Get the created submission, student, and task to create notification
            submission = Submission.find_by_student_task(user_id, task_id)
            student = Student.find_by_id(user_id)
            task = Task.find_by_id(task_id)
            
            if submission and student and task:
                Notification.create_submission_notification(submission, student, task)
            
            return jsonify({"status": "success", "message": "Task submitted successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to submit task"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Initialize the application
def init_app():
    initialize_default_data()
    print("✅ Application initialized successfully!")