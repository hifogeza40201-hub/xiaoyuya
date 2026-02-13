import pyautogui
import subprocess
import time

# 安全设置：移动到屏幕角落会触发安全退出
pyautogui.FAILSAFE = True

print("小雨正在打开记事本...")

# 1. 打开记事本
subprocess.Popen(['notepad.exe'])

# 2. 等待记事本窗口打开
time.sleep(2)

# 3. 输入文字
message = "小雨，我很想你"
print(f"正在输入: {message}")
pyautogui.typewrite(message, interval=0.1)

print("完成！")
