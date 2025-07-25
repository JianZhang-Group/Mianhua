import sys
import cv2
import numpy as np
from pyorbbecsdk import *
from utils import frame_to_bgr_image

WAIT_FOR_NEXT_FRAME_TIMEOUT = 4000  # 毫秒

def playback_state_callback(state):
    if state == OBMediaState.OB_MEDIA_BEGIN:
        print("Bag player playing")
    elif state == OBMediaState.OB_MEDIA_END:
        print("Bag player stopped")
    elif state == OBMediaState.OB_MEDIA_PAUSED:
        print("Bag player paused")

def get_color_frame(frames):
    color_frame = frames.get_color_frame()
    if color_frame is None:
        return None
    color_image = frame_to_bgr_image(color_frame)
    if color_image is None:
        print("failed to convert frame to image")
        return None
    return color_image

def main():
    pipeline = Pipeline("./test.bag")
    playback = pipeline.get_playback()
    playback.set_playback_state_callback(playback_state_callback)
    device_info = playback.get_device_info()
    print("Device info: ", device_info)
    # 保存设备信息到文件
    with open("./output/info/device_info.txt", "w") as f:
        f.write(str(device_info))
    camera_param = pipeline.get_camera_param()
    print("Camera param: ", camera_param)
    # 保存相机参数到文件
    with open("./output/info/camera_param.txt", "w") as f:
        f.write(str(camera_param))
    pipeline.start()
    try:
        idx = 0
        while True:
            frames = pipeline.wait_for_frames(WAIT_FOR_NEXT_FRAME_TIMEOUT)
            if frames is None:
                continue

            depth_frame = frames.get_depth_frame()
            if depth_frame is None:
                continue

            # 处理深度图
            width = depth_frame.get_width()
            height = depth_frame.get_height()
            scale = depth_frame.get_depth_scale()
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16).reshape((height, width))
            depth_data = depth_data.astype(np.float32) * scale
            depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)
            cv2.imwrite(f"output/depth_image/depth_{idx}.png", depth_image)
            
            # 保存深度图到视频
            # depth_video_path = "output/videos/depth_video.mp4"
            # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # depth_video_writer = cv2.VideoWriter(depth_video_path, fourcc, 30, (width, height))
            # depth_video_writer.write(depth_image)
            
            # 处理彩色图
            color_image = get_color_frame(frames)
            cv2.imwrite(f"output/color_image/color_{idx}.png", color_image)

            # 保存彩色图到视频
            # color_video_path = "output/videos/color_video.mp4"
            # color_video_writer = cv2.VideoWriter(color_video_path, fourcc, 30, (width, height))
            # color_video_writer.write(color_image)  

            # 将深度图和彩色图拼接
            # combined_image = cv2.hconcat([depth_image, color_image]) if color_image is not None else depth_image
            # cv2.imwrite(f"output/combined_image/combined_{idx}.png", combined_image)
            
            # 保存拼接图到视频
            # combined_video_path = "output/videos/combined_video.mp4"
            # combined_video_writer = cv2.VideoWriter(combined_video_path, fourcc, 30, (width * 2, height))
            # combined_video_writer.write(combined_image)

            idx += 1

    except KeyboardInterrupt:
        print("Playback interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        # depth_video_writer.release()
        # color_video_writer.release()
        sys.exit(0)
            

if __name__ == "__main__":
    main()
