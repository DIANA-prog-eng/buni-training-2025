"""
    ----------------------------------------------------------------------------
    DHT22 SENSOR READING
    > Components:
        - Raspberry Pi Pico MCU
        - DHT22 sensor.
    > Operation:
        - Read temperature and humidity using Raspberry Pi Pico
        - Display the read value in the console
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

# ===== CONFIGURATION =====
DHT_PIN = 10                    # GPIO pin connected to DHT22 data pin
READ_INTERVAL = 5.0             # Seconds between readings
DECIMAL_PLACES = 2              # Number of decimal places for rounding

# ===== SENSOR SETUP =====
# Initialize DHT22 sensor on specified pin
# Pin.PULL_UP enables internal pull-up resistor for stable readings
dht_sensor = PicoDHT22(Pin(DHT_PIN, Pin.IN, Pin.PULL_UP))

# ===== FUNCTION DEFINITIONS =====
def read_sensor_data():
    """
    Reads temperature and humidity data from DHT22 sensor
    Returns: tuple (temperature, humidity) or (None, None) if reading fails
    """
    try:
        # Read raw temperature and humidity values from sensor
        temperature, humidity = dht_sensor.read()

        # Check for valid readings (DHT22 returns None on failure)
        if temperature is None or humidity is None:
            print("Error: Failed to read from DHT22 sensor")
            return None, None

        # Round values to specified decimal places
        temperature = round(temperature, DECIMAL_PLACES)
        humidity = round(humidity, DECIMAL_PLACES)

        # Display formatted results on serial monitor
        print(f" Temperature: {temperature} °C")
        print(f" Humidity: {humidity} %")
        print("─" * 30)  # Separator line for better readability

        return temperature, humidity

    except Exception as error:
        print(f"Sensor Error: {error}")
        return None, None

def main():
    """
    Main program execution - continuously reads sensor data
    """
    print("DHT22 Environmental Sensor Monitor")
    print("==================================")
    print(f"Reading sensor on GPIO pin {DHT_PIN}")
    print(f"Update interval: {READ_INTERVAL} seconds")
    print("Press Ctrl+C to stop the program")
    print("─" * 50)

    reading_count = 0

    # Main program loop
    while True:
        reading_count += 1
        print(f"Reading #{reading_count}:")

        # Read sensor data
        temperature, humidity = read_sensor_data()

        # Optional: Add a simple control handler here
        if temperature is not None and humidity is not None:
            # Example: Simple comfort level check
            if temperature > 30:
                print("Hot environment detected!")
            elif humidity > 80:
                print("High humidity detected!")

        # Wait before next reading
        sleep(READ_INTERVAL)

# ===== PROGRAM EXECUTION =====
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
