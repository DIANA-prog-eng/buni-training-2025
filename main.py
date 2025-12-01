import network
import urequests as requests # MicroPython uses urequests
import time
from machine import Pin, ADC
import dht # Use standard MicroPython DHT library

# --- CONFIGURATION ---
SSID = 'Jenga254' #wifi name
PASSWORD = 'JeNg@KenHA07254' #wifi password

# Notification Settings
SEND_BOTH = True
PHONE_NUMBER = '+254770554363'
# REPLACE THESE WITH YOUR ACTUAL KEYS
WA_API_KEY = '7044765' 
TG_BOT_TOKEN = "7930559839:AAHzL7RfL2jOMXbK510hS-ytrBZm4qhRfHk"
TG_CHAT_ID = "64854828"

# Hardware Pins
DHT_PIN_NUM = 10
LED_PIN_NUM = 12
ADC_PIN_NUM = 29 # Note: On Pico W, GP29 is usually VSYS. Ensure you are using the correct ADC pin (GP26, 27, or 28).

# Thresholds
TEMP_HIGH_LIMIT = 30
HUM_LOW_LIMIT = 40
TDS_HIGH_LIMIT = 800

# --- CLASSES ---

class WiFiConnection:
    @staticmethod
    def connect(ssid, password):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, password)
        
        # Wait for connect
        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('Waiting for connection...')
            time.sleep(1)

        if wlan.status() != 3:
            print('Network connection failed')
            return False
        else:
            print('Connected')
            print('IP:', wlan.ifconfig()[0])
            return True

class WhatsApp:
    def __init__(self, phone, api_key):
        self.phone = phone
        self.api_key = api_key

    def send(self, message):
        # WhatsApp CallMeBot requires URL encoding (spaces = %20)
        encoded_msg = message.replace(' ', '%20')
        url = f'https://api.callmebot.com/whatsapp.php?phone={self.phone}&text={encoded_msg}&apikey={self.api_key}'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("WhatsApp Sent!")
            else:
                print(f"WhatsApp Error: {response.text}")
            response.close()
        except Exception as e:
            print("WhatsApp Request Failed:", e)

class Telegram:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send(self, message):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&text={message}"
        try:
            response = requests.get(url)
            response.close()
            print("Telegram Sent!")
        except Exception as e:
            print("Telegram Request Failed:", e)

class SensorManager:
    def __init__(self, dht_pin, adc_pin):
        # Initialize DHT
        self.dht_sensor = dht.DHT22(Pin(dht_pin))
        # Initialize ADC
        self.adc = ADC(adc_pin)
        self.vref = 3.3

    def read_dht(self):
        try:
            self.dht_sensor.measure()
            temp = self.dht_sensor.temperature()
            hum = self.dht_sensor.humidity()
            return temp, hum
        except Exception as e:
            print("DHT Read Error:", e)
            return None, None

    def read_tds(self, temperature=25):
        # 1. Read Raw
        raw = self.adc.read_u16()
        # 2. Convert to Voltage
        voltage = (raw / 65535.0) * self.vref
        # 3. Calculate TDS (Approximation)
        # Simplified TDS logic for demo purposes
        ec = (voltage * 1000) / 560 
        compensation_coeff = 1 + 0.02 * (temperature - 25)
        ec_25 = ec / compensation_coeff
        tds_val = ec_25 * 0.5 * 1000 # Scaling up for display visibility usually
        return round(tds_val, 2)

class LEDController:
    def __init__(self, pin):
        self.led = Pin(pin, Pin.OUT)
        self.led.value(0)

    def alert(self):
        # Fast blink for alert
        for _ in range(3):
            self.led.value(1)
            time.sleep(0.2)
            self.led.value(0)
            time.sleep(0.2)

    def normal(self):
        # Slow blink or solid on to show "System Alive"
        self.led.value(1)
        time.sleep(0.1)
        self.led.value(0)

# --- MAIN PROGRAM ---

def main():
    # 1. Setup Hardware
    led_ctrl = LEDController(LED_PIN_NUM)
    sensors = SensorManager(DHT_PIN_NUM, ADC_PIN_NUM)
    
    # 2. Setup Network
    if not WiFiConnection.connect(SSID, PASSWORD):
        print("Stopping program due to WiFi failure.")
        return

    # 3. Setup Messengers
    wa = WhatsApp(PHONE_NUMBER, WA_API_KEY)
    tg = Telegram(TG_BOT_TOKEN, TG_CHAT_ID)

    print("System Started...")
    
    # Variables to manage message spamming
    last_alert_time = 0
    ALERT_COOLDOWN = 60  # Only send messages once every 60 seconds

    while True:
        # Read Sensors
        temp, hum = sensors.read_dht()
        
        # Handle cases where DHT fails
        current_temp_for_tds = temp if temp is not None else 25
        tds_val = sensors.read_tds(current_temp_for_tds)

        alert_message = ""
        is_alert = False

        # Check Conditions
        if temp is not None:
            print(f"Temp: {temp}C, Hum: {hum}%, TDS: {tds_val}")
            
            if temp > TEMP_HIGH_LIMIT:
                alert_message = f"ALERT: High Temp detected! {temp}C"
                is_alert = True
            elif hum < HUM_LOW_LIMIT:
                alert_message = f"ALERT: Low Humidity! {hum}%"
                is_alert = True
            
            if tds_val > TDS_HIGH_LIMIT:
                alert_message = f"ALERT: High TDS! {tds_val} ppm"
                is_alert = True
        else:
            print("Sensor Error: Could not read DHT22")

        # Handle Alerts
        if is_alert:
            led_ctrl.alert()
            
            # Check if enough time has passed since last message
            if (time.time() - last_alert_time) > ALERT_COOLDOWN:
                print(f"Sending Message: {alert_message}")
                
                if SEND_BOTH:
                    wa.send(alert_message)
                    tg.send(alert_message)
                else:
                    wa.send(alert_message)
                
                last_alert_time = time.time() # Reset cooldown
        else:
            led_ctrl.normal()

        time.sleep(5)

if __name__ == "__main__":
    main()