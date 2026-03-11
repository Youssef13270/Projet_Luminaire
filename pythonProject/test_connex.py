import smbus2
import time

bus = smbus2.SMBus(1)
address = 0x48

while True:
    # On lit l'entrée AIN3 (la vis bleue)
    bus.write_byte(address, 0x43)
    bus.read_byte(address)  # Lecture de vidage
    valeur = bus.read_byte(address)

    print(f"Valeur brute lue : {valeur}")
    time.sleep(0.2)