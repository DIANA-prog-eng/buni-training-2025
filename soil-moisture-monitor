# main.py - Unified Soil Moisture
# Author: diana
# Target: Raspberry Pi Pico / Pico W (MicroPython)

import time
try:
    import network
except:
    network = None
try:
    import urequests as requests
except:
    import requests

from machine import Pin, ADC
import dht

# ===== CONFIG =====
# Wi-Fi
SSID = "NZYOKA FAHM"
PASSWORD = "Diana Dee23"

# Notification: WhatsApp (callmebot) and Telegram
SEND_BOTH = True
CALLMEBOT_PHONE = "+254713738890"
CALLMEBOT_APIKEY = "7044765"   # replace with your real key
TELEGRAM_BOT_TOKEN = "7930559839:AAHzL7RfL2jOMXbK510hS-ytrBZm4qhRfHk"
TELEGRAM_CHAT_ID = "64854828"

# Pins (GP numbers)
DHT_PIN = 10           # GPIO10 for DHT22 data pin
SOIL_ADC_PIN = 27      # GP27 analog for soil moisture (ADC( Pin(27) ))
TDS_ADC_PIN = 29       # GP29 analog for TDS (note: check your board; GP26-28 are standard ADC pins)

# Soil moisture calibration (update via calibrate_sensor())
DRY_VALUE = 65535
WET_VALUE = 31405

# Thresholds
DRY_THRESHOLD = 30     # percent
WET_THRESHOLD = 70     # percent
TEMP_HIGH_LIMIT = 30   # degC
HUM_LOW_LIMIT = 40     # %
TDS_HIGH_LIMIT = 800   # ppm

# Timing
SAMPLE_INTERVAL = 5        # seconds between cycles
ALERT_COOLDOWN = 60        # seconds between alert messages

# LED indicator pin
LED_PIN = 12

# ===== Utilities =====
def safe_sleep(s):
    """Wrapper to allow KeyboardInterrupt clean exit during sleeps."""
    try:
        time.sleep(s)
    except KeyboardInterrupt:
        raise

# ===== WiFi =====
class WiFi:
    @staticmethod
    def connect(ssid, password, timeout=15):
        if network is None:
            print("Network module not available on this build.")
            return False
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if wlan.isconnected():
            print("Already connected:", wlan.ifconfig())
            return True
        wlan.connect(ssid, password)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if wlan.isconnected():
                print("WiFi connected:", wlan.ifconfig())
                return True
            print("Waiting for WiFi...")
            time.sleep(1)
        print("WiFi connection failed.")
        return False

# ===== Notifiers =====
class WhatsAppNotifier:
    def __init__(self, phone, apikey):
        self.phone = phone
        self.apikey = apikey

    def send(self, message):
        # callmebot expects URL encoded text; spaces -> %20
        msg = str(message).replace(" ", "%20")
        url = f"https://api.callmebot.com/whatsapp.php?phone={self.phone}&text={msg}&apikey={self.apikey}"
        try:
            resp = requests.get(url)
            if hasattr(resp, "status_code"):
                ok = resp.status_code == 200
            else:
                ok = True
            print("WhatsApp send ->", "OK" if ok else "ERR")
            try:
                resp.close()
            except:
                pass
            return ok
        except Exception as e:
            print("WhatsApp send error:", e)
            return False

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send(self, message):
        url_msg = str(message).replace(" ", "%20")
        url = f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&text={url_msg}"
        try:
            resp = requests.get(url)
            if hasattr(resp, "status_code"):
                ok = resp.status_code == 200
            else:
                ok = True
            print("Telegram send ->", "OK" if ok else "ERR")
            try:
                resp.close()
            except:
                pass
            return ok
        except Exception as e:
            print("Telegram send error:", e)
            return False

# ===== Sensors =====
class DHT22Sensor:
    def __init__(self, pin_no):
        self.pin = Pin(pin_no)
        self.sensor = dht.DHT22(self.pin)

    def read(self):
        """Return (temp_c, hum_percent) or (None, None) on failure."""
        try:
            self.sensor.measure()
            t = self.sensor.temperature()
            h = self.sensor.humidity()
            # Cast to float for calculations
            return float(t), float(h)
        except Exception as e:
            print("DHT read error:", e)
            return None, None

class SoilMoisture:
    def __init__(self, analog_pin, dry=DRY_VALUE, wet=WET_VALUE):
        self.adc = ADC(Pin(analog_pin))
        self.dry = int(dry)
        self.wet = int(wet)

    def read_raw(self):
        return int(self.adc.read_u16())

    def read_percent(self):
        raw = self.read_raw()
        # Guard: if same values or inverted config:
        if self.wet >= self.dry:
            # misconfigured calibration; clamp and return 0-100 via a safe mapping
            pct = 0 if raw >= self.dry else 100
        else:
            if raw >= self.dry:
                pct = 0
            elif raw <= self.wet:
                pct = 100
            else:
                # compute percentage step by step to reduce arithmetic mistakes:
                numer = raw - self.wet
                denom = self.dry - self.wet
                frac = numer / denom   # 0..1
                pct = 100 - (frac * 100)
        return int(pct), raw

