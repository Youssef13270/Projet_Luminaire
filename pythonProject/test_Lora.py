import serial
import time
while True:

    # --- CONFIGURATION ---
    # On utilise le port série relié aux pins 8 et 10
    port_serie = '/dev/serial0'
    vitesse = 9600

    print(f"🔌 Ouverture du port {port_serie}...")

    try:
        # Initialisation de la connexion série
        ser = serial.Serial(port_serie, vitesse, timeout=2)


        # Fonction pour envoyer une commande et lire la réponse
        def envoyer_commande(commande):
            print(f"\n[Envoi] : {commande}")
             # Le module a besoin de \r\n à la fin pour valider
            ser.write((commande + "\r\n").encode())

            # On attend un peu que le module réfléchisse
            time.sleep(1)  # Augmenter à 5s pour le JOIN si besoin

            # On lit tout ce que le module répond
            if ser.in_waiting > 0:
                reponse = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"[Réponse Module] :\n{reponse.strip()}")
                return reponse
            else:
                print("[Réponse Module] : (Aucune réponse - Vérifie les fils)")
                return ""


        # --- DÉBUT DU TEST ---

        # 1. Vérifier que le module est vivant
        envoyer_commande("AT")

        # 2. Vérifier la connexion au réseau LoRaWAN
        # Comme tu l'as déjà fait sur PC, il devrait dire "Joined" ou "Already joined"
        reponse_join = envoyer_commande("AT+JOIN")

        # 3. Envoyer les données (Seulement si connecté)
        if "Joined" in reponse_join or "joined" in reponse_join or "OK" in reponse_join:
            print("\n🚀 Tentative d'envoi du message '01 02 03' vers TTN...")

            # Commande standard pour envoyer de l'Hexadécimal
            # Le message est 01 02 03 (3 octets)
            envoyer_commande('AT+CMSGHEX="010203"')

            print("\n✅ Si tu as eu 'OK' ou 'Done', va voir sur le site The Things Network !")
        else:
            print("\n❌ Le module ne semble pas connecté au réseau. Relance le script ou vérifie l'antenne.")

        # Fermeture propre
        ser.close()

    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE : {e}")
        print("Conseil : Vérifie que le port série est activé dans 'sudo raspi-config' > Interface Options > Serial Port")
