import serial

# UART5 correspond généralement à /dev/ttyAMA1 après activation
try:
    ser = serial.Serial("/dev/ttyAMA1", 9600, timeout=1)
    print("Lecture sur UART5 (Pins 32/33) activée...")
    print("Envoyez une donnée depuis TeraTerm (PC)...")

    while True:
        ligne = ser.readline().decode('utf-8', errors='ignore').strip()
        if ligne:
            print(f"Reçu : {ligne}")
except Exception as e:
    print(f"Erreur : {e}")