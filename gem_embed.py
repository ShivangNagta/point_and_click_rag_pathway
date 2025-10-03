import sys
import subprocess
import time
import win32gui
import win32process
import win32con
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QWindow, QCloseEvent
from PyQt6.QtCore import Qt, QTimer

# --- !!! IMPORTANT !!! ---
# CHANGE THIS PATH TO THE EXECUTABLE OF THE GAME/APP YOU WANT TO EMBED
# Using Windows Calculator as a safe example.
# Example for a game: r"C:\Games\MyAwesomeGame\bin\game.exe"
APP_PATH = r"C:\Windows\System32\calc.exe"

def find_window_for_pid(pid: int, timeout: int = 10) -> int:
    """
    Finds the main window handle (HWND) for a given Process ID (PID).

    This function iterates through all top-level windows, checks their associated PID,
    and returns the handle of the first visible window with a title that matches.

    Args:
        pid: The Process ID of the application to find.
        timeout: How many seconds to wait for the window to appear.

    Returns:
        The window handle (HWND) as an integer, or 0 if not found.
    """
    start_time = time.time()
    result_hwnd = 0

    while time.time() - start_time < timeout:
        # Inner function (callback) to be used with EnumWindows
        def callback(hwnd, hwnds):
            nonlocal result_hwnd
            # if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                result_hwnd = hwnd
                return False # Stop enumeration
            return True # Continue enumeration

        # Enumerate all top-level windows
        win32gui.EnumWindows(callback, [])
        
        if result_hwnd:
            return result_hwnd
            
        time.sleep(0.1) # Wait a bit before retrying

    print(f"Error: Could not find window for PID {pid} within {timeout} seconds.")
    return 0


class GameContainer(QWidget):
    """
    A QWidget that launches and embeds an external application window.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_process = None
        self.game_hwnd = 0
        self.embedded_window = None

        # Set a background color to see the container area
        self.setStyleSheet("background-color: black;")
        
        # Using a QTimer to delay the embedding process slightly
        # This gives the main window time to be created and shown first.
        QTimer.singleShot(500, self.embed_application)

    def embed_application(self):
        """
        Launches, finds, and embeds the application window.
        """
        print(f"Attempting to launch application: {APP_PATH}")
        try:
            # 1. Launch the Game/Application
            # Popen starts the process without blocking the Python script.
            self.game_process = subprocess.Popen([APP_PATH])
            print(f"Process launched with PID: {self.game_process.pid}")
        except FileNotFoundError:
            print(f"Error: Application not found at '{APP_PATH}'")
            return
        except Exception as e:
            print(f"Failed to start application: {e}")
            return
            
        # 2. Find the Game's Window Handle
        self.game_hwnd = find_window_for_pid(self.game_process.pid)
        if not self.game_hwnd:
            print("Failed to find the application window. Terminating process.")
            self.game_process.terminate()
            return
            
        print(f"Found window handle (HWND): {self.game_hwnd}")

        # 3. Embed the Window
        # Create a QWindow object from the native window handle
        self.embedded_window = QWindow.fromWinId(self.game_hwnd)
        
        # Make this QWindow a child of the GameContainer widget
        # createWindowContainer is the magic function that makes a QWindow usable as a QWidget
        widget = QWidget.createWindowContainer(self.embedded_window, self)
        
        # Add the new widget to this container's layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        
        # --- Optional: For more seamless integration ---
        # Remove the embedded window's border, title bar, etc.
        # This makes it look like it's truly part of your app.
        style = win32gui.GetWindowLong(self.game_hwnd, win32con.GWL_STYLE)
        style &= ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME
        win32gui.SetWindowLong(self.game_hwnd, win32con.GWL_STYLE, style)
        
        # Force the window to redraw with the new style
        win32gui.SetWindowPos(self.game_hwnd, 0, 0, 0, 0, 0, 
                             win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | 
                             win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
        
    def closeEvent(self, event: QCloseEvent):
        """
        Clean up the game process when the window is closed.
        """
        print("Closing application...")
        if self.game_process and self.game_process.poll() is None:
            # If the process is still running, terminate it
            self.game_process.terminate()
            self.game_process.wait(timeout=5) # Wait for termination
        super().closeEvent(event)


class MainWindow(QMainWindow):
    """
    The main application window that will host the game container.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Game Embedding Example")
        self.setGeometry(100, 100, 1280, 720) # Set initial size
        
        # Create the central widget which will contain the game
        self.game_container = GameContainer(self)
        self.setCentralWidget(self.game_container)
        
    def closeEvent(self, event: QCloseEvent):
        """
        Pass the close event to the child container to handle process cleanup.
        """
        self.game_container.closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())