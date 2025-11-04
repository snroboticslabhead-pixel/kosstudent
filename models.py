from datetime import datetime
from database import db
import bcrypt
import uuid

class BaseModel:
    @staticmethod
    def generate_id():
        return str(uuid.uuid4())
    
    @staticmethod
    def format_datetime(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

class Student(BaseModel):
    table_name = 'students'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            studentID VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            campus VARCHAR(50) NOT NULL,
            grade VARCHAR(20) NOT NULL,
            section VARCHAR(50),
            passwordHash VARCHAR(255) NOT NULL,
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def create(cls, data):
        student_id = cls.generate_id()
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        query = f"""
        INSERT INTO {cls.table_name} (id, studentID, name, campus, grade, section, passwordHash, createdAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            student_id,
            data['studentID'],
            data['name'],
            data['campus'],
            data['grade'],
            data.get('section', 'LL'),
            password_hash,
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        return student_id
    
    @classmethod
    def find_by_id(cls, student_id):
        query = f"SELECT * FROM {cls.table_name} WHERE studentID = %s"
        result = db.execute_query(query, (student_id,))
        return result[0] if result else None
    
    @classmethod
    def verify_password(cls, student_id, password):
        student = cls.find_by_id(student_id)
        if student and bcrypt.checkpw(password.encode('utf-8'), student['passwordHash'].encode('utf-8')):
            return student
        return None
    
    @classmethod
    def get_by_campus_grade(cls, campus, grade):
        query = f"SELECT * FROM {cls.table_name} WHERE campus = %s AND grade = %s"
        return db.execute_query(query, (campus, grade))
    
    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name} ORDER BY createdAt DESC"
        return db.execute_query(query)
    
    @classmethod
    def count_by_campus(cls, campus):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name} WHERE campus = %s"
        result = db.execute_query(query, (campus,))
        return result[0]['count'] if result else 0
    
    @classmethod
    def get_total_count(cls):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        result = db.execute_query(query)
        return result[0]['count'] if result else 0
    
    @classmethod
    def get_by_campus_grade_section(cls, campus, grade, section):
        query = f"SELECT * FROM {cls.table_name} WHERE campus = %s AND grade = %s AND section = %s"
        return db.execute_query(query, (campus, grade, section))
    
    @classmethod
    def update(cls, student_id, data):
        set_clause = []
        params = []
        
        if 'name' in data:
            set_clause.append("name = %s")
            params.append(data['name'])
        if 'campus' in data:
            set_clause.append("campus = %s")
            params.append(data['campus'])
        if 'grade' in data:
            set_clause.append("grade = %s")
            params.append(data['grade'])
        if 'section' in data:
            set_clause.append("section = %s")
            params.append(data['section'])
        if 'password' in data:
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            set_clause.append("passwordHash = %s")
            params.append(password_hash)
        
        if not set_clause:
            return False
            
        params.append(student_id)
        query = f"UPDATE {cls.table_name} SET {', '.join(set_clause)} WHERE studentID = %s"
        
        return db.execute_query(query, params)
    
    @classmethod
    def delete(cls, student_id):
        query = f"DELETE FROM {cls.table_name} WHERE studentID = %s"
        return db.execute_query(query, (student_id,))

class Task(BaseModel):
    table_name = 'tasks'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            language VARCHAR(20) NOT NULL,
            campusTarget JSON,
            gradeTarget JSON,
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def create(cls, data):
        task_id = cls.generate_id()
        
        query = f"""
        INSERT INTO {cls.table_name} (id, title, description, language, campusTarget, gradeTarget, createdAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        import json
        params = (
            task_id,
            data['title'],
            data['description'],
            data['language'],
            json.dumps(data['campusTarget']),
            json.dumps(data['gradeTarget']),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        return task_id
    
    @classmethod
    def find_by_id(cls, task_id):
        query = f"SELECT * FROM {cls.table_name} WHERE id = %s"
        result = db.execute_query(query, (task_id,))
        return result[0] if result else None
    
    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name} ORDER BY createdAt DESC"
        return db.execute_query(query)
    
    @classmethod
    def get_for_student(cls, campus, grade):
        query = f"SELECT * FROM {cls.table_name}"
        tasks = db.execute_query(query)
        
        import json
        filtered_tasks = []
        for task in tasks:
            campus_target = json.loads(task['campusTarget']) if task['campusTarget'] else []
            grade_target = json.loads(task['gradeTarget']) if task['gradeTarget'] else []
            
            if campus in campus_target and grade in grade_target:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    @classmethod
    def delete(cls, task_id):
        query = f"DELETE FROM {cls.table_name} WHERE id = %s"
        return db.execute_query(query, (task_id,))
    
    @classmethod
    def update(cls, task_id, data):
        set_clause = []
        params = []
        
        if 'title' in data:
            set_clause.append("title = %s")
            params.append(data['title'])
        if 'description' in data:
            set_clause.append("description = %s")
            params.append(data['description'])
        if 'language' in data:
            set_clause.append("language = %s")
            params.append(data['language'])
        if 'campusTarget' in data:
            import json
            set_clause.append("campusTarget = %s")
            params.append(json.dumps(data['campusTarget']))
        if 'gradeTarget' in data:
            import json
            set_clause.append("gradeTarget = %s")
            params.append(json.dumps(data['gradeTarget']))
        
        if not set_clause:
            return False
            
        params.append(task_id)
        query = f"UPDATE {cls.table_name} SET {', '.join(set_clause)} WHERE id = %s"
        
        return db.execute_query(query, params)
    
    @classmethod
    def get_total_count(cls):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        result = db.execute_query(query)
        return result[0]['count'] if result else 0

class Submission(BaseModel):
    table_name = 'submissions'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            studentId VARCHAR(20) NOT NULL,
            taskId VARCHAR(36) NOT NULL,
            code TEXT,
            output TEXT,
            status VARCHAR(20) DEFAULT 'completed',
            submittedAt DATETIME NOT NULL,
            FOREIGN KEY (studentId) REFERENCES students(studentID),
            FOREIGN KEY (taskId) REFERENCES tasks(id)
        )
        """
        db.execute_query(query)
    
    @classmethod
    def create(cls, data):
        submission_id = cls.generate_id()
        
        query = f"""
        INSERT INTO {cls.table_name} (id, studentId, taskId, code, output, status, submittedAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            submission_id,
            data['studentId'],
            data['taskId'],
            data.get('code', ''),
            data.get('output', ''),
            data.get('status', 'completed'),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        return submission_id
    
    @classmethod
    def find_by_student_task(cls, student_id, task_id):
        query = f"SELECT * FROM {cls.table_name} WHERE studentId = %s AND taskId = %s"
        result = db.execute_query(query, (student_id, task_id))
        return result[0] if result else None
    
    @classmethod
    def get_by_student(cls, student_id):
        query = f"SELECT * FROM {cls.table_name} WHERE studentId = %s"
        return db.execute_query(query, (student_id,))
    
    @classmethod
    def get_task_completions(cls, task_id):
        query = f"SELECT * FROM {cls.table_name} WHERE taskId = %s"
        return db.execute_query(query, (task_id,))
    
    @classmethod
    def get_completion_count(cls, task_id):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name} WHERE taskId = %s"
        result = db.execute_query(query, (task_id,))
        return result[0]['count'] if result else 0
    
    @classmethod
    def get_student_completions(cls, student_id):
        return cls.get_by_student(student_id)
    
    @classmethod
    def get_completed_students_for_task(cls, task_id):
        query = """
        SELECT s.* FROM students s
        JOIN submissions sub ON s.studentID = sub.studentId
        WHERE sub.taskId = %s
        """
        return db.execute_query(query, (task_id,))

class Admin(BaseModel):
    table_name = 'admins'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            passwordHash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'super_admin',
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def create_default(cls):
        # Check if any admin exists
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        result = db.execute_query(query)
        
        if result and result[0]['count'] == 0:
            admin_id = cls.generate_id()
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            
            query = f"""
            INSERT INTO {cls.table_name} (id, username, passwordHash, role, createdAt)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                admin_id,
                'admin',
                password_hash,
                'super_admin',
                datetime.utcnow()
            )
            
            db.execute_query(query, params)
            print("✅ Default admin created: admin / admin123")
    
    @classmethod
    def verify_password(cls, username, password):
        query = f"SELECT * FROM {cls.table_name} WHERE username = %s"
        result = db.execute_query(query, (username,))
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0]['passwordHash'].encode('utf-8')):
            return result[0]
        return None

class Teacher(BaseModel):
    table_name = 'teachers'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            teacherID VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            campus VARCHAR(50) NOT NULL,
            passwordHash VARCHAR(255) NOT NULL,
            can_manage_students BOOLEAN DEFAULT FALSE,
            can_manage_tasks BOOLEAN DEFAULT FALSE,
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def create(cls, data):
        teacher_id = cls.generate_id()
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        query = f"""
        INSERT INTO {cls.table_name} (id, teacherID, name, email, campus, passwordHash, can_manage_students, can_manage_tasks, createdAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            teacher_id,
            data['teacherID'],
            data['name'],
            data.get('email', ''),
            data['campus'],
            password_hash,
            data.get('can_manage_students', False),
            data.get('can_manage_tasks', False),
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        return teacher_id
    
    @classmethod
    def find_by_id(cls, teacher_id):
        query = f"SELECT * FROM {cls.table_name} WHERE teacherID = %s"
        result = db.execute_query(query, (teacher_id,))
        return result[0] if result else None
    
    @classmethod
    def verify_password(cls, teacher_id, password):
        teacher = cls.find_by_id(teacher_id)
        if teacher and bcrypt.checkpw(password.encode('utf-8'), teacher['passwordHash'].encode('utf-8')):
            return teacher
        return None
    
    @classmethod
    def get_by_campus(cls, campus):
        query = f"SELECT * FROM {cls.table_name} WHERE campus = %s"
        return db.execute_query(query, (campus,))
    
    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name} ORDER BY createdAt DESC"
        return db.execute_query(query)
    
    @classmethod
    def count_by_campus(cls, campus):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name} WHERE campus = %s"
        result = db.execute_query(query, (campus,))
        return result[0]['count'] if result else 0
    
    @classmethod
    def get_total_count(cls):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        result = db.execute_query(query)
        return result[0]['count'] if result else 0
    
    @classmethod
    def update(cls, teacher_id, data):
        set_clause = []
        params = []
        
        if 'name' in data:
            set_clause.append("name = %s")
            params.append(data['name'])
        if 'email' in data:
            set_clause.append("email = %s")
            params.append(data['email'])
        if 'campus' in data:
            set_clause.append("campus = %s")
            params.append(data['campus'])
        if 'can_manage_students' in data:
            set_clause.append("can_manage_students = %s")
            params.append(data['can_manage_students'] == 'on' if isinstance(data['can_manage_students'], str) else data['can_manage_students'])
        if 'can_manage_tasks' in data:
            set_clause.append("can_manage_tasks = %s")
            params.append(data['can_manage_tasks'] == 'on' if isinstance(data['can_manage_tasks'], str) else data['can_manage_tasks'])
        if 'password' in data:
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            set_clause.append("passwordHash = %s")
            params.append(password_hash)
        
        if not set_clause:
            return False
            
        params.append(teacher_id)
        query = f"UPDATE {cls.table_name} SET {', '.join(set_clause)} WHERE teacherID = %s"
        
        return db.execute_query(query, params)
    
    @classmethod
    def delete(cls, teacher_id):
        query = f"DELETE FROM {cls.table_name} WHERE teacherID = %s"
        return db.execute_query(query, (teacher_id,))

