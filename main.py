from machine import Pin
from machine import ADC
from time import sleep
from PicoDHT22 import PicoDHT22
import time
import urequests
import network
import requests
from time import sleep

# Wi-Fi credentials
ssid = 'Jenga254'
password = 'JeNg@KenHA07254'

SEND_BOTH = True


phone_number = '+254770554363'


# Your callmebot API key
api_key = '7044765'


BOT_TOKEN = "7930559839:AAHzL7RfL2jOMXbK510hS-ytrBZm4qhRfHk"
CHAT_ID = "64854828"

DHT_PIN = 10                    # GPIO pin connected to DHT22 data pin
READ_INTERVAL = 5.0             # Seconds between readings
DECIMAL_PLACES = 2              # Number of decimal places for rounding


LED_PIN = 12
BLINK_COUNT = 5
ON_DURATION = 2.0
OFF_DURATION = 1.5

adc_pin = 29


# Init Wi-Fi Interface
def init_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Connect to your network
    wlan.connect(ssid, password)
    # Wait for Wi-Fi connection
    connection_timeout = 10
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        print('Waiting for Wi-Fi connection...')
        sleep(1)
    # Check if connection is successful
    if wlan.status() != 3:
        return False
    else:
        print('Connection successful!')
        network_info = wlan.ifconfig()
        print('IP address:', network_info[0])
        return True

class WhatsApp:
    def send_message(self, phone_number, api_key, message):
        # Set the URL
        url = f'https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={message}&apikey={api_key}'

        # Make the request
        response = requests.get(url)
        # check if it was successful
        if (response.status_code == 200):
            print('Success!')
        else:
            print('Error')
            print(response.text)
    try: 
        # Connect to WiFi
        if init_wifi(ssid, password):
            # Send message to WhatsApp "Hello"
            # ENTER YOUR MESSAGE BELOW (URL ENCODED) https://www.urlencoder.io/
            message = 'Hello%20from%20the%20Raspberry%20Pi%20Pico%21' 
            send_message(phone_number, api_key, message)
    except Exception as e:
        print('Error:', e)




class Telegram:
    def send(self, message):
        try:
            url = (
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                f"?chat_id={CHAT_ID}&text={message}"
                )
            resp = urequests.get(url)
            resp.close()
            return True
        except Exception as e:
            print("Telegram error:", e)
            return False

class DHTSensor:
    def __init__(self, pin):
        self.sensor = PicoDHT22(Pin(DHT_PIN, Pin.IN, Pin.PULL_UP))
        
    def read(self):
        try:
            self.sensor.read()
            temp = self.sensor.temperature()
            hum = self.sensor.humidity()
            
            if temperature is None or humidity is None:
                print("Error: Failed to read from DHT22 sensor")
                return None, None
                
            return {"temp": temp, "humidity": hum, "status": "OK"}
        except Exception as e:
            return {"temp": None, "humidity": None, "status": f"ERROR: {e}"}

class TDSSensor:
    def __init__(self, adc_pin, vref=3.3):
        self.adc = ADC(adc_pin)
        self.vref = vref
        
    def read_raw(self):
        return self.adc.read_u16()
    
    def read_tds(self, temperature):
        """
            temperature: float (deg C) from DHT22
        """
        
        #1.) Converting raw ADC reading to voltage
        raw = self.read_raw()
        voltage = (raw / 65535.0) * self.vref
        
        #2.) Electrical Conductivity (EC) calculation
        ec = (voltage * 1000) / 560 #Constant is assumed to be 560
        
        #3.) Temperature compensation
        #EC at reference 25°C(room temperature)
        compensation_coeff = 1 + 0.02 * (temperature - 25)
        ec_25 = ec / compensation_coeff
        
        #4.) Converting EC to TDS (typical 0.5 factor)
        tds = ec_25 * 0.5
        
        return {
            "raw" : raw,
            "voltage" : round(voltage, 3),
            "ec" : round(ec_25, 2),
            "tds" : round(tds, 2),
            "status" : "OK"
            }


class leds:
    def __init__(self, LED_PIN):
        self.led = Pin(LED_PIN, Pin.OUT)
     
    def led_off(self):
        self.led.value(0)
            
    def normal(self):
        self.led.value(1)
        sleep(ON_DURATION)
            
    def warning(self):
        self.led.value(1)
        sleep(0.5)
        self.led.value(0)
        sleep(0.5)
            
    def blink_led(self, BLINK_COUNT):
        self.led.value(1)
        sleep(ON_DURATION)
        self.led.value(0)
        sleep(OFF_DURATION)

def main():
    
    reading_count = 0
    tds = TDSSensor(tds_pin)

    # Main program loop
    while True:
        reading_count += 1
        print(f"Reading #{reading_count}:")

        dht_data = DHTSensor.read()
        temp = dht_data["temp"]
        hum = dht_data["hum"]
        tds_data = TDSSensor.read_tds(dht_data["temp"] if dht_data["temp"] else 25)
        tg = Telegram()
        led = leds()
        tds_ppm = tds_data["tds"]
        wa = Whatsapp()
        
        
        if temp is not None and hum is not None:
                # Simple comfort level check
                if temp > 30:
                    alert_msg = print("Hot environment detected!")
                    led.warning()
                elif hum < 40:
                    alert_msg = print("Low humidity detected!")
                    led.warning()
                elif (temp > 30) & (hum < 40):
                    alert_msg = print("Ambient conditions")
                    led.normal()
        if temp is None or hum is None:
            led.blink_led()
            continue
        if tds_ppm > 800: #ppm
            led.warning()
            alert_msg = print(f"High TDS Alert: {tds_ppm} ppm")
        
        if SEND_BOTH:
            wa.send(phone_number, api_key,alert_msg)
            tg.send(alert_msg)
        else:
            wa.send(alert_msg)
        
    