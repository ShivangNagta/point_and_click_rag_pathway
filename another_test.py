import ctypes
from ctypes import wintypes
from PyQt6.QtGui import QWindow
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication, QPushButton

def get_window_id(name: str):
    """
    Get the HWND (window handle) of a top-level window with the given title.
    Works on Windows.
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    IsWindowVisible = user32.IsWindowVisible
    GetWindowTextLength = user32.GetWindowTextLengthW
    GetWindowText = user32.GetWindowTextW

    results = []

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                window_name = buff.value
                if window_name == name:  # exact match
                    results.append(hwnd)
                    return False  # stop enumeration
        return True  # continue

    EnumWindows(EnumWindowsProc(foreach_window), 0)

    return results[0] if results else None

def run_app(window_id):
    app = QApplication([])
    main_widget = QWidget()
    layout = QVBoxLayout(main_widget)

    window = QWindow.fromWinId(window_id)
    widget = QWidget.createWindowContainer(window)
    layout.addWidget(widget)

    button = QPushButton('Close')
    button.clicked.connect(main_widget.close)
    layout.addWidget(button)

    main_widget.show()
    app.exec()

if __name__ == '__main__':
    window_id = get_window_id('WhatsApp')
    if window_id:
        run_app(window_id)
    else:
        print("Couldn't find!")