class Campus(BaseModel):
    table_name = 'campuses'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(10) NOT NULL,
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def initialize_defaults(cls):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        result = db.execute_query(query)
        
        if result and result[0]['count'] == 0:
            default_campuses = [
                (cls.generate_id(), 'Subhash Nagar', 'SUB', datetime.utcnow()),
                (cls.generate_id(), 'Yamuna', 'YAM', datetime.utcnow()),
                (cls.generate_id(), 'I20', 'I20', datetime.utcnow())
            ]
            
            query = f"""
            INSERT INTO {cls.table_name} (id, name, code, createdAt)
            VALUES (%s, %s, %s, %s)
            """
            
            db.execute_many(query, default_campuses)
            print("✅ Default campuses initialized")
    
    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name} ORDER BY name"
        return db.execute_query(query)

class Grade(BaseModel):
    table_name = 'grades'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(20) NOT NULL,
            level INT NOT NULL,
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def initialize_defaults(cls):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        result = db.execute_query(query)
        
        if result and result[0]['count'] == 0:
            default_grades = []
            for grade_level in range(1, 11):
                grade_id = cls.generate_id()
                grade_name = f"{grade_level}th Class"
                default_grades.append((grade_id, grade_name, grade_level, datetime.utcnow()))
            
            query = f"""
            INSERT INTO {cls.table_name} (id, name, level, createdAt)
            VALUES (%s, %s, %s, %s)
            """
            
            db.execute_many(query, default_grades)
            print("✅ Default grades initialized (1st to 10th Class)")
    
    @classmethod
    def get_all(cls):
        query = f"SELECT * FROM {cls.table_name} ORDER BY level"
        return db.execute_query(query)

