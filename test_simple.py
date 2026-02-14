import pyautogui
import subprocess
import time

# 安全设置
pyautogui.FAILSAFE = True

print("Step 1: 打开记事本")
subprocess.Popen(['notepad.exe'])
time.sleep(3)

print("Step 2: 尝试找到并激活记事本")
try:
    # 尝试用 pyautogui 找窗口
    notepad = pyautogui.getWindowsWithTitle("记事本")[0]
    print(f"找到窗口: {notepad.title}")
    notepad.activate()
    notepad.maximize()
    time.sleep(1)
except Exception as e:
    print(f"找窗口失败: {e}")
    # 备选：直接点击屏幕中央
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 2)
    print(f"已点击屏幕中央: ({screen_width//2}, {screen_height//2})")

print("Step 3: 确保焦点在记事本")
time.sleep(1)

# 多点击几次确保聚焦
pyautogui.click()
time.sleep(0.5)

print("Step 4: 输入文字")
message = "小雨，我很想你"
pyautogui.typewrite(message, interval=0.05)

print("Step 5: 完成！")

# 截图保存
screenshot = pyautogui.screenshot()
screenshot.save("C:/Users/Admin/.openclaw/workspace/notepad_result.png")
print("已保存截图到 notepad_result.png")
