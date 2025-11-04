import jwt
from datetime import datetime, timedelta
from config import Config
import pandas as pd
from io import BytesIO
import bcrypt

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

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

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