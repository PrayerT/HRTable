import re
import os

def parse_schedule_text(schedule_text, employee_dir):
    week_days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    schedule = {day: [] for day in week_days}
    
    # 获取照片文件夹下的所有文件名
    employees = [file.split('.')[0] for file in os.listdir(employee_dir)]
    
    lines = schedule_text.split('\n')
    for line in lines:
        # 使用正则表达式提取员工名称和工作日信息
        match = re.search(r'\d+\. ([\u4e00-\u9fa5A-Za-z]+).*?([\d]+)', line)
        if match:
            # 提取员工名字并去掉职位标签
            employee = re.sub(r'(全职|兼职|店长)', '', match.group(1)).strip()
            work_days = match.group(2)
            # 仅当提取出的员工名字是照片文件夹下的文件名时，才将其添加到排班表中
            if employee in employees:
                for day in work_days:
                    schedule[week_days[int(day) - 1]].append(employee)
    
    return schedule

if __name__ == "__main__":
    text = """
    下周报班开始啦4.24-4. 30
    请各位妹子继续给予支持，积极报班哦，爱你们~
    全职在名称后面备注一下，兼职不用。全职不占兼职保底名额，阿里嘎多。
    例 桃酱1234567

    1. 小白店长 134567【周一开会不准休】
    2. 早早全职123567【1天机动未定】
    3. 锦鲤 全职123457  一天机动未定
    4. 织野全职1234567机动
    5. 小敏 全职 567 机动
    6. 东妹店长234567
    7. 小铃铛1234567一天机动未定
    8. 小卷 全职 12356
    9. 香菜全职 1234567（67机动）
    10. 花井兼职 3567 67机动
    11. 菲儿全职1234567 34机动
    12. uu兼职 34567 34567机动
    13. 舒华兼职 1234567 1234567机动
    14. 泡泡兼职67
    """
    
    print(parse_schedule_text(text, "照片"))