class Notification(BaseModel):
    table_name = 'notifications'
    
    @classmethod
    def create_table(cls):
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            id VARCHAR(36) PRIMARY KEY,
            type VARCHAR(50),
            title VARCHAR(255) NOT NULL,
            message TEXT,
            relatedId VARCHAR(100),
            targetUserType VARCHAR(20),
            targetCampus VARCHAR(50),
            targetGrade VARCHAR(20),
            icon VARCHAR(50),
            isRead BOOLEAN DEFAULT FALSE,
            createdAt DATETIME NOT NULL
        )
        """
        db.execute_query(query)
    
    @classmethod
    def create(cls, data):
        notification_id = cls.generate_id()
        
        query = f"""
        INSERT INTO {cls.table_name} (id, type, title, message, relatedId, targetUserType, targetCampus, targetGrade, icon, isRead, createdAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            notification_id,
            data.get('type'),
            data['title'],
            data.get('message', ''),
            data.get('relatedId'),
            data.get('targetUserType'),
            data.get('targetCampus'),
            data.get('targetGrade'),
            data.get('icon', 'fas fa-bell'),
            False,
            datetime.utcnow()
        )
        
        db.execute_query(query, params)
        return notification_id
    
    @classmethod
    def get_for_user(cls, user_type, user_id=None, campus=None, grade=None):
        query = f"SELECT * FROM {cls.table_name} WHERE "
        
        conditions = []
        params = []
        
        if user_type == 'admin':
            conditions.append("(targetUserType = 'admin' OR targetUserType = 'admin_and_teachers' OR targetUserType = 'admin_and_students')")
        elif user_type == 'teacher':
            if campus:
                conditions.append("((targetUserType = 'teacher' AND targetCampus = %s) OR targetUserType = 'all_teachers' OR targetUserType = 'admin_and_teachers')")
                params.append(campus)
        elif user_type == 'student':
            if campus and grade:
                conditions.append("((targetUserType = 'student' AND targetCampus = %s AND targetGrade = %s) OR targetUserType = 'all_students' OR targetUserType = 'admin_and_students')")
                params.extend([campus, grade])
        
        if not conditions:
            return []
            
        query += " OR ".join(conditions) + " ORDER BY createdAt DESC LIMIT 50"
        return db.execute_query(query, params)
    
    @classmethod
    def get_unread_count(cls, user_type, user_id=None, campus=None, grade=None):
        query = f"SELECT COUNT(*) as count FROM {cls.table_name} WHERE isRead = FALSE AND "
        
        conditions = []
        params = []
        
        if user_type == 'admin':
            conditions.append("(targetUserType = 'admin' OR targetUserType = 'admin_and_teachers' OR targetUserType = 'admin_and_students')")
        elif user_type == 'teacher':
            if campus:
                conditions.append("((targetUserType = 'teacher' AND targetCampus = %s) OR targetUserType = 'all_teachers' OR targetUserType = 'admin_and_teachers')")
                params.append(campus)
        elif user_type == 'student':
            if campus and grade:
                conditions.append("((targetUserType = 'student' AND targetCampus = %s AND targetGrade = %s) OR targetUserType = 'all_students' OR targetUserType = 'admin_and_students')")
                params.extend([campus, grade])
        
        if not conditions:
            return 0
            
        query += " OR ".join(conditions)
        result = db.execute_query(query, params)
        return result[0]['count'] if result else 0
    
    @classmethod
    def mark_as_read(cls, notification_id, user_type, user_id=None, campus=None, grade=None):
        # First verify the user has access to this notification
        notifications = cls.get_for_user(user_type, user_id, campus, grade)
        accessible_ids = [n['id'] for n in notifications]
        
        if notification_id not in accessible_ids:
            return 0
        
        query = f"UPDATE {cls.table_name} SET isRead = TRUE WHERE id = %s"
        return db.execute_query(query, (notification_id,))
    
    @classmethod
    def mark_all_as_read(cls, user_type, user_id=None, campus=None, grade=None):
        query = f"UPDATE {cls.table_name} SET isRead = TRUE WHERE isRead = FALSE AND "
        
        conditions = []
        params = []
        
        if user_type == 'admin':
            conditions.append("(targetUserType = 'admin' OR targetUserType = 'admin_and_teachers' OR targetUserType = 'admin_and_students')")
        elif user_type == 'teacher':
            if campus:
                conditions.append("((targetUserType = 'teacher' AND targetCampus = %s) OR targetUserType = 'all_teachers' OR targetUserType = 'admin_and_teachers')")
                params.append(campus)
        elif user_type == 'student':
            if campus and grade:
                conditions.append("((targetUserType = 'student' AND targetCampus = %s AND targetGrade = %s) OR targetUserType = 'all_students' OR targetUserType = 'admin_and_students')")
                params.extend([campus, grade])
        
        if not conditions:
            return 0
            
        query += " OR ".join(conditions)
        return db.execute_query(query, params)
    
    @classmethod
    def create_task_notification(cls, task, action="created"):
        # Notify admin
        cls.create({
            'type': 'task',
            'title': f'Task {action.capitalize()}',
            'message': f'Task "{task["title"]}" has been {action}',
            'relatedId': task['id'],
            'targetUserType': 'admin',
            'icon': 'fas fa-tasks'
        })
        
        # Notify teachers and students for each campus and grade
        import json
        campus_target = json.loads(task['campusTarget']) if isinstance(task['campusTarget'], str) else task.get('campusTarget', [])
        grade_target = json.loads(task['gradeTarget']) if isinstance(task['gradeTarget'], str) else task.get('gradeTarget', [])
        
        for campus in campus_target:
            # Notify teachers
            cls.create({
                'type': 'task',
                'title': f'New Task {action.capitalize()}',
                'message': f'New task "{task["title"]}" has been {action} for {campus} campus',
                'relatedId': task['id'],
                'targetUserType': 'teacher',
                'targetCampus': campus,
                'icon': 'fas fa-tasks'
            })
            
            # Notify students
            for grade in grade_target:
                cls.create({
                    'type': 'task',
                    'title': 'New Task Assigned',
                    'message': f'New task "{task["title"]}" has been assigned to your class',
                    'relatedId': task['id'],
                    'targetUserType': 'student',
                    'targetCampus': campus,
                    'targetGrade': grade,
                    'icon': 'fas fa-tasks'
                })
    
    @classmethod
    def create_student_notification(cls, student, action="added"):
        # Notify admin
        cls.create({
            'type': 'student',
            'title': f'Student {action.capitalize()}',
            'message': f'Student "{student["name"]}" has been {action} to {student["campus"]} campus',
            'relatedId': student['studentID'],
            'targetUserType': 'admin',
            'icon': 'fas fa-user-graduate'
        })
        
        # Notify teachers in the same campus
        cls.create({
            'type': 'student',
            'title': f'New Student {action.capitalize()}',
            'message': f'New student "{student["name"]}" has been {action} to your campus',
            'relatedId': student['studentID'],
            'targetUserType': 'teacher',
            'targetCampus': student['campus'],
            'icon': 'fas fa-user-graduate'
        })
    
    @classmethod
    def create_teacher_notification(cls, teacher, action="added"):
        # Notify admin
        cls.create({
            'type': 'teacher',
            'title': f'Teacher {action.capitalize()}',
            'message': f'Teacher "{teacher["name"]}" has been {action} to {teacher["campus"]} campus',
            'relatedId': teacher['teacherID'],
            'targetUserType': 'admin',
            'icon': 'fas fa-chalkboard-teacher'
        })
    
    @classmethod
    def create_submission_notification(cls, submission, student, task):
        # Notify admin
        cls.create({
            'type': 'submission',
            'title': 'Task Submitted',
            'message': f'Student "{student["name"]}" submitted task "{task["title"]}"',
            'relatedId': submission['id'],
            'targetUserType': 'admin',
            'icon': 'fas fa-check-circle'
        })
        
        # Notify teachers in the same campus
        cls.create({
            'type': 'submission',
            'title': 'Task Submission',
            'message': f'Student "{student["name"]}" submitted task "{task["title"]}"',
            'relatedId': submission['id'],
            'targetUserType': 'teacher',
            'targetCampus': student['campus'],
            'icon': 'fas fa-check-circle'
        })

def initialize_default_data():
    """Initialize all database tables and default data"""
    # Create tables
    Student.create_table()
    Teacher.create_table()
    Task.create_table()
    Submission.create_table()
    Admin.create_table()
    Campus.create_table()
    Grade.create_table()
    Notification.create_table()
    
    # Initialize default data
    Admin.create_default()
    Campus.initialize_defaults()
    Grade.initialize_defaults()
    
    print("✅ All database tables and default data initialized successfully!")