import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextBrowser, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDateTime

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.responses = [
            "That's interesting!",
            "Could you tell me more about that?",
            "I'm not sure I understand.",
            "Let me think about that for a moment.",
            "Okay, what's next?",
            "Fascinating. Please continue."
        ]

    def init_ui(self):
        self.setWindowTitle("Chat and Logging Application")
        self.setGeometry(200, 200, 1000, 600)

        main_split_layout = QHBoxLayout()

        chat_container = QWidget()
        chat_layout = QVBoxLayout()

        self.chat_display = QTextBrowser(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                font-size: 14px;
                padding: 10px;
            }
        """)

        input_layout = QHBoxLayout()

        self.message_input = QLineEdit(self)
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
        """)

        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)


        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_layout)
        chat_container.setLayout(chat_layout)

        self.log_display = QTextBrowser(self)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextBrowser {
                background-color: #2E2E2E; /* Dark background */
                color: #A9B7C6; /* Light gray text */
                border: 1px solid #444444;
                border-radius: 5px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 13px;
                padding: 10px;
            }
        """)
        self.log_message("System log initialized.")

        main_split_layout.addWidget(chat_container)
        main_split_layout.addWidget(self.log_display)
        main_split_layout.setStretch(0, 2)
        main_split_layout.setStretch(1, 1)

        self.setLayout(main_split_layout)

    def log_message(self, log_text):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
        self.log_display.append(f"[{timestamp}] {log_text}")

    def send_message(self):
        user_message = self.message_input.text().strip()
        if user_message:
            self.log_message(f"User sending message: '{user_message}'")
            self.add_message(user_message, is_user=True)
            self.message_input.clear()
            self.receive_response()

    def receive_response(self):
        response_message = random.choice(self.responses)
        self.log_message(f"System generating response: '{response_message}'")
        self.add_message(response_message, is_user=False)

    def add_message(self, message, is_user):
        message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if is_user:
            formatted_message = f"""
            <div align="right" style="margin-bottom: 10px;">
                <span style="background-color: #E1F5FE; color: #333; padding: 10px; border-radius: 10px; font-size: 15px; display: inline-block; max-width: 60%;">
                    {message}
                </span>
            </div>
            """
        else:
            formatted_message = f"""
            <div align="left" style="margin-bottom: 10px;">
                <span style="background-color: #F1F0F0; color: #333; padding: 10px; border-radius: 10px; font-size: 15px; display: inline-block; max-width: 60%;">
                    {message}
                </span>
            </div>
            """
        self.chat_display.append(formatted_message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())