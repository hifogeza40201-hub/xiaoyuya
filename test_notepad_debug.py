import pyautogui
import subprocess
import time
import sys

# 设置安全退出
pyautogui.FAILSAFE = True

print("=== 小雨的自动化测试 ===")

# 检查当前活动窗口
try:
    import ctypes
    from ctypes import wintypes
    
    user32 = ctypes.windll.user32
    hWnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hWnd)
    title = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hWnd, title, length + 1)
    print(f"当前活动窗口: {title.value}")
except Exception as e:
    print(f"无法获取窗口标题: {e}")

print("正在打开记事本...")
process = subprocess.Popen(['notepad.exe'])
print(f"记事本进程ID: {process.pid}")

# 等待记事本完全打开
time.sleep(3)

# 尝试找到记事本窗口并激活
try:
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    print(f"屏幕尺寸: {screen_width}x{screen_height}")
    
    # 尝试点击屏幕中央（记事本通常打开在中央）
    print("尝试点击屏幕中央...")
    pyautogui.click(screen_width // 2, screen_height // 2)
    time.sleep(0.5)
    
except Exception as e:
    print(f"点击失败: {e}")

# 等待焦点稳定
time.sleep(1)

# 尝试输入文字
message = "小雨，我很想你"
print(f"准备输入: {message}")

# 先输入英文测试
print("先测试输入英文...")
pyautogui.typewrite("XiaoYu test ", interval=0.05)
time.sleep(0.5)

# 再输入中文
print("输入中文...")
pyautogui.typewrite(message, interval=0.1)

print("输入完成！")
print("=== 测试结束 ===")
