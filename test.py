import serial

print("Testing PySerial import...")
print("serial module path:", serial.__file__)

try:
    arduino = serial.Serial('COM9', 9600, timeout=1)
    print("[SUCCESS] Connected to Arduino on COM9")
    arduino.close()
except Exception as e:
    print("[ERROR]", str(e))