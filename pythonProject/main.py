import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,QHBoxLayout, QLabel, QProgressBar, QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor


class IHM_Luminaire_Pro(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- VARIABLES DE SIMULATION ---
        self.tension_actuelle = 12.8  # Batterie pleine au départ
        self.temperature_actuelle = 22.0  # Température ambiante

        # --- CONFIGURATION FENÊTRE ---
        self.setWindowTitle("Supervision Luminaire - Interface IR3")
        self.setGeometry(100, 100, 900, 550)  # Un peu plus grand
        # Feuille de style globale (CSS) pour un look moderne
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: white; font-family: 'Segoe UI', Arial; }
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

        # 1. TITRE (Header)
        header = QLabel("SUPERVISION SMARTLIGHT")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Segoe UI", 26, QFont.Bold))
        header.setStyleSheet("color: #00E676; letter-spacing: 2px; margin-top: 10px; margin-bottom: 20px;")
        layout_principal.addWidget(header)

        # 2. CORPS (Grid Layout pour diviser en 2 colonnes)
        grid = QGridLayout()
        grid.setSpacing(20)  # Espace entre les cases
        layout_principal.addLayout(grid)

        # --- COLONNE GAUCHE : BATTERIE & SYSTEME ---

        # Carte Batterie
        frame_batt = self.creer_carte("BATTERIE")
        layout_batt = QVBoxLayout()

        self.lbl_tension = QLabel(f"{self.tension_actuelle} V")
        self.lbl_tension.setAlignment(Qt.AlignCenter)
        self.lbl_tension.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.lbl_tension.setStyleSheet("color: #4fc3f7;")  # Bleu clair

        self.barre_batterie = QProgressBar()
        self.barre_batterie.setRange(0, 100)
        self.barre_batterie.setValue(80)
        self.barre_batterie.setFixedHeight(25)

        layout_batt.addWidget(self.lbl_tension)
        layout_batt.addWidget(self.barre_batterie)
        frame_batt.setLayout(layout_batt)
        grid.addWidget(frame_batt, 0, 0)  # Ligne 0, Colonne 0

        # Carte Température
        frame_temp = self.creer_carte("TEMPÉRATURE")
        layout_temp = QVBoxLayout()

        self.lbl_temp = QLabel(f"{self.temperature_actuelle} °C")
        self.lbl_temp.setAlignment(Qt.AlignCenter)
        self.lbl_temp.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.lbl_temp.setStyleSheet("color: #ffb74d;")  # Orange clair

        layout_temp.addWidget(self.lbl_temp)
        frame_temp.setLayout(layout_temp)
        grid.addWidget(frame_temp, 1, 0)  # Ligne 1, Colonne 0

        # --- COLONNE DROITE : CONTROLE & LEDS ---

        # Carte État
        frame_etat = self.creer_carte("ÉTAT DU LUMINAIRE")
        layout_etat = QVBoxLayout()

        self.lbl_etat = QLabel("ÉTEINT")
        self.lbl_etat.setAlignment(Qt.AlignCenter)
        self.lbl_etat.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_etat.setStyleSheet("color: #EF5350; border: 2px solid #EF5350; border-radius: 10px; padding: 10px;")

        self.lbl_courant = QLabel("Conso: 0 mA")
        self.lbl_courant.setAlignment(Qt.AlignCenter)
        self.lbl_courant.setFont(QFont("Segoe UI", 14))
        self.lbl_courant.setStyleSheet("color: #aaa; margin-top: 10px;")

        layout_etat.addWidget(self.lbl_etat)
        layout_etat.addWidget(self.lbl_courant)
        frame_etat.setLayout(layout_etat)
        grid.addWidget(frame_etat, 0, 1)  # Ligne 0, Colonne 1

        # Carte Boutons (Control)
        frame_ctrl = self.creer_carte("PILOTAGE MANUEL")
        layout_ctrl = QHBoxLayout()  # Horizontal pour mettre les boutons côte à côte

        self.btn_on = QPushButton("ON")
        self.btn_on.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.btn_on.setCursor(Qt.PointingHandCursor)
        self.btn_on.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: white; border-radius: 10px; height: 60px; }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:pressed { background-color: #1b5e20; }
        """)

        self.btn_off = QPushButton("OFF")
        self.btn_off.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.btn_off.setCursor(Qt.PointingHandCursor)
        self.btn_off.setStyleSheet("""
            QPushButton { background-color: #c62828; color: white; border-radius: 10px; height: 60px; }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:pressed { background-color: #b71c1c; }
        """)

        # Connexions
        self.btn_on.clicked.connect(self.action_allumer)
        self.btn_off.clicked.connect(self.action_eteindre)

        layout_ctrl.addWidget(self.btn_on)
        layout_ctrl.addWidget(self.btn_off)
        frame_ctrl.setLayout(layout_ctrl)
        grid.addWidget(frame_ctrl, 1, 1)  # Ligne 1, Colonne 1

        # --- TIMER SIMULATION ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(500)  # Mise à jour toutes les 500ms

    # --- DESIGN ---
    def creer_carte(self, titre_texte):
        """Crée un joli cadre avec un titre"""
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d; border-radius: 15px;")

        layout_interne = QVBoxLayout()
        # Titre de la carte
        lbl = QLabel(titre_texte)
        lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl.setStyleSheet("color: #888; margin-bottom: 5px;")
        lbl.setAlignment(Qt.AlignCenter)

        # Conteneur pour le contenu spécifique
        contenu = QWidget()

        # On ne met pas de layout au frame directement ici, on le fait à l'extérieur
        # Mais pour simplifier l'ajout du titre, on va tricher un peu dans l'usage :
        # Je retourne le frame, mais je prépare le layout qui recevra les widgets.
        return frame

    # --- ACTIONS ---
    def action_allumer(self):
        if self.tension_actuelle > 11.6:
            self.lbl_etat.setText("ALLUMÉ")
            self.lbl_etat.setStyleSheet(
                "color: #00E676; border: 2px solid #00E676; border-radius: 10px; padding: 10px;")
        else:
            self.lbl_etat.setText("BATTERIE VIDE")
            self.lbl_etat.setStyleSheet("color: orange; border: 2px solid orange; border-radius: 10px; padding: 10px;")

    def action_eteindre(self):
        self.lbl_etat.setText("ÉTEINT")
        self.lbl_etat.setStyleSheet("color: #EF5350; border: 2px solid #EF5350; border-radius: 10px; padding: 10px;")
        self.lbl_courant.setText("Conso: 0 mA")

    # --- SIMULATION INTELLIGENTE ---
    def update_simulation(self):
        est_allume = (self.lbl_etat.text() == "ALLUMÉ")

        # 1. Logique Physique
        if est_allume:
            self.tension_actuelle -= 0.02  # Baisse
            self.temperature_actuelle += 0.1  # Chauffe
            courant = random.randint(345, 355)
            self.lbl_courant.setText(f"Conso: {courant} mA")
        else:
            self.tension_actuelle += 0.02  # Charge
            self.temperature_actuelle -= 0.1  # Refroidit
            self.lbl_courant.setText("Conso: 0 mA")

        # 2. Bornes (Limites)
        self.tension_actuelle = max(11.5, min(13.5, self.tension_actuelle))
        self.temperature_actuelle = max(15.0, min(50.0, self.temperature_actuelle))

        # 3. Sécurité Coupure
        if self.tension_actuelle <= 11.5 and est_allume:
            self.action_eteindre()

        # 4. Affichage arrondi
        v_round = round(self.tension_actuelle, 2)
        t_round = round(self.temperature_actuelle, 1)

        self.lbl_tension.setText(f"{v_round} V")
        self.lbl_temp.setText(f"{t_round} °C")

        # 5. Gestion Barre Batterie (Couleur dynamique)
        pourcentage = int((v_round - 11.5) / (13.5 - 11.5) * 100)
        self.barre_batterie.setValue(pourcentage)

        if pourcentage > 50:
            c = "#00E676"  # Vert
        elif pourcentage > 20:
            c = "#FFCA28"  # Orange
        else:
            c = "#F44336"  # Rouge

        self.barre_batterie.setStyleSheet(f"""
            QProgressBar {{ 
                border: 2px solid #444; 
                border-radius: 8px; 
                background-color: #2d2d2d;
                text-align: center; 
                color: white; 
            }}
            QProgressBar::chunk {{ 
                background-color: {c}; 
                border-radius: 6px;
            }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = IHM_Luminaire_Pro()
    fenetre.show()
    sys.exit(app.exec_())

