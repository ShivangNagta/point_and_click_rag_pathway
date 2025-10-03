import sys
import time
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QWindow

try:
    import win32gui
    import win32process
    import win32con
    import psutil
except ImportError:
    print("Error: This script requires 'pywin32' and 'psutil' libraries.")
    print("Install them with: pip install pywin32 psutil")
    sys.exit(1)


# Predefined applications
PREDEFINED_APPS = {
    'Notepad': r'C:\Windows\System32\notepad.exe',
    'Calculator': r'C:\Windows\System32\calc.exe',
    'Paint': r'C:\Windows\System32\mspaint.exe',
    'WordPad': r'C:\Program Files\Windows NT\Accessories\wordpad.exe',
    'Command Prompt': r'C:\Windows\System32\cmd.exe',
}


def get_hwnds_for_pid(pid):
    """
    Returns all window handles (HWNDs) for a given process ID.
    Only returns visible and enabled windows.
    """
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def get_child_processes(parent_pid):
    """Get all child processes of a parent PID"""
    try:
        parent = psutil.Process(parent_pid)
        return parent.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return []


def find_window_by_title_pattern(pattern, exclude_titles=None):
    """Find window by partial title match"""
    found_windows = []
    exclude_titles = exclude_titles or []
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            # Skip excluded titles
            if any(excl.lower() in title.lower() for excl in exclude_titles):
                return True
            # Match pattern
            if pattern and pattern.lower() in title.lower():
                windows.append((hwnd, title))
        return True
    
    win32gui.EnumWindows(callback, found_windows)
    return found_windows


