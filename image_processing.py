import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import matplotlib.font_manager as fm
from datetime import datetime
import random

from database import get_image_mtime, save_image_mtime

# 将 face_cascade 定义为全局变量
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res/汉仪喵魂梦境 W.ttf")


def detect_face(image):
    global face_cascade
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 4)

    if len(faces) == 0:
        return None

    return faces[0]

def crop_face(image, face_center, max_distance, image_name):
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

       
    image_name, extension = os.path.splitext(image_name)
    save_path = os.path.join("原头像", f"{image_name}原头像.png")
    cv2.imwrite(save_path, square)

    return square

def rotate_text(image, text, angle):
    target_width = 1700  # 目标宽度
    height, width, _ = image.shape
    aspect_ratio = height / width
    target_height = int(target_width * aspect_ratio)
    # 调整图像尺寸
    image = cv2.resize(image, (target_width, target_height))
    font = ImageFont.truetype(font_path, 400)  # 设置字体大小为300
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)
    text_size = draw.textsize(text, font)
    text_image = Image.new('RGBA', text_size, (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), text, font=font, fill=(225, 115, 160))  # 设置文本颜色为(255, 193, 193)
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

def process_all_images(input_folder, output_folder, output_folder_raw):
    if not os.path.exists('头像'):
        os.mkdir('头像')

    if not os.path.exists('原头像'):
        os.mkdir('原头像')

    # 在这里实现批量处理图片功能
    for image_name in os.listdir(input_folder):
        image_path = os.path.join(input_folder, image_name)
        image_mtime = os.path.getmtime(image_path)

        # 如果已处理过该图片，并且修改时间未发生变化，则跳过处理
        saved_mtime = get_image_mtime(image_name)
        if saved_mtime is not None and saved_mtime == image_mtime:
            print(f"跳过已处理且未更改的图片： {image_name}")
            continue
        image = cv2.imread(image_path)

        if image is None:
            print(f"无法加载图片: {image_name}")
            continue

        face = detect_face(image)
        height, width, _ = image.shape
        aspect_ratio = width / height

        if face is None and aspect_ratio != 1:
            print(f"人脸识别失败，请手动截取人脸： {image_name}")
            continue

        if face is not None:
            print(f"人脸识别成功： {image_name}")
            face_center = (face[0] + face[2] // 2, face[1] + face[3] // 2)
            max_distance = min(face_center[0], face_center[1], image.shape[1] - face_center[0], image.shape[0] - face_center[1])
        else:  # 当检测不到人脸且宽高比为1:1时，直接使用图像中心作为人脸中心
            print(f"人脸识别失败，但图像宽高比为1:1，使用图像中心作为人脸中心： {image_name}")
            face_center = (int(width / 2), int(height / 2))
            max_distance = min(face_center[0], face_center[1], image.shape[1] - face_center[0], image.shape[0] - face_center[1])

        cropped_face = crop_face(image, face_center, max_distance, image_name)

        name = os.path.splitext(image_name)[0]
        named_image = add_name_to_image(cropped_face, name)

        output_path = os.path.join(output_folder, f"{name}头像.png")
        cv2.imwrite(output_path, named_image)
        print(f"已保存头像： {output_path}")
        save_image_mtime(image_name, image_mtime)


    # 调用 remove_deleted_images 函数删除已删除图片的头像
    remove_deleted_images(input_folder, output_folder, output_folder_raw)

def remove_deleted_images(input_folder, output_folder, output_folder_raw):
    input_images = {os.path.splitext(image_name)[0] for image_name in os.listdir(input_folder)}
    output_images = {os.path.splitext(image_name)[0].rstrip('头像') for image_name in os.listdir(output_folder)}
    # output_images_raw = {os.path.splitext(image_name)[0].rstrip('原头像') for image_name in os.listdir(output_folder_raw)}

    for name in output_images - input_images:
        output_image_path = os.path.join(output_folder, f"{name}头像.png")
        print(f"删除了：{output_images}")
        os.remove(output_image_path)
    # for name in output_images_raw - input_images:
    #     output_image_path = os.path.join(output_folder, f"{name}原头像.png")
    #     os.remove(output_image_path)

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
    bg_image = Image.open("res/背景图.png")
    store_logo = Image.open("res/logo.png")
    qr_code = Image.open("res/qr_code.png")
    cat_pic = Image.open("res/猫娘.png")

    # 应用高斯模糊
    # bg_image = bg_image.filter(ImageFilter.GaussianBlur(5))

    # 设置字体和颜色
    font = ImageFont.truetype(font_path, 40)
    font_flag = ImageFont.truetype(font_path, 40)
    font_title = ImageFont.truetype(font_path, 80)
    font_day = ImageFont.truetype(font_path, 30)
    font_color = (225, 115, 160)  # 黑色

    # 在图片上添加店名+Logo 图片（水平居中）
    bg_width, bg_height = bg_image.size

    # 计算内容总高度
    content_height = 0
    for employees in schedule_data.values():
        if employees:
            _, lines_needed = create_employee_rectangle(employees, avatar_size=100, avatar_padding=10, max_width=int(bg_width * 1))
            content_height += 1 * 100 + 30  # 30 = text height + padding
            print(f"lines_needed: {lines_needed}")
        else:
            _, lines_needed = create_no_employee_rectangle("今天店内休息哦～", font_flag, font_color, avatar_size=100, avatar_padding=10, max_width=int(bg_width * 1))
            content_height += 1 * 100 + 30
            print(f"lines_needed: {lines_needed}")

    # 在图片上添加店名，共两行，第一行为“桃酱·二次元·助教·桌游”，第二行为“CLUB”，两行文字的中心线对齐
    store_name_1 = "桃酱·二次元·助教·桌游"
    store_name_2 = "CLUB"
    store_name_width_1, store_name_height_1 = font_title.getsize(store_name_1)
    store_name_width_2, store_name_height_2 = font_title.getsize(store_name_2)

    logo_height_scaled = int(store_name_height_1 + store_name_height_2 + 10)
    logo_width_scaled = int(store_logo.size[0] * (logo_height_scaled / store_logo.size[1]))
    store_logo = store_logo.resize((logo_width_scaled, logo_height_scaled), Image.ANTIALIAS)

    total_width = store_name_width_1 + logo_width_scaled + 10  # 10像素间距


    # 计算二维码高度
    qr_code_width, qr_code_height = qr_code.size
    # qr_code_height_scaled = int(bg_height * 0.2)
    # qr_code_width_scaled = int(qr_code_width * (qr_code_height_scaled / qr_code_height))
    # qr_code = qr_code.resize((qr_code_width_scaled, qr_code_height_scaled), Image.ANTIALIAS)
    content_height += qr_code_height
    content_height += logo_height_scaled + 10

    # 计算地址和电话高度
    address = "地址：祥源大厦第A栋1单元26层5号"
    phone = "电话：17585171001"

    # 根据计算出的高度调整背景图的大小
    new_bg_height = content_height + 20
    new_bg_width = int(bg_width * (new_bg_height / bg_height))
    bg_image = bg_image.resize((new_bg_width, new_bg_height), Image.ANTIALIAS)
    bg_width, bg_height = bg_image.size  # 更新 bg_height
    store_logo_position = (((bg_width - total_width) // 2, 30))
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
    # 使用随机大小和位置的Logo
    num_of_logos = 20  # 更改此值以设置要添加的Logo数量
    for _ in range(num_of_logos):
        paste_random_size_position_logo(bg_image, store_logo, 0.4, 1)
    # 应用20%的白色遮罩
    bg_image = bg_image.convert("RGBA")
    overlay = Image.new("RGBA", bg_image.size, (255, 255, 255, int(255 * 0.4)))
    bg_image = Image.alpha_composite(bg_image, overlay)

    # 将cat_pic缩放并粘贴到背景图的最右下角
    cat_pic_width_scaled = 0.15 * bg_image.width
    cat_pic_height_scaled = cat_pic_width_scaled * cat_pic.height / cat_pic.width
    cat_pic = cat_pic.resize((int(cat_pic_width_scaled), int(cat_pic_height_scaled)), Image.ANTIALIAS)
    bg_image.paste(cat_pic, (bg_image.width - cat_pic.width, bg_image.height - cat_pic.height), cat_pic)

    # 应用20%的白色遮罩
    bg_image = Image.alpha_composite(bg_image, overlay)


    bg_image.paste(store_logo, store_logo_position, store_logo)
    store_name_position_1 = ((bg_width - total_width) // 2 + logo_width_scaled + 10, 80)
    store_name_position_2 = ((bg_width - store_name_width_2) // 2, 80 + store_name_height_1)

    ImageDraw.Draw(bg_image).text(store_name_position_1, store_name_1, font=font_title, fill=(225, 115, 160))
    ImageDraw.Draw(bg_image).text(store_name_position_2, store_name_2, font=font_title, fill=(225, 115, 160))


    y_offset = 30 + store_name_height_1 + store_name_height_2 + 150  # 更新y_offset
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
        spacing = 20  # 更改这个值以调整间距
        text_margin = (bg_width - (text_width + rect_width + spacing)) // 2
        # 绘制周几文本，使其与圆角矩形中线对齐
        text_position = (text_margin, y_offset + (text_height // 2))
        print(f"text_position: {text_position} text_width:{text_width}")
        # draw.text(text_position, day_text, font=font_day, fill=font_color)
        ImageDraw.Draw(bg_image).text(text_position, day_text, font=font_day, fill=font_color)
        rect_position = (text_margin + spacing + text_width, y_offset)
        print(f"rect_position: {rect_position}")
        bg_image.paste(rectangle, rect_position, rectangle)
        y_offset += rect_height + 30  # 注意这里已经更新了
        print(f"y_offset updated to: {y_offset}")

    # 在图片上添加二维码（水平居中）
    qr_code_height_scaled = int(bg_height * 0.2)
    qr_code_width_scaled = int(qr_code_width * (qr_code_height_scaled / qr_code_height))
    qr_code = qr_code.resize((qr_code_width_scaled, qr_code_height_scaled), Image.ANTIALIAS)
    bg_image_height, bg_image_width = bg_image.size
    qr_code_position = (20, bg_image_height - qr_code_height_scaled-20)
    bg_image.paste(qr_code, qr_code_position, qr_code)

    address_position = ((bg_width-address_width)//2, y_offset + 100)
    ImageDraw.Draw(bg_image).text(address_position, address, font=font, fill=font_color)
    # draw.text(address_position, address, font=font, fill=font_color)
    phone_position = ((bg_width-phone_width)//2, y_offset + address_height + 110)
    ImageDraw.Draw(bg_image).text(phone_position, phone, font=font, fill=font_color)
    print(f"phone_position: {phone_position}")
    # draw.text(phone_position, phone, font=font, fill=font_color)

    return bg_image

def paste_random_size_position_logo(bg_image, logo, min_scale, max_scale):
    # 随机缩放Logo
    scale = random.uniform(min_scale, max_scale)
    logo_width, logo_height = logo.size
    logo = logo.resize((int(logo_width * scale), int(logo_height * scale)), Image.ANTIALIAS)

    # 随机选择位置
    bg_width, bg_height = bg_image.size
    logo_width, logo_height = logo.size
    x_position = random.randint(0 - logo_width, bg_width)
    y_position = random.randint(0 - logo_height, bg_height)

    # 在背景图上粘贴Logo
    bg_image.paste(logo, (x_position, y_position), logo)

