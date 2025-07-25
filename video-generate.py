import cv2
import os
import re
from tqdm import tqdm

def numerical_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def images_to_video(image_folder, output_video_path, fps=30):
    image_files = sorted([
        f for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ], key=numerical_sort_key)

    if not image_files:
        print("❌ 找不到图片文件")
        return

    first_image_path = os.path.join(image_folder, image_files[0])
    first_image = cv2.imread(first_image_path)
    height, width, _ = first_image.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    print(f"开始合成视频，共 {len(image_files)} 张图片。")

    for image_file in tqdm(image_files, desc="合成中", unit="帧"):
        image_path = os.path.join(image_folder, image_file)
        img = cv2.imread(image_path)

        if img is None:
            print(f"⚠️ 无法读取图片: {image_file}，已跳过")
            continue

        if len(img.shape) == 2 or img.shape[2] == 1:  # 灰度
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        if img.shape[:2] != (height, width):
            img = cv2.resize(img, (width, height))

        video_writer.write(img)

    video_writer.release()
    print(f"✅ 视频已保存到: {output_video_path}")


if __name__ == "__main__":
    # 示例参数：你可以修改以下路径和帧率
    folder_path = "output\color_image"  # 存放图片的文件夹
    output_path = "output\color_video.mp4"  # 输出视频路径
    frame_rate = 10

    images_to_video(folder_path, output_path, frame_rate)
