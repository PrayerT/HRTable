import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm
from datetime import datetime

# 将 face_cascade 定义为全局变量
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def detect_face(image):
    global face_cascade
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return None

    return faces[0]

def crop_face(image, face_center, max_distance):
    height, width, channels = image.shape
    
    if channels == 3:
        # 将输入图像转换为具有透明通道的 4 通道图像
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # 创建一个透明底的正方形
    square_size = 2 * max_distance
    square = np.zeros((square_size, square_size, 4), dtype=np.uint8)

    # 遍历图片所有像素
    circle_radius_sq = max_distance**2
    for y in range(height):
        for x in range(width):
            dx = x - face_center[0]
            dy = y - face_center[1]
            # 如果像素在圆内，则复制到透明正方形中的对应位置
            if dx**2 + dy**2 <= circle_radius_sq:
                square_y = max_distance - face_center[1] + y
                square_x = max_distance - face_center[0] + x
                # 检查索引是否在正方形边界内
                if 0 <= square_y < square_size and 0 <= square_x < square_size:
                    square[square_y, square_x] = image[y, x]

    return square

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
        max_distance = min(face_center[0], face_center[1], image.shape[1] - face_center[0], image.shape[0] - face_center[1])
        cropped_face = crop_face(image, face_center, max_distance)
        
        name = os.path.splitext(image_name)[0]
        named_image = add_name_to_image(cropped_face, name)

        output_path = os.path.join(output_folder, f"{name}头像.png")
        cv2.imwrite(output_path, named_image)

    # 调用 remove_deleted_images 函数删除已删除图片的头像
    remove_deleted_images(input_folder, output_folder)

def remove_deleted_images(input_folder, output_folder):
    input_images = {os.path.splitext(image_name)[0] for image_name in os.listdir(input_folder)}
    output_images = {os.path.splitext(image_name)[0].rstrip('头像') for image_name in os.listdir(output_folder)}

    for name in output_images - input_images:
        output_image_path = os.path.join(output_folder, f"{name}头像.jpg")
        os.remove(output_image_path)

def generate_schedule_image(self, schedule_data):
        # 读取背景图片（正方形），店名+Logo 图片和二维码图片
        bg_image = Image.open("background.jpg")
        store_logo = Image.open("store_logo.jpg")
        qr_code = Image.open("qr_code.png")
        
        # 创建 ImageDraw 对象，用于在背景图片上绘制文本和其他元素
        draw = ImageDraw.Draw(bg_image)
        
        # 设置字体和颜色
        font = ImageFont.truetype("arial.ttf", 24)
        font_color = (0, 0, 0)  # 黑色
        
        # 在图片上添加店名+Logo 图片（水平居中）
        logo_width, logo_height = store_logo.size
        bg_width, bg_height = bg_image.size
        logo_position = ((bg_width - logo_width) // 2, 10)
        bg_image.paste(store_logo, logo_position)
        
        # 在图片上添加每天的排班信息
        y_offset = logo_height + 20
        for day, employees in schedule_data.items():
            day_text = f"{day}:"
            text_width, text_height = draw.textsize(day_text, font)
            draw.text(((bg_width - text_width) // 2, y_offset), day_text, font=font, fill=font_color)
            
            # 在这里添加绘制员工头像的代码
            # ...
            
            y_offset += text_height + 10
        
        # 添加联系方式和地址
        contact_info = "联系方式：************，地址：************"
        text_width, text_height = draw.textsize(contact_info, font)
        draw.text(((bg_width - text_width) // 2, y_offset), contact_info, font=font, fill=font_color)
        
        # 在图片左下角添加二维码
        qr_width, qr_height = qr_code.size
        qr_position = (10, bg_height - qr_height - 10)
        bg_image.paste(qr_code, qr_position)
        
        # 保存排班表图片
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        bg_image.save(f"{timestamp}.jpg")
