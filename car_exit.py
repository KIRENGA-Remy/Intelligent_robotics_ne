import cv2
from ultralytics import YOLO
import pytesseract
import os
import time
import serial
import serial.tools.list_ports
from collections import Counter
from database import ParkingDatabase
from datetime import datetime
import signal
import sys

# Set tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load YOLOv8 model
model = YOLO('best.pt')

# Plate save directory
save_dir = 'plates'
os.makedirs(save_dir, exist_ok=True)

# Initialize database
db = ParkingDatabase()

# Global variables for cleanup
arduino = None
cap = None
gate_open = False

def cleanup():
    """Cleanup function to ensure gate is closed and resources are released"""
    global arduino, cap, gate_open
    
    print("\n[SYSTEM] Cleaning up...")
    
    # Close gate if it's open
    if gate_open and arduino:
        try:
            print("[GATE] Ensuring gate is closed...")
            arduino.write(b'0')
            time.sleep(1)  # Give Arduino time to process
        except:
            pass
    
    # Close resources
    if arduino:
        try:
            arduino.close()
            print("[ARDUINO] Connection closed")
        except:
            pass
    
    if cap:
        try:
            cap.release()
            print("[CAMERA] Released")
        except:
            pass
    
    cv2.destroyAllWindows()
    print("[SYSTEM] Cleanup complete")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print("\n[SYSTEM] Received shutdown signal")
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ===== Auto-detect Arduino Serial Port =====
def detect_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "COM" in port.device or "COM" in port.device:
            return port.device
    return None

# Initialize Arduino connection
arduino_port = detect_arduino_port()
if arduino_port:
    try:
        arduino = serial.Serial(arduino_port, 9600, timeout=1)
        print(f"[ARDUINO] Connected to {arduino_port}")
    except:
        print("[ARDUINO] Failed to connect")
        arduino = None

def check_payment_status(plate_number):
    """Check if vehicle has paid and update exit time"""
    try:
        with db.conn.cursor() as cur:
            # Get the most recent paid entry
            cur.execute("""
                SELECT id, entry_time 
                FROM vehicles 
                WHERE plate_number = %s 
                AND payment_status = 1 
                AND exit_time IS NULL
                ORDER BY entry_time DESC 
                LIMIT 1
            """, (plate_number,))
            result = cur.fetchone()
            
            if result:
                vehicle_id, entry_time = result
                # Update exit time
                cur.execute("""
                    UPDATE vehicles 
                    SET exit_time = %s
                    WHERE id = %s
                """, (datetime.now(), vehicle_id))
                db.conn.commit()
                return True
            return False
    except Exception as e:
        print(f"[ERROR] Database error: {str(e)}")
        return False

def control_gate(action):
    """Control the gate with proper error handling"""
    global arduino, gate_open
    
    if not arduino:
        print("[ERROR] Arduino not connected")
        return False
        
    try:
        if action == 'open':
            arduino.write(b'1')
            print("[GATE] Opening gate")
            gate_open = True
        elif action == 'close':
            arduino.write(b'0')
            print("[GATE] Closing gate")
            gate_open = False
        return True
    except Exception as e:
        print(f"[ERROR] Gate control error: {str(e)}")
        return False

# Mock ultrasonic sensor for testing
def mock_ultrasonic_distance():
    return 30  # Simulate vehicle at 30cm

# Initialize webcam
cap = cv2.VideoCapture(0)
plate_buffer = []
exit_cooldown = 300  # 5 minutes
last_saved_plate = None
last_exit_time = 0

