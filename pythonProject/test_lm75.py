import serial
import smbus
import time

# --- CONFIGURATION ---
ADRESSE = 0x48
CANAL_LUMIERE = 0  # AIN0 (Jumper P5)
CANAL_TEMP = 1  # AIN1 (Jumper P4)
CANAL_MOLETTE = 3  # AIN3 (Jumper P6 - Parfois c'est le 2, tu verras)

# Initialisation
lora = serial.Serial('/dev/ttyS0', 9600, timeout=1)
bus = smbus.SMBus(1)


def lire_analogique(canal):
    try:
        bus.write_byte(ADRESSE, 0x40 + canal)
        bus.read_byte(ADRESSE)
        return bus.read_byte(ADRESSE)
    except:
        return 0


def envoyer_commande(cmd, attendre=1):
    print(f"📡 Envoi commande : {cmd}")
    lora.write((cmd + "\r\n").encode())
    time.sleep(attendre)

    # On lit la réponse du module
    reponse = ""
    if lora.in_waiting > 0:
        reponse = lora.read(lora.in_waiting).decode('utf-8', errors='ignore').strip()
        print(f"   👉 Réponse module : {reponse}")
    return reponse


# --- DÉMARRAGE SÉCURISÉ ---
print("\n🚀 DÉMARRAGE DU SYSTÈME...")

# 1. On réveille le module
envoyer_commande("AT")

# 2. ON FORCE LA CONNEXION (LE JOIN)
print("⏳ Tentative de connexion au réseau (JOIN)...")
envoyer_commande("AT+JOIN")

# 3. ON ATTEND 20 SECONDES (OBLIGATOIRE)
# Si on n'attend pas ici, le premier envoi plantera
for i in range(20, 0, -1):
    print(f"   Attente connexion... {i}s")
    time.sleep(1)

print("✅ Fin de l'attente. Démarrage de la boucle d'envoi !\n")

# --- BOUCLE PRINCIPALE ---
while True:
    try:
        # Lecture
        lum = lire_analogique(CANAL_LUMIERE)
        temp = lire_analogique(CANAL_TEMP)
        molette = lire_analogique(CANAL_MOLETTE)

        print(f"📊 Capteurs : Lum={lum} | Temp={temp} | Molette={molette}")

        # Encodage
        payload = "{:02X}{:02X}{:02X}".format(lum, temp, molette)

        # Envoi
        print(f"📦 Envoi du message : {payload}")
        reponse = envoyer_commande(f'AT+CMSGHEX="{payload}"', attendre=2)

        # Vérification d'erreur
        if "ERROR" in reponse or "Please Join" in reponse:
            print("❌ ERREUR : Le module n'est pas connecté ! Retentative de JOIN...")
            envoyer_commande("AT+JOIN")
            time.sleep(15)

        # Pause avant le prochain
        print("💤 Pause 30s...")
        time.sleep(30)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Erreur script : {e}")