from database import ParkingDatabase
import sys

def test_connection():
    try:
        db = ParkingDatabase()
        print("✅ Successfully connected to PostgreSQL database!")
        
        # Test adding a vehicle
        test_plate = "RA123A"
        db.add_vehicle_entry(test_plate)
        print(f"✅ Successfully added test vehicle: {test_plate}")
        
        # Test retrieving vehicle
        entry_time = db.get_unpaid_entry(test_plate)
        if entry_time:
            print(f"✅ Successfully retrieved vehicle entry time: {entry_time}")
        
        # Test updating payment
        db.update_payment(test_plate, 500.00)
        print(f"✅ Successfully updated payment for {test_plate}")
        
        print("\nAll database operations successful! 🎉")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your .env file configuration")
        print("3. Verify database 'robotics_parking_system' exists")
        print("4. Confirm your PostgreSQL credentials")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    success = test_connection()
    sys.exit(0 if success else 1) 