print("[SYSTEM] Ready. Press 'q' to exit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        distance = mock_ultrasonic_distance()
        print(f"[SENSOR] Distance: {distance} cm")

        if distance <= 50:
            results = model(frame)

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    plate_img = frame[y1:y2, x1:x2]

                    # Plate Image Processing
                    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                    blur = cv2.GaussianBlur(gray, (5, 5), 0)
                    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                    # OCR Extraction
                    plate_text = pytesseract.image_to_string(
                        thresh, config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                    ).strip().replace(" ", "")

                    # Plate Validation
                    if "RA" in plate_text:
                        start_idx = plate_text.find("RA")
                        plate_candidate = plate_text[start_idx:]
                        if len(plate_candidate) >= 7:
                            plate_candidate = plate_candidate[:7]
                            prefix, digits, suffix = plate_candidate[:3], plate_candidate[3:6], plate_candidate[6]
                            if (prefix.isalpha() and prefix.isupper() and
                                digits.isdigit() and suffix.isalpha() and suffix.isupper()):
                                print(f"[VALID] Plate Detected: {plate_candidate}")
                                plate_buffer.append(plate_candidate)

                                # Decision after 3 captures
                                if len(plate_buffer) >= 3:
                                    most_common = Counter(plate_buffer).most_common(1)[0][0]
                                    current_time = time.time()

                                    if (most_common != last_saved_plate or
                                        (current_time - last_exit_time) > exit_cooldown):

                                        # Check payment status
                                        if check_payment_status(most_common):
                                            print(f"[AUTHORIZED] Exit granted for {most_common}")
                                            if control_gate('open'):
                                                try:
                                                    time.sleep(15)  # Gate open duration
                                                finally:
                                                    control_gate('close')
                                        else:
                                            print(f"[ALERT] Unauthorized exit attempt for {most_common}")
                                            db.record_unauthorized_exit(most_common)
                                            if arduino:
                                                arduino.write(b'2')  # Signal for alarm
                                                time.sleep(5)
                                                arduino.write(b'0')

                                        last_saved_plate = most_common
                                        last_exit_time = current_time
                                    else:
                                        print("[SKIPPED] Duplicate within 5 min window.")

                                    plate_buffer.clear()

                    cv2.imshow("Plate", plate_img)
                    cv2.imshow("Processed", thresh)
                    time.sleep(0.5)

        annotated_frame = results[0].plot() if distance <= 50 else frame
        cv2.imshow('Webcam Feed', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n[SYSTEM] Interrupted by user")
except Exception as e:
    print(f"\n[ERROR] An error occurred: {str(e)}")
finally:
    cleanup()






















# import cv2
# from ultralytics import YOLO
# import pytesseract
# import os
# import time
# import serial
# import serial.tools.list_ports
# from collections import Counter
# from database import ParkingDatabase
# from datetime import datetime
# import signal
# import sys

# # Set tesseract path for Windows
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# # Load YOLOv8 model
# model = YOLO('best.pt')

# # Plate save directory
# save_dir = 'plates'
# os.makedirs(save_dir, exist_ok=True)

# # Initialize database
# db = ParkingDatabase()

# # Global variables for cleanup
# arduino = None
# cap = None
# gate_open = False

# def cleanup():
#     """Cleanup function to ensure gate is closed and resources are released"""
#     global arduino, cap, gate_open
    
#     print("\n[SYSTEM] Cleaning up...")
    
#     # Close gate if it's open
#     if gate_open and arduino:
#         try:
#             print("[GATE] Ensuring gate is closed...")
#             arduino.write(b'0')
#             time.sleep(1)  # Give Arduino time to process
#         except:
#             pass
    
#     # Close resources
#     if arduino:
#         try:
#             arduino.close()
#             print("[ARDUINO] Connection closed")
#         except:
#             pass
    
#     if cap:
#         try:
#             cap.release()
#             print("[CAMERA] Released")
#         except:
#             pass
    
#     cv2.destroyAllWindows()
#     print("[SYSTEM] Cleanup complete")

# def signal_handler(signum, frame):
#     """Handle system signals for graceful shutdown"""
#     print("\n[SYSTEM] Received shutdown signal")
#     cleanup()
#     sys.exit(0)

# # Register signal handlers
# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)

# # ===== Auto-detect Arduino Serial Port =====
# def detect_arduino_port():
#     ports = list(serial.tools.list_ports.comports())
#     for port in ports:
#         if "COM" in port.device or "ACM" in port.device:
#             return port.device
#     return None

# # Initialize Arduino connection
# arduino_port = detect_arduino_port()
# if arduino_port:
#     try:
#         arduino = serial.Serial(arduino_port, 9600, timeout=1)
#         print(f"[ARDUINO] Connected to {arduino_port}")
#     except:
#         print("[ARDUINO] Failed to connect")
#         arduino = None

# def check_payment_status(plate_number):
#     """Check if vehicle has paid and update exit time"""
#     try:
#         with db.conn.cursor() as cur:
#             # Get the most recent paid entry
#             cur.execute("""
#                 SELECT id, entry_time 
#                 FROM vehicles 
#                 WHERE plate_number = %s 
#                 AND payment_status = 1 
#                 AND exit_time IS NULL
#                 ORDER BY entry_time DESC 
#                 LIMIT 1
#             """, (plate_number,))
#             result = cur.fetchone()
            
#             if result:
#                 vehicle_id, entry_time = result
#                 # Update exit time
#                 cur.execute("""
#                     UPDATE vehicles 
#                     SET exit_time = %s
#                     WHERE id = %s
#                 """, (datetime.now(), vehicle_id))
#                 db.conn.commit()
#                 return True
#             return False
#     except Exception as e:
#         print(f"[ERROR] Database error: {str(e)}")
#         return False

# def control_gate(action):
#     """Control the gate with proper error handling"""
#     global arduino, gate_open
    
#     if not arduino:
#         print("[ERROR] Arduino not connected")
#         return False
        
#     try:
#         if action == 'open':
#             arduino.write(b'1')
#             print("[GATE] Opening gate")
#             gate_open = True
#         elif action == 'close':
#             arduino.write(b'0')
#             print("[GATE] Closing gate")
#             gate_open = False
#         return True
#     except Exception as e:
#         print(f"[ERROR] Gate control error: {str(e)}")
#         return False

# # Mock ultrasonic sensor for testing
# def mock_ultrasonic_distance():
#     return 30  # Simulate vehicle at 30cm

# # Initialize webcam
# cap = cv2.VideoCapture(0)
# plate_buffer = []
# exit_cooldown = 300  # 5 minutes
# last_saved_plate = None
# last_exit_time = 0

# print("[SYSTEM] Ready. Press 'q' to exit.")

# try:
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         distance = mock_ultrasonic_distance()
#         print(f"[SENSOR] Distance: {distance} cm")

#         if distance <= 50:
#             results = model(frame)

#             for result in results:
#                 for box in result.boxes:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     plate_img = frame[y1:y2, x1:x2]

#                     # Plate Image Processing
#                     gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
#                     blur = cv2.GaussianBlur(gray, (5, 5), 0)
#                     thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

#                     # OCR Extraction
#                     plate_text = pytesseract.image_to_string(
#                         thresh, config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
#                     ).strip().replace(" ", "")

#                     # Plate Validation
#                     if "RA" in plate_text:
#                         start_idx = plate_text.find("RA")
#                         plate_candidate = plate_text[start_idx:]
#                         if len(plate_candidate) >= 7:
#                             plate_candidate = plate_candidate[:7]
#                             prefix, digits, suffix = plate_candidate[:3], plate_candidate[3:6], plate_candidate[6]
#                             if (prefix.isalpha() and prefix.isupper() and
#                                 digits.isdigit() and suffix.isalpha() and suffix.isupper()):
#                                 print(f"[VALID] Plate Detected: {plate_candidate}")
#                                 plate_buffer.append(plate_candidate)

#                                 # Decision after 3 captures
#                                 if len(plate_buffer) >= 3:
#                                     most_common = Counter(plate_buffer).most_common(1)[0][0]
#                                     current_time = time.time()

#                                     if (most_common != last_saved_plate or
#                                         (current_time - last_exit_time) > exit_cooldown):

#                                         # Check payment status and handle gate/alarm
#                                         if check_payment_status(most_common):
#                                             print(f"[AUTHORIZED] Exit granted for {most_common}")
#                                             if arduino:
#                                                 arduino.write(b'1')  # Tell Arduino to open gate
#                                                 print("[GATE] Opening gate for 15 seconds")
#                                                 time.sleep(15)
#                                                 arduino.write(b'0')  # Close gate
#                                                 print("[GATE] Closed")
#                                         else:
#                                             print(f"[ALERT] Unauthorized exit attempt for {most_common}")
#                                             db.record_unauthorized_exit(most_common)
#                                             if arduino:
#                                                 arduino.write(b'2')  # Trigger alarm
#                                                 print("[ALARM] Triggered for unauthorized vehicle")
#                                                 time.sleep(5)
#                                                 arduino.write(b'0')  # Reset system

#                                         last_saved_plate = most_common
#                                         last_exit_time = current_time
#                                     else:
#                                         print("[SKIPPED] Duplicate within 5 min window.")

#                                     plate_buffer.clear()

#                     cv2.imshow("Plate", plate_img)
#                     cv2.imshow("Processed", thresh)
#                     time.sleep(0.5)

#         annotated_frame = results[0].plot() if distance <= 50 else frame
#         cv2.imshow('Webcam Feed', annotated_frame)

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# except KeyboardInterrupt:
#     print("\n[SYSTEM] Interrupted by user")
# except Exception as e:
#     print(f"\n[ERROR] An error occurred: {str(e)}")
# finally:
#     cleanup()