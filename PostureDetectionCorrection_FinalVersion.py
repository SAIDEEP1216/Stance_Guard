import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt, pyqtSlot
import paho.mqtt.client as mqtt
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from joblib import load
import time
from win10toast import ToastNotifier


class PostureGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # MQTT broker settings
        self.client_id = "xxxxxxxx"
        self.hostname = "xxxxxxxx.messaging.internetofthings.ibmcloud.com"
        self.port = 1883
        self.username = "xxxxxxxx"
        self.password = "xxxxxxxxh"
        self.topic = "iot-2/type/ESP32/id/78F5C6CD31E8/evt/status/fmt/json"

        # Load the trained model and scaler
        self.model_path = "C:\\Users\Desktop\\565 Project\\rf_model.pkl"
        self.scaler_path = "C:\\Users\Desktop\\565 Project\\scaler.pkl"
        self.best_params = {
            'n_estimators': 200,
            'max_depth': None,
            'min_samples_split': 5
        }
        self.best_rf_classifier = RandomForestClassifier(random_state=42, **self.best_params)
        self.best_rf_classifier = load(self.model_path)
        self.scaler = load(self.scaler_path)

        # MQTT client initialization
        self.client = mqtt.Client(protocol=mqtt.MQTTv311)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_mqtt)

        # Disconnect button
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_mqtt)

        # Connection label
        self.connection_label = QLabel("Not Connected")
        self.connection_label.setAlignment(Qt.AlignCenter)

        # Prediction label
        self.prediction_label = QLabel("No Prediction")
        self.prediction_label.setAlignment(Qt.AlignCenter)

        # Set background image
        background_path = "C:\\Users\\pajjuri1216\\Desktop\\background.jpg"
        self.background_pixmap = QPixmap(background_path)

        # Toast notifier
        self.toaster = ToastNotifier()

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.connection_label)
        layout.addWidget(self.prediction_label)
        self.setLayout(layout)

    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Posture Project GUI")
        self.setGeometry(100, 100, 800, 600)

    def paintEvent(self, event):
        # Paint the background image
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background_pixmap)

    @pyqtSlot()
    def connect_mqtt(self):
        # Connect to the MQTT broker
        print("Connecting to MQTT broker...")
        self.client = mqtt.Client(self.client_id)
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.hostname, self.port, 60)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.loop_start()

    @pyqtSlot()
    def disconnect_mqtt(self):
        # Disconnect from the MQTT broker
        print("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        self.connection_label.setText("Disconnected")

    @pyqtSlot()
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connection_label.setText("Connected to MQTT broker")
            self.client.subscribe(self.topic)
        else:
            self.connection_label.setText("Failed to connect to MQTT broker")

    @pyqtSlot()
    def on_message(self, client, userdata, msg):
        # Decode the payload as JSON
        payload = json.loads(msg.payload)

        # Extract the values of each sensor
        sensor1_value = payload["d"]["sensor1"]
        sensor2_value = payload["d"]["sensor2"]
        sensor3_value = payload["d"]["sensor3"]
        sensor4_value = payload["d"]["sensor4"]

        # Preprocess the input data
        new_data = pd.DataFrame({
            'TopRight': [sensor1_value],
            'TopLeft': [sensor2_value],
            'BttmRight': [sensor3_value],
            'Seat': [sensor4_value]
        })
        new_data = new_data[['TopRight', 'TopLeft', 'BttmRight', 'Seat']]
        new_data_scaled = self.scaler.transform(new_data)

        # Predict the posture
        predicted_postures = self.best_rf_classifier.predict(new_data_scaled)

        # Update the prediction label
        self.prediction_label.setText("Predicted Posture: " + predicted_postures[0])

        # Show toast notification for the predicted posture
        self.show_toast_notification(predicted_postures[0])

    def show_toast_notification(self, posture):
        if posture == "Declined":
            # image_path = "C:\\Users\Desktop\\declined.jpg"
            message = "You are in Declined Posture, correct your posture!!."
        elif posture == "Inclined":
            # image_path = "C:\\Users\Desktop\\inclined.jpg"
            message = "You are in Inclined Posture, correct your posture!!."
        elif posture == "Forward":
            # image_path = "C:\\Users\Desktop\\correct.jpg"
            message = "You are in Forward Posture, correct your posture!!."
        else:
            return

        # Display toast notification with image and message
        notification = ToastNotifier()
        notification.show_toast("Posture Prediction", message, duration=10)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = PostureGUI()
    gui.show()
    sys.exit(app.exec_())
