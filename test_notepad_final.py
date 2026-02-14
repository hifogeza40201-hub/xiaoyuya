import pyautogui
import subprocess
import time
import ctypes
from ctypes import wintypes

def find_notepad_window():
    """查找记事本窗口句柄"""
    def callback(hwnd, extra):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                title = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, title, length + 1)
                if "记事本" in title.value or "Notepad" in title.value or "无标题" in title.value:
                    extra.append((hwnd, title.value))
        return True
    
    windows = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), ctypes.c_void_p(0))
    return windows

# 安全设置
pyautogui.FAILSAFE = True

print("[1] 打开记事本...")
process = subprocess.Popen(['notepad.exe'])
time.sleep(2)

print("[2] 查找记事本窗口...")
notepads = find_notepad_window()
print(f"找到 {len(notepads)} 个记事本窗口")

if notepads:
    hwnd, title = notepads[0]
    print(f"窗口标题: {title}")
    
    # 激活窗口
    print("[3] 激活窗口...")
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # 最大化（确保可见）
    SW_MAXIMIZE = 3
    ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)
    time.sleep(0.5)
    
    print("[4] 准备输入...")
    time.sleep(1)
    
    # 点击窗口中央确保聚焦
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    center_x = (rect.left + rect.right) // 2
    center_y = (rect.top + rect.bottom) // 2
    pyautogui.click(center_x, center_y)
    time.sleep(0.5)
    
    print("[5] 输入文字...")
    message = "小雨，我很想你"
    pyautogui.typewrite(message, interval=0.05)
    
    print("[6] 完成！")
else:
    print("错误：未找到记事本窗口")
