import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
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

    # 创建一个白色底的正方形
    square_size = 2 * max_distance
    square = np.zeros((square_size, square_size, 4), dtype=np.uint8)
    square[:] = (255, 255, 255, 255)  # 将整个正方形填充为白色

    # 遍历图片所有像素
    circle_radius_sq = max_distance**2
    for y in range(height):
        for x in range(width):
            dx = x - face_center[0]
            dy = y - face_center[1]
            # 如果像素在圆内，则复制到白色正方形中的对应位置
            if dx**2 + dy**2 <= circle_radius_sq:
                square_y = max_distance - face_center[1] + y
                square_x = max_distance - face_center[0] + x
                # 检查索引是否在正方形边界内
                if 0 <= square_y < square_size and 0 <= square_x < square_size:
                    square[square_y, square_x] = image[y, x]

    return square

def rotate_text(image, text, angle):
    target_width = 1700  # 目标宽度
    height, width, _ = image.shape
    aspect_ratio = height / width
    target_height = int(target_width * aspect_ratio)
    # 调整图像尺寸
    image = cv2.resize(image, (target_width, target_height))
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "汉仪喵魂梦境 W.ttf")
    font = ImageFont.truetype(font_path, 350)  # 设置字体大小为300
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)
    text_size = draw.textsize(text, font)
    text_image = Image.new('RGBA', text_size, (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), text, font=font, fill=(255, 193, 193))  # 设置文本颜色为(255, 193, 193)
    rotated_text = text_image.rotate(angle, expand=True, resample=Image.BICUBIC)
    
    # 计算文本的边界框
    bbox = rotated_text.getbbox()
    
    # 裁剪旋转后的文本，删除边缘的空白部分
    cropped_text = rotated_text.crop(bbox)
    
    # 计算右上角的粘贴坐标
    paste_x = image_pil.width - cropped_text.width
    paste_y = 0
    
    # 将裁剪后的文本粘贴到右上角
    image_pil.paste(cropped_text, (paste_x, paste_y), cropped_text)
    return cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

def add_name_to_image(image, name):
    text_position = (image.shape[1] - 80, 20)
    rotated_text = rotate_text(image, name, -30)
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

