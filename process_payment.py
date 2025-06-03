import serial
import time
from datetime import datetime
from database import ParkingDatabase

RATE_PER_HOUR = 500

# Initialize database
db = ParkingDatabase()

# Initialize serial connection
try:
    ser = serial.Serial('COM9', 9600, timeout=2)
    print("✅ Successfully connected to serial port COM9")
except Exception as e:
    print(f"❌ Error connecting to serial port: {str(e)}")
    print("Please check if:")
    print("1. The Arduino is connected")
    print("2. The correct COM port is being used")
    print("3. No other program is using the port")
    exit(1)

time.sleep(2)  # Wait for Arduino to reset

print("\nWelcome to Parking management system👋")
print("Waiting for card scan...\n")

def read_serial_line():
    """Read a line from serial port with timeout"""
    try:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            print(f"[DEBUG] Received from Arduino: {line}")
            return line
        return None
    except Exception as e:
        print(f"[ERROR] Serial read error: {str(e)}")
        return None

def parse_data(line):
    """Parse the data received from Arduino"""
    try:
        print(f"[DEBUG] Parsing line: {line}")
        parts = line.split(';')
        if len(parts) != 2:
            print(f"[ERROR] Invalid data format. Expected 2 parts, got {len(parts)}")
            return None, None
            
        plate = parts[0].split(':')[1]
        balance = float(parts[1].split(':')[1])
        print(f"[DEBUG] Parsed - Plate: {plate}, Balance: {balance}")
        return plate, balance
    except Exception as e:
        print(f"[ERROR] Failed to parse data: {str(e)}")
        return None, None

def calculate_payment(entry_time):
    """Calculate payment based on entry time"""
    if not entry_time:
        return None, None
    
    current_time = datetime.now()
    duration = current_time - entry_time
    duration_hours = max(1, int(duration.total_seconds() / 3600))
    amount_due = duration_hours * RATE_PER_HOUR
    
    return duration_hours, amount_due

def wait_for_card_data():
    """Wait for valid card data from Arduino"""
    print("Waiting for card data...")
    while True:
        line = read_serial_line()
        if line is None:
            time.sleep(0.1)
            continue
            
        # Skip Arduino's initial message
        if "Place your RFID card" in line:
            continue
            
        # Check for valid card data format
        if "PLATE:" in line and "BALANCE:" in line:
            return line
            
        print(f"[DEBUG] Ignoring message: {line}")

def wait_for_arduino_response(timeout=5):
    """Wait for Arduino response with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = read_serial_line()
        if response:
            return response
        time.sleep(0.1)
    return None

def process_single_payment():
    """Process a single payment and exit"""
    try:
        # Wait for valid card data
        line = wait_for_card_data()
        if not line:
            print("[ERROR] No valid card data received")
            return False
            
        print(f"\n[INFO] Card detected!")
        plate, balance = parse_data(line)
        
        if not plate or balance is None:
            print("[ERROR] Invalid data received from card")
            return False

        # Get entry time from database
        print(f"[INFO] Checking database for plate: {plate}")
        entry_time = db.get_unpaid_entry(plate)
        
        if not entry_time:
            print(f"[ERROR] No valid unpaid entry found for plate {plate}")
            return False

        print(f"\n[INFO] Card Details:")
        print(f"Plate Number: {plate}")
        print(f"Current Balance: {balance} RWF")
        
        # Calculate payment
        duration_hours, amount_due = calculate_payment(entry_time)
        if amount_due is None:
            print("[ERROR] Could not calculate payment amount")
            return False

        print(f"\n[INFO] Parking Duration: {duration_hours} hours")
        print(f"[INFO] Amount Due: {amount_due} RWF")

        # Check if sufficient balance
        if balance < amount_due:
            print(f"[ERROR] Insufficient balance. Required: {amount_due} RWF, Available: {balance} RWF")
            ser.write(b"INSUFFICIENT\n")
            return False
        
        # Process payment
        new_balance = balance - amount_due
        print(f"\n[INFO] Processing payment of {amount_due} RWF")
        print(f"[INFO] New balance will be: {new_balance} RWF")

        # Send amount to Arduino
        print(f"[DEBUG] Sending amount to Arduino: {amount_due}")
        ser.write(f"{amount_due}\n".encode())
        time.sleep(1)  # Give Arduino time to process

        # Wait for response
        response = wait_for_arduino_response()
        if response == "DONE":
            # Update database with payment details
            payment_time = datetime.now()
            if db.update_payment(plate, amount_due, payment_time):
                print(f"\n[SUCCESS] Payment processed successfully!")
                print(f"Plate: {plate}")
                print(f"Amount Paid: {amount_due} RWF")
                print(f"Payment Time: {payment_time}")
                print(f"Remaining Balance: {new_balance} RWF")
                return True
            else:
                print("[ERROR] Failed to update database")
                return False
        elif response == "INSUFFICIENT":
            print("[ERROR] Payment failed - insufficient balance on card")
        else:
            print(f"[ERROR] Unexpected response from card: {response}")
            # Even if we don't get a response, try to update the database
            payment_time = datetime.now()
            if db.update_payment(plate, amount_due, payment_time):
                print("[INFO] Database updated despite no Arduino response")
                return True
        
        return False

    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        if process_single_payment():
            print("\n[INFO] Payment completed successfully. Exiting...")
        else:
            print("\n[INFO] Payment failed. Exiting...")
    except KeyboardInterrupt:
        print("\n[INFO] Program terminated by user")
    finally:
        if 'ser' in locals():
            ser.close()
            print("[INFO] Serial port closed")
