/**
 * Light Controller for IoT Light Scheduler
 * 
 * This sketch receives commands via Serial ('0' or '1')
 * and controls a relay connected to an Arduino to turn a light on or off.
 */

const int relayPin = 7;  // Digital pin connected to the relay module

void setup() {
  // Initialize serial communication at 9600 bps
  Serial.begin(9600);
  
  // Set relay pin as output
  pinMode(relayPin, OUTPUT);
  
  // Ensure light is off at startup (LOW for active-low relay)
  digitalWrite(relayPin, LOW);
  
  // Send startup message
  Serial.println("Arduino Light Controller Ready");
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Read the incoming byte
    char command = Serial.read();
    
    // Process the command
    if (command == '1') {
      digitalWrite(relayPin, HIGH);  // Turn ON the light
      Serial.println("Light ON");
    } 
    else if (command == '0') {
      digitalWrite(relayPin, LOW);   // Turn OFF the light
      Serial.println("Light OFF");
    }
    
    // Clear any remaining data in the buffer
    while (Serial.available() > 0) {
      Serial.read();
    }
  }
} 