import subprocess
import os
import time
import win32gui
import win32process
import psutil

def get_all_hwnds():
    hwnds_info = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            p = psutil.Process(pid)
            ppid = p.ppid()
            hwnds_info.append((hwnd, title, pid, ppid))
        return True
    
    win32gui.EnumWindows(callback, None)
    return hwnds_info

def find_main_window_for_pid(pid):
    processes = get_all_hwnds()
    for process in processes:
        print(f"{process[1]}: {process[0]} (hwnd), {process[2]} (pid), {process[3]} (ppid)")
        if process[3] == pid:
            return process
    print("---\n\n")
    return None

def run_process_and_get_hwnd(exe_path, timeout=100):
    proc = subprocess.Popen([exe_path])
    launched_pid = proc.pid
    
    my_pid = os.getpid()
    print(f"Python script is running with PID: {my_pid}")
    print(f"Launched {exe_path} with PID: {launched_pid}")
    print(f"Searching for the main window of PID {launched_pid}...")

    hwnd = None
    start_time = time.time()

    while time.time() - start_time < timeout:
        hwnd = find_main_window_for_pid(launched_pid)
        if hwnd:
            # Found it!
            break
        # Wait a bit before trying again
        time.sleep(0.25)
    
    # If the loop finishes, hwnd will be None or the found handle
    return hwnd


if __name__ == "__main__":
    notepad_path = "notepad.exe"
    hwnd = run_process_and_get_hwnd(notepad_path)

    if hwnd:
        title = win32gui.GetWindowText(hwnd)
        print(f"\n✅ Found window!")
        print(f"   -> HWND:  {hwnd}")
        print(f"   -> Title: '{title}'")
    else:
        print(f"\n❌ Could not find the main window for {notepad_path} within the timeout period.")