from database import ParkingDatabase
import psycopg2
from tabulate import tabulate
import os
from dotenv import load_dotenv

def get_table_info(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    return [table[0] for table in cursor.fetchall()]

def get_table_contents(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return columns, rows

def main():
    # Load environment variables
    load_dotenv()
    
    # Get connection parameters
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'robotics_parking_system'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        print("✅ Successfully connected to database!")
        
        # Get list of tables
        tables = get_table_info(conn)
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"- {table}")
        
        # Show contents of each table
        for table in tables:
            print(f"\n{'='*50}")
            print(f"Contents of table: {table}")
            print('='*50)
            
            columns, rows = get_table_contents(conn, table)
            if rows:
                print(tabulate(rows, headers=columns, tablefmt='grid'))
            else:
                print("Table is empty")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your .env file configuration")
        print("3. Verify database 'robotics_parking_system' exists")
        print("4. Confirm your PostgreSQL credentials")

if __name__ == "__main__":
    main() 