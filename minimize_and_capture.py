import pyautogui
import ctypes
from ctypes import wintypes
import time

def minimize_browser():
    """最小化所有浏览器窗口"""
    user32 = ctypes.windll.user32
    
    def enum_proc(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value.lower()
                # 匹配浏览器窗口
                if any(x in title for x in ['chrome', 'edge', 'firefox', 'openclaw control']):
                    user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE = 6
        return True
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_proc), 0)

# 最小化浏览器
print("正在最小化浏览器窗口...")
minimize_browser()
time.sleep(1)

# 全屏截图
print("正在截图...")
screenshot = pyautogui.screenshot()
screenshot.save("C:/Users/Admin/.openclaw/workspace/fullscreen.png")
print("已保存全屏截图")
