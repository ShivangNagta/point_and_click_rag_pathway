import time
import os
from datetime import datetime
import pygetwindow as gw
from pynput import mouse
import platform
from PIL import ImageGrab
import ctypes

TARGET_APP_NAME = ""
SCREENSHOT_FOLDER = "./screenshots"
SCREENSHOT_WAIT_SEC = 0.8

ctypes.windll.shcore.SetProcessDpiAwareness(2)

'''
cd reinforced_game_rag
conda activate pathway
python window_embedding.py
'''
def screenshot_window(active_window):
    bbox = (active_window.left, active_window.top, active_window.right, active_window.bottom)
    screenshot = ImageGrab.grab(bbox=bbox)

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filepath = os.path.join(SCREENSHOT_FOLDER, f"click_{timestamp_str}.png")
    screenshot.save(filepath)

def on_click(x, y, button, pressed):
    if pressed:
        try:
            active_window = gw.getActiveWindow()
            if active_window and TARGET_APP_NAME.lower() in active_window.title.lower():
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                relative_x = x - active_window.left
                relative_y = y - active_window.top
                print(
                    f"[{timestamp}] Click detected on '{active_window.title}' | "
                    f"Button: {button} | Relative Position: ({relative_x}, {relative_y})"
                )

                if (0 <= relative_x and relative_x <= active_window.width and 0 <= relative_y and relative_y <= active_window.height):
                    time.sleep(SCREENSHOT_WAIT_SEC)
                    screenshot_window(active_window)
        except Exception as e:
            # This handles cases where there might not be an active window (e.g., clicking on the desktop).
            # We can ignore these errors silently.
            pass

def main():
    global TARGET_APP_NAME
    TARGET_APP_NAME = input("Enter the name of the application window to track (e.g., 'Notepad', 'Chrome'): ")

    if not TARGET_APP_NAME:
        print("Error: Application name cannot be empty.")
        return
    
    listener = mouse.Listener(on_click=on_click)
    listener.start()

    try:
        while True:
            window_titles = gw.getAllTitles()
            app_is_running = any(TARGET_APP_NAME.lower() in title.lower() for title in window_titles if title)

            if not app_is_running:
                print(f"\n[*] Target application '{TARGET_APP_NAME}' appears to be closed.")
                break

            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Tracker stopped by user.")
    finally:
        print("[*] Shutting down listener and exiting.")
        listener.stop()

if __name__ == "__main__":
    main()
