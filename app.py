from flask import Flask, render_template, session, redirect, url_for
from routes import *
from config import Config
from models import Teacher, initialize_default_data

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Register routes
app.add_url_rule('/', 'login', login, methods=['GET', 'POST'])
app.add_url_rule('/logout', 'logout', logout)
app.add_url_rule('/admin/dashboard', 'admin_dashboard', admin_dashboard)
app.add_url_rule('/admin/students', 'manage_students', manage_students)
app.add_url_rule('/admin/students/add', 'add_student', add_student, methods=['GET', 'POST'])
app.add_url_rule('/admin/students/edit/<student_id>', 'edit_student', edit_student, methods=['GET', 'POST'])
app.add_url_rule('/admin/students/delete/<student_id>', 'delete_student', delete_student, methods=['POST'])
app.add_url_rule('/admin/students/upload', 'upload_students', upload_students, methods=['POST'])
app.add_url_rule('/admin/students/export', 'export_students', export_students)
app.add_url_rule('/admin/teachers', 'manage_teachers', manage_teachers)
app.add_url_rule('/admin/teachers/add', 'add_teacher', add_teacher, methods=['GET', 'POST'])
app.add_url_rule('/admin/teachers/edit/<teacher_id>', 'edit_teacher', edit_teacher, methods=['GET', 'POST'])
app.add_url_rule('/admin/teachers/delete/<teacher_id>', 'delete_teacher', delete_teacher, methods=['POST'])
app.add_url_rule('/admin/teachers/export', 'export_teachers', export_teachers)
app.add_url_rule('/admin/tasks', 'manage_tasks', manage_tasks)
app.add_url_rule('/admin/tasks/add', 'add_task', add_task, methods=['GET', 'POST'])
app.add_url_rule('/admin/tasks/edit/<task_id>', 'edit_task', edit_task, methods=['GET', 'POST'])
app.add_url_rule('/admin/tasks/delete/<task_id>', 'delete_task', delete_task, methods=['POST'])
app.add_url_rule('/admin/analytics', 'analytics', analytics)
app.add_url_rule('/admin/task/<task_id>', 'task_details', task_details)
app.add_url_rule('/admin/submission/<task_id>/<student_id>', 'view_submission', view_submission)
app.add_url_rule('/teacher/dashboard', 'teacher_dashboard', teacher_dashboard)
app.add_url_rule('/teacher/students', 'teacher_students', teacher_students)
app.add_url_rule('/teacher/students/add', 'teacher_add_student', teacher_add_student, methods=['GET', 'POST'])
app.add_url_rule('/teacher/students/edit/<student_id>', 'teacher_edit_student', teacher_edit_student, methods=['GET', 'POST'])
app.add_url_rule('/teacher/students/delete/<student_id>', 'teacher_delete_student', teacher_delete_student, methods=['POST'])
app.add_url_rule('/teacher/students/export', 'teacher_export_students', teacher_export_students)
app.add_url_rule('/teacher/tasks', 'teacher_tasks', teacher_tasks)
app.add_url_rule('/teacher/tasks/add', 'teacher_add_task', teacher_add_task, methods=['GET', 'POST'])
app.add_url_rule('/teacher/tasks/edit/<task_id>', 'teacher_edit_task', teacher_edit_task, methods=['GET', 'POST'])
app.add_url_rule('/teacher/tasks/delete/<task_id>', 'teacher_delete_task', teacher_delete_task, methods=['POST'])
app.add_url_rule('/teacher/task/<task_id>', 'teacher_task_details', teacher_task_details)
app.add_url_rule('/teacher/submission/<task_id>/<student_id>', 'teacher_view_submission', teacher_view_submission)
app.add_url_rule('/student/dashboard', 'student_dashboard', student_dashboard)
app.add_url_rule('/student/editor', 'web_editor', web_editor)
app.add_url_rule('/student/practice', 'practice_editor', practice_editor)

# New OpenRouter AI Integration Routes
app.add_url_rule('/simulate_run', 'simulate_code_execution', simulate_code_execution, methods=['POST'])
app.add_url_rule('/generate_code', 'generate_code', generate_code, methods=['POST'])
app.add_url_rule('/ai_chat', 'ai_chat', ai_chat, methods=['POST'])

# Notification Routes
app.add_url_rule('/notifications', 'get_notifications', get_notifications, methods=['GET'])
app.add_url_rule('/notifications/<notification_id>/read', 'mark_notification_read', mark_notification_read, methods=['POST'])
app.add_url_rule('/notifications/read-all', 'mark_all_notifications_read', mark_all_notifications_read, methods=['POST'])

@app.context_processor
def inject_user():
    """
    Inject user information into all templates
    """
    token = session.get('token')
    user_type = session.get('user_type')
    username = session.get('username')
    student_name = session.get('student_name')
    teacher_name = session.get('teacher_name')
    teacher_campus = session.get('teacher_campus')
    
    # For teachers, we need to get the teacher's permissions
    teacher_can_manage_students = False
    teacher_can_manage_tasks = False
    
    if user_type == 'teacher':
        teacher_id = session.get('teacher_id')
        if teacher_id:
            teacher = Teacher.find_by_id(teacher_id)
            if teacher:
                teacher_can_manage_students = teacher.get('can_manage_students', False)
                teacher_can_manage_tasks = teacher.get('can_manage_tasks', False)
    
    return {
        'user_type': user_type,
        'username': username,
        'student_name': student_name,
        'teacher_name': teacher_name,
        'teacher_campus': teacher_campus,
        'teacher_can_manage_students': teacher_can_manage_students,
        'teacher_can_manage_tasks': teacher_can_manage_tasks
    }

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors
    """
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors
    """
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    """
    Handle 403 Forbidden errors
    """
    return render_template('403.html'), 403

@app.errorhandler(401)
def unauthorized(error):
    """
    Handle 401 Unauthorized errors
    """
    return redirect(url_for('login'))

@app.before_request
def before_request():
    """
    Execute before each request
    """
    # Add any pre-request logic here if needed
    pass

def init_app():
    """
    Initialize the application with default data
    """
    try:
        initialize_default_data()
        print("✅ Application initialized successfully!")
        print("📊 Default data loaded:")
        print("   - Admin account created (admin/admin123)")
        print("   - Default campuses initialized")
        print("   - Default grades initialized")
    except Exception as e:
        print(f"❌ Error initializing application: {e}")

if __name__ == '__main__':
    # Create default data and run the application
    init_app()
    print("🚀 Starting TaskBoard application...")
    print("🌐 Server running on http://0.0.0.0:5000")
    print("📝 Debug mode: ON")
    app.run(debug=True, host='0.0.0.0', port=5000)