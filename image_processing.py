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
text_color = (225, 115, 160, 255)  # RGBA

def detect_face(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 4)

    if len(faces) == 0:
        return None

    return faces[0]

def crop_face(image_pil, face_center, max_distance, image_name):
    # 创建一个空白的正方形
    square_size = 2 * max_distance
    square = Image.new("RGBA", (square_size, square_size), (255, 255, 255, 0))

    # 遍历图片所有像素
    circle_radius_sq = max_distance**2
    for y in range(image_pil.height):
        for x in range(image_pil.width):
            dx = x - face_center[0]
            dy = y - face_center[1]
            # 如果像素在圆内，则复制到白色正方形中的对应位置
            if dx**2 + dy**2 <= circle_radius_sq:
                square_y = max_distance - face_center[1] + y
                square_x = max_distance - face_center[0] + x
                # 检查索引是否在正方形边界内
                if 0 <= square_y < square_size and 0 <= square_x < square_size:
                    square.putpixel((square_x, square_y), image_pil.getpixel((x, y)))

    save_path = os.path.join("原头像", f"{image_name}原头像.png")
    square.save(save_path)

    return square

def draw_stroked_text(draw, text, position, font, text_color, stroke_color, stroke_width):
    x, y = position
    draw.text((x-stroke_width, y), text, font=font, fill=stroke_color)
    draw.text((x+stroke_width, y), text, font=font, fill=stroke_color)
    draw.text((x, y-stroke_width), text, font=font, fill=stroke_color)
    draw.text((x, y+stroke_width), text, font=font, fill=stroke_color)

    # then draw the text over it
    draw.text(position, text, font=font, fill=text_color)

def rotate_text(image_pil, text, angle, target_size):
    # Resize the image
    image_pil = image_pil.resize(target_size)

    font = ImageFont.truetype(font_path, 200)  # Set the font size to 200

    # Create a new Image object for the text
    text_img = Image.new('RGBA', image_pil.size, (255, 255, 255, 0))

    # Create a draw object and write the text onto the text image
    draw = ImageDraw.Draw(text_img)
    draw_stroked_text(draw, text, (0, 0), font, (225, 115, 160, 255), (255, 255, 255, 255), 10)  # draw the text with stroke

    rotated_text = text_img.rotate(angle, expand=True, resample=Image.BICUBIC)

    # Calculate the bounding box of the text
    bbox = rotated_text.getbbox()

    # Crop the rotated text to remove the empty margins
    cropped_text = rotated_text.crop(bbox)

    # Calculate the paste coordinates for the top-right corner
    paste_x = image_pil.width - cropped_text.width
    paste_y = 0

    # Paste the cropped text onto the top-right corner
    image_pil.alpha_composite(cropped_text, (paste_x, paste_y))

    return image_pil

