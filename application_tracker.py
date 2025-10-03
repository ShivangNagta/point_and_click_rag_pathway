import sys
import os
import time
import random
import threading
import ctypes
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextBrowser, QLineEdit, 
    QPushButton, QHBoxLayout, QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal

import pygetwindow as gw
from pynput import mouse
from PIL import ImageGrab

class AppSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Application to Track")
        self.setGeometry(300, 300, 400, 500)
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.window_map = {}
        for window in gw.getAllWindows():
            if window.title:
                self.list_widget.addItem(QListWidgetItem(window.title))
                self.window_map[window.title] = window
        layout.addWidget(self.list_widget)

        self.ok_button = QPushButton("Start Tracking")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def get_selected_app(self):
        item = self.list_widget.currentItem()
        if item:
            title = item.text()
            window = self.window_map.get(title)
            if window:
                return {'title': title, 'hwnd': window._hWnd}
        return None

class ChatAndTrackerWindow(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, target_app_info):
        super().__init__()
        self.target_app_name = target_app_info['title']
        self.target_hwnd = target_app_info['hwnd']
        self.listener_thread = None
        self.mouse_listener = None
        self.init_ui()
        self.start_click_listener()

        self.responses = [
            "That's interesting!", "Could you tell me more?", "I see.",
            "Okay, what's next?", "Fascinating. Please continue."
        ]

    def init_ui(self):
        self.setWindowTitle(f"Chat & Tracker | Tracking: {self.target_app_name}")
        self.setGeometry(200, 200, 1200, 700)

        main_layout = QHBoxLayout(self)

        # --- LEFT PANEL: Chat UI ---
        self.chat_display = QTextBrowser()
        self.chat_display.setStyleSheet("font-size: 14px; padding: 10px;")
        
        self.message_input = QLineEdit(placeholderText="Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_layout)

        chat_container = QWidget()
        chat_container.setLayout(chat_layout)

        self.log_display = QTextBrowser()
        self.log_display.setStyleSheet("""
            background-color: #2E2E2E; color: #A9B7C6; 
            font-family: 'Courier New', Courier, monospace; font-size: 13px;
        """)
        self.log_signal.connect(self.log_message)

        self.log_message("System log initialized.")
        self.log_message(f"Started tracking clicks on: '{self.target_app_name}'")

        main_layout.addWidget(chat_container, 2) # Chat takes 2/3 width
        main_layout.addWidget(self.log_display, 1) # Log takes 1/3 width

    def log_message(self, log_text):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
        self.log_display.append(f"[{timestamp}] {log_text}")

    def send_message(self):
        user_message = self.message_input.text().strip()
        if user_message:
            self.log_signal.emit(f"User sending message: '{user_message}'")
            self.add_message(user_message, is_user=True)
            self.message_input.clear()
            self.receive_response()
        

    def receive_response(self):
        response = random.choice(self.responses)
        self.log_signal.emit(f"System generating response: '{response}'")
        self.add_message(response, is_user=False)

    def add_message(self, message, is_user):
        message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        align, bubble_style = (
            ("right", "color: #23F056;") if is_user else
            ("left", "color: #F0F0F0;")
        )
        formatted_message = f"""
            <div align="{align}" style="margin-bottom: 10px;">
                <span style="{bubble_style} padding: 10px; border-radius: 10px; font-size: 15px; display: inline-block; max-width: 60%;">
                    {message}
                </span>
            </div>
        """
        self.chat_display.append(formatted_message)

    def on_click(self, x, y, button, pressed):
        if pressed:
            try:
                active_window = gw.getActiveWindow()
                if active_window and active_window._hWnd == self.target_hwnd:
                    rel_x = x - active_window.left
                    rel_y = y - active_window.top
                    if not (0 <= rel_x and rel_x <= active_window.width and 0 <= rel_y and rel_y <= active_window.height):
                        return
                    
                    time.sleep(1)
                    self.take_screenshot(active_window)
            except Exception as e:
                self.log_signal.emit(f"Error checking active window: {e}")

    def take_screenshot(self, window):
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        
        x1, y1, width, height = window.left, window.top, window.width, window.height
        x2, y2 = x1 + width, y1 + height
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join("screenshots", f"screenshot_{timestamp}.png")
        
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        screenshot.save(filepath)
        self.log_signal.emit(f"Screenshot saved to {filepath}")
        
    def run_click_listener(self):
        with mouse.Listener(on_click=self.on_click) as listener:
            self.mouse_listener = listener
            listener.join()
    
    def start_click_listener(self):
        self.listener_thread = threading.Thread(target=self.run_click_listener, daemon=True)
        self.listener_thread.start()

    def closeEvent(self, event):
        if self.mouse_listener:
            self.mouse_listener.stop()
        event.accept()

if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    app = QApplication(sys.argv)
    
    dialog = AppSelectionDialog()
    if dialog.exec():
        selected_app_info = dialog.get_selected_app()
        if selected_app_info:
            main_window = ChatAndTrackerWindow(selected_app_info)
            main_window.show()
            sys.exit(app.exec())
    else:
        sys.exit()

