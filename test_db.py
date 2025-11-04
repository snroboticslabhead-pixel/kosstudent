import pymysql
from config import Config

def test_connection():
    try:
        # First, let's try to connect without specifying a database
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Show available databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("Available databases:")
            for db in databases:
                print(f"- {db['Database']}")
        
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()