def process_all_images(input_folder, input_folder_raw, output_folder, output_folder_raw):
    target_size = (1024, 1024)  # All images will be resized to this size

    if not os.path.exists('头像'):
        os.mkdir('头像')

    if not os.path.exists('原头像'):
        os.mkdir('原头像')

    if not os.path.exists('照片改'):
        os.mkdir('照片改')

    # 在这里实现批量处理图片功能
    for image_name in os.listdir(input_folder):
        if image_name.startswith('.'):
            continue  # Skip hidden files like .DS_Store

        image_path = os.path.join(input_folder, image_name)
        image_mtime = os.path.getmtime(image_path)

        saved_mtime = get_image_mtime(image_name)
        if saved_mtime is not None and saved_mtime == image_mtime:
            print(f"跳过已处理且未更改的图片： {image_name}")
            continue

        image_pil = Image.open(image_path)

        if image_pil is None:
            print(f"无法加载图片: {image_name}")
            continue

        face = detect_face(image_pil)
        aspect_ratio = image_pil.width / image_pil.height

        if face is not None:
            print(f"人脸识别成功： {image_name}")
            face_center = (face[0] + face[2] // 2, face[1] + face[3] // 2)
            max_distance = min(face_center[0], face_center[1], image_pil.width - face_center[0], image_pil.height - face_center[1])
        else:
            matching_images = [filename for filename in os.listdir(input_folder_raw) if os.path.splitext(filename)[0] == os.path.splitext(image_name)[0]]
            if len(matching_images) > 0:
                print(f"使用照片改中的文件： {image_name}")
                modified_image_name = matching_images[0]
                modified_image_path = os.path.join(input_folder_raw, modified_image_name)
                modified_image_pil = Image.open(modified_image_path)
                aspect_ratio = modified_image_pil.width / modified_image_pil.height
                if aspect_ratio == 1:
                    face_center = (int(modified_image_pil.width / 2), int(modified_image_pil.height / 2))
                    max_distance = min(face_center[0], face_center[1], modified_image_pil.width - face_center[0], modified_image_pil.height - face_center[1])
                    image_pil = modified_image_pil
                else:
                    print(f"照片改中的文件宽高比不为1:1： {image_name}")
                    continue
            else:
                print(f"人脸识别失败，请手动截取人脸： {image_name}")
                continue

        cropped_face_pil = crop_face(image_pil, face_center, max_distance, image_name)

        name = os.path.splitext(image_name)[0]
        named_image_pil = rotate_text(cropped_face_pil, name, -30, target_size)

        output_path = os.path.join(output_folder, f"{name}头像.png")
        named_image_pil.save(output_path)
        print(f"已保存头像： {output_path}")
        save_image_mtime(image_name, image_mtime)

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

def create_employee_rectangle(employees, max_employees, avatar_size=100, avatar_padding=10):
    rect_width = max_employees * (avatar_size + avatar_padding) + avatar_padding
    rect_height = avatar_size + 2 * avatar_padding

    rectangle = Image.new("RGBA", (rect_width, rect_height), (255, 255, 255, 0))
    radius = 10
    ImageDraw.Draw(rectangle).rounded_rectangle([0, 0, rect_width, rect_height], radius=radius, fill=(255, 255, 255, 255))

    x_offset = avatar_padding

    for employee in employees:
        avatar = Image.open(os.path.join("头像", f"{employee}头像.png")).convert("RGBA")
        avatar = avatar.resize((avatar_size, avatar_size), Image.ANTIALIAS)
        rectangle.paste(avatar, (x_offset, avatar_padding), avatar)

        x_offset += avatar_size + avatar_padding

    return rectangle, rect_width

def create_title_image(main_title, sub_title, main_font_size=100, sub_font_size=80):
    # Create fonts
    main_font = ImageFont.truetype(font_path, main_font_size)
    sub_font = ImageFont.truetype(font_path, sub_font_size)

    # Calculate text width and height
    main_width, main_height = main_font.getsize(main_title)
    sub_width, sub_height = sub_font.getsize(sub_title)
    text_width = max(main_width, sub_width)
    text_height = main_height + sub_height

    # Create image
    title_image = Image.new('RGBA', (text_width, text_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(title_image)

    # Draw main title
    main_title_x = (text_width - main_width) // 2
    draw.text((main_title_x, 0), main_title, font=main_font, fill=text_color)

    # Draw sub title
    sub_title_x = (text_width - sub_width) // 2
    draw.text((sub_title_x, main_height), sub_title, font=sub_font, fill=text_color)

    return title_image

def create_day_schedule(day, employees, max_employees, avatar_size=120, avatar_padding=15):
    # Create an image for the employees
    employee_img, employee_width = create_employee_rectangle(employees, max_employees, avatar_size, avatar_padding)

    # Create an image for the day name
    day_font = ImageFont.truetype(font_path, int(avatar_size/2))
    day_width, day_height = day_font.getsize(day)
    day_img = Image.new('RGBA', (day_width, day_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(day_img)
    draw.text((0, 0), day, font=day_font, fill=text_color)

    # Combine the day image and the employee image
    width = day_width + employee_width
    height = max(day_height, employee_img.height)
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    img.paste(day_img, (0, (height - day_height) // 2))
    img.paste(employee_img, (day_width, (height - employee_img.height) // 2))

    return img

def create_info_image(address, phone, font_size=40):
    # Create fonts
    info_font = ImageFont.truetype(font_path, font_size)

    # Calculate text width and height
    address_width, address_height = info_font.getsize(address)
    phone_width, phone_height = info_font.getsize(phone)
    text_width = max(address_width, phone_width)
    text_height = address_height + phone_height

    # Create image
    info_image = Image.new('RGBA', (text_width, text_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(info_image)

    # Draw address
    address_x = (text_width - address_width) // 2
    draw.text((address_x, 0), address, font=info_font, fill=text_color)

    # Draw phone
    phone_x = (text_width - phone_width) // 2
    draw.text((phone_x, address_height), phone, font=info_font, fill=text_color)

    return info_image


def generate_schedule_image(schedule_data, avatar_size=120, avatar_padding=15, page_margin=20):
    print(f"Initial schedule_data: {schedule_data}")

    store_logo = Image.open(os.path.join("res", "logo.png")).convert("RGBA")
    qr_code = Image.open(os.path.join("res", "qr_code.png")).convert("RGBA")
    cat_pic = Image.open(os.path.join("res", "猫娘.png")).convert("RGBA")
    main_title = "桃酱·二次元·助教·桌游"
    sub_title = "排班表"
    title_image = create_title_image(main_title,sub_title)

    # Resize store_logo to match title height
    store_logo = store_logo.resize((title_image.height, title_image.height), Image.ANTIALIAS)
    
    # Resize qr_code and cat_pic to match each other
    qr_code = qr_code.resize((int(qr_code.width * title_image.height / qr_code.height), title_image.height), Image.ANTIALIAS)
    cat_pic = cat_pic.resize((qr_code.width, int(cat_pic.height * qr_code.width / cat_pic.width)), Image.ANTIALIAS)

    # Combine logo and title
    logo_title_width = store_logo.width + title_image.width
    logo_title_image = Image.new('RGBA', (logo_title_width, title_image.height), (255, 255, 255, 0))
    logo_title_image.paste(store_logo, (0, 0))
    logo_title_image.paste(title_image, (store_logo.width, 0))

    # Find the maximum number of employees in a day
    max_employees = max(len(employees) for employees in schedule_data.values())

    # Create an image for each day
    day_imgs = [create_day_schedule(day, employees, max_employees, avatar_size, avatar_padding) for day, employees in schedule_data.items()]

    # Adjust day_imgs to have the same width
    max_width = max(img.width for img in day_imgs)
    day_imgs = [img.resize((max_width, img.height), Image.ANTIALIAS) for img in day_imgs]

    # Combine the day images
    schedule_width = max(img.width for img in day_imgs)
    schedule_height = sum(img.height for img in day_imgs) + 20 * (len(day_imgs) - 1) # Added gap heights
    schedule = Image.new('RGBA', (schedule_width, schedule_height), (255, 255, 255, 0))
    y_offset = 0
    for img in day_imgs:
        schedule.paste(img, ((schedule_width - img.width) // 2, y_offset))
        y_offset += img.height + 20

    # Create the information image
    address = "地址：祥源大厦第A栋1单元26层5号"
    phone = "电话：17585171001"
    info_img = create_info_image(address, phone)

    # Compute the width of each main section
    logo_title_width = logo_title_image.width
    schedule_width = schedule.width
    info_width = info_img.width

    # Determine the maximum width of the three main sections
    max_main_section_width = max(logo_title_width, schedule_width, info_width)

    # Compute the final width
    final_width = max_main_section_width + qr_code.width + cat_pic.width
    # Compute the final height
    final_height = logo_title_image.height + schedule_height + info_img.height + 2 * page_margin
    # Create a white canvas
    white_canvas = Image.new('RGBA', (final_width, final_height), (255, 255, 255, 255))
    num_of_logos = 40  # 更改此值以设置要添加的Logo数量
    for _ in range(num_of_logos):
        paste_random_size_position_logo(white_canvas, store_logo, 0.6, 0.9)
    # 应用20%的白色遮罩
    overlay = Image.new("RGBA", white_canvas.size, (255, 255, 255, int(255 * 0.6)))
    white_canvas = Image.alpha_composite(white_canvas, overlay)

    # Paste the components onto the white canvas
    y_offset = page_margin

    # Store Logo and Store Name
    logo_title_x = (final_width - logo_title_image.width) // 2
    white_canvas.paste(logo_title_image, (logo_title_x, y_offset), logo_title_image)
    y_offset += logo_title_image.height


    # Schedule
    white_canvas.paste(schedule, ((final_width - schedule_width) // 2, y_offset),schedule)
    y_offset += schedule_height

    # Info
    white_canvas.paste(info_img, ((final_width - info_img.width) // 2, y_offset), info_img)

    # QR Code
    white_canvas.paste(qr_code, (0, white_canvas.height - qr_code.height), qr_code)

    # Cat Pic
    white_canvas.paste(cat_pic, (final_width - cat_pic.width, final_height - cat_pic.height), cat_pic)

    return white_canvas

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
        avatar_path = os.path.join("原头像", f"{name}原头像.png")
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

    # 确保缩放后的图像尺寸大于或等于目标尺寸，以避免在裁剪时出现黑边
    if aspect_ratio > target_ratio:
        # 图片宽度过大，先将高度缩放到目标尺寸的高度，宽度会大于等于目标尺寸的宽度
        resized_image = image.resize((round(size[1] * aspect_ratio), size[1]), Image.ANTIALIAS)
    else:
        # 图片高度过大，先将宽度缩放到目标尺寸的宽度，高度会大于等于目标尺寸的高度
        resized_image = image.resize((size[0], round(size[0] / aspect_ratio)), Image.ANTIALIAS)

    # 计算裁剪边界
    left = (resized_image.width - size[0]) / 2
    right = (resized_image.width + size[0]) / 2
    top = (resized_image.height - size[1]) / 2
    bottom = (resized_image.height + size[1]) / 2

    # 裁剪图片
    resized_image = resized_image.crop((left, top, right, bottom))

    return resized_image

def draw_title(draw, title_text, title_font, global_y, margin, canvas_width):
    title_size = draw.textsize(title_text, font=title_font)
    title_position = ((canvas_width - title_size[0]) // 2, global_y)
    draw.text(title_position, title_text, font=title_font, fill=text_color)
    return title_position[1] + title_size[1] + margin, title_position

def draw_subtitle(draw, subtitle_text, subtitle_font, global_y, margin, canvas_width):
    subtitle_size = draw.textsize(subtitle_text, font=subtitle_font)
    subtitle_position = ((canvas_width - subtitle_size[0]) // 2, global_y)
    draw.text(subtitle_position, subtitle_text, font=subtitle_font, fill=text_color)
    return subtitle_position[1] + subtitle_size[1] + margin * 2

def paste_cat_image(canvas, cat_image_path, canvas_width, global_y, margin):
    cat_image = Image.open(cat_image_path)
    cat_image.thumbnail((400, 400))
    canvas.paste(cat_image, (canvas_width - cat_image.width - margin, global_y), cat_image)
    return global_y + cat_image.height

def draw_employee(canvas, draw, employee, employee_image_path, name_font, global_x, global_y, margin, canvas_width):
    # 加载并调整员工照片的大小
    employee_image = Image.open(employee_image_path)
    employee_image = resize_and_crop(employee_image, (600, 800))  # 调整员工照片的大小并裁剪
    canvas.paste(employee_image, (global_x, global_y))
    # 绘制员工姓名
    name_position = (global_x + (employee_image.width - draw.textsize(employee, font=name_font)[0]) // 2, global_y + employee_image.height)
    draw.text(name_position, employee, font=name_font, fill=text_color)
    return global_x + employee_image.width + margin, employee_image

def draw_separator(draw, y, canvas_width, line_color=text_color, line_width=3):
    draw.line([(0, int(y)), (int(canvas_width), int(y))], fill=line_color, width=line_width)
    print(f"separator_y = {y}")

def generate_show_image(employees_by_ranking):
    # 设置参数
    margin = 20
    max_images_per_row = 3
    title_text = "桃酱·二次元·助教·桌游CLUB"
    subtitle_text = "助教一览表"
    cat_image_path = os.path.join("res", "猫娘.png")
    line_color = (225, 115, 160)
    line_width = 8

    # 加载字体
    title_font = ImageFont.truetype(font_path, 150)
    subtitle_font = ImageFont.truetype(font_path, 130)
    name_font = ImageFont.truetype(font_path, 100)
    ranking_font = ImageFont.truetype(font_path, 120)

    # 计算画布的大小
    image_width = 600  # 假设所有图片的宽度都为600
    canvas_width = image_width * max_images_per_row + margin * (max_images_per_row + 1)
    canvas_height = 0

    # 创建一个画笔对象，用于计算文本大小
    temp_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(temp_img)

    # 计算标题、副标题的高度并更新画布高度
    title_size = draw.textsize(title_text, font=title_font)
    subtitle_size = draw.textsize(subtitle_text, font=subtitle_font)

    # 计算猫娘图片的大小
    cat_image = Image.open(cat_image_path)
    cat_image.thumbnail((400, 400))  # 假设你把猫娘图片放大到原来的两倍
    cat_image_width, cat_image_height = cat_image.size

    # 计算标题、副标题和猫娘图片整体的高度
    total_height = max(title_size[1] + subtitle_size[1] + margin, cat_image_height)

    canvas_height += total_height + margin * 2  # 这里修改为总高度加上上下间距

    # 计算员工照片高度并更新画布高度
    for ranking, employees in employees_by_ranking.items():
        rows = math.ceil(len(employees) / max_images_per_row)
        image_path = os.path.join("员工展示", f"{employees[0]}.jpg")
        if not os.path.exists(image_path):
            image_path = os.path.join("员工展示", f"{employees[0]}.jpeg")
        employee_image = Image.open(image_path)
        ranking_size = draw.textsize(ranking, font=ranking_font)
        name_size = draw.textsize(employees[0], font=name_font)  # 假设所有员工姓名的高度相同
        canvas_height += rows * (employee_image.height * image_width // employee_image.width + ranking_size[1] + name_size[1] + margin * 5)

    # 此时我们知道了画布的大小，所以我们可以创建画布
    canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))
    logo = Image.open(os.path.join("res", "logo.png"))
    # 使用随机大小和位置的Logo
    num_of_logos = 20  # 更改此值以设置要添加的Logo数量
    for _ in range(num_of_logos):
        paste_random_size_position_logo(canvas, logo, 0.4, 1)
    # 应用20%的白色遮罩
    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, int(255 * 0.4)))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # 使用全局坐标
    global_x = margin
    global_y = margin

    # 绘制标题
    global_y, title_position = draw_title(draw, title_text, title_font, global_y + (total_height - title_size[1] - subtitle_size[1] - margin) // 2, margin, canvas_width)

    # 绘制副标题
    global_y = draw_subtitle(draw, subtitle_text, subtitle_font, global_y + margin, margin, canvas_width)

    # 粘贴猫娘图片
    # paste_cat_image(canvas, cat_image_path, canvas_width, margin, margin)

    # 更新 y 坐标
    global_y = total_height + margin * 5

    # 遍历员工照片
    for ranking_index, (ranking, employees) in enumerate(sorted(employees_by_ranking.items(), key=lambda item: item[0], reverse=True)):
        separator_y = global_y  # 分割线的y坐标
        draw.line([(0, int(separator_y)), (int(canvas_width), int(separator_y))], fill=line_color, width=line_width)
        global_y += margin * 2

        global_y += margin
        ranking_size = draw.textsize(ranking, font=ranking_font)
        ranking_position = ((canvas_width - ranking_size[0]) // 2, global_y - ranking_size[1] // 2)
        ranking_text = str.upper(ranking) + "级"
        draw.text(ranking_position, ranking_text, font=ranking_font, fill=text_color)  # 绘制等级
        global_y += ranking_size[1] + margin * 2

        employee_count = 0
        max_name_height = 0
        employee_images = []

        for employee in employees:
            image_path = os.path.join("员工展示", f"{employee}.jpg")
            if not os.path.exists(image_path):
                image_path = os.path.join("员工展示", f"{employee}.jpeg")
            name_size = draw.textsize(employee, font=name_font)
            max_name_height = max(max_name_height, name_size[1])
            employee_images.append((employee, image_path))

        for employee, image_path in employee_images:
            global_x, employee_image = draw_employee(canvas, draw, employee, image_path, name_font, global_x, global_y, margin, canvas_width)
            employee_count += 1

            if employee_count == len(employees):  # 如果是当前级别的最后一个员工
                global_x = margin
                if ranking == "S":
                    global_y += employee_image.height + max_name_height + margin * 4  # 调整S级员工的位置
                elif ranking == "R":
                    global_y += employee_image.height + max_name_height + margin * 3  # 调整R级员工的位置
                else:
                    global_y += employee_image.height + max_name_height + margin * 2  # 调整A级员工的位置
            elif employee_count % max_images_per_row == 0:
                global_x = margin
                global_y += employee_image.height + max_name_height + margin * 2

            print(f"员工：{employee}，等级：{ranking}，粘贴位置：(x={global_x}, y={global_y})")

    last_row_height = 800 + max_name_height + margin * 2  # 计算最后一行的高度
    print(f"last_row_height:{last_row_height}, final_height:{global_y + last_row_height},canvas_height:{canvas.size[1]}")
    canvas = canvas.crop((0, 0, canvas_width, global_y))  # 裁剪画布
    print(f"new_canvas_height:{canvas.size[1]}")

    canvas.save("output.png")
