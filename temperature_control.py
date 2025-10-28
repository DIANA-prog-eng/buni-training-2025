"""
    ----------------------------------------------------------------------------
    TEMPERATURE CONTROL SYSTEM:
    > Components:
        - Raspberry Pi Pico MCU
        - DHT22 sensor, Relay and signal LED
    > Operation:
        - Monitor temperature against a set threshold
        - Activates relay and turns ON signal LED when temperature exceeds set threshold.
        - Deactivates relay and turns OFF signal LED when temperature normalizes
    ---
    Author: Angaza Elimu - Buni Team
    Version: 1.0.025
    ----------------------------------------------------------------------------
"""

# ===== IMPORT ESSENTIALS =====
import machine
from time import sleep
from machine import Pin
from PicoDHT22 import PicoDHT22
from pcf8574 import *

# ===== CONFIGURATION =====
# --- LED ---
LED_PIN = 12           # GPIO pin where LED is connected
ON_STATE = 1           # led on state value
OFF_STATE = 0          # led off state value

# --- DHT22 ---
DHT_PIN = 10                    # GPIO pin connected to DHT22 data pin
RELAY_PIN = PCF8574_PIN.RELAY1_PIN  # Relay pin on PCF8574 expander
TEMPERATURE_THRESHOLD = 30.0    # Temperature trigger point in °C
READ_INTERVAL = 10.0             # Seconds between sensor readings

# ===== HARDWARE SETUP =====
# Initialize LED on specified pin as output
led = Pin(LED_PIN, Pin.OUT)

# Initialize DHT22 temperature sensor
dht_sensor = PicoDHT22(Pin(DHT_PIN, Pin.IN, Pin.PULL_UP))

# Initialize Relay 1 on PCF8574 I/O expander
relay = PCF8574_PIN(RELAY_PIN, PCF8574_PIN.OUT)

# ===== VARIABLE INITIALIZATION =====
current_relay_state = False  # Track whether relay is currently ON or OFF

# ===== FUNCTION DEFINITIONS =====

# --- Control led blink ---
def blink_led(led_state):
    """
    Toggle LED between ON/OFF states
    """
    led.value(led_state)     # Turn LED ON/OFF (send HIGH/LOW signal)

# --- dht22 sensor read handler ---
def read_temperature():
    """
    Reads temperature from DHT22 sensor
    Returns: temperature in °C or None if reading fails
    """
    try:
        temperature, humidity = dht_sensor.read()

        # Check if reading was successful
        if temperature is None:
            print("Failed to read temperature from sensor")
            return None

        # Round to 1 decimal place for readability
        temperature = round(temperature, 1)
        return temperature

    except Exception as error:
        print(f"Sensor Error: {error}")
        return None

# --- relay control handler ---
def control_relay_based_on_temperature(temperature):
    """
    Controls relay based on temperature reading
    Turns relay ON if temperature > threshold, OFF if temperature < threshold
    """
    global current_relay_state

    if temperature > TEMPERATURE_THRESHOLD:
        # Temperature is ABOVE threshold - activate cooling
        if not current_relay_state:
            print(f"Temperature {temperature}°C > {TEMPERATURE_THRESHOLD}°C")
            print("ACTIVATING RELAY - Turning on cooling device")
            relay.toggle()  # Turn relay ON
            current_relay_state = True

            # toogle led ON
            blink_led(ON_STATE)
    else:
        # Temperature is BELOW threshold - deactivate cooling
        if current_relay_state:
            print(f"Temperature {temperature}°C ≤ {TEMPERATURE_THRESHOLD}°C")
            print("DEACTIVATING RELAY - Turning off cooling device")
            relay.toggle()  # Turn relay OFF
            current_relay_state = False

            # toogle led OFF
            blink_led(OFF_STATE)


def display_status(temperature, humidity):
    """
    Displays current system status on serial monitor
    """
    print("\n" + "="*40)
    print("TEMPERATURE CONTROL SYSTEM")
    print("="*40)

    if temperature is not None:
        print(f"Current Temperature: {temperature}°C")
        print(f"Current Humidity: {humidity}%")
        print(f"Temperature Threshold: {TEMPERATURE_THRESHOLD}°C")

        # Show relay status with appropriate icon
        relay_status = "ON" if current_relay_state else "OFF"
        print(f"Relay Status: {relay_status}")

        # Show current action needed
        if temperature > TEMPERATURE_THRESHOLD:
            print("Action: Cooling required")
        else:
            print("Action: Temperature normal")
    else:
        print("No sensor data available")

    print("="*40)

def main():
    """
    Main program execution - continuously monitors temperature and controls relay
    """
    print("Starting DHT22 Temperature Controller")
    print(f"Temperature threshold: {TEMPERATURE_THRESHOLD}°C")
    print(f"Reading interval: {READ_INTERVAL} seconds")
    print("Relay will activate when temperature > threshold")
    print("Press Ctrl+C to stop the program\n")

    reading_count = 0

    # Main control loop
    while True:
        reading_count += 1
        print(f"\nReading #{reading_count}")

        # Read sensor data
        temperature = read_temperature()

        # If reading successful, control relay and display status
        if temperature is not None:
            humidity = round(dht_sensor.read()[1], 1)  # Get humidity for display

            # Control relay based on temperature
            control_relay_based_on_temperature(temperature)

            # Display current system status
            display_status(temperature, humidity)
        else:
            print("Retrying sensor reading...")

        # Wait before next reading
        sleep(READ_INTERVAL)

# ===== PROGRAM EXECUTION =====
if __name__ == "__main__":
    try:
        # Start with relay OFF
        print("Initializing system...")
        if current_relay_state:  # Ensure relay starts in OFF position
            relay.toggle()
            current_relay_state = False
        print("System initialized - Relay is OFF")

        main()

    except KeyboardInterrupt:
        print("\n\nProgram stopped by user")
        # Ensure relay is turned off when program exits
        if current_relay_state:
            relay.toggle()
            print("Relay turned OFF for safety")
        print("Goodbye!")

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        # Safety: Ensure relay is off on error
        if current_relay_state:
            relay.toggle()
