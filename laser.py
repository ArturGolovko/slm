#laser
#pip install pyserial

import serial
import time

# === CONFIGURATION ===
COM_PORT = 'COM3'       # check our port first
BAUD_RATE = 115200
TIMEOUT = 1

# === COMMANDS ===
ACCESS_LEVEL_3 = b'c u 3 38845\r'
TURN_ON_LASER = b'e 1\r'
SET_CURRENT_79MA = b'c 3 79\r'
READ_CURRENT_STATUS = b'r r\r'

# === CONNECT TO LASER ===
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=TIMEOUT)
    time.sleep(2)  # Wait for port to initialize

    # === UNLOCK ACCESS LEVEL 3 ===
    print("[INFO] Unlocking access level 3...")
    ser.write(ACCESS_LEVEL_3)
    response = ser.readline().decode().strip()
    print(" → Response:", response)

    # === TURN LASER ON ===
    print("[INFO] Turning laser ON...")
    ser.write(TURN_ON_LASER)
    response = ser.readline().decode().strip()
    print(" → Response:", response)

    # === SET CURRENT TO 79 mA ===
    print("[INFO] Setting diode current to 79 mA...")
    ser.write(SET_CURRENT_79MA)
    response = ser.readline().decode().strip()
    print(" → Response:", response)

    # === OPTIONAL: Read current laser status ===
    print("[INFO] Reading laser status...")
    ser.write(READ_CURRENT_STATUS)
    response = ser.readline().decode().strip()
    print(" → Status:", response)

    # === DONE ===
    ser.close()
    print("[DONE] Laser command sequence completed.")

except Exception as e:
    print("[ERROR]", e)
