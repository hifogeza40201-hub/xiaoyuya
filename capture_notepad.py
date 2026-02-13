import pyautogui
import ctypes
from ctypes import wintypes
import time

def capture_notepad():
    user32 = ctypes.windll.user32
    
    # 找到记事本窗口
    def enum_proc(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                if "记事本" in buffer.value or "Notepad" in buffer.value:
                    handles.append(hwnd)
        return True
    
    handles = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_proc), 0)
    
    if not handles:
        print("未找到记事本窗口")
        return False
    
    hwnd = handles[0]
    print(f"找到记事本窗口: {hwnd}")
    
    # 获取窗口位置和大小
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    left = rect.left
    top = rect.top
    
    print(f"窗口位置: ({left}, {top}), 大小: {width}x{height}")
    
    # 截图指定区域
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot.save("C:/Users/Admin/.openclaw/workspace/notepad_only.png")
    print("已保存记事本窗口截图")
    return True

capture_notepad()
