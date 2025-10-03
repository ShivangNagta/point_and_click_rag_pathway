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
from PIL import ImageGrab, ImageDraw, Image

from utils import click_in_bounds

import asyncio
from concurrent.futures import ThreadPoolExecutor

SCREENSHOT_FOLDER = "./screenshots"
SCREENSHOT_TIMER_SEC = 0.75
MARKER_RADIUS = 15

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
        self.latest_ss = None
        self.chat_history = []

        self.init_ui()
        self.start_click_listener()

        self.responses = [
            "That's interesting!", "Could you tell me more?", "I see.",
            "Okay, what's next?", "Fascinating. Please continue."
        ]

        self.log("System log initialized.")
        self.log(f"Started tracking clicks on: '{self.target_app_name}'")

    def init_ui(self):
        self.setWindowTitle(f"Chat & Tracker | Tracking: {self.target_app_name}")
        self.setGeometry(200, 200, 1200, 700)

        main_layout = QHBoxLayout(self)

        # Chat UI
        self.chat_display = QTextBrowser()
        self.chat_display.setStyleSheet("font-size: 14px; padding: 10px;")
        
        # Input area
        self.message_input = QLineEdit(placeholderText="Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        # Collecting Input area and Send button
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        # Collecting Chat display and message layout
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_display)
        chat_layout.addLayout(input_layout)

        # Final Chat layout
        chat_container = QWidget()
        chat_container.setLayout(chat_layout)

        # Log UI
        self.log_display = QTextBrowser()
        self.log_display.setStyleSheet("""
            background-color: #2E2E2E; color: #A9B7C6; 
            font-family: 'Courier New', Courier, monospace; font-size: 13px;
        """)
        self.log_signal.connect(self.log)

        # Integrating chat and log
        main_layout.addWidget(chat_container, 2)
        main_layout.addWidget(self.log_display, 1)

    # Logging
    def log(self, log_text):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")
        self.log_display.append(f"[{timestamp}] {log_text}")

    # Chat Methods
    async def get_llm_response(self, user_message, list_of_paths, api):
        try:
            # TODO: Replace this with your actual LLM API call
            # Also use self.latest_ss and self.chat_history as context
            return ""
        except Exception as e:
            self.log_signal.emit(f"Error getting LLM response: {e}")
            return "Sorry, I encountered an error processing your request."

    def process_llm_response(self, user_message, list_of_paths, api):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(self.get_llm_response(user_message, list_of_paths, api))
        loop.close()
        return response

    def send_message(self):
        user_message = self.message_input.text().strip()
        if not user_message: return

        self.set_chat_enabled(False)
        self.log_signal.emit(f"User sent message: '{user_message}'")
        self.show_message(user_message, is_user=True)
        self.show_message("Thinking...", is_user=False)
        self.message_input.clear()

        with ThreadPoolExecutor() as executor:
            response = self.process_query(user_message)
            self.chat_display.undo()
            self.log_signal.emit(f"LLM generated response: '{response}'")
            self.show_message(response, is_user=False)

        self.set_chat_enabled(True)

    def process_query(self, user_message):
        self.log("BACKGROUND: Retrieving files from Pathway...")
        ret_res = retrieve(user_message, k=K)
        list_of_paths = [os.path.join(PATHWAY_DIR, ret["metadata"]["path"]) for ret in ret_res]
        
        self.log("BACKGROUND: Generating response from LLM...")
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.process_llm_response, user_message, list_of_paths, API)
            ai_response = future.result()
        
        self.chat_history.append({'user': user_message, 'response': ai_response})
        return ai_response

    def set_chat_enabled(self, enabled: bool):
        self.message_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.message_input.setFocus()
        self.log(f"Chat UI {'re-enabled' if enabled else 'disabled'}.")

    def show_message(self, message, is_user):
        message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        bubble_style = "color: #23F056;" if is_user else "color: #F0F0F0;"
        label = "You" if is_user else "AI"
        formatted_message = f"""
            <div align="left" style="margin-bottom: 10px;">
                <div style="color: #2356F0; font-weight: bold; margin-bottom: 5px;">
                    {label}: 
                </div>
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
            except Exception as e:
                self.log_signal.emit(f"Error checking active window: {e}")
                return
            
            rel_x = x - active_window.left
            rel_y = y - active_window.top

            if not (
                active_window and
                active_window._hWnd == self.target_hwnd and
                click_in_bounds(rel_x, rel_y, active_window)
            ): return

            self.log_signal.emit(f"Click detected at ({rel_x}, {rel_y})")
            ss_before, ss_after = self.click_and_changed_screenshot(active_window, rel_x, rel_y)
            self.log_signal.emit(f"Screenshots saved at: {ss_before} and {ss_after}")

            # SEND TO RAG MODEL HERE

    # Screenshot Methods
    def take_screenshot(self, window, filepath=None):
        if not os.path.exists(SCREENSHOT_FOLDER):
            os.makedirs(SCREENSHOT_FOLDER)
        
        x1, y1, width, height = window.left, window.top, window.width, window.height
        x2, y2 = x1 + width, y1 + height
        
        if filepath is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(SCREENSHOT_FOLDER, f"screenshot_{timestamp}.png")

        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        screenshot.save(filepath)
        return filepath
    
    def click_and_changed_screenshot(self, window, click_x, click_y):
        before_path = self.take_screenshot(window)
        self.process_click_screenshot(before_path, click_x, click_y)

        time.sleep(SCREENSHOT_TIMER_SEC)
        after_path = self.take_screenshot(window)
        self.latest_ss = after_path
        return before_path, after_path

    def process_click_screenshot(self, screenshot_path, click_x, click_y):
        with Image.open(screenshot_path) as img:
            draw = ImageDraw.Draw(img)
            radius = MARKER_RADIUS
            circle_bbox = [
                click_x - radius, click_y - radius,
                click_x + radius, click_y + radius
            ]
            
            draw.ellipse(circle_bbox, outline='yellow', width=2)
            img.save(screenshot_path)

    # Click Listeners
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

