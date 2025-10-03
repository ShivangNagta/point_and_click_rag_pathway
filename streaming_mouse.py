import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QTextEdit, QFrame, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent
import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll, c_long, c_ulong, Structure, POINTER
import ctypes

class ClickableLabel(QLabel):
    """Custom QLabel that emits mouse events"""
    mouse_clicked = pyqtSignal(int, int, int)  # x, y, button
    mouse_moved = pyqtSignal(int, int)  # x, y
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        button = event.button()
        pos = event.pos()
        self.mouse_clicked.emit(pos.x(), pos.y(), button.value)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.pos()
        self.mouse_moved.emit(pos.x(), pos.y())
        super().mouseMoveEvent(event)

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
        
        # Input method selection
        self.focus_check = QCheckBox("Focus window on click")
        self.focus_check.setChecked(True)
        control_layout.addWidget(self.focus_check)
        
        self.sendinput_check = QCheckBox("Use SendInput")
        self.sendinput_check.setChecked(False)
        self.sendinput_check.setToolTip("Use SendInput instead of PostMessage (may work better for some games)")
        control_layout.addWidget(self.sendinput_check)
        
        # Debug button
        self.debug_btn = QPushButton("Test Click Center")
        self.debug_btn.clicked.connect(self.test_click_center)
        control_layout.addWidget(self.debug_btn)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # Stream display frame (custom widget for mouse events)
        self.stream_label = ClickableLabel()
        self.stream_label.setMinimumSize(800, 450)
        self.stream_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stream_label.setStyleSheet("background-color: #1a1a1a; border: 2px solid #444;")
        self.stream_label.setText("Stream will appear here...")
        self.stream_label.setScaledContents(False)
        self.stream_label.mouse_clicked.connect(self.handle_click)
        self.stream_label.mouse_moved.connect(self.handle_mouse_move)
        main_layout.addWidget(self.stream_label, stretch=1)
        
        # Store the current frame dimensions for coordinate mapping
        self.current_frame_size = None
        self.current_window_size = None
        
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
            
            # Store frame dimensions for coordinate mapping
            self.current_frame_size = (width, height)
            left, top, right, bottom = win32gui.GetWindowRect(self.target_hwnd)
            self.current_window_size = (right - left, bottom - top)
            
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
    
    def map_coordinates(self, label_x, label_y):
        """Map label coordinates to window coordinates"""
        if not self.current_frame_size or not self.target_hwnd:
            return None, None
        
        # Get the pixmap size (actual displayed image size)
        pixmap = self.stream_label.pixmap()
        if not pixmap:
            return None, None
        
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()
        label_width = self.stream_label.width()
        label_height = self.stream_label.height()
        
        # Calculate offset (image is centered in label)
        offset_x = (label_width - pixmap_width) // 2
        offset_y = (label_height - pixmap_height) // 2
        
        # Adjust click coordinates relative to pixmap
        adjusted_x = label_x - offset_x
        adjusted_y = label_y - offset_y
        
        # Check if click is within pixmap bounds
        if adjusted_x < 0 or adjusted_y < 0 or adjusted_x >= pixmap_width or adjusted_y >= pixmap_height:
            return None, None
        
        # Map to original window coordinates
        frame_width, frame_height = self.current_frame_size
        window_x = int((adjusted_x / pixmap_width) * frame_width)
        window_y = int((adjusted_y / pixmap_height) * frame_height)
        
        return window_x, window_y
    
    def handle_click(self, x, y, button):
        """Handle click on the stream label"""
        if not self.target_hwnd:
            return
        
        # Map coordinates
        window_x, window_y = self.map_coordinates(x, y)
        
        if window_x is None or window_y is None:
            return
        
        # Try to focus the window first if option is enabled
        if self.focus_check.isChecked():
            try:
                # Bring window to foreground
                win32gui.SetForegroundWindow(self.target_hwnd)
                # Set focus
                win32gui.SetFocus(self.target_hwnd)
            except:
                pass
        
        # Use SendInput method if enabled (more reliable for games)
        if self.sendinput_check.isChecked():
            self.send_click_sendinput(window_x, window_y, button)
        else:
            self.send_click_postmessage(window_x, window_y, button)
    
    def send_click_postmessage(self, window_x, window_y, button):
        """Send click using PostMessage (legacy method)"""
        lParam = win32api.MAKELONG(window_x, window_y)
        
        try:
            if button == Qt.MouseButton.LeftButton.value:
                # Try multiple methods
                result1 = win32gui.SendMessage(self.target_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                result2 = win32gui.SendMessage(self.target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                self.statusBar().showMessage(f"PostMessage: Left click at ({window_x}, {window_y}) - Results: {result1}, {result2}")
                self.info_text.append(f"Sent WM_LBUTTONDOWN and WM_LBUTTONUP to HWND {self.target_hwnd} at ({window_x}, {window_y})")
            elif button == Qt.MouseButton.RightButton.value:
                win32gui.SendMessage(self.target_hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
                win32gui.SendMessage(self.target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                self.statusBar().showMessage(f"PostMessage: Right click at ({window_x}, {window_y})")
            elif button == Qt.MouseButton.MiddleButton.value:
                win32gui.SendMessage(self.target_hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, lParam)
                win32gui.SendMessage(self.target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                self.statusBar().showMessage(f"PostMessage: Middle click at ({window_x}, {window_y})")
        except Exception as e:
            self.info_text.append(f"PostMessage Error: {e}")
    
    def send_click_sendinput(self, window_x, window_y, button):
        """Send click using SendInput (works better for games)"""
        try:
            # Save current mouse position
            current_pos = win32api.GetCursorPos()
            
            # Get window position on screen
            left, top, right, bottom = win32gui.GetWindowRect(self.target_hwnd)
            screen_x = left + window_x
            screen_y = top + window_y
            
            self.info_text.append(f"Window rect: ({left}, {top}, {right}, {bottom})")
            self.info_text.append(f"Calculated screen position: ({screen_x}, {screen_y})")
            
            # Method 1: Use win32api.SetCursorPos and mouse_event
            win32api.SetCursorPos((screen_x, screen_y))
            
            # Small delay to ensure cursor moved
            QApplication.processEvents()
            
            # Determine button
            if button == Qt.MouseButton.LeftButton.value:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
                button_name = "Left"
            elif button == Qt.MouseButton.RightButton.value:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, screen_x, screen_y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, screen_x, screen_y, 0, 0)
                button_name = "Right"
            elif button == Qt.MouseButton.MiddleButton.value:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, screen_x, screen_y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, screen_x, screen_y, 0, 0)
                button_name = "Middle"
            else:
                return
            
            # Restore cursor position
            win32api.SetCursorPos(current_pos)
            
            self.statusBar().showMessage(f"SendInput: {button_name} click at screen ({screen_x}, {screen_y})")
            self.info_text.append(f"Sent {button_name} click to screen position ({screen_x}, {screen_y})")
            
        except Exception as e:
            self.statusBar().showMessage(f"SendInput error: {e}")
            self.info_text.append(f"SendInput Error: {e}")
            # Fallback to PostMessage
            self.send_click_postmessage(window_x, window_y, button)
    
    def handle_mouse_move(self, x, y):
        """Handle mouse move on the stream label"""
        if not self.target_hwnd or self.sendinput_check.isChecked():
            return  # Don't send mouse move with SendInput to avoid interference
        
        # Map coordinates
        window_x, window_y = self.map_coordinates(x, y)
        
        if window_x is None or window_y is None:
            return
        
        # Send mouse move message
        lParam = win32api.MAKELONG(window_x, window_y)
        win32gui.PostMessage(self.target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
    
    def test_click_center(self):
        """Test click at the center of the target window"""
        if not self.target_hwnd:
            self.info_text.append("❌ No window is being streamed")
            return
        
        self.info_text.clear()
        self.info_text.append("=== Testing Click at Window Center ===")
        
        # Get window dimensions
        left, top, right, bottom = win32gui.GetWindowRect(self.target_hwnd)
        width = right - left
        height = bottom - top
        
        # Calculate center
        center_x = width // 2
        center_y = height // 2
        
        self.info_text.append(f"Window HWND: {self.target_hwnd}")
        self.info_text.append(f"Window title: {win32gui.GetWindowText(self.target_hwnd)}")
        self.info_text.append(f"Window rect: ({left}, {top}, {right}, {bottom})")
        self.info_text.append(f"Window size: {width}x{height}")
        self.info_text.append(f"Center coordinates: ({center_x}, {center_y})")
        self.info_text.append(f"\nAttempting click...")
        
        # Try the click
        if self.sendinput_check.isChecked():
            self.send_click_sendinput(center_x, center_y, Qt.MouseButton.LeftButton.value)
        else:
            self.send_click_postmessage(center_x, center_y, Qt.MouseButton.LeftButton.value)
    
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