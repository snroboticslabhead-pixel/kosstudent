from database import db
from models import Admin, Campus, Grade
import bcrypt
import datetime

def setup_database():
    # Create default admin user
    admin_collection = db.get_collection('admins')
    if admin_collection.count_documents({}) == 0:
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin_collection.insert_one({
            'username': 'admin',
            'passwordHash': password_hash,
            'role': 'super_admin',
            'createdAt': datetime.datetime.utcnow()
        })
        print("✅ Default admin created: username='admin', password='admin123'")
    
    # Create default campuses
    campuses_collection = db.get_collection('campuses')
    if campuses_collection.count_documents({}) == 0:
        default_campuses = [
            {'name': 'Subhash Nagar', 'code': 'SUB', 'createdAt': datetime.datetime.utcnow()},
            {'name': 'Yamuna', 'code': 'YAM', 'createdAt': datetime.datetime.utcnow()},
            {'name': 'I20', 'code': 'I20', 'createdAt': datetime.datetime.utcnow()}
        ]
        campuses_collection.insert_many(default_campuses)
        print("✅ Default campuses created")
    
    # Create default grades
    grades_collection = db.get_collection('grades')
    if grades_collection.count_documents({}) == 0:
        default_grades = []
        for grade_level in range(1, 11):  # Grades 1 to 10
            grade_name = f"{grade_level}th Class"
            default_grades.append({
                'name': grade_name,
                'level': grade_level,
                'createdAt': datetime.datetime.utcnow()
            })
        grades_collection.insert_many(default_grades)
        print("✅ Default grades created (1st to 10th Class)")
    
    print("🎉 Database setup completed!")

if __name__ == "__main__":
    setup_database()