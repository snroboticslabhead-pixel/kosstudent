import pymysql
from config import Config
import time

class Database:
    def __init__(self):
        self.connection = None
        self.connect_with_retry()
    
    def connect_with_retry(self, max_retries=3, retry_delay=2):
        for attempt in range(max_retries):
            try:
                self.connection = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True,
                    connect_timeout=10
                )
                print("✅ Successfully connected to MySQL database!")
                return
                
            except pymysql.err.OperationalError as e:
                error_code = e.args[0]
                
                if error_code == 1049:  # Unknown database
                    print(f"❌ Database doesn't exist. Attempting to create it...")
                    self.create_database()
                    continue
                    
                elif error_code == 1044:  # Access denied
                    print(f"❌ Access denied to database '{Config.MYSQL_DB}'. Available databases:")
                    self.list_available_databases()
                    raise
                    
                else:
                    print(f"❌ MySQL connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    
            except Exception as e:
                print(f"❌ Unexpected error (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        raise Exception(f"Failed to connect to MySQL after {max_retries} attempts")
    
    def list_available_databases(self):
        """List all databases available to the user"""
        try:
            temp_conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with temp_conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                print("Available databases:")
                for db in databases:
                    print(f"  - {db['Database']}")
            
            temp_conn.close()
            
        except Exception as e:
            print(f"Error listing databases: {e}")
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            temp_conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with temp_conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}`")
                print(f"✅ Database '{Config.MYSQL_DB}' created successfully")
            
            temp_conn.close()
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            raise
    
    def get_connection(self):
        if self.connection and self.connection.open:
            return self.connection
        else:
            self.connect_with_retry()
            return self.connection
    
    def execute_query(self, query, params=None):
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    self.connection.commit()
                    return cursor.lastrowid
        except Exception as e:
            print(f"Query error: {e}")
            self.connection.rollback()
            raise
    
    def execute_many(self, query, params_list):
        try:
            with self.get_connection().cursor() as cursor:
                cursor.executemany(query, params_list)
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Query error: {e}")
            self.connection.rollback()
            raise

# Global database instance
db = Database()