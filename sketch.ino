#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Set the LCD address (0x27 or 0x3F, depending on your display)
LiquidCrystal_I2C lcd(0x27, 16, 2);  // 16 columns and 2 rows

char command;
unsigned long lastCommandTime = 0; // Track when command was received
const unsigned long DISPLAY_TIMEOUT = 2000; // 2 seconds in milliseconds

void setup() {
  // Initialize Serial communication and LCD display
  Serial.begin(9600);
  lcd.begin();      // Initialize the LCD screen without specifying the size
  lcd.backlight();       // Turn on the backlight
  lcd.clear();           // Clear the screen
}

void loop() {
  // Clear display if 2 seconds have passed since last command
  if (lastCommandTime > 0 && millis() - lastCommandTime >= DISPLAY_TIMEOUT) {
    lcd.clear();
    lastCommandTime = 0;
  }

  if (Serial.available() > 0) {
    command = Serial.read();
    lcd.clear();
    lastCommandTime = millis(); // Record time when command received
    
    switch(command) {
      case 'P':
        lcd.setCursor(0, 0);
        lcd.print("Playback:");
        lcd.setCursor(0, 1);
        lcd.print("Initiated/Pause");
        break;
        
      case 'N':
        lcd.setCursor(0, 0);
        lcd.print("Next Track");
        break;
        
      case 'B':
        lcd.setCursor(0, 0);
        lcd.print("Previous Track");
        break;
        
      default:
        lcd.setCursor(0, 0);
        lcd.print("Unknown cmd: ");
        lcd.print(command);
        break;
    }
  }
}
