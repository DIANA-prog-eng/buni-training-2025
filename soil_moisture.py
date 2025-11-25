"""
    ----------------------------------------------------------------------------
    MOISTURE MONITORING SYSTEM:
    > Components:
        - Raspberry Pi Pico MCU
        - Soil Moisture sensor,
    > Operation:
        - Monitor soil moisture against a set threshold
        - Displays moisture readings and alerts the farmer as per the readings
    ---
    Author: Eddie - Buni-IOT Training (Group II)
    Version: 1.0
    ----------------------------------------------------------------------------
"""

# Import the essenstials
import machine
from machine import Pin, ADC
import time

# configuration
ANALOG_PIN = 27          # GPIO27 for analog input (AO)

# Calibration value
DRY_VALUE = 65535         # Analog value when sensor is dry (in air)
WET_VALUE = 31405         # Analog value when sensor is in water

# Moisture thresholds (percentage)
DRY_THRESHOLD = 30       # Below this = dry warning
WET_THRESHOLD = 70       # Above this = wet warning

SAMPLE_INTERVAL = 5      # Seconds between readings


# Initialize analog pin (ADC)
adc = ADC(Pin(ANALOG_PIN))

def read_moisture_percentage():
    """
    Reads analog value and converts to percentage
    0% = completely dry, 100% = completely wet
    """
    analog_value = adc.read_u16()
    
    # Invert and map to percentage (lower value = more moisture)
    if analog_value >= DRY_VALUE:
        moisture = 0
    elif analog_value <= WET_VALUE:
        moisture = 100
    else:
        moisture = 100 - ((analog_value - WET_VALUE) * 100 / (DRY_VALUE - WET_VALUE))
    
    return int(moisture), analog_value

def get_moisture_status(percentage):
    """Returns status message based on moisture level"""
    if percentage < DRY_THRESHOLD:
        return "Soil is Dry - Water needed!"
    elif percentage > WET_THRESHOLD:
        return "Soil is Wet - Too much water!"
    else:
        return "Soil moisture is Optimal."

def calibrate_sensor():
    """Function to find the sensor's dry and wet values"""
    print("\----- CALIBRATION MODE -----")
    print("Remove sensor from soil (dry in air)")
    input("Press Enter when ready...")
    
    dry_readings = []
    for i in range(10):
        dry_readings.append(adc.read_u16())
        time.sleep(0.1)
    dry_avg = sum(dry_readings) // len(dry_readings)
    
    print(f"Dry value: {dry_avg}")
    print("\nNow submerge sensor in water")
    input("Press Enter when ready...")
    
    wet_readings = []
    for i in range(10):
        wet_readings.append(adc.read_u16())
        time.sleep(0.1)
    wet_avg = sum(wet_readings) // len(wet_readings)
    
    print(f"Wet value: {wet_avg}")
    print(f"\nUpdate these values in your code:")
    print(f"DRY_VALUE = {dry_avg}")
    print(f"WET_VALUE = {wet_avg}")
    print("---------------------\n")

# Main monitoring loop (continuously monitor soil moisture)
def monitor_soil():
    print("\n" + "="*50)
    print("SOIL MOISTURE MONITORING SYSTEM")
    print("-"*50)
    print(f"Dry Threshold: {DRY_THRESHOLD}% | Wet Threshold: {WET_THRESHOLD}%")
    print("-"*50 + "\n")
    
    try:
        while True:
            # Read moisture percentage
            moisture_pct, raw_value = read_moisture_percentage()
            
            # Get status message
            status = get_moisture_status(moisture_pct)
            
            # Print readings
            print(f"Time: {time.localtime()}")
            print(f"Analog Raw: {raw_value:4d} | Moisture: {moisture_pct:3d}% ]")
            print(f"Status: {status}")
            print("-" * 50)
            
            time.sleep(SAMPLE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n Monitoring stopped by user")

# ---------- RUN PROGRAM -----------
# Uncomment the next line to calibrate the sensor first
#calibrate_sensor()

# Start monitoring
monitor_soil()