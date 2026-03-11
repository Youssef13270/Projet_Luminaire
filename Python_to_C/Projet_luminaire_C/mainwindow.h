#include <QApplication>
#include <QMainWindow>
#include <QSerialPort>
#include <QSerialPortInfo>
#include <QVBoxLayout>
#include <QLabel>
#include <QProgressBar>
#include <QTimer>
#include <QDebug>

class LuminaireIHM : public QMainWindow {
    Q_OBJECT

private:
    QSerialPort *serial;
    QLabel *lblTension;
    QLabel *lblTemp;
    QProgressBar *barreBatterie;
    float tension = 0.0;
    float temperature = 0.0;

public:
    LuminaireIHM() {
        // --- CONFIGURATION DU PORT SÉRIE (UART5) ---
        serial = new QSerialPort(this);
        serial->setPortName("/dev/ttyAMA5");
        serial->setBaudRate(QSerialPort::Baud9600);
        serial->setDataBits(QSerialPort::Data8);
        serial->setParity(QSerialPort::NoParity);
        serial->setStopBits(QSerialPort::OneStop);
        serial->setFlowControl(QSerialPort::NoFlowControl);

        if (!serial->open(QIODevice::ReadWrite)) {
            qDebug() << "Erreur : Impossible d'ouvrir /dev/ttyAMA5";
        }

        // --- DESIGN DE L'INTERFACE (STYLE ORIGINAL) ---
        this->setWindowTitle("Supervision Luminaire C++");
        this->setFixedSize(900, 550);
        this->setStyleSheet("background-color: #1e1e1e; color: white;");

        QWidget *central = new QWidget();
        QVBoxLayout *layout = new QVBoxLayout(central);

        lblTension = new QLabel("0.0 V");
        lblTension->setStyleSheet("font-size: 50px; font-weight: bold; color: #4fc3f7;");
        lblTension->setAlignment(Qt::AlignCenter);

        lblTemp = new QLabel("0.0 °C");
        lblTemp->setStyleSheet("font-size: 50px; font-weight: bold; color: #ffb74d;");
        lblTemp->setAlignment(Qt::AlignCenter);

        barreBatterie = new QProgressBar();
        barreBatterie->setRange(0, 100);
        barreBatterie->setStyleSheet("QProgressBar { border: 2px solid #444; border-radius: 8px; text-align: center; } "
                                     "QProgressBar::chunk { background-color: #4fc3f7; }");

        layout->addWidget(new QLabel("BATTERIE"));
        layout->addWidget(lblTension);
        layout->addWidget(barreBatterie);
        layout->addWidget(new QLabel("TEMPÉRATURE"));
        layout->addWidget(lblTemp);

        setCentralWidget(central);

        // --- CONNEXION DES DONNÉES ---
        // Chaque fois que des données arrivent sur le port série
        connect(serial, &QSerialPort::readyRead, this, &LuminaireIHM::lireDonnees);
    }

private slots:
    void lireDonnees() {
     // Dans ta fonction readyRead() de Qt Creator
    void LuminaireIHM::lireDonnees() {
    static QString buffer; // Conserve les données entre deux appels
    buffer += serial->readAll();

    if (buffer.contains("!") && buffer.contains("?")) {
        int start = buffer.indexOf("?");
        int end = buffer.indexOf("!");

        QString message = buffer.mid(start + 1, end - start - 1);
        QStringList data = message.split(",");

        if (data.size() == 2) {
            float v = data[0].toFloat();
            float t = data[1].toFloat();
            // Mise à jour de tes labels ici...
            lblTension->setText(QString::number(v) + " V");
        }
        buffer.clear(); // On vide pour la suite
    }
}
};

#include "main.moc"

int main(int argc, char *argv[]) {
    QApplication a(argc, argv);
    LuminaireIHM w;
    w.show();
    return a.exec();
}