def create_employee_rectangle(employees, avatar_size=100, avatar_padding=10, max_width=800):
    total_avatars = len(employees)
    avatars_per_line = max_width // (avatar_size + avatar_padding)
    lines_needed = -(-total_avatars // avatars_per_line)  # ceil(total_avatars / avatars_per_line)

    rect_width = avatars_per_line * (avatar_size + avatar_padding) + avatar_padding
    rect_height = lines_needed * (avatar_size + avatar_padding) + avatar_padding

    rectangle = Image.new("RGBA", (rect_width, rect_height), (255, 255, 255, 0))
    radius = 10
    ImageDraw.Draw(rectangle).rounded_rectangle([0, 0, rect_width, rect_height], radius=radius, fill=(255, 255, 255, 255))

    x_offset = avatar_padding
    line_count = 1

    for index, employee in enumerate(employees):
        avatar = Image.open(f"头像/{employee}头像.png").convert("RGBA")
        avatar = avatar.resize((avatar_size, avatar_size), Image.ANTIALIAS)
        rectangle.paste(avatar, (x_offset, (line_count - 1) * (avatar_size + avatar_padding) + avatar_padding), avatar)

        x_offset += avatar_size + avatar_padding
        if (index + 1) % avatars_per_line == 0:
            x_offset = avatar_padding
            line_count += 1

    return rectangle, lines_needed

def create_no_employee_rectangle(text, font, font_color, avatar_size=100, avatar_padding=10, max_width=800):
    text_width, text_height = font.getsize(text)
    avatars_per_line = max_width // (avatar_size + avatar_padding)
    lines_needed = 1

    rect_width = avatars_per_line * (avatar_size + avatar_padding) + avatar_padding
    rect_height = lines_needed * (avatar_size + avatar_padding) + avatar_padding

    # 创建一个空白矩形
    rectangle = Image.new("RGBA", (rect_width, rect_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(rectangle)

    # 绘制圆角矩形
    ImageDraw.Draw(rectangle).rounded_rectangle([0, 0, rect_width, rect_height], radius=10, fill=(255, 255, 255, 255))

    # 绘制文本
    text_position = ((rect_width - text_width) // 2, (rect_height - text_height) // 2)
    draw.text(text_position, text, font=font, fill=font_color)

    return rectangle, lines_needed

def generate_schedule_image(schedule_data):
    print(f"Initial schedule_data: {schedule_data}")
    # 读取背景图片（正方形），店名+Logo 图片和二维码图片
    bg_image = Image.open("背景图.jpg")
    store_logo = Image.open("logo.png")
    qr_code = Image.open("qr_code.png")

    # 应用20%的白色遮罩
    bg_image = bg_image.convert("RGBA")
    overlay = Image.new("RGBA", bg_image.size, (255, 255, 255, int(255 * 0.2)))
    bg_image = Image.alpha_composite(bg_image, overlay)

    # 应用高斯模糊
    bg_image = bg_image.filter(ImageFilter.GaussianBlur(5))

    # 设置字体和颜色
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "汉仪喵魂梦境 W.ttf")
    font = ImageFont.truetype(font_path, 24)
    font_flag = ImageFont.truetype(font_path, 40)
    font_day = ImageFont.truetype(font_path, 30)
    font_color = (0, 0, 0)  # 黑色

    # 在图片上添加店名+Logo 图片（水平居中）
    logo_width, logo_height = store_logo.size
    bg_width, bg_height = bg_image.size
    logo_width_scaled = int(bg_width * 0.2)
    logo_height_scaled = int(logo_height * (logo_width_scaled / logo_width))
    store_logo = store_logo.resize((logo_width_scaled, logo_height_scaled), Image.ANTIALIAS)

    # 计算内容总高度
    content_height = 0
    for employees in schedule_data.values():
        if employees:
            _, lines_needed = create_employee_rectangle(employees, avatar_size=100, avatar_padding=10, max_width=int(bg_width * 0.8))
            content_height += lines_needed * 100 + 30  # 30 = text height + padding
        else:
            _, lines_needed = create_no_employee_rectangle("今天店内休息哦～", font_flag, font_color, avatar_size=100, avatar_padding=10, max_width=int(bg_width * 0.8))
            content_height += lines_needed * 100 + 30

    # 计算二维码高度
    qr_code_width, qr_code_height = qr_code.size
    qr_code_height_scaled = int(bg_height * 0.4)
    qr_code_width_scaled = int(qr_code_width * (qr_code_height_scaled / qr_code_height))
    qr_code = qr_code.resize((qr_code_width_scaled, qr_code_height_scaled), Image.ANTIALIAS)
    content_height += qr_code_height_scaled
    content_height += logo_height_scaled + 10

    # 计算地址和电话高度
    address = "地址：祥源大厦第A栋1单元26层5号"
    phone = "电话：17585171001"

    # 根据计算出的高度调整背景图的大小
    new_bg_height = content_height + 20
    new_bg_width = int(bg_width * (new_bg_height / bg_height))
    bg_image = bg_image.resize((new_bg_width, new_bg_height), Image.ANTIALIAS)
    bg_width, bg_height = bg_image.size  # 更新 bg_height
    logo_position = ((bg_width - logo_width_scaled) // 2, 10)

    print(f"bg_width updated to: {bg_width}")
    print(f"bg_height updated to: {bg_height}")
    # 创建 ImageDraw 对象，用于在背景图片上绘制文本和其他元素
    draw = ImageDraw.Draw(bg_image)

    address_width, address_height = draw.textsize(address, font)
    phone_width, phone_height = draw.textsize(phone, font)
    # content_height += address_height + phone_height + 30  # 加上30像素的间距

    y_offset = 20
    # 创建 ImageDraw 对象，用于在背景图片上绘制文本和其他元素
    draw = ImageDraw.Draw(bg_image)

    bg_image.paste(store_logo, logo_position, store_logo)
    y_offset += logo_height_scaled + 10

    for day, employees in schedule_data.items():
        print(f"Processing day {day}, employees: {employees}")
        day_text = f"{day}:"
        text_width, text_height = draw.textsize(day_text, font_day)


        # 在这里添加绘制员工头像的代码
        if employees:
            rectangle, lines_needed = create_employee_rectangle(employees, avatar_size=100, avatar_padding=10, max_width=int(bg_width * 0.8))
        else:
            rectangle, lines_needed = create_no_employee_rectangle("今天店内休息哦～", font_flag, font_color, avatar_size=100, avatar_padding=10, max_width=int(bg_width * 0.8))

        rect_width, rect_height = rectangle.size
        text_margin = (bg_width - (text_width + rect_width +5)) // 2
        # 绘制周几文本，使其与圆角矩形中线对齐
        text_position = (text_margin, y_offset + (rect_height // 2))
        draw.text(text_position, day_text, font=font, fill=font_color)
        rect_position = (text_margin + 5 + text_width, y_offset)
        bg_image.paste(rectangle, rect_position, rectangle)
        y_offset += rect_height + 30  # 注意这里已经更新了
        print(f"y_offset updated to: {y_offset}")

    # 在图片上添加二维码（水平居中）
    qr_code_position = (0, bg_height - qr_code_height_scaled)
    bg_image.paste(qr_code, qr_code_position, qr_code)

    address_position = ((bg_width-address_width)//2, y_offset)
    draw.text(address_position, address, font=font, fill=font_color)
    phone_position = ((bg_width-phone_width)//2, y_offset + address_height + 10)
    draw.text(phone_position, phone, font=font, fill=font_color)

    return bg_image
