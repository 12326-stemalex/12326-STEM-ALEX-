#include <WiFi.h>       // Include the Wi-Fi library
#include "DHTesp.h"     // Include the DHTesp library for DHT11 support
#include <HTTPClient.h> // Include HTTPClient library for HTTP requests

// Wi-Fi credentials
const char* ssid = "ASHRAF123";            // Correct Wi-Fi SSID
const char* password = "123456789123";     // Correct Wi-Fi Password

// Python server URL (Replace with your server IP and port)
const char* serverURL = "http://192.168.137.1:5000/data";

// Pin Definitions
#define TEMP_SENSOR_PIN 4  // GPIO pin for DHT11 Temperature sensor
#define HUM_SENSOR_PIN 5   // GPIO pin for DHT11 Humidity sensor
#define SOUND_SENSOR_PIN 34  // GPIO pin for Microphone Sound Detection (analog)

// LED Pins
#define TEMP_LED_PIN 18  // LED for temperature condition
#define HUM_LED_PIN 32   // LED for humidity condition
#define SOUND_LED_PIN 33 // LED for sound condition

DHTesp dhtTemp, dhtHum;  // Create instances for the DHT sensors

// Global variables to store sensor data
float temperature = 0.0;
float humidity = 0.0;
int soundValue = 0;

// Function to initialize DHT11 sensors
void initializeDHT() {
  dhtTemp.setup(TEMP_SENSOR_PIN, DHTesp::DHT11);  // Setup for temperature sensor
  dhtHum.setup(HUM_SENSOR_PIN, DHTesp::DHT11);    // Setup for humidity sensor
  Serial.println("DHT11 Sensors Initialized.");
}

// Function to read data from DHT11 sensors (Temperature and Humidity)
void readDHTData() {
  TempAndHumidity tempData = dhtTemp.getTempAndHumidity();
  TempAndHumidity humData = dhtHum.getTempAndHumidity();
  temperature = tempData.temperature;
  humidity = humData.humidity;
}

// Function to read sound level (analog input)
void readSoundLevel() {
  soundValue = analogRead(SOUND_SENSOR_PIN);  // Read analog sound value
}

// Function to control LEDs based on conditions
void controlLEDs() {
  digitalWrite(TEMP_LED_PIN, temperature >= 25.6 ? HIGH : LOW);
  digitalWrite(HUM_LED_PIN, humidity > 40.0 ? HIGH : LOW);
  digitalWrite(SOUND_LED_PIN, soundValue >= 200 ? HIGH : LOW);
}

// Function to connect to Wi-Fi
void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// Function to send data to Python server
void sendDataToPythonServer() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Prepare JSON payload
    String payload = "{";
    payload += "\"temperature\":" + String(temperature, 1) + ",";
    payload += "\"humidity\":" + String(humidity, 1) + ",";
    payload += "\"sound\":" + String(soundValue);
    payload += "}";

    // Send POST request
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(payload);

    // Handle response
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("Response: ");
      Serial.println(response);
    } else {
      Serial.print("Error sending data: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("Wi-Fi disconnected. Cannot send data.");
  }
}

void setup() {
  Serial.begin(115200);  // Start serial communication
  connectToWiFi();       // Connect to Wi-Fi
  initializeDHT();       // Initialize DHT11 sensors

  pinMode(TEMP_LED_PIN, OUTPUT);
  pinMode(HUM_LED_PIN, OUTPUT);
  pinMode(SOUND_LED_PIN, OUTPUT);
}

void loop() {
  // Read sensor data
  readDHTData();
  readSoundLevel();
  controlLEDs();

  // Print data to Serial Monitor
  Serial.print("Temperature: ");
  Serial.print(temperature, 1);
  Serial.print(" °C || Humidity: ");
  Serial.print(humidity, 1);
  Serial.print(" % || Sound Level: ");
  Serial.println(soundValue);

  // Send data to Python server
  sendDataToPythonServer();

  delay(15000);  // Wait 15 seconds before the next reading and sending data
}
