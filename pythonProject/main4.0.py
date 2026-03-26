import sys
import serial
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont


# ==============================================================================
# CLASSE : Gestion de toutes les communications (Série + LoRa)
# ==============================================================================
class CommunicationManager:
    def __init__(self):
        self.lora = None
        self.ser_capteurs = None
        self.buffer_serie = ""
        self._init_lora()
        self._init_capteurs()

    def _init_lora(self):
        try:
            self.lora = serial.Serial('/dev/ttyS0', 9600, timeout=1)
            self.lora.write(b"AT+JOIN\r\n")
            print("LoRa initialisé sur /dev/ttyS0")
        except Exception as e:
            print(f"Erreur LoRa : {e}")
            self.lora = None

    def _init_capteurs(self):
        try:
            self.ser_capteurs = serial.Serial('/dev/ttyAMA5', 9600, timeout=0.05)
            print("Lecture PC initialisée sur /dev/ttyAMA5")
        except Exception as e:
            print(f"Erreur Capteurs : {e}")
            self.ser_capteurs = None

    def lire_capteurs(self):
        """
        Lecture IDENTIQUE au code original : un caractère par appel,
        on accumule dans le buffer jusqu'à trouver '!'.
        Retourne (tension, temperature) ou None.
        """
        if self.ser_capteurs and self.ser_capteurs.in_waiting > 0:
            # --- EXACTEMENT comme le code original ---
            char = self.ser_capteurs.read().decode('utf-8', errors='ignore')
            self.buffer_serie += char

            if "!" in self.buffer_serie:
                start = self.buffer_serie.find("?")
                end = self.buffer_serie.find("!")
                if start != -1 and end > start:
                    msg = self.buffer_serie[start + 1:end].split(",")
                    self.buffer_serie = ""
                    if len(msg) == 2:
                        try:
                            tension = float(msg[0])
                            temperature = float(msg[1])
                            # Vérification de plage correctement sur float
                            if 11.0 <= tension <= 14.0:
                                return tension, temperature
                            else:
                                print(f"⚠️ Tension hors plage : {tension} V")
                                return None
                        except ValueError as e:
                            print(f"⚠️ Données invalides : {msg} → {e}")
                            return None
                else:
                    self.buffer_serie = ""
        return None

    def envoyer_lora(self, tension: float, temperature: float):
        if self.lora is None or not self.lora.is_open:
            print("⚠️ LoRa non disponible.")
            return
        try:
            self.lora.write(b'AT+KEY=APPKEY,"D0B958CBF80F95F9BCAA57276EF075F3"\r\n')
            time.sleep(0.5)
            self.lora.write(b"AT+JOIN\r\n")
            time.sleep(0.5)
            self.lora.write(f'AT+MSG="{tension:.2f}V"\r\n'.encode('utf-8'))
            time.sleep(0.3)
            self.lora.write(f'AT+MSG="{temperature:.2f}C"\r\n'.encode('utf-8'))
            print(f"✅ LoRa envoyé → {tension:.2f}V | {temperature:.2f}°C")
        except Exception as e:
            print(f"❌ Erreur LoRa : {e}")
            self.lora = None

    def fermer(self):
        if self.lora and self.lora.is_open:
            self.lora.close()
        if self.ser_capteurs and self.ser_capteurs.is_open:
            self.ser_capteurs.close()


# ==============================================================================
# CLASSE : Fenêtre principale de l'IHM
# ==============================================================================
class IHM_Luminaire_Pro(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tension_actuelle = 0.0
        self.temperature_actuelle = 0.0
        self.compteur_lora = 0

        self.comm = CommunicationManager()

        self.setWindowTitle("Supervision Luminaire - IR3")
        self.setGeometry(100, 100, 900, 550)
        self.setStyleSheet("QMainWindow { background-color: #1e1e1e; } QLabel { color: white; }")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QVBoxLayout(central_widget)

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

        # Timer 50ms — identique à l'original
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all)
        self.timer.start(50)

    def creer_carte(self):
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d; border-radius: 15px; padding: 10px;")
        return frame

    def update_all(self):
        resultat = self.comm.lire_capteurs()
        if resultat is not None:
            self.tension_actuelle, self.temperature_actuelle = resultat
            self.lbl_tension.setText(f"{self.tension_actuelle} V")
            self.lbl_temp.setText(f"{self.temperature_actuelle} °C")
            p = int((self.tension_actuelle / 12.6) * 100)
            self.barre_batterie.setValue(max(0, min(100, p)))

        self.compteur_lora += 1
        if self.compteur_lora >= 400:
            self.comm.envoyer_lora(self.tension_actuelle, self.temperature_actuelle)
            self.compteur_lora = 0

    def closeEvent(self, event):
        self.comm.fermer()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = IHM_Luminaire_Pro()
    ex.showFullScreen()
    sys.exit(app.exec_())
