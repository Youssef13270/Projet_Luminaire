import sys
import smbus2  # Bibliothèque I2C pour Raspberry Pi
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QProgressBar, QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont


class IHM_Luminaire_Pro(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- CONFIGURATION I2C (Vital pour la com avec l'étudiant EC) ---
        # Tu as trouvé 48 dans le scan, donc l'adresse est 0x48
        self.I2C_ADRESSE = 0x48

        # Ouvre le port I2C du Raspberry (Pin 3 et 5)
        try:
            self.bus = smbus2.SMBus(1)
            print("Connexion au bus I2C réussie.")
        except Exception as e:
            print(f"Erreur d'ouverture du bus I2C : {e}")

        # --- REGISTRES (DEMANDE A L'ETUDIANT EC DE CONFIRMER CES NUMEROS !) ---
        self.REG_TENSION = 0x10  # Case mémoire pour la Tension
        self.REG_TEMP = 0x11  # Case mémoire pour la Température
        self.REG_COURANT = 0x12  # Case mémoire pour le Courant
        self.REG_ETAT = 0x13  # Case mémoire pour ON/OFF (1=ON, 0=OFF)

        # Variables initiales
        self.tension_actuelle = 0.0
        self.temperature_actuelle = 0.0

        # --- CONFIGURATION FENÊTRE ---
        self.setWindowTitle("Supervision Luminaire - Interface Réelle")
        self.setGeometry(0, 0, 800, 480)  # Taille écran tactile
        # Decommente la ligne dessous pour mettre en plein écran "Mode Kiosque"
        # self.showFullScreen()

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: white; font-family: 'Arial'; }
            QProgressBar { 
                border: 2px solid #444; 
                border-radius: 8px; 
                background-color: #2d2d2d;
                text-align: center; 
                color: white; 
                font-weight: bold;
            }
            QProgressBar::chunk { border-radius: 5px; }
        """)

        # --- CONSTRUCTION DE L'INTERFACE ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout()
        central_widget.setLayout(layout_principal)

        # 1. TITRE
        header = QLabel("SUPERVISION SMARTLIGHT")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 26, QFont.Bold))
        header.setStyleSheet("color: #00E676; margin-bottom: 10px;")
        layout_principal.addWidget(header)

        # 2. GRILLE (Organisation des blocs)
        grid = QGridLayout()
        grid.setSpacing(20)
        layout_principal.addLayout(grid)

        # --- COLONNE GAUCHE (BATTERIE & TEMP) ---

        # Carte Batterie
        frame_batt = self.creer_carte("BATTERIE")
        layout_batt = QVBoxLayout()
        self.lbl_tension = QLabel("0.0 V")
        self.lbl_tension.setAlignment(Qt.AlignCenter)
        self.lbl_tension.setFont(QFont("Arial", 30, QFont.Bold))
        self.lbl_tension.setStyleSheet("color: #4fc3f7;")
        self.barre_batterie = QProgressBar()
        self.barre_batterie.setRange(0, 100)
        self.barre_batterie.setValue(0)
        self.barre_batterie.setFixedHeight(25)
        layout_batt.addWidget(self.lbl_tension)
        layout_batt.addWidget(self.barre_batterie)
        frame_batt.setLayout(layout_batt)
        grid.addWidget(frame_batt, 0, 0)

        # Carte Température
        frame_temp = self.creer_carte("TEMPÉRATURE")
        layout_temp = QVBoxLayout()
        self.lbl_temp = QLabel("0.0 °C")
        self.lbl_temp.setAlignment(Qt.AlignCenter)
        self.lbl_temp.setFont(QFont("Arial", 30, QFont.Bold))
        self.lbl_temp.setStyleSheet("color: #ffb74d;")
        layout_temp.addWidget(self.lbl_temp)
        frame_temp.setLayout(layout_temp)
        grid.addWidget(frame_temp, 1, 0)

        # --- COLONNE DROITE (ETAT & BOUTONS) ---

        # Carte État
        frame_etat = self.creer_carte("ÉTAT DU LUMINAIRE")
        layout_etat = QVBoxLayout()
        self.lbl_etat = QLabel("INCONNU")
        self.lbl_etat.setAlignment(Qt.AlignCenter)
        self.lbl_etat.setFont(QFont("Arial", 24, QFont.Bold))
        self.lbl_etat.setStyleSheet("color: gray; border: 2px solid gray; border-radius: 10px; padding: 10px;")
        self.lbl_courant = QLabel("Conso: -- mA")
        self.lbl_courant.setAlignment(Qt.AlignCenter)
        self.lbl_courant.setFont(QFont("Arial", 14))
        self.lbl_courant.setStyleSheet("color: #aaa; margin-top: 10px;")
        layout_etat.addWidget(self.lbl_etat)
        layout_etat.addWidget(self.lbl_courant)
        frame_etat.setLayout(layout_etat)
        grid.addWidget(frame_etat, 0, 1)

        # Carte Contrôle (Boutons)
        frame_ctrl = self.creer_carte("PILOTAGE MANUEL")
        layout_ctrl = QHBoxLayout()
        self.btn_on = QPushButton("ON")
        self.btn_on.setFont(QFont("Arial", 16, QFont.Bold))
        self.btn_on.setStyleSheet("background-color: #2e7d32; color: white; border-radius: 10px; height: 60px;")
        self.btn_off = QPushButton("OFF")
        self.btn_off.setFont(QFont("Arial", 16, QFont.Bold))
        self.btn_off.setStyleSheet("background-color: #c62828; color: white; border-radius: 10px; height: 60px;")

        self.btn_on.clicked.connect(self.envoyer_commande_on)
        self.btn_off.clicked.connect(self.envoyer_commande_off)

        layout_ctrl.addWidget(self.btn_on)
        layout_ctrl.addWidget(self.btn_off)
        frame_ctrl.setLayout(layout_ctrl)
        grid.addWidget(frame_ctrl, 1, 1)

        # --- TIMER DE LECTURE (C'est lui qui va chercher les infos toutes les secondes) ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.lecture_capteurs_i2c)
        self.timer.start(1000)  # 1000 ms = 1 seconde

    # --- DESIGN ---
    def creer_carte(self, titre):
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d; border-radius: 15px;")
        return frame

    # --- ENVOI DE COMMANDES (ECRITURE I2C) ---
    def envoyer_commande_on(self):
        try:
            # Ecrit '1' dans le registre 0x13 pour dire "Allume-toi"
            self.bus.write_byte_data(self.I2C_ADRESSE, self.REG_ETAT, 1)
            print("Commande ON envoyée au registre 0x13")

            # On met à jour l'affichage tout de suite pour être réactif
            self.lbl_etat.setText("ALLUMÉ")
            self.lbl_etat.setStyleSheet(
                "color: #00E676; border: 2px solid #00E676; border-radius: 10px; padding: 10px;")
        except Exception as e:
            print(f"Erreur envoi ON : {e}")

    def envoyer_commande_off(self):
        try:
            # Ecrit '0' dans le registre 0x13 pour dire "Eteins-toi"
            self.bus.write_byte_data(self.I2C_ADRESSE, self.REG_ETAT, 0)
            print("Commande OFF envoyée au registre 0x13")

            self.lbl_etat.setText("ÉTEINT")
            self.lbl_etat.setStyleSheet("color: gray; border: 2px solid gray; border-radius: 10px; padding: 10px;")
        except Exception as e:
            print(f"Erreur envoi OFF : {e}")

    # --- LECTURE DES DONNÉES (LECTURE I2C) ---
    def lecture_capteurs_i2c(self):
        try:
            # 1. Lecture TENSION (Registre 0x10)
            # On suppose que l'EC envoie la valeur x10 (ex: 125 pour 12.5V)
            val_tension = self.bus.read_byte_data(self.I2C_ADRESSE, self.REG_TENSION)
            self.tension_actuelle = val_tension / 10.0

            # 2. Lecture TEMPÉRATURE (Registre 0x11)
            val_temp = self.bus.read_byte_data(self.I2C_ADRESSE, self.REG_TEMP)
            self.temperature_actuelle = float(val_temp)

            # 3. Lecture COURANT (Registre 0x12)
            # Attention : un octet ne va que jusqu'à 255.
            val_courant = self.bus.read_byte_data(self.I2C_ADRESSE, self.REG_COURANT)
            courant_ma = val_courant * 10  # On suppose une echelle x10
            self.lbl_courant.setText(f"Conso: {courant_ma} mA")

            # --- Mise à jour de l'affichage ---
            self.lbl_tension.setText(f"{self.tension_actuelle} V")
            self.lbl_temp.setText(f"{self.temperature_actuelle} °C")

            # Gestion de la barre verte/orange/rouge
            pourcentage = int((self.tension_actuelle - 11.5) / (13.5 - 11.5) * 100)
            pourcentage = max(0, min(100, pourcentage))  # Bloque entre 0 et 100
            self.barre_batterie.setValue(pourcentage)

            if pourcentage > 50:
                c = "#00E676"
            elif pourcentage > 20:
                c = "#FFCA28"
            else:
                c = "#F44336"

            self.barre_batterie.setStyleSheet(f"""
                QProgressBar {{ border: 2px solid #444; border-radius: 8px; background-color: #2d2d2d; text-align: center; color: white; }}
                QProgressBar::chunk {{ background-color: {c}; border-radius: 6px; }}
            """)

        except Exception as e:
            # Cette erreur s'affiche si la carte EC ne répond pas ou est débranchée
            print(f"Erreur lecture I2C : {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = IHM_Luminaire_Pro()
    fenetre.show()
    sys.exit(app.exec_())