def find_application_window(initial_pid, app_name_hint=None, max_attempts=50, sleep_interval=0.2):
    """
    Find application window handling various launcher process scenarios.
    Strategy:
    1. Check the initial PID
    2. Check all child processes of initial PID
    3. Look for windows by app name as fallback (if provided)
    """
    all_checked_pids = set()
    
    for attempt in range(max_attempts):
        # Strategy 1: Check initial PID
        pids_to_check = [initial_pid]
        
        # Strategy 2: Check child processes
        children = get_child_processes(initial_pid)
        for child in children:
            try:
                pids_to_check.append(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Check all PIDs
        for pid in pids_to_check:
            if pid in all_checked_pids:
                continue
            all_checked_pids.add(pid)
            
            hwnds = get_hwnds_for_pid(pid)
            if hwnds:
                print(f"Attempt {attempt + 1}: Found {len(hwnds)} window(s) for PID {pid}")
                for hwnd in hwnds:
                    title = win32gui.GetWindowText(hwnd)
                    print(f"  HWND {hwnd}: '{title}'")
                    if title:  # Return first window with title
                        return hwnd
                # Return first window even without title
                return hwnds[0]
        
        # Strategy 3: Fallback - search by app name if provided
        if app_name_hint and attempt > 10:  # After 2 seconds, try title search
            windows = find_window_by_title_pattern(
                app_name_hint,
                exclude_titles=['PyQt6 Application Embedder']  # Exclude our own window
            )
            if windows:
                print(f"Attempt {attempt + 1}: Found window by title search '{app_name_hint}'")
                for hwnd, title in windows:
                    print(f"  HWND {hwnd}: '{title}'")
                return windows[0][0]
        
        if attempt % 5 == 0:
            print(f"Attempt {attempt + 1}: Checked PIDs {pids_to_check}, no windows found yet...")
        
        time.sleep(sleep_interval)
    
    return None


class AppEmbedder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyQt6 Application Embedder')
        self.setGeometry(100, 100, 1000, 750)
        
        self.process = None
        self.process_pid = None
        self.embedded_widget = None
        self.hwnd = None
        
        self.setup_ui()
        
        # Process monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_process_alive)
    
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.layout.setSpacing(10)
        self.setCentralWidget(central_widget)
        
        # Title label
        title_label = QLabel('Application Embedder')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        self.layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel('Ready to embed application')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 8px; font-size: 11pt; color: #555;")
        self.layout.addWidget(self.status_label)
        
        # Control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_panel.setStyleSheet("background-color: #000000; border-radius: 5px; padding: 10px;")
        
        # Row 1: Predefined apps dropdown
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Predefined Apps:'))
        self.combo_apps = QComboBox()
        self.combo_apps.addItems(['-- Select --'] + list(PREDEFINED_APPS.keys()))
        self.combo_apps.currentTextChanged.connect(self.on_predefined_app_selected)
        row1.addWidget(self.combo_apps, stretch=1)
        control_layout.addLayout(row1)
        
        # Row 2: Custom executable path
        row2 = QHBoxLayout()
        row2.addWidget(QLabel('Or Custom Path:'))
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText('Enter full path to executable or browse...')
        row2.addWidget(self.txt_path, stretch=1)
        self.btn_browse = QPushButton('Browse')
        self.btn_browse.clicked.connect(self.browse_executable)
        row2.addWidget(self.btn_browse)
        control_layout.addLayout(row2)
        
        # Row 3: Optional app name hint
        row3 = QHBoxLayout()
        row3.addWidget(QLabel('App Name (optional):'))
        self.txt_app_name = QLineEdit()
        self.txt_app_name.setPlaceholderText('e.g., "Notepad", "Calculator" (helps find window)')
        row3.addWidget(self.txt_app_name, stretch=1)
        control_layout.addLayout(row3)
        
        # Row 4: Launch button
        self.btn_launch = QPushButton('Launch & Embed Application')
        self.btn_launch.setFixedHeight(45)
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_launch.clicked.connect(self.launch_and_embed)
        control_layout.addWidget(self.btn_launch)
        
        self.layout.addWidget(control_panel)
        
        # Container for embedded window
        self.container = QWidget(self)
        self.container.setMinimumSize(900, 450)
        self.container.setStyleSheet("""
            background-color: #e8e8e8;
            border: 3px dashed #999;
            border-radius: 5px;
        """)
        container_layout = QVBoxLayout(self.container)
        placeholder = QLabel('Embedded application will appear here')
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-size: 14pt;")
        container_layout.addWidget(placeholder)
        
        self.layout.addWidget(self.container, stretch=1)
    
    def on_predefined_app_selected(self, app_name):
        """Handle predefined app selection"""
        if app_name in PREDEFINED_APPS:
            self.txt_path.setText(PREDEFINED_APPS[app_name])
            self.txt_app_name.setText(app_name)
    
    def browse_executable(self):
        """Browse for executable file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Executable",
            "C:\\",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.txt_path.setText(file_path)
    
    def update_status(self, message, color='#555'):
        """Update status label with current operation"""
        print(f"Status: {message}")
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"padding: 8px; font-size: 11pt; color: {color};")
        QApplication.processEvents()
    
    def launch_and_embed(self):
        """Launch and embed the selected application"""
        if self.process_pid:
            self.update_status("Process already running", '#ff9800')
            return
        
        # Get executable path
        exe_path = self.txt_path.text().strip()
        if not exe_path:
            self.update_status("Please select or enter an application path", '#f44336')
            return
        
        # Get app name hint
        app_name = self.txt_app_name.text().strip()
        
        self.btn_launch.setEnabled(False)
        self.update_status(f"Starting application...", '#2196F3')
        
        # Launch application
        try:
            self.process = subprocess.Popen(
                [exe_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.process_pid = self.process.pid
            
        except FileNotFoundError:
            self.update_status(f"Error: Executable not found at '{exe_path}'", '#f44336')
            self.btn_launch.setEnabled(True)
            return
        except Exception as e:
            self.update_status(f"Error: Failed to start - {str(e)}", '#f44336')
            self.btn_launch.setEnabled(True)
            return
        
        self.update_status(f"Application started (PID: {self.process_pid}). Searching for window...", '#2196F3')
        print(f"\n=== Searching for application window (Initial PID: {self.process_pid}) ===")
        
        # Find window handle
        self.hwnd = find_application_window(
            self.process_pid,
            app_name_hint=app_name if app_name else None,
            max_attempts=50,
            sleep_interval=0.5
        )
        
        if not self.hwnd:
            self.update_status(f"Error: Could not find application window after 10 seconds", '#f44336')
            print("Failed to find window. Terminating process.")
            self.kill_process_tree()
            self.btn_launch.setEnabled(True)
            return
        
        window_title = win32gui.GetWindowText(self.hwnd)
        self.update_status(f"Found window: '{window_title}' (HWND: {self.hwnd})", '#4CAF50')
        print(f"\n=== Successfully found window ===")
        print(f"HWND: {self.hwnd}")
        print(f"Title: '{window_title}'")
        
        # Small delay to ensure window is fully initialized
        time.sleep(0.5)
        
        # Embed the window
        self.embed_window()
        
        # Start monitoring
        self.monitor_timer.start(1000)
    
    def embed_window(self):
        """Embed the external window into our Qt application"""
        try:
            # Get current window style
            style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
            print(f"\nOriginal window style: {hex(style)}")
            
            # Remove window decorations and make it a child window
            new_style = style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | 
                                  win32con.WS_MINIMIZE | win32con.WS_MAXIMIZE | 
                                  win32con.WS_SYSMENU)
            new_style |= win32con.WS_CHILD
            
            print(f"New window style: {hex(new_style)}")
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, new_style)
            
            # Create Qt window container
            window = QWindow.fromWinId(self.hwnd)
            self.embedded_widget = QWidget.createWindowContainer(window, self.container)
            
            # Clear container and add embedded widget
            for i in reversed(range(self.layout.count())):
                widget = self.layout.itemAt(i).widget()
                if widget == self.container:
                    self.layout.removeWidget(self.container)
                    self.container.hide()
                    break
            
            self.layout.addWidget(self.embedded_widget, stretch=1)
            
            # Force window to show and update
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self.hwnd)
            
            window_title = win32gui.GetWindowText(self.hwnd)
            self.update_status(f"✓ Successfully embedded '{window_title}'", '#4CAF50')
            self.btn_launch.hide()
            print("=== Embedding complete ===\n")
            
        except Exception as e:
            self.update_status(f"Error embedding window: {str(e)}", '#f44336')
            print(f"Error during embedding: {str(e)}")
            import traceback
            traceback.print_exc()
            self.kill_process_tree()
            self.btn_launch.setEnabled(True)
    
    def check_process_alive(self):
        """Check if the embedded process is still running"""
        if not self.hwnd:
            return
        
        # Check if window still exists
        if not win32gui.IsWindow(self.hwnd):
            print("Window no longer exists")
            self.on_process_finished()
    
    def kill_process_tree(self):
        """Kill process and all its children"""
        if not self.process_pid:
            return
        
        try:
            parent = psutil.Process(self.process_pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Kill parent
            try:
                parent.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def on_process_finished(self):
        """Handle process termination"""
        self.monitor_timer.stop()
        self.update_status("Embedded process terminated", '#ff9800')
        self.btn_launch.show()
        self.btn_launch.setEnabled(True)
        
        if self.embedded_widget:
            self.embedded_widget.hide()
            self.layout.removeWidget(self.embedded_widget)
            self.embedded_widget.deleteLater()
            self.embedded_widget = None
        
        # Restore container
        self.layout.addWidget(self.container, stretch=1)
        self.container.show()
        
        self.hwnd = None
        self.process = None
        self.process_pid = None
        
        # Reset form
        self.combo_apps.setCurrentIndex(0)
    
    def closeEvent(self, event):
        """Clean up when main window closes"""
        self.monitor_timer.stop()
        if self.process_pid:
            print("Closing application, terminating embedded process...")
            self.kill_process_tree()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = AppEmbedder()
    main_win.show()
    sys.exit(app.exec())