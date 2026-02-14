import pyautogui
import subprocess
import time
import pyperclip
import ctypes
from ctypes import wintypes

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

print("=== 管理员权限下的记事本测试 ===")

# 1. 打开记事本
print("[1/5] 打开记事本...")
proc = subprocess.Popen(['notepad.exe'])
time.sleep(2)

# 2. 找到并激活窗口（管理员权限应该能正确激活）
print("[2/5] 激活记事本窗口...")
user32 = ctypes.windll.user32

def get_notepad():
    handles = []
    def enum_proc(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if "记事本" in buf.value or "Notepad" in buf.value or "无标题" in buf.value:
                    handles.append(hwnd)
        return True
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_proc), 0)
    return handles[0] if handles else None

hwnd = get_notepad()
if hwnd:
    print(f"找到窗口: {hwnd}")
    # 强制前台
    user32.SetForegroundWindow(hwnd)
    # 恢复并最大化
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    time.sleep(0.3)
    user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    time.sleep(1)
else:
    print("未找到窗口，使用快捷键...")
    pyautogui.keyDown('alt')
    pyautogui.keyDown('tab')
    pyautogui.keyUp('tab')
    pyautogui.keyUp('alt')
    time.sleep(1)

# 3. 复制中文
print("[3/5] 复制文字到剪贴板...")
pyperclip.copy("小雨，我很想你")
time.sleep(0.5)

# 4. 点击编辑区
print("[4/5] 点击编辑区...")
if hwnd:
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = wintypes.POINT(rect.left + (rect.right-rect.left)//2, 
                           rect.top + (rect.bottom-rect.top)//2)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    pyautogui.click(point.x, point.y)
else:
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 3)

time.sleep(0.5)

# 5. 粘贴
print("[5/5] 粘贴文字...")
pyautogui.hotkey('ctrl', 'v')
time.sleep(1)

print("=== 完成！===")

# 截图验证
try:
    screenshot = pyautogui.screenshot()
    screenshot.save("C:/Users/Admin/.openclaw/workspace/admin_test_result.png")
    print("已保存截图: admin_test_result.png")
except:
    print("截图失败")
