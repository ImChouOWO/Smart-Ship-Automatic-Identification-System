import serial

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

while True:
    data = ser.readline().decode('utf-8').strip()
    if data:
        print(f"Received: {data}")
