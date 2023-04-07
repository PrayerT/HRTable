import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm

# 将 face_cascade 定义为全局变量
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def detect_face(image):
    global face_cascade
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return None

    return faces[0]

def crop_face(image, face_center, face_radius):
    mask = np.zeros_like(image)
    cv2.circle(mask, face_center, face_radius, (255, 255, 255), -1)
    return cv2.bitwise_and(image, mask)

def rotate_text(image, text, angle):
    arial_font_path = fm.findfont(fm.FontProperties(family='Arial'))
    font = ImageFont.truetype(arial_font_path, 20)
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)
    text_size = draw.textsize(text, font)
    text_image = Image.new('RGBA', text_size, (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), text, font=font, fill=(0, 0, 0, 255))
    rotated_text = text_image.rotate(angle, expand=True, resample=Image.BICUBIC)
    image_pil.paste(rotated_text, (0, 0), rotated_text)
    return cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

def add_name_to_image(image, name):
    text_position = (image.shape[1] - 80, 20)
    rotated_text = rotate_text(image, name, 30)
    cv2.putText(rotated_text, name, text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return rotated_text

def process_all_images(input_folder, output_folder):
    # 在这里实现批量处理图片功能
    for image_name in os.listdir(input_folder):
        image_path = os.path.join(input_folder, image_name)
        image = cv2.imread(image_path)

        if image is None:
            print(f"无法加载图片: {image_name}")
            continue
        
        face = detect_face(image)
        if face is None:
            print(f"无法检测到人脸: {image_name}")
            continue
        
        face_center = (face[0] + face[2] // 2, face[1] + face[3] // 2)
        face_radius = min(face[2], face[3]) // 2
        cropped_face = crop_face(image, face_center, face_radius)
        
        name = os.path.splitext(image_name)[0]
        named_image = add_name_to_image(cropped_face, name)

        output_path = os.path.join(output_folder, f"{name}头像.jpg")
        cv2.imwrite(output_path, named_image)

    # 调用 remove_deleted_images 函数删除已删除图片的头像
    remove_deleted_images(input_folder, output_folder)

def remove_deleted_images(input_folder, output_folder):
    input_images = {os.path.splitext(image_name)[0] for image_name in os.listdir(input_folder)}
    output_images = {os.path.splitext(image_name)[0].rstrip('头像') for image_name in os.listdir(output_folder)}

    for name in output_images - input_images:
        output_image_path = os.path.join(output_folder, f"{name}头像.jpg")
        os.remove(output_image_path)
