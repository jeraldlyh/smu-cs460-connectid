#include "Arduino.h"
#include "SoftwareSerial.h"
#include "DFRobotDFPlayerMini.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>

ESP8266WiFiMulti WiFiMulti;
SoftwareSerial mySoftwareSerial(12, 13);  // RX, TX
LiquidCrystal_I2C lcd(0x27, 16, 2);
DFRobotDFPlayerMini myDFPlayer;
void printDetail(uint8_t type, int value);
int button = 15;
int buttonState = 0;

void setup() {
  //this following code is to configure the button to be a input source, where the INPUT_PULLUP is to make use of the inbuilt resistor in the NodeMCU.
  pinMode(button, INPUT_PULLUP);
  //the following code is for the NodeMCU to talk to the DFPlayer MP3. the number is something like the frequency.
  mySoftwareSerial.begin(9600);
  //the Serial Begin is just for console log. So can just comment it out.
  Serial.begin(115200);

  //the following code is to connect to the I2C LCD Adapter.
  Wire.begin(2, 0);
  // This is to boot up the LCD screen.
  lcd.begin();
  // This is to turn on the backlight of the LCD.
  lcd.backlight();
  lcd.print("Setting up MP3");
  settingUpMP3();
  delay(2000);
  //to allow the PWID to see that the MP3 is done.
  lcd.setCursor(0, 1);
  lcd.print("MP3 setup done");
  myDFPlayer.play(1);  //playing the setting up wifi mp3.
  delay(2000);

  // Letting the PWID know that we are connecting to WiFi now
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");
  myDFPlayer.play(2);  //playing the setting up wifi mp3.

  //connecting to the WiFi Hotspot.
  for (uint8_t t = 4; t > 0; t--) {
    Serial.printf("[SETUP] WAIT %d...\n", t);
    Serial.flush();
    delay(1000);
  }

  WiFi.mode(WIFI_STA);
  WiFiMulti.addAP("JY Phone", "kendrick0808");
  while (WiFiMulti.run() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  lcd.setCursor(0, 1);
  lcd.print("WiFi Connected");  //letting them know that the WiFi is connected.
  myDFPlayer.play(3);           //playing the setting up wifi mp3.

  delay(1000);
  lcd.clear();
  lcd.print("Hello Kai Ming");
  myDFPlayer.play(4);  //Playing the Hello Kai Ming message
}

//the loop() code will run forever.
void loop() {
  //the following code is to read the input of the button and store it in buttonState.
  //0 -> not pressed
  //1 -> pressed
  buttonState = digitalRead(button);
  if (buttonState == 1) {
    String request = sendReq();  //this is to get the name of the responder that will be coming down.
    // How the DFPlayer works is that it will play based on how the mp3 file is copied in.
    // Currently, the 1st one is "Help is on the way" in a Japanese accent.
    myDFPlayer.play(5);  //Play the first mp3
    printingLCD(request);
  }
  //the following is mainly for debugging also.
  if (myDFPlayer.available()) {
    printDetail(myDFPlayer.readType(), myDFPlayer.read());  //Print the detail message from DFPlayer to handle different errors and states.
  }
}
void printingLCD(String name) {
  lcd.clear();
  delay(1000);
  Serial.println("Inside printing LCD");
  Serial.println(name);
  lcd.print(name);
  // lcd.print("Help is on the");
  delay(1000);
  lcd.setCursor(0, 1);
  delay(1000);
  lcd.print("is coming");
  delay(1000);
}
void settingUpMP3() {
  Serial.println();
  Serial.println(F("DFRobot DFPlayer Mini Demo"));
  Serial.println(F("Initializing DFPlayer ... (May take 3~5 seconds)"));

  if (!myDFPlayer.begin(mySoftwareSerial)) {  //Use softwareSerial to communicate with mp3.
    Serial.println(F("Unable to begin:"));
    Serial.println(F("1.Please recheck the connection!"));
    Serial.println(F("2.Please insert the SD card!"));
    while (true) {
      delay(0);  // Code to compatible with ESP8266 watch dog.
    }
  }
  Serial.println(F("DFPlayer Mini online."));
  Serial.println(F("DFPlayer Mini done."));
}
String sendReq() {
  if ((WiFiMulti.run() == WL_CONNECTED)) {

    std::unique_ptr<BearSSL::WiFiClientSecure> client(new BearSSL::WiFiClientSecure);

    // client->setFingerprint(fingerprint);
    // Or, if you happy to ignore the SSL certificate, then use the following line instead:
    client->setInsecure();

    HTTPClient https;

    Serial.print("[HTTPS] begin...\n");
    if (https.begin(*client, "https://plankton-app-jgfdd.ondigitalocean.app/sos?name=Wu Kai Ming")) {  // HTTPS

      Serial.print("[HTTPS] GET...\n");
      // start connection and send HTTP header
      int httpCode = https.GET();

      // httpCode will be negative on error
      if (httpCode > 0) {
        // HTTP header has been send and Server response header has been handled
        Serial.printf("[HTTPS] GET... code: %d\n", httpCode);

        // file found at server
        if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_MOVED_PERMANENTLY) {
          String payload = https.getString();
          Serial.println("hello");
          Serial.println(payload);
          return payload;  //it will now return the name of the responder.
        }
      } else {
        Serial.printf("[HTTPS] GET... failed, error: %s\n", https.errorToString(httpCode).c_str());
      }

      https.end();
    } else {
      Serial.printf("[HTTPS] Unable to connect\n");
    }
  }
  return "";
}
//this one is just to debug the MP3 player
void printDetail(uint8_t type, int value) {
  switch (type) {
    case TimeOut:
      Serial.println(F("Time Out!"));
      break;
    case WrongStack:
      Serial.println(F("Stack Wrong!"));
      break;
    case DFPlayerCardInserted:
      Serial.println(F("Card Inserted!"));
      break;
    case DFPlayerCardRemoved:
      Serial.println(F("Card Removed!"));
      break;
    case DFPlayerCardOnline:
      Serial.println(F("Card Online!"));
      break;
    case DFPlayerUSBInserted:
      Serial.println("USB Inserted!");
      break;
    case DFPlayerUSBRemoved:
      Serial.println("USB Removed!");
      break;
    case DFPlayerPlayFinished:
      Serial.print(F("Number:"));
      Serial.print(value);
      Serial.println(F(" Play Finished!"));
      break;
    case DFPlayerError:
      Serial.print(F("DFPlayerError:"));
      switch (value) {
        case Busy:
          Serial.println(F("Card not found"));
          break;
        case Sleeping:
          Serial.println(F("Sleeping"));
          break;
        case SerialWrongStack:
          Serial.println(F("Get Wrong Stack"));
          break;
        case CheckSumNotMatch:
          Serial.println(F("Check Sum Not Match"));
          break;
        case FileIndexOut:
          Serial.println(F("File Index Out of Bound"));
          break;
        case FileMismatch:
          Serial.println(F("Cannot Find File"));
          break;
        case Advertise:
          Serial.println(F("In Advertise"));
          break;
        default:
          break;
      }
      break;
    default:
      break;
  }
}
