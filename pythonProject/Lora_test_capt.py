import serial
import time
import struct  # Pour convertir les nombres en hexadécimal

# --- CONFIGURATION LORA ---
# On utilise ttyS0 car c'est celui qui a marché pour toi
lora = serial.Serial('/dev/ttyS0', 9600, timeout=1)


# --- FONCTIONS UTILES ---

def envoyer_commande_lora(commande):
    # Envoie la commande au module
    lora.write((commande + "\r\n").encode())
    time.sleep(0.5)

    # Lit la réponse (optionnel, pour debug)
    if lora.in_waiting > 0:
        return lora.read(lora.in_waiting).decode('utf-8', errors='ignore').strip()
    return ""


def recuperer_donnees_capteur():
    # ⚠️ ICI : C'est là que tu mettras ton code de capteur I2C
    # Pour l'instant, je simule des valeurs fixes pour tester
    temperature = 24.5  # Exemple : 24.5°C
    humidite = 60.0  # Exemple : 60%

    # Si tu as ton code capteur, remplace les lignes au-dessus par :
    # temperature = bme280.temperature
    # humidite = bme280.humidity

    return temperature, humidite


# --- DÉMARRAGE ---
print("🚀 Démarrage du système LoRa...")

# On vérifie la connexion une fois au début
envoyer_commande_lora("AT")
reponse = envoyer_commande_lora("AT+JOIN")
print(f"État connexion : {reponse}")

time.sleep(2)  # Petite pause

# --- BOUCLE INFINIE (C'est parti !) ---
while True:
    try:
        # 1. Lire le capteur
        temp, hum = recuperer_donnees_capteur()
        print(f"\n🌡️ Mesure : {temp}°C | 💧 {hum}%")

        # 2. Préparer le message (Encodage)
        # On multiplie par 100 pour garder 2 chiffres après la virgule et virer le point
        valeur_temp = int(temp * 100)
        valeur_hum = int(hum * 100)

        # On transforme en Hexadécimal (4 caractères chaque chiffre)
        # {:04X} veut dire : Hexadécimal majuscule sur 4 chiffres
        payload_hex = "{:04X}{:04X}".format(valeur_temp, valeur_hum)

        print(f"📦 Envoi du paquet : {payload_hex}")
        # Exemple : Si Temp 24.50 et Hum 60.00 -> Envoie "09921770"

        # 3. Envoyer via LoRa
        commande = f'AT+CMSGHEX="{payload_hex}"'
        statut = envoyer_commande_lora(commande)

        print(f"📡 Réponse module : {statut}")

        # 4. Attendre avant le prochain envoi
        # ATTENTION : En LoRa, on n'a pas le droit de spammer.
        # Mets au moins 60 secondes en classe, ou 15s pour les tests rapides.
        print("⏳ Attente 30 secondes...")
        time.sleep(30)

    except Exception as e:
        print(f"Erreur : {e}")
        time.sleep(5)