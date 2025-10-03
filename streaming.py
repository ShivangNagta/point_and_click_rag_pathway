import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QTextEdit, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import win32gui
import win32ui
import win32con
from ctypes import windll

class GameStreamCapture(QMainWindow):
    def __init__(self):
        super().__init__()
        self.target_hwnd = None
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.capture_frame)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Game Window Streaming - PyQt6")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Window Title:"))
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Game, Browser, Application")
        self.title_input.setMinimumWidth(200)
        control_layout.addWidget(self.title_input)
        
        self.list_btn = QPushButton("List Windows")
        self.list_btn.clicked.connect(self.list_windows)
        control_layout.addWidget(self.list_btn)
        
        self.start_btn = QPushButton("Start Streaming")
        self.start_btn.clicked.connect(self.start_streaming)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Streaming")
        self.stop_btn.clicked.connect(self.stop_streaming)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addWidget(QLabel("FPS:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["10", "15", "30", "60"])
        self.fps_combo.setCurrentText("30")
        control_layout.addWidget(self.fps_combo)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # Stream display frame
        self.stream_label = QLabel()
        self.stream_label.setMinimumSize(800, 450)
        self.stream_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stream_label.setStyleSheet("background-color: #1a1a1a; border: 2px solid #444;")
        self.stream_label.setText("Stream will appear here...")
        self.stream_label.setScaledContents(False)
        main_layout.addWidget(self.stream_label, stretch=1)
        
        # Info text area
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setPlaceholderText("Window information will appear here...")
        main_layout.addWidget(self.info_text)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def get_window_list(self):
        """Get list of all visible windows"""
        windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 0:
                    windows.append((hwnd, title))
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    def list_windows(self):
        """Display list of available windows"""
        self.info_text.clear()
        windows = self.get_window_list()
        
        self.info_text.append("Available Windows:")
        self.info_text.append("-" * 80)
        
        for hwnd, title in windows[:50]:  # Limit to first 50
            self.info_text.append(f"HWND: {hwnd} | Title: {title}")
        
        if len(windows) > 50:
            self.info_text.append(f"\n... and {len(windows) - 50} more windows")
        
        self.info_text.append(f"\nTotal: {len(windows)} windows found")
    
    def find_window_by_title(self, partial_title):
        """Find window handle by partial title match"""
        windows = self.get_window_list()
        
        for hwnd, title in windows:
            if partial_title.lower() in title.lower():
                return hwnd
        return None
    
    def capture_window_gdi(self, hwnd):
        """Capture window using GDI (works for most applications)"""
        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Get window device context
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)
            
            # Copy screen to bitmap
            result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
            
            # Convert to numpy array
            bmpinfo = bitmap.GetInfo()
            bmpstr = bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape(height, width, 4)
            
            # Clean up
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            if result == 1:
                # Convert BGRA to RGB
                img = img[:, :, [2, 1, 0]]
                return img
            else:
                return None
                
        except Exception as e:
            print(f"Capture error: {e}")
            return None
    
    def start_streaming(self):
        """Start streaming the target window"""
        title_search = self.title_input.text().strip()
        
        if not title_search:
            self.info_text.clear()
            self.info_text.append("❌ Please enter a window title to search for.")
            return
        
        # Find the window
        self.target_hwnd = self.find_window_by_title(title_search)
        
        if not self.target_hwnd:
            self.info_text.clear()
            self.info_text.append(f"❌ No window found with title containing: '{title_search}'")
            self.info_text.append("\nClick 'List Windows' to see available windows.")
            return
        
        # Get window info
        window_title = win32gui.GetWindowText(self.target_hwnd)
        left, top, right, bottom = win32gui.GetWindowRect(self.target_hwnd)
        width = right - left
        height = bottom - top
        
        self.info_text.clear()
        self.info_text.append(f"✅ Streaming window: {window_title}")
        self.info_text.append(f"HWND: {self.target_hwnd}")
        self.info_text.append(f"Resolution: {width}x{height}")
        
        # Set FPS
        fps = int(self.fps_combo.currentText())
        interval = int(1000 / fps)
        self.capture_timer.start(interval)
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.title_input.setEnabled(False)
        self.fps_combo.setEnabled(False)
        
        self.statusBar().showMessage(f"Streaming at {fps} FPS...")
    
    def capture_frame(self):
        """Capture and display a frame"""
        if not self.target_hwnd:
            return
        
        # Check if window still exists
        if not win32gui.IsWindow(self.target_hwnd):
            self.stop_streaming()
            self.info_text.append("\n⚠️ Target window was closed.")
            return
        
        # Capture the window
        frame = self.capture_window_gdi(self.target_hwnd)
        
        if frame is not None:
            # Convert numpy array to QImage
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            
            # Make sure the array is contiguous and convert to bytes
            frame_contiguous = np.ascontiguousarray(frame)
            q_image = QImage(frame_contiguous.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Keep a reference to prevent garbage collection
            self._frame_data = frame_contiguous
            
            # Scale to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.stream_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.stream_label.setPixmap(scaled_pixmap)
    
    def stop_streaming(self):
        """Stop streaming"""
        self.capture_timer.stop()
        self.target_hwnd = None
        
        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.title_input.setEnabled(True)
        self.fps_combo.setEnabled(True)
        
        self.statusBar().showMessage("Stopped")
        self.stream_label.clear()
        self.stream_label.setText("Stream stopped")
    
    def closeEvent(self, event):
        """Clean up when closing"""
        self.stop_streaming()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = GameStreamCapture()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()