import sys
import serial
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont


class IHM_Luminaire_Pro(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- VARIABLES ---
        self.buffer_serie = ""
        self.tension_actuelle = 0.0
        self.temperature_actuelle = 0.0
        self.compteur_lora = 0

        # --- CONFIGURATION LoRa (Pins 8/10) ---
        try:
            self.lora = serial.Serial('/dev/ttyS0', 9600, timeout=1)
            self.lora.write(b"AT+JOIN\r\n")
            print("LoRa initialisé sur /dev/ttyS0")
        except Exception as e:
            print(f"Erreur LoRa : {e}")
            self.lora = None

        # --- CONFIGURATION CAPTEURS (PC - Pins 32/33) ---
        try:
            self.ser_capteurs = serial.Serial('/dev/ttyAMA5', 9600, timeout=0.05)
            print("Lecture PC initialisée sur /dev/ttyAMA5")
        except Exception as e:
            print(f"Erreur Capteurs : {e}")
            self.ser_capteurs = None

        # --- DESIGN (Ton Style Original) ---
        self.setWindowTitle("Supervision Luminaire - IR3")
        self.setGeometry(100, 100, 900, 550)
        self.setStyleSheet("QMainWindow { background-color: #1e1e1e; } QLabel { color: white; }")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout(central_widget)

        # Grille de l'IHM
        grid = QGridLayout()
        layout_principal.addLayout(grid)

        # Carte Batterie
        frame_batt = self.creer_carte()
        layout_batt = QVBoxLayout(frame_batt)
        self.lbl_tension = QLabel("0.0 V")
        self.lbl_tension.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.barre_batterie = QProgressBar()
        layout_batt.addWidget(QLabel("BATTERIE"))
        layout_batt.addWidget(self.lbl_tension)
        layout_batt.addWidget(self.barre_batterie)
        grid.addWidget(frame_batt, 0, 0)

        # Carte Température
        frame_temp = self.creer_carte()
        layout_temp = QVBoxLayout(frame_temp)
        self.lbl_temp = QLabel("0.0 °C")
        self.lbl_temp.setFont(QFont("Segoe UI", 30, QFont.Bold))
        layout_temp.addWidget(QLabel("TEMPÉRATURE"))
        layout_temp.addWidget(self.lbl_temp)
        grid.addWidget(frame_temp, 1, 0)

        # Boutons État
        self.lbl_etat = QLabel("ÉTEINT")
        btn_on = QPushButton("ON")
        btn_off = QPushButton("OFF")
        btn_on.clicked.connect(lambda: self.lbl_etat.setText("ALLUMÉ"))
        btn_off.clicked.connect(lambda: self.lbl_etat.setText("ÉTEINT"))
        layout_principal.addWidget(self.lbl_etat)
        layout_principal.addWidget(btn_on)
        layout_principal.addWidget(btn_off)

        # --- TIMER (Lecture 20 fois par seconde) ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all)
        self.timer.start(50)

    def creer_carte(self):
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d; border-radius: 15px; padding: 10px;")
        return frame

    def update_all(self):
        # 1. Lecture du port PC (avec ? et !)
        if self.ser_capteurs and self.ser_capteurs.in_waiting > 0:
            char = self.ser_capteurs.read().decode('utf-8', errors='ignore')
            self.buffer_serie += char
            if "!" in self.buffer_serie:
                start = self.buffer_serie.find("?")
                end = self.buffer_serie.find("!")
                if start != -1 and end > start:
                    msg = self.buffer_serie[start + 1:end].split(",")
                    if len(msg) == 2:
                        if 11 <= msg[0] <= 14:
                            self.tension_actuelle = float(msg[0])
                        self.temperature_actuelle = float(msg[1])
                        self.lbl_tension.setText(f"{self.tension_actuelle} V")
                        self.lbl_temp.setText(f"{self.temperature_actuelle} °C")
                        p = int((self.tension_actuelle / 12.6) * 100)
                        self.barre_batterie.setValue(max(0, min(100, p)))
                    self.buffer_serie = ""

        # 2. Envoi LoRa toutes les 20 secondes (400 * 50ms)
        self.compteur_lora += 1
        if self.compteur_lora >= 400:
            self.envoyer_lora()
            self.compteur_lora = 0

    def envoyer_lora(self):
        """Fonction qui crypte et envoie les données sur TTN"""
        if self.lora and self.lora.is_open:
            try:
                self.lora = serial.Serial('/dev/ttyS0', 9600, timeout=1)
                # 1. Configurer la clé d'abord !
                self.lora.write(b'AT+KEY=APPKEY,"D0B958CBF80F95F9BCAA57276EF075F3"\r\n')
                time.sleep(0.5)
                # 2. Lancer le Join
                self.lora.write(b"AT+JOIN\r\n")
                print("📡 LoRa : Configuration clé et envoi AT+JOIN...")
            except Exception as e:
                print(f"❌ Erreur LoRa : {e}")
                self.lora = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = IHM_Luminaire_Pro()
    ex.showFullScreen()
    sys.exit(app.exec_())