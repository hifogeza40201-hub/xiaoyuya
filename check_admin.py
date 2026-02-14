import ctypes
import sys
import os

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_privileges():
    print("=== 权限检查 ===")
    
    # 1. 检查管理员权限
    admin = is_admin()
    print(f"[1/4] 管理员权限: {'✅ 是' if admin else '❌ 否'}")
    
    # 2. 检查能否写入系统目录
    try:
        test_file = "C:\\Windows\\Temp\\openclaw_test.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        sys_write = True
    except:
        sys_write = False
    print(f"[2/4] 系统目录写入: {'✅ 可以' if sys_write else '❌ 不可以'}")
    
    # 3. 检查当前用户
    print(f"[3/4] 当前用户: {os.getlogin()}")
    
    # 4. 检查进程信息
    print(f"[4/4] 进程PID: {os.getpid()}")
    
    print("\n=== 总结 ===")
    if admin:
        print("✅ 小雨现在拥有管理员权限！")
        print("可以执行：系统修改、服务管理、完整桌面控制")
    else:
        print("❌ 仍然没有管理员权限")
        print("可能原因：计划任务未生效，或需要重启")
    
    return admin

if __name__ == "__main__":
    is_admin()
