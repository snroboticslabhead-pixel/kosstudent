from database import db
from models import initialize_default_data

def setup_database():
    print("🚀 Setting up database...")
    
    try:
        # This will initialize all tables and default data
        initialize_default_data()
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

if __name__ == "__main__":
    setup_database()