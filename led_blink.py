"""
    ----------------------------------------------------------------------------
    SIMPLE LED BLINK CONTROLER
    > Components:
        - Raspberry Pi Pico MCU
        - Onboard LED.
    > Operation:
        - Blink LED at different set internals
    ---
    Author: Angaza Elimu - Buni Team
    Version: 1.0.025
    ----------------------------------------------------------------------------
"""

from machine import Pin
from time import sleep

# ===== CONFIGURATION =====
LED_PIN = 12           # GPIO pin where LED is connected
BLINK_COUNT = 5        # Number of times to blink
ON_DURATION = 2.0      # Seconds to keep LED ON
OFF_DURATION = 2.0     # Seconds to keep LED OFF

# ===== HARDWARE SETUP =====
# Initialize LED on specified pin as output
led = Pin(LED_PIN, Pin.OUT)

# ===== FUNCTION DEFINITIONS =====
def blink_led():
    """
    Blinks the LED once - turns ON, waits, then OFF, waits
    """
    led.value(1)              # Turn LED ON (send HIGH signal)
    sleep(ON_DURATION)        # Keep LED ON for specified time
    led.value(0)              # Turn LED OFF (send LOW signal)
    sleep(OFF_DURATION)       # Keep LED OFF for specified time

def main():
    """
    Main program execution - blinks LED specified number of times
    """
    print(f"Starting LED blink program...")
    print(f"LED will blink {BLINK_COUNT} times")

    # Blink loop
    for blink_number in range(BLINK_COUNT):
        print(f"Blink #{blink_number + 1}")
        blink_led()

    print("Program completed!")

# ===== PROGRAM EXECUTION =====
if __name__ == "__main__":
    main()