class TDSSensor:
    def __init__(self, analog_pin, vref=3.3):
        self.adc = ADC(Pin(analog_pin))
        self.vref = float(vref)

    def read_raw(self):
        return int(self.adc.read_u16())

    def read_tds(self, temperature_c=25.0):
        """
        Convert ADC raw to voltage, then to EC and approximate TDS (ppm).
        This is a rough approximation — calibrate with known standards for accuracy.
        """
        raw = self.read_raw()
        # ADC range is 0..65535
        voltage = (raw / 65535.0) * self.vref  # volts
        # EC calculation: this depends on your probe & circuit; we use a demo constant
        # ec (mS/cm) ~ (voltage * 1000) / K where K is a resistance/scale constant.
        # Use K = 560 as in original; then convert with temperature compensation.
        K = 560.0
        ec = (voltage * 1000.0) / K  # mS/cm (approx)
        # Temperature compensation: coeff ~ 2% per degC
        compensation_coeff = 1.0 + 0.02 * (temperature_c - 25.0)
        if compensation_coeff == 0:
            ec_25 = ec
        else:
            ec_25 = ec / compensation_coeff
        # Convert EC to TDS (typical factor ~0.5 - 0.7). We'll use 0.5 here.
        tds = ec_25 * 0.5 * 1000.0  # convert to ppm (scaled)
        # Round into reasonable values
        return {
            "raw": raw,
            "voltage": round(voltage, 3),
            "ec": round(ec_25, 3),
            "tds": int(round(tds)),
        }

# ===== LED controller =====
class LEDController:
    def __init__(self, pin_no):
        self.led = Pin(pin_no, Pin.OUT)
        self.off()

    def on(self):
        self.led.value(1)

    def off(self):
        self.led.value(0)

    def blink(self, times=3, on_s=0.2, off_s=0.2):
        for _ in range(times):
            self.on()
            time.sleep(on_s)
            self.off()
            time.sleep(off_s)

# ===== Main =====
def main():
    print("Starting system...")

    # Initialize hardware
    led = LEDController(LED_PIN)
    dht_sensor = DHT22Sensor(DHT_PIN)
    soil = SoilMoisture(SOIL_ADC_PIN, dry=DRY_VALUE, wet=WET_VALUE)
    tds = TDSSensor(TDS_ADC_PIN)

    # Connect WiFi (optional but needed for notifications)
    wifi_ok = False
    try:
        wifi_ok = WiFi.connect(SSID, PASSWORD)
    except Exception as e:
        print("WiFi connect exception:", e)

    # Notifiers
    wa = WhatsAppNotifier(CALLMEBOT_PHONE, CALLMEBOT_APIKEY)
    tg = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

    last_alert_time = 0

    print("Entering main loop. Press Ctrl-C to stop.")
    try:
        cycle = 0
        while True:
            cycle += 1
            print("\n--- Cycle", cycle, " ---")
            # Read sensors
            temp, hum = dht_sensor.read()
            soil_pct, soil_raw = soil.read_percent()
            tds_info = tds.read_tds(temperature_c=(temp if temp is not None else 25.0))
            tds_ppm = tds_info["tds"]

            # Print readings
            now = time.localtime()
            print("Time:", now)
            print("DHT -> Temp: {} C, Humidity: {} %".format(temp, hum))
            print("Soil -> Raw: {}, Moisture: {}%".format(soil_raw, soil_pct))
            print("TDS -> Raw: {}, Voltage: {} V, EC: {} (mS/cm), TDS: {} ppm".format(
                tds_info["raw"], tds_info["voltage"], tds_info["ec"], tds_info["tds"]
            ))

            # Determine status & alerts
            alerts = []
            if temp is None or hum is None:
                alerts.append("Sensor error: DHT22 read failed.")
            else:
                if temp > TEMP_HIGH_LIMIT:
                    alerts.append(f"High temperature: {temp} C (limit {TEMP_HIGH_LIMIT} C)")
                if hum < HUM_LOW_LIMIT:
                    alerts.append(f"Low humidity: {hum}% (limit {HUM_LOW_LIMIT}%)")

            if soil_pct < DRY_THRESHOLD:
                alerts.append(f"Soil dry: {soil_pct}% (threshold {DRY_THRESHOLD}%)")
            elif soil_pct > WET_THRESHOLD:
                alerts.append(f"Soil wet: {soil_pct}% (threshold {WET_THRESHOLD}%)")

            if tds_ppm > TDS_HIGH_LIMIT:
                alerts.append(f"High TDS: {tds_ppm} ppm (limit {TDS_HIGH_LIMIT} ppm)")

            # LED logic
            if alerts:
                print("ALERTS:", alerts)
                led.blink(times=3, on_s=0.15, off_s=0.15)
            else:
                print("All readings normal.")
                # short heartbeat blink
                led.blink(times=1, on_s=0.05, off_s=0.05)

            # Send notifications if needed and cooldown passed
            now_ts = time.time()
            if alerts and (now_ts - last_alert_time) >= ALERT_COOLDOWN:
                alert_msg = " | ".join(alerts)
                # Always attempt to send (if wifi_ok)
                if wifi_ok:
                    if SEND_BOTH:
                        try:
                            wa.send(alert_msg)
                        except Exception as e:
                            print("WA send exception:", e)
                        try:
                            tg.send(alert_msg)
                        except Exception as e:
                            print("TG send exception:", e)
                    else:
                        # fallback to WhatsApp only
                        try:
                            wa.send(alert_msg)
                        except Exception as e:
                            print("WA send exception:", e)
                else:
                    print("Skipping network alerts: WiFi not connected.")
                last_alert_time = now_ts
            else:
                if alerts:
                    print("Alert suppressed due to cooldown.")

            # Wait until next sample
            safe_sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("Stopping monitoring (user interrupt).")
        led.off()

if __name__ == "__main__":
    main()
