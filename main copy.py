# -*- coding: utf-8 -*-
"""
深度相机ROS Bag文件回放与可视化程序
功能：从Orbbec相机生成的ROS Bag文件中读取深度帧和彩色帧，进行深度图可视化、图像保存及视频录制
依赖：Orbbec SDK（pyorbbecsdk）、OpenCV（cv2）、数值计算（numpy）、系统操作（sys）
"""

# ---------------------------- 基础库与模块导入 ----------------------------
import sys                  # Python系统模块，用于处理命令行参数、退出程序等
import cv2                  # OpenCV库，用于图像处理、视频读写、窗口显示等
import numpy as np          # 数值计算库，用于处理深度数据的数组运算
from pyorbbecsdk import *   # Orbbec相机官方SDK，提供深度相机数据读取、管道（Pipeline）控制等功能
from utils import frame_to_bgr_image  # 自定义工具函数，用于将相机帧转换为BGR格式图像（OpenCV兼容格式）

ESC_KEY = 27               # ESC键的ASCII码值（十进制），用于监听用户退出按键


# ---------------------------- 播放状态回调函数 ----------------------------
def playback_state_callback(state):
    """
    播放器状态变化的回调函数（当Bag文件播放状态改变时触发）
    参数：
        state (OBMediaState): 播放器状态枚举值（来自Orbbec SDK）
    """
    if state == OBMediaState.OB_MEDIA_BEGIN:
        # 注意：根据常规逻辑，"BEGIN"可能表示播放开始，但此处打印"停止"，可能为SDK定义或代码笔误
        print("Bag player stopped")  # 状态提示（可能与实际状态名存在语义偏差）
    elif state == OBMediaState.OB_MEDIA_END:
        # 注意："END"可能表示播放结束，但此处打印"播放中"，可能为SDK定义或代码笔误
        print("Bag player playing")  # 状态提示（可能与实际状态名存在语义偏差）
    elif state == OBMediaState.OB_MEDIA_PAUSED:
        print("Bag player paused")   # 播放暂停状态提示（逻辑一致）


# ---------------------------- 彩色帧获取函数 ----------------------------
def get_color_frame(frames):
    """
    从帧集合中提取并转换彩色帧为BGR格式（OpenCV兼容）
    参数：
        frames (FrameSet): Orbbec SDK的帧集合对象（包含深度帧、彩色帧等）
    返回：
        numpy.ndarray/None: BGR格式的彩色图像（若获取失败返回None）
    """
    # 从帧集合中获取彩色帧（可能为None，若当前帧无彩色数据）
    color_frame = frames.get_color_frame()
    if color_frame is None:
        return None  # 无彩色帧时返回None
    
    # 将原始彩色帧转换为BGR格式（OpenCV默认使用BGR而非RGB）
    color_image = frame_to_bgr_image(color_frame)
    if color_image is None:
        print("failed to convert frame to image")  # 转换失败提示
        return None  # 转换失败时返回None
    
    return color_image  # 返回BGR格式的彩色图像


