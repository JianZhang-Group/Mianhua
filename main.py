import win32gui
import win32con
import time
import threading
import cv2
# 其他原有导入...

def close_playback_window():
    """查找并关闭名为'playbackViewer'的窗口"""
    print("正在尝试关闭 playbackViewer 窗口...")
    
    # 等待一段时间，确保窗口已经创建
    for attempt in range(10):  # 最多尝试10次
        time.sleep(0.5)  # 每次检查间隔0.5秒
        
        # 查找窗口句柄
        hwnd = win32gui.FindWindow(None, "playbackViewer")
        if hwnd:
            print(f"找到窗口句柄: {hwnd}, 正在关闭...")
            # 发送关闭消息
            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return True
        else:
            print(f"第{attempt+1}次检查：未找到窗口")
    
    print("未能找到或关闭 playbackViewer 窗口")
    return False

def your_main_function():  # 这里替换为您的主函数名
    """您原来的主函数代码"""
    try:
        # 初始化代码...
        
        # 启动关闭窗口的线程
        close_thread = threading.Thread(target=close_playback_window)
        close_thread.daemon = True  # 设为守护线程，主程序退出时，此线程也会退出
        close_thread.start()
        
        # 原有的主程序逻辑...
        # 包括OrbbecSDK的初始化、相机操作、数据处理等
        
        # 等待足够的时间让关闭窗口的线程工作
        time.sleep(2)
        
        # 继续执行其他操作...
        
    except Exception as e:
        print(f"程序执行出错: {e}")
    finally:
        # 清理代码...
        pass

if __name__ == "__main__":
    your_main_function()  # 调用您的主函数