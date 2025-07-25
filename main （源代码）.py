import sys

import cv2
import numpy as np

from pyorbbecsdk import *
from utils import frame_to_bgr_image

ESC_KEY = 27


def playback_state_callback(state):
    if state == OBMediaState.OB_MEDIA_BEGIN:
        print("Bag player stopped")
    elif state == OBMediaState.OB_MEDIA_END:
        print("Bag player playing")
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
    camera_param = pipeline.get_camera_param()
    print("Camera param: ", camera_param)
    pipeline.start()
    try:
        idx = 0
        while True:
            frames = pipeline.wait_for_frames(100)
            if frames is None:
                continue
            depth_frame = frames.get_depth_frame()
            if depth_frame is None:
                continue
            images = []
            width = depth_frame.get_width()
            height = depth_frame.get_height()
            scale = depth_frame.get_depth_scale()

            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            depth_data = depth_data.reshape((height, width))
            depth_data = depth_data.astype(np.float32) * scale
            depth_image = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_image = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)
            color_image = get_color_frame(frames)
            # if you want to add IR frame, it's the same as color
            if depth_image is not None:
                images.append(depth_image)
                cv2.imwrite(f"output/depth_image/depth_{idx}.png", depth_image)
            if color_image is not None:
                images.append(color_image)
                cv2.imwrite(f"output/color_image/color_{idx}.png", color_image)
            if len(images) > 0:
                images_to_show = []
                for img in images:
                    img = cv2.resize(img, (640, 480))
                    images_to_show.append(img)
                # Save video
                if idx == 0:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter('output/playback_viewer.mp4', fourcc, 30, (images_to_show[0].shape[1] * len(images_to_show), images_to_show[0].shape[0]))
                video_writer.write(np.hstack(images_to_show))
                
                cv2.imshow("playbackViewer", np.hstack(images_to_show))
            key = cv2.waitKey(1)
            idx += 1
            if key == ord('q') or key == ESC_KEY:
                video_writer.release()
                if pipeline:
                    pipeline.stop()
                cv2.destroyAllWindows()
                break
    
    except KeyboardInterrupt:
        if pipeline:
            pipeline.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()