#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9
MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

// Validation functions
bool isValidPlateNumber(const String& plate) {
  // Check length (must be exactly 7 characters)
  if (plate.length() != 7) return false;
  
  // Check each character is alphanumeric
  for (int i = 0; i < 7; i++) {
    char c = plate[i];
    if (!isalnum(c)) return false;
  }
  
  return true;
}

bool isValidBalance(float balance) {
  // Balance must be positive and reasonable (adjust max value as needed)
  return (balance >= 0.0f && balance <= 20000.0f);
}

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  Serial.println("\nPlace your RFID card...");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  Serial.print("Card UID:");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(rfid.uid.uidByte[i], HEX);
  }
  Serial.println();

  byte plateBlock = 1;
  byte balanceBlock = 2; 
  byte data[16];
  memset(data, 0, 16); 

  // Plate number input with validation
  String plate;
  bool validPlate = false;
  
  while (!validPlate) {
    Serial.println("Type plate number (exactly 7 alphanumeric characters) and press ENTER:");
    while (!Serial.available());
    
    plate = Serial.readStringUntil('\n');
    plate.trim();
    plate.toUpperCase(); // Convert to uppercase for consistency
    
    if (isValidPlateNumber(plate)) {
      validPlate = true;
    } else {
      Serial.println("Invalid plate number! Must be exactly 7 alphanumeric characters.");
    }
  }

  // Copy to data buffer
  plate.getBytes(data, 8);

  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;
  MFRC522::StatusCode status = rfid.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, plateBlock, &key, &(rfid.uid));
  if (status != MFRC522::STATUS_OK) {
    Serial.print("Auth failed: "); Serial.println(rfid.GetStatusCodeName(status));
    return;
  }

  status = rfid.MIFARE_Write(plateBlock, data, 16);
  if (status != MFRC522::STATUS_OK) {
    Serial.print("Write failed: "); Serial.println(rfid.GetStatusCodeName(status));
  } else {
    Serial.println("Plate number written successfully!");
  }

  delay(2000);

  // Balance input with validation
  float balance = 0.0;
  bool validBalance = false;
  
  while (!validBalance) {
    Serial.println("Enter positive balance amount to store (e.g., 1000.00) and press ENTER:");
    while (!Serial.available());
    
    String balanceStr = Serial.readStringUntil('\n');
    balanceStr.trim();
    balance = balanceStr.toFloat();
    
    if (isValidBalance(balance)) {
      validBalance = true;
    } else {
      Serial.println("Invalid balance! Must be a positive number between 0 and 20,000.");
    }
  }

  byte balanceData[16];
  memcpy(balanceData, &balance, sizeof(balance));

  status = rfid.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, balanceBlock, &key, &(rfid.uid));
  if (status != MFRC522::STATUS_OK) {
    Serial.print("Auth failed: "); Serial.println(rfid.GetStatusCodeName(status));
    return;
  }

  status = rfid.MIFARE_Write(balanceBlock, balanceData, 16);
  if (status != MFRC522::STATUS_OK) {
    Serial.print("Write failed: "); Serial.println(rfid.GetStatusCodeName(status));
  } else {
    Serial.println("Balance written successfully!");
  }

  delay(2000);

  // Verification read
  byte readBuffer[18];
  byte size = sizeof(readBuffer);
  
  status = rfid.MIFARE_Read(plateBlock, readBuffer, &size);
  if (status != MFRC522::STATUS_OK) {
    Serial.print("Plate Read failed: "); Serial.println(rfid.GetStatusCodeName(status));
  } else {
    Serial.print("Stored plate number: ");        
    for (int i = 0; i < 7; i++) {
      Serial.print((char)readBuffer[i]);
    }

    Serial.println();
  }

  status = rfid.MIFARE_Read(balanceBlock, readBuffer, &size);
  if (status != MFRC522::STATUS_OK) {
    Serial.print("Balance Read failed: "); Serial.println(rfid.GetStatusCodeName(status));
  } else {
    float storedBalance;
    memcpy(&storedBalance, readBuffer, sizeof(float));
    Serial.print("Stored balance: ");
    Serial.println(storedBalance, 2);
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}