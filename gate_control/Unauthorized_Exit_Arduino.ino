#include <Stepper.h>

#define TRIG_PIN 7
#define ECHO_PIN 8
#define BUZZER_PIN 6
#define RED_LED_PIN 5
#define STEPS 2048  // Steps per revolution for stepper motor

// Stepper motor connected to ULN2003AN driver
Stepper stepper(STEPS, 2, 3, 4, 5);  // Pins 2, 3, 4, 5

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  stepper.setSpeed(15);  // Set stepper speed
  Serial.println("Exit Detection Ready");
}

void loop() {
  // Detect vehicle with ultrasonic sensor
  long duration;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  duration = pulseIn(ECHO_PIN, HIGH);
  float distance = duration * 0.034 / 2;

  if (distance < 50) { // Vehicle detected within 50cm
    Serial.println("EXIT_VEHICLE_DETECTED");
    delay(1000); // Avoid multiple triggers
  }

  // Handle commands from Python
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') { // Open gate
      stepper.step(512); // Rotate 90 degrees to open
      Serial.println("GATE_OPENED");
      delay(15000); // Keep gate open for 15 seconds
      stepper.step(-512); // Rotate back to close
      Serial.println("GATE_CLOSED");
    } else if (command == '2') { // Trigger alarm
      for (int i = 0; i < 5; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        digitalWrite(RED_LED_PIN, HIGH);
        tone(BUZZER_PIN, 1000); // 1kHz tone
        delay(500);
        digitalWrite(BUZZER_PIN, LOW);
        digitalWrite(RED_LED_PIN, LOW);
        noTone(BUZZER_PIN);
        delay(500);
      }
      Serial.println("ALARM_TRIGGERED");
    } else if (command == '0') { // Close gate/reset
      stepper.step(-512); // Ensure gate is closed
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(RED_LED_PIN, LOW);
      noTone(BUZZER_PIN);
      Serial.println("GATE_CLOSED");
    }
  }
}