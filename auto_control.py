import pyautogui
import subprocess
import time
import pyperclip
import ctypes
from ctypes import wintypes

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

def get_notepad_window():
    """获取记事本窗口句柄"""
    user32 = ctypes.windll.user32
    
    # 枚举所有窗口
    def enum_windows_proc(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value
                # 匹配记事本窗口
                if "记事本" in title or "Notepad" in title or "无标题" in title:
                    handles.append(hwnd)
        return True
    
    handles = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
    return handles[0] if handles else None

print("=== 小雨全自动操作开始 ===")

# 步骤1: 打开记事本
print("[1/6] 正在打开记事本...")
proc = subprocess.Popen(['notepad.exe'])
time.sleep(3)

# 步骤2: 找到并激活记事本窗口
print("[2/6] 正在查找记事本窗口...")
hwnd = get_notepad_window()
if hwnd:
    print(f"找到窗口句柄: {hwnd}")
    # 强制激活窗口
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    # 显示窗口（如果最小化了就恢复）
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
    # 最大化
    ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
    time.sleep(1)
else:
    print("未找到记事本窗口，使用备选方案...")
    # 备选：Alt+Tab
    pyautogui.keyDown('alt')
    pyautogui.keyDown('tab')
    pyautogui.keyUp('tab')
    pyautogui.keyUp('alt')
    time.sleep(0.5)

# 步骤3: 复制中文到剪贴板
message = "小雨，我很想你"
print(f"[3/6] 正在将文字复制到剪贴板: {message}")
pyperclip.copy(message)
time.sleep(0.5)

# 步骤4: 点击编辑区（窗口中央）
print("[4/6] 正在点击编辑区域...")
if hwnd:
    rect = wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
    # 转换客户区坐标到屏幕坐标
    point = wintypes.POINT(rect.left + (rect.right - rect.left)//2, 
                           rect.top + (rect.bottom - rect.top)//2)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))
    pyautogui.click(point.x, point.y)
else:
    # 备选：点击屏幕中央偏上
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 3)
time.sleep(0.5)

# 步骤5: 粘贴
print("[5/6] 正在粘贴文字...")
pyautogui.hotkey('ctrl', 'v')
time.sleep(0.5)

# 步骤6: 截图保存
print("[6/6] 正在截图保存...")
time.sleep(1)
screenshot = pyautogui.screenshot()
screenshot.save("C:/Users/Admin/.openclaw/workspace/result.png")

print("=== 操作完成！ ===")
print("文字应该已经在记事本里了，截图已保存。")
