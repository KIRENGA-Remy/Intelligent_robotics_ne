import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class ParkingDatabase:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'robotics_parking_system'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Database connection error: {str(e)}")
            raise

    def get_connection(self):
        return self.conn

    def init_db(self):
        """Initialize required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id SERIAL PRIMARY KEY,
                plate_number VARCHAR(10) NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP,
                payment_status INTEGER DEFAULT 0,
                payment_amount DECIMAL(10, 2),
                payment_time TIMESTAMP
            )
        ''')

        # unauthorized_exits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unauthorized_exits (
                id SERIAL PRIMARY KEY,
                vehicle_id VARCHAR(50),
                reason TEXT,
                plate_number VARCHAR(10) NOT NULL,
                exit_time TIMESTAMP NOT NULL,
                gate_location VARCHAR(10) NOT NULL
            )
        ''')

        conn.commit()
        cursor.close()

    def add_vehicle(self, plate_number):
        """Add a new vehicle entry"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vehicles (plate_number, entry_time, payment_status)
                    VALUES (%s, %s, 0)
                """, (plate_number, datetime.now()))
                self.conn.commit()
                print(f"✅ Vehicle {plate_number} added to database")
                return True
        except Exception as e:
            print(f"❌ Error adding vehicle: {str(e)}")
            self.conn.rollback()
            return False

    def get_unpaid_entry(self, plate_number):
        """Get unpaid vehicle entry"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT entry_time FROM vehicles
                    WHERE plate_number = %s AND exit_time IS NULL AND payment_status = 0
                    ORDER BY entry_time DESC LIMIT 1
                """, (plate_number,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting unpaid entry: {str(e)}")
            return None

    def update_payment(self, plate_number, amount, payment_time=None):
        """Mark vehicle payment"""
        try:
            if not payment_time:
                payment_time = datetime.now()

            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM vehicles 
                    WHERE plate_number = %s AND payment_status = 0
                    ORDER BY entry_time DESC LIMIT 1
                """, (plate_number,))
                result = cur.fetchone()

                if not result:
                    print(f"❌ No unpaid entry found for plate {plate_number}")
                    return False

                vehicle_id = result[0]
                cur.execute("""
                    UPDATE vehicles 
                    SET payment_status = 1, payment_amount = %s, payment_time = %s
                    WHERE id = %s
                """, (amount, payment_time, vehicle_id))

                self.conn.commit()
                print(f"✅ Payment updated for plate {plate_number}")
                return True
        except Exception as e:
            print(f"❌ Error updating payment: {str(e)}")
            self.conn.rollback()
            return False

    def detect_unauthorized_exit(self, plate_number, gate_location="ExitGate1"):
        """Check and log unauthorized exits"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM vehicles 
                    WHERE plate_number = %s AND exit_time IS NULL AND payment_status = 0
                    ORDER BY entry_time DESC LIMIT 1
                """, (plate_number,))
                result = cur.fetchone()

                if result:
                    vehicle_id = result[0]

                    # 🚨 Trigger alarm
                    self.trigger_alarm()

                    # 📝 Log unauthorized exit
                    cur.execute("""
                        INSERT INTO unauthorized_exits (vehicle_id, plate_number, exit_time, gate_location)
                        VALUES (%s, %s, %s, %s)
                    """, (vehicle_id, plate_number, datetime.now(), gate_location))

                    self.conn.commit()
                    print(f"🚨 Unauthorized exit logged for {plate_number}")
                    return True
                else:
                    print(f"✅ Authorized or already exited: {plate_number}")
                    return False
        except Exception as e:
            print(f"❌ Error detecting unauthorized exit: {str(e)}")
            self.conn.rollback()
            return False

    def trigger_alarm(self):
        """Placeholder for alarm system integration"""
        print("🔔 Alarm triggered!")

    def record_unauthorized_exit(self, plate_number, gate_location="Unknown"):
        """Manual unauthorized exit record"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO unauthorized_exits (plate_number, exit_time, gate_location)
                    VALUES (%s, %s, %s)
                """, (plate_number, datetime.now(), gate_location))
                self.conn.commit()
                print(f"✅ Unauthorized exit recorded for {plate_number}")
                return True
        except Exception as e:
            print(f"❌ Error recording unauthorized exit: {str(e)}")
            self.conn.rollback()
            return False

    def get_vehicle_history(self, plate_number=None, limit=100):
        """Retrieve vehicle history"""
        try:
            with self.conn.cursor() as cur:
                if plate_number:
                    cur.execute("""
                        SELECT * FROM vehicles WHERE plate_number = %s
                        ORDER BY entry_time DESC LIMIT %s
                    """, (plate_number, limit))
                else:
                    cur.execute("""
                        SELECT * FROM vehicles ORDER BY entry_time DESC LIMIT %s
                    """, (limit,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching vehicle history: {str(e)}")
            return []

    def get_unauthorized_exits(self, limit=100):
        """List recent unauthorized exits"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT plate_number, exit_time, gate_location
                    FROM unauthorized_exits
                    ORDER BY exit_time DESC LIMIT %s
                """, (limit,))
                return [
                    {'plate_number': r[0], 'exit_time': r[1], 'gate_location': r[2]}
                    for r in cur.fetchall()
                ]
        except Exception as e:
            print(f"Error getting unauthorized exits: {str(e)}")
            return []

    def get_all_vehicles(self):
        """List all vehicle records"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT plate_number, entry_time, payment_status, payment_amount, payment_time
                    FROM vehicles ORDER BY entry_time DESC
                """)
                return [
                    {'plate_number': r[0], 'entry_time': r[1], 'payment_status': r[2],
                     'payment_amount': r[3], 'payment_time': r[4]}
                    for r in cur.fetchall()
                ]
        except Exception as e:
            print(f"Error fetching all vehicles: {str(e)}")
            return []

    def get_total_vehicles(self):
        """Total vehicle count"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM vehicles")
                return cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting total vehicles: {str(e)}")
            return 0

    def get_current_vehicles(self):
        """Vehicles currently in parking"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM vehicles WHERE exit_time IS NULL")
                return cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting current vehicles: {str(e)}")
            return 0

    def get_total_revenue(self):
        """Total revenue collected"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(payment_amount), 0) 
                    FROM vehicles WHERE payment_status = 1
                """)
                return cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting total revenue: {str(e)}")
            return 0

    def get_unauthorized_exits_count(self):
        """Count of unauthorized exits"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM unauthorized_exits")
                return cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting unauthorized exits count: {str(e)}")
            return 0

    def __del__(self):
        if self.conn:
            self.conn.close()
            print("🛑 Database connection closed")
