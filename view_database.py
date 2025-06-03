from database import ParkingDatabase

def main():
    db = ParkingDatabase()
    
    print("\n=== Vehicle History ===")
    vehicles = db.get_vehicle_history()
    for vehicle in vehicles:
        print(f"ID: {vehicle[0]}")
        print(f"Plate: {vehicle[1]}")
        print(f"Entry Time: {vehicle[2]}")
        print(f"Exit Time: {vehicle[3]}")
        print(f"Payment Status: {'Paid' if vehicle[4] else 'Unpaid'}")
        print(f"Payment Amount: {vehicle[5]}")
        print(f"Payment Time: {vehicle[6]}")
        print("-" * 50)

    print("\n=== Unauthorized Exits ===")
    unauthorized = db.get_unauthorized_exits()
    for exit in unauthorized:
        print(f"ID: {exit[0]}")
        print(f"Plate: {exit[1]}")
        print(f"Time: {exit[2]}")
        print(f"Gate: {exit[3]}")
        print("-" * 50)

if __name__ == "__main__":
    main() 