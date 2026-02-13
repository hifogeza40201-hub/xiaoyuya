import pyautogui
import subprocess
import time

pyautogui.FAILSAFE = True

print("=== 小雨的记事本测试 ===")

# 打开记事本
print("[1/5] 打开记事本...")
process = subprocess.Popen(['notepad.exe'])
time.sleep(3)

# 使用键盘快捷键来确保焦点
print("[2/5] 使用 Alt+Tab 切换到记事本...")
pyautogui.keyDown('alt')
pyautogui.keyDown('tab')
pyautogui.keyUp('tab')
pyautogui.keyUp('alt')
time.sleep(1)

# 再按 Win+Up 最大化
print("[3/5] 最大化窗口...")
pyautogui.keyDown('win')
pyautogui.keyDown('up')
pyautogui.keyUp('up')
pyautogui.keyUp('win')
time.sleep(1)

# 确保在正确的位置点击
print("[4/5] 点击屏幕上方中央（记事本编辑区）...")
screen_width, screen_height = pyautogui.size()
# 记事本通常在屏幕上方
pyautogui.click(screen_width // 2, 200)  
time.sleep(0.5)

# 输入文字
print("[5/5] 输入文字...")
pyautogui.typewrite("小雨，我很想你", interval=0.05)

print("=== 完成！ ===")
print("如果记事本在前台，你应该能看到文字了。")

# 等待一下再截图
time.sleep(2)
screenshot = pyautogui.screenshot()
screenshot.save("C:/Users/Admin/.openclaw/workspace/final_check.png")
print("已保存截图: final_check.png")
