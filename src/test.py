import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QTimer, QObject, pyqtSlot, QFile, QTextStream
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel

from src.file.create import save_text_to_file
from src.agent.agent_utils import screenshot_to_text, get_user_response
from src.client_functions.endpoints import answer, summarize, retrieve, list_documents, statistics, health_check, search_documents, ask_with_context
from src.chat.manage import format_history, add_to_chat_history, chat_history


# --- Load environment variables ---
from dotenv import load_dotenv
load_dotenv()

# --- Your existing constants ---
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_FILE_DIR, ".."))
LIVE_DIR = os.path.join(ROOT_DIR, "pathway", "data")
PATHWAY_DIR = os.path.join(ROOT_DIR, "pathway")
os.makedirs(LIVE_DIR, exist_ok=True)
API = os.getenv("GEMINI_API_KEY")
K = os.environ("K")

# -------------------- JavaScript Bridge Object --------------------
class Bridge(QObject):
    py_clicked = pyqtSignal(int, int)

    @pyqtSlot(int, int)
    def on_js_click(self, x, y):
        self.py_clicked.emit(x, y)

# -------------------- Main Application --------------------
class GameStreamApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.screenshot_counter = 0
        self.screenshots_dir = "game_screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        self.before_screenshot = None
        self.click_coords = None

        self.init_ui()
        self.log("Application started. JS Bridge is active.")

    def init_ui(self):
        self.setWindowTitle("Unity WebGL Stream App (iFrame Final)")
        self.resize(1400, 800)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Unity WebGL URL here...")
        self.load_btn = QPushButton("Load Game")
        self.load_btn.clicked.connect(self.load_game_url)
        left_layout.addWidget(QLabel("Game URL:"))
        left_layout.addWidget(self.url_input)
        left_layout.addWidget(self.load_btn)
        log_label = QLabel("Logging:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(300)
        left_layout.addWidget(log_label)
        left_layout.addWidget(self.log_text, 2)
        chat_label = QLabel("Chat:")
        self.chat_text = QTextEdit()
        self.chat_text.setReadOnly(True)
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(60)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_chat)
        left_layout.addWidget(chat_label)
        left_layout.addWidget(self.chat_text, 3)
        left_layout.addWidget(self.chat_input)
        left_layout.addWidget(self.send_btn)
        splitter.addWidget(left_panel)
        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.bridge = Bridge()
        self.channel = QWebChannel()
        self.channel.registerObject("py_bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        self.bridge.py_clicked.connect(self.handle_web_view_click)
        self.web_view.page().loadFinished.connect(self.on_page_load_finished)

    def load_game_url(self):
        url = self.url_input.text().strip()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        if url:
            self.web_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            self.web_view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            self.web_view.load(QUrl(url))
            self.log(f"Loading game URL: {url}")

    def on_page_load_finished(self, ok):
        if not ok:
            self.log("ERROR: Page failed to load.")
            return
        self.log("Page loaded. Injecting JS...")
        
        js_file = QFile(":/qtwebchannel/qwebchannel.js")
        if not js_file.open(QFile.ReadOnly):
            # Fallback for environments where resources aren't compiled
            try:
                from PyQt5 import QtWebEngineCore
                js_path = os.path.join(os.path.dirname(QtWebEngineCore.__file__), 'qtwebchannel', 'qwebchannel.js')
                js_file = QFile(js_path)
                js_file.open(QFile.ReadOnly)
            except Exception as e:
                self.log(f"FATAL ERROR: Could not find or open qwebchannel.js: {e}")
                return

        js_source = QTextStream(js_file).readAll()
        self.web_view.page().runJavaScript(js_source)
        self.log("Injected qwebchannel.js library.")
        
        bridge_script = """
            new QWebChannel(qt.webChannelTransport, function (channel) {
                function attachListener(doc) {
                    if (!doc) return;
                    console.log('Attaching listener to document:', doc.location.href);
                    doc.addEventListener('mousedown', function(event) {
                        channel.objects.py_bridge.on_js_click(event.clientX, event.clientY);
                    }, true);
                }
                attachListener(window.document);
                var iframes = document.getElementsByTagName('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    try {
                        attachListener(iframes[i].contentDocument);
                    } catch (e) {
                        console.error('Could not access iframe content:', e);
                    }
                }
            });
        """
        self.web_view.page().runJavaScript(bridge_script)
        self.log("iFrame-aware bridge script injected successfully.")

    def handle_web_view_click(self, x, y):
        self.log(f"SUCCESS: Click detected via JS Bridge at ({x}, {y}). Capturing 'before' screenshot.")
        self.click_coords = (x, y)
        self.capture_screenshot(self.on_before_screenshot_captured)
    
    def capture_screenshot(self, callback):
        pixmap = self.web_view.grab()
        callback(pixmap)

    def on_before_screenshot_captured(self, before_pixmap):
        if before_pixmap.isNull():
            self.log("ERROR: 'Before' screenshot is empty! Cannot proceed.")
            return
        
        self.log("'Before' screenshot captured. Executing JS click and waiting for render.")
        self.before_screenshot = before_pixmap
        x, y = self.click_coords
        js_click_code = f"document.elementFromPoint({x}, {y}).click();"
        self.web_view.page().runJavaScript(js_click_code)
        QTimer.singleShot(500, self.take_after_screenshot)

    def take_after_screenshot(self):
        self.log("Capturing 'after' screenshot.")
        self.capture_screenshot(self.on_after_screenshot_captured)

    def on_after_screenshot_captured(self, after_pixmap):
        if after_pixmap.isNull():
            self.log("ERROR: 'After' screenshot is empty!")
            return # Return early to avoid errors
        self.log("Both screenshots ready. Saving to disk.")
        self.save_and_process_click_screenshots(self.before_screenshot, after_pixmap)
        self.before_screenshot = None
        self.click_coords = None

    def save_and_process_click_screenshots(self, before_pixmap, after_pixmap):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        before_path, after_path = None, None

        if before_pixmap and not before_pixmap.isNull():
            before_path = os.path.join(self.screenshots_dir, f"click_{self.screenshot_counter}_before_{timestamp}.png")
            if before_pixmap.save(before_path, "PNG"): self.log(f"SUCCESS: Saved {os.path.basename(before_path)}")
            else: self.log(f"ERROR: Failed to save 'before' screenshot.")
        
        if after_pixmap and not after_pixmap.isNull():
            after_path = os.path.join(self.screenshots_dir, f"click_{self.screenshot_counter}_after_{timestamp}.png")
            if after_pixmap.save(after_path, "PNG"): self.log(f"SUCCESS: Saved {os.path.basename(after_path)}")
            else: self.log(f"ERROR: Failed to save 'after' screenshot.")
        
        self.screenshot_counter += 1

        if before_path and after_path:
            caption = screenshot_to_text([before_path, after_path], API)
            self.log(f"Caption for Click generated")
            file_path = save_text_to_file(caption, LIVE_DIR)
            self.log(f"New file created for caption: {file_path}")

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")
        QApplication.processEvents()

    def send_chat(self):
        msg = self.chat_input.toPlainText().strip()
        if not msg:
            return

        # ---  Take screenshot on chat send ---
        self.log("Capturing screenshot for chat context...")
        pixmap = self.web_view.grab()
        screenshot_path = None

        if not pixmap.isNull():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_context_{timestamp}.png"
            path = os.path.join(self.screenshots_dir, filename)
            
            if pixmap.save(path, "PNG"):
                screenshot_path = os.path.abspath(path)
                self.log(f"SUCCESS: Chat context screenshot saved to: {screenshot_path}")
            else:
                self.log("ERROR: Failed to save chat context screenshot.")
        else:
            self.log("ERROR: Captured pixmap for chat context is empty.")
                    

        # --- Original chat functionality continues ---
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_text.append(f"[{timestamp}] You: {msg}")
        ret_res = retrieve(msg, k=K)
        self.log(f"Retrived top {K} Files from Pathway.")
        list_of_paths = []
        for ret in ret_res:
            abs_path = os.path.join(PATHWAY_DIR, ret["metadata"]["path"])
            list_of_paths.append(abs_path)
        self.log(f"List of {K} filepaths retrieved from Pathway: {list_of_paths}")
        formatted_chat_history = format_history(chat_history)
        ai_response = get_user_response(msg, formatted_chat_history, screenshot_path, list_of_paths, API)
        self.log(f"Response generated by LLM.")
        self.chat_text.append(f"[{timestamp}] AI: {ai_response}")
        add_to_chat_history(msg, ai_response)
        self.chat_input.clear()



def main():
    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9224"
    app = QApplication(sys.argv)
    window = GameStreamApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
