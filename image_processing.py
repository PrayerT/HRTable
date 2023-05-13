import math
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
    square[:] = (255, 255, 255, 0)  # 将整个正方形填充为白色

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

def process_all_images(input_folder, input_folder_raw, output_folder, output_folder_raw):
    if not os.path.exists('头像'):
        os.mkdir('头像')

    if not os.path.exists('原头像'):
        os.mkdir('原头像')

    if not os.path.exists('照片改'):
        os.mkdir('照片改')

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

        if face is not None:
            print(f"人脸识别成功： {image_name}")
            face_center = (face[0] + face[2] // 2, face[1] + face[3] // 2)
            max_distance = min(face_center[0], face_center[1], image.shape[1] - face_center[0], image.shape[0] - face_center[1])
        else:
            # Search for a matching image in the "照片改" folder
            matching_images = [filename for filename in os.listdir(input_folder_raw) if os.path.splitext(filename)[0] == os.path.splitext(image_name)[0]]
            if len(matching_images) > 0:
                print(f"使用照片改中的文件： {image_name}")
                modified_image_name = matching_images[0]
                modified_image_path = os.path.join(input_folder_raw, modified_image_name)
                modified_image = cv2.imread(modified_image_path)
                height, width, _ = modified_image.shape
                aspect_ratio = width / height
                if aspect_ratio == 1:
                    face_center = (int(width / 2), int(height / 2))
                    max_distance = min(face_center[0], face_center[1], width - face_center[0], height - face_center[1])
                    image = modified_image
                else:
                    print(f"照片改中的文件宽高比不为1:1： {image_name}")
                    continue
            else:
                print(f"人脸识别失败，请手动截取人脸： {image_name}")
                continue

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

def generate_rank_image(rank, month):

    # 读取金银铜奖牌图片
    gold_img = Image.open(os.path.join("res", "gold.png"))
    silver_img = Image.open(os.path.join("res", "silver.png"))
    copper_img = Image.open(os.path.join("res", "copper.png"))

    ranked_avatars = []  # 存储带奖牌的头像图片
    
    for i in range(3):
        # 打开原头像
        name = rank[i][0]
        count = rank[i][1]
        avatar_path = os.path.join("./原头像", f"{name}原头像.png")
        avatar_img = Image.open(avatar_path)
        
        # 调整头像大小并添加金银铜奖牌
        avatar_img = avatar_img.resize((800, 800))
        avatar_img = avatar_img.convert("RGBA")

        # 获取头像图片的像素数据
        avatar_data = avatar_img.load()

        # 获取头像图片的内切圆半径
        radius = int(min(avatar_img.width, avatar_img.height) / 2)

        # 创建一个与头像图片大小相同的透明底图
        mask = Image.new("L", avatar_img.size, 0)

        # 在透明底图上绘制一个圆形掩码，以保留头像图片中心的圆形部分
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
                # 应用掩码，去除头像图片外的部分
        avatar_img.putalpha(mask)

        if i == 0:
            avatar_img.paste(gold_img, (600, 600), gold_img)
        elif i == 1:
            avatar_img.paste(silver_img, (600, 600), silver_img)
        elif i == 2:
            avatar_img.paste(copper_img, (600, 600), copper_img)
        
        avatar_img = avatar_img.resize((300, 300))

        ranked_avatars.append(avatar_img)



    # 创建排名图
    banner_img = Image.open(os.path.join("res", "banner.png"))
    cat_img = Image.open(os.path.join("res", "猫娘.png"))
    store_logo = Image.open(os.path.join("res", "logo.png"))
    cat_width, cat_height = cat_img.size
    cat_width = banner_img.width
    cat_height = int(cat_height * (cat_width / cat_img.width))
    cat_img = cat_img.resize((cat_width, cat_height), Image.ANTIALIAS)

    # 创建临时的 ImageDraw.Draw 对象以获取文本尺寸
    temp_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)

    font_path = "./res/汉仪喵魂梦境 W.ttf"  # 请提供字体文件路径
    font_big = ImageFont.truetype(font_path, 200)
    font_small = ImageFont.truetype(font_path, 100)

    title1 = "桃酱·二次元·助教·桌游"
    title2 = month + "桃气女仆排行榜"

    # 计算标题尺寸
    title1_size = temp_draw.textsize(title1, font=font_big)
    title2_size = temp_draw.textsize(title2, font=font_small)
    # 计算最大文本宽度
    max_text_width = max(title1_size[0], title2_size[0], 40 * 2 + avatar_img.width + 300)
    print(max_text_width)

    # 计算底图大小
    width = max_text_width + 40 + banner_img.width + cat_img.width + 40
    height = 40 + (len(rank) * 300) + title1_size[1] + title2_size[1]

    # 创建底图
    final_img = Image.new("RGBA", (width, height), (255, 255, 255, 255))

    num_of_logos = 20  # 更改此值以设置要添加的Logo数量
    for _ in range(num_of_logos):
        paste_random_size_position_logo(final_img, store_logo, 0.4, 0.8)
    # 应用20%的白色遮罩
    final_img = final_img.convert("RGBA")
    overlay = Image.new("RGBA", final_img.size, (255, 255, 255, int(255 * 0.6)))
    final_img = Image.alpha_composite(final_img, overlay)

    # 添加文本
    draw = ImageDraw.Draw(final_img)
    ImageDraw.Draw(final_img).text(((width - title1_size[0]) // 2, 20), title1, font=font_big, fill=(225, 115, 160))
    ImageDraw.Draw(final_img).text(((width - title2_size[0]) // 2, 20 + title1_size[1]), title2, font=font_small, fill=(225, 115, 160))

    # 将Banner贴在左上角
    # final_img.paste(banner_img, (20, 20), banner_img)

    # 添加排名信息
    first_horizontal_offset = None

    for i, (name, count) in enumerate(rank):
        if i < 3:
            avatar_img = ranked_avatars[i]
            avatar_height = avatar_img.height

            # 调整字体大小以使文字等高
            font_size = avatar_height
            adjusted_font = ImageFont.truetype(font_path, font_size)


            text = f"TOP.{i + 1}  {name} {count}朵"
            text_size = draw.textsize(text, font=font_big)

            # 计算文字垂直偏移量以实现中线对齐
            vertical_offset = (avatar_height - text_size[1]) // 2

            # 计算水平偏移量以使第一条文字居中显示
            if i == 0:
                first_horizontal_offset = ((width - text_size[0] - 10) // 2) - 200

            # 将头像粘贴到文字右边
            text_position = (first_horizontal_offset, banner_img.height + (i * 300) + vertical_offset - 350)
            ImageDraw.Draw(final_img).text(text_position, text, font=font_big, fill=(225, 115, 160))
            if count<100:
                final_img.paste(avatar_img, (text_position[0] + text_size[0] + 100, text_position[1] - vertical_offset), avatar_img)
            else:
                final_img.paste(avatar_img, (text_position[0] + text_size[0] + 50, text_position[1] - vertical_offset), avatar_img)
        else:
            # 调整字体大小以使文字等高
            font_size = 200  # 调整为合适的字体大小
            adjusted_font = ImageFont.truetype(font_path, font_size)

            text = f"TOP.{i + 1}  {name} {count}朵"
            text_size = draw.textsize(text, font=font_big)

            # 将文字添加到图片中，与第一条文字左端对齐
            text_position = (first_horizontal_offset, banner_img.height + (i * 300) - 350)
            ImageDraw.Draw(final_img).text(text_position, text, font=font_big, fill=(225, 115, 160))

    # 粘贴猫娘图片
    cat_position = (width - cat_img.width, height - cat_img.height)
    final_img.paste(cat_img, cat_position, cat_img)

    # 保存图片
    # final_img.save("ranked_image.png")
    return final_img

def resize_and_crop(image, size):
    # 计算纵横比
    aspect_ratio = image.width / image.height
    target_ratio = size[0] / size[1]

    # 调整宽度并裁剪
    if aspect_ratio > target_ratio:
        # 图片宽度过大，裁剪宽度
        resized_image = image.resize((size[0], int(size[0] / aspect_ratio)))
        # 计算上下裁剪的边界
        top = (resized_image.height - size[1]) / 2
        bottom = (resized_image.height + size[1]) / 2
        # 裁剪图片
        resized_image = resized_image.crop((0, top, size[0], bottom))
    else:
        # 图片高度过大，裁剪高度
        resized_image = image.resize((int(size[1] * aspect_ratio), size[1]))
        # 计算左右裁剪的边界
        left = (resized_image.width - size[0]) / 2
        right = (resized_image.width + size[0]) / 2
        # 裁剪图片
        resized_image = resized_image.crop((left, 0, right, size[1]))

    return resized_image

def draw_title(draw, title_text, title_font, global_y, margin, canvas_width):
    title_size = draw.textsize(title_text, font=title_font)
    title_position = ((canvas_width - title_size[0]) // 2, global_y)
    draw.text(title_position, title_text, font=title_font, fill=(0, 0, 0))
    return title_position[1] + title_size[1] + margin

def draw_subtitle(draw, subtitle_text, subtitle_font, global_y, margin, canvas_width):
    subtitle_size = draw.textsize(subtitle_text, font=subtitle_font)
    subtitle_position = ((canvas_width - subtitle_size[0]) // 2, global_y)
    draw.text(subtitle_position, subtitle_text, font=subtitle_font, fill=(0, 0, 0))
    return subtitle_position[1] + subtitle_size[1] + margin * 2

def paste_cat_image(canvas, cat_image_path, canvas_width, global_y, margin):
    cat_image = Image.open(cat_image_path)
    cat_image.thumbnail((200, 200))
    canvas.paste(cat_image, (canvas_width - cat_image.width - margin, global_y), cat_image)
    return global_y + cat_image.height

def draw_employee(canvas, draw, employee, employee_image_path, name_font, global_x, global_y, margin, canvas_width, current_ranking):
    # 加载并调整员工照片的大小
    employee_image = Image.open(employee_image_path)
    employee_image = resize_and_crop(employee_image, (600, 800))  # 调整员工照片的大小并裁剪
    canvas.paste(employee_image, (global_x, global_y))
    # 绘制员工姓名
    name_position = (global_x + (employee_image.width - draw.textsize(employee, font=name_font)[0]) // 2, global_y + employee_image.height)
    draw.text(name_position, employee, font=name_font, fill=(0, 0, 0))
    # 更新坐标
    global_x += employee_image.width + margin
    if global_x > canvas_width - employee_image.width - margin:
        global_x = margin
        if current_ranking == "S":
            global_y += employee_image.height + margin * 4  # 调整S级员工的位置
        else:
            global_y += employee_image.height + margin * 2
    return global_x, global_y, employee_image

def draw_separator(draw, y, canvas_width, line_color=(0, 0, 0), line_width=3):
    draw.line([(0, int(y)), (int(canvas_width), int(y))], fill=line_color, width=line_width)
    print(f"separator_y = {y}")

def generate_show_image(employees_by_ranking):
    # 设置参数
    margin = 20
    max_images_per_row = 4
    title_text = "桃酱·二次元·助教·桌游CLUB"
    subtitle_text = "助教一览表"
    cat_image_path = "./res/猫娘.png"

    # 加载字体
    title_font = ImageFont.truetype(font_path, 50)
    subtitle_font = ImageFont.truetype(font_path, 30)
    name_font = ImageFont.truetype(font_path, 24)
    ranking_font = ImageFont.truetype(font_path, 40)

    # 计算画布的大小
    canvas_width = 800 * max_images_per_row + margin * (max_images_per_row + 1)
    canvas_height = 0

    # 创建一个画笔对象，用于计算文本大小
    temp_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(temp_img)

    # 计算标题和副标题高度并更新画布高度
    title_size = draw.textsize(title_text, font=title_font)
    subtitle_size = draw.textsize(subtitle_text, font=subtitle_font)
    canvas_height += title_size[1] + subtitle_size[1] + margin * 4

    # 计算员工照片高度并更新画布高度
    for ranking, employees in employees_by_ranking.items():
        rows = math.ceil(len(employees) / max_images_per_row)
        image_path = f"./照片/{employees[0]}.jpg"  # 假设所有员工照片的高度相同
        if not os.path.exists(image_path):
            image_path = f"./照片/{employees[0]}.jpeg"
        employee_image = Image.open(image_path)
        canvas_height += rows * (employee_image.height * 800 // employee_image.width + margin * 2)

    # 此时我们知道了画布的大小，所以我们可以创建画布
    canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # 使用全局坐标
    global_x = margin
    global_y = margin

    # 绘制标题
    global_y = draw_title(draw, title_text, title_font, global_y, margin, canvas_width)

    # 绘制副标题
    global_y = draw_subtitle(draw, subtitle_text, subtitle_font, global_y, margin, canvas_width)

    # 粘贴猫娘图片
    global_y += paste_cat_image(canvas, cat_image_path, canvas_width, global_y, margin)

    # 插入分隔线
    draw_separator(draw, global_y, canvas_width)
    global_y += margin * 2

    # 遍历员工照片
    for ranking_index, (ranking, employees) in enumerate(sorted(employees_by_ranking.items(), key=lambda item: item[0], reverse=True)):
        if ranking_index > 0:  # 如果不是第一个等级，插入分隔线
            draw_separator(draw, global_y, canvas_width)
            global_y += margin * 2

        global_y += margin
        draw.text((margin, global_y), ranking, font=ranking_font, fill=(0, 0, 0))  # 绘制等级
        global_y += margin * 2

        employee_count = 0

        for employee in employees:
            image_path = f"./照片/{employee}.jpg"
            if not os.path.exists(image_path):
                image_path = f"./照片/{employee}.jpeg"

            global_x, global_y, employee_image = draw_employee(canvas, draw, employee, image_path, name_font, global_x, global_y, margin, canvas_width, ranking)
            employee_count += 1

            # 如果S级员工的照片没有填满一行，剩下的位置将被空出来
            if ranking == "S" and employee_count == len(employees) and employee_count % max_images_per_row != 0:
                global_x = margin
                global_y += employee_image.height + margin * 4  # 调整S级员工的位置
            elif employee_count % max_images_per_row == 0:
                global_x = margin
                global_y += employee_image.height + margin * 2  # 调整A级员工的位置
            else:
                global_x += margin

    canvas.save("output.png")