# ---------------------------- 主函数（程序入口） ----------------------------
def main():
    """
    主函数：完成深度相机Bag文件回放、深度图可视化、图像保存及视频录制的全流程控制
    """
    # -------------------- 初始化阶段 --------------------
    # 创建Pipeline对象，指定要回放的ROS Bag文件路径（./test.bag）
    # Pipeline是Orbbec SDK的核心类，用于管理数据读取、设备控制等流程
    pipeline = Pipeline("./test.bag")
    
    # 从Pipeline中获取回放控制器（用于控制Bag文件的播放状态）
    playback = pipeline.get_playback()
    
    # 设置播放状态回调函数（当播放状态变化时触发playback_state_callback）
    playback.set_playback_state_callback(playback_state_callback)
    
    # 获取设备信息（如相机型号、序列号、固件版本等）并打印
    device_info = playback.get_device_info()
    print("Device info: ", device_info)
    
    # 获取相机参数（如内参矩阵、畸变系数、深度比例尺等）并打印
    camera_param = pipeline.get_camera_param()
    print("Camera param: ", camera_param)
    
    # 启动Pipeline（开始从Bag文件中读取并解析数据）
    pipeline.start()


    # -------------------- 主循环（持续处理帧数据） --------------------
    try:
        idx = 0  # 帧索引（用于图片命名和视频录制）
        while True:  # 无限循环，直到用户主动退出
            # 从Pipeline中等待获取一帧数据（超时时间100ms）
            # wait_for_frames()返回FrameSet对象（包含同步的深度帧、彩色帧等）
            frames = pipeline.wait_for_frames(100)
            if frames is None:  # 超时未获取到有效帧时跳过当前循环
                continue
            
            # 从帧集合中提取深度帧（可能为None，若当前帧无深度数据）
            depth_frame = frames.get_depth_frame()
            if depth_frame is None:  # 无深度帧时跳过当前循环
                continue
            
            images = []  # 存储待显示/保存的图像（深度图+彩色图）
            
            # -------------------- 深度数据处理 --------------------
            # 获取深度帧的分辨率（宽高）
            width = depth_frame.get_width()
            height = depth_frame.get_height()
            # 获取深度比例尺（将原始深度值转换为实际距离的系数，单位：米/单位值）
            scale = depth_frame.get_depth_scale()
            
            # 从深度帧中提取原始数据（uint16类型数组，存储原始深度值）
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            # 重塑为一维数组为二维矩阵（形状：[高度, 宽度]）
            depth_data = depth_data.reshape((height, width))
            # 转换为浮点型并乘以比例尺，得到实际深度值（单位：米）
            depth_data = depth_data.astype(np.float32) * scale
            
            # 归一化深度值到0-255范围（便于显示），并转换为8位无符号整型
            depth_image = cv2.normalize(
                depth_data,          # 输入深度数据
                None,                # 输出数组（不指定时自动创建）
                0, 255,              # 归一化目标范围
                cv2.NORM_MINMAX,     # 归一化方法（最小-最大值拉伸）
                dtype=cv2.CV_8U    # 输出数据类型（8位无符号整型）
            )
            # 应用伪彩色映射（COLORMAP_JET：蓝-青-黄-红渐变，增强深度差异可视化）
            depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)
            
            # -------------------- 彩色帧获取 --------------------
            # 调用自定义函数获取BGR格式的彩色图像
            color_image = get_color_frame(frames)
            
            # -------------------- 图像保存 --------------------
            # 若深度图有效，添加到待显示列表并保存为PNG
            if depth_image is not None:
                images.append(depth_image)
                cv2.imwrite(f"output/depth_image/depth_{idx}.png", depth_image)  # 保存深度图
            
            # 若彩色图有效，添加到待显示列表并保存为PNG
            if color_image is not None:
                images.append(color_image)
                cv2.imwrite(f"output/color_image/color_{idx}.png", color_image)  # 保存彩色图
            
            # -------------------- 实时显示与视频录制 --------------------
            if len(images) > 0:  # 若有待显示的图像
                images_to_show = []  # 存储调整尺寸后的图像（用于显示和视频）
                
                # 将每张图像缩放到640x480（统一尺寸便于拼接和显示）
                for img in images:
                    img = cv2.resize(img, (640, 480))
                    images_to_show.append(img)
                
                # -------------------- 视频录制初始化（仅首次循环执行） --------------------
                if idx == 0:
                    # 定义视频编码格式（mp4v对应MPEG-4编码）
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    # 创建VideoWriter对象，参数：
                    # - 输出路径：'output/playback_viewer.mp4'
                    # - 编码格式：fourcc
                    # - 帧率：30fps（需与实际回放帧率匹配）
                    # - 帧尺寸：单张图像宽度×图像数量（水平拼接后的总宽度），单张图像高度
                    video_writer = cv2.VideoWriter(
                        'output/playback_viewer.mp4',
                        fourcc,
                        30,
                        (images_to_show[0].shape[1] * len(images_to_show), images_to_show[0].shape[0])
                    )
                
                # 将水平拼接的多张图像写入视频文件
                video_writer.write(np.hstack(images_to_show))
                
                # 实时显示拼接后的画面（窗口标题："playbackViewer"）
                cv2.imshow("playbackViewer", np.hstack(images_to_show))
            
            # 监听用户按键（阻塞1ms，避免CPU高占用）
            key = cv2.waitKey(1)
            idx += 1  # 帧索引自增
            
            # 退出条件：按下'q'键或ESC键（ASCII码27）
            if key == ord('q') or key == ESC_KEY:
                # 释放视频写入器（避免资源泄漏）
                video_writer.release()
                # 停止Pipeline（停止回放Bag文件）
                if pipeline:
                    pipeline.stop()
                # 关闭所有OpenCV窗口
                cv2.destroyAllWindows()
                break  # 退出主循环


    # -------------------- 异常处理 --------------------
    except KeyboardInterrupt:  # 捕获用户强制终止信号（如Ctrl+C）
        # 停止Pipeline（确保资源释放）
        if pipeline:
            pipeline.stop()
        # 退出程序（返回状态码0表示正常退出）
        sys.exit(0)


# 程序入口：当脚本直接运行时执行main函数
if __name__ == "__main__":
    main()