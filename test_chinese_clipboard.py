import pyautogui
import subprocess
import time
import pyperclip

pyautogui.FAILSAFE = True

print("=== 小雨的记事本测试（剪贴板版）===")

# 1. 打开记事本
print("[1/4] 打开记事本...")
subprocess.Popen(['notepad.exe'])
time.sleep(2)

# 2. 复制中文到剪贴板
message = "小雨，我很想你"
print(f"[2/4] 复制文字到剪贴板: {message}")
pyperclip.copy(message)

# 3. 最大化并聚焦窗口
print("[3/4] 聚焦记事本窗口...")
pyautogui.keyDown('alt')
pyautogui.keyDown('tab')
pyautogui.keyUp('tab')
pyautogui.keyUp('alt')
time.sleep(0.5)

pyautogui.keyDown('win')
pyautogui.keyDown('up')
pyautogui.keyUp('up')
pyautogui.keyUp('win')
time.sleep(0.5)

# 4. 粘贴
print("[4/4] 粘贴文字...")
pyautogui.keyDown('ctrl')
pyautogui.keyDown('v')
pyautogui.keyUp('v')
pyautogui.keyUp('ctrl')

print("=== 完成！ ===")
