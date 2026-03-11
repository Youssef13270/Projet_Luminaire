# Fichier: gestion_i2c.py
try:
    from smbus2 import SMBus # Bibliothèque pour Raspberry Pi
except ImportError:
    from unittest.mock import MagicMock
    SMBus = MagicMock # Pour ne pas planter sur PC Windows
    print("Mode PC : I2C simulé")

class CapteurLuminaire:
    def __init__(self, adresse=0x12): # 0x12 est un exemple, demande à l'étudiant EC !
        self.adresse = adresse
        self.bus = SMBus(1) # 1 = Bus I2C standard du Raspberry Pi

    def lire_tension(self):
        try:
            # On demande au registre 0x10 la tension (exemple)
            # data = self.bus.read_byte_data(self.adresse, 0x10)
            # return data / 10.0 # Si la valeur est envoyée en deciVolts
            return 12.5 # Valeur bidon en attendant le vrai matériel
        except:
            return 0.0

    def lire_courant(self):
        try:
            # data = self.bus.read_byte_data(self.adresse, 0x11)
            return 0
        except:
            return 0