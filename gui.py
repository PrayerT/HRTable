import subprocess
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPixmap
from image_processing import generate_rank_image, generate_show_image, process_all_images, remove_deleted_images, generate_schedule_image
from database import init_database, register_user, login_user, update_schedule, get_schedule, isRegistered
import os
import openpyxl
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import word_processing

class LoginWindow(QtWidgets.QWidget):
    login_success = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        self.username_label = QtWidgets.QLabel('用户名：')
        self.username_input = QtWidgets.QLineEdit()
        self.password_label = QtWidgets.QLabel('密码：')
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login_button = QtWidgets.QPushButton('登录')
        self.register_button = QtWidgets.QPushButton('注册')

        # 将控件添加到布局中
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        if not isRegistered:
            layout.addWidget(self.register_button)

        # 设置布局
        self.setLayout(layout)

        # 连接信号和槽
        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)
        self.password_input.returnPressed.connect(self.login)

    def login(self):
        DEBUG = True
        username = self.username_input.text()
        password = self.password_input.text()
        if DEBUG:
            self.login_success.emit()
            return
        login_result = login_user(username, password)
        print(f"Login result: {login_result}")  # 添加这一行进行调试
        if login_user(username, password):
            self.login_success.emit()
        else:
            QtWidgets.QMessageBox.warning(self, '错误', '用户名或密码错误')

    def register(self):
        self.parent().setCurrentIndex(1)


class RegisterWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        process_all_images("./照片", "./照片改","./头像","./原头像")

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        self.username_label = QtWidgets.QLabel('用户名：')
        self.username_input = QtWidgets.QLineEdit()
        self.password_label = QtWidgets.QLabel('密码：')
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_password_label = QtWidgets.QLabel('确认密码：')
        self.confirm_password_input = QtWidgets.QLineEdit()
        self.confirm_password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.register_button = QtWidgets.QPushButton('注册')
        self.back_button = QtWidgets.QPushButton('返回')

        # 将控件添加到布局中
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(self.register_button)
        layout.addWidget(self.back_button)

        # 设置布局
        self.setLayout(layout)

        # 连接信号和槽
        self.register_button.clicked.connect(self.register)
        self.back_button.clicked.connect(self.back)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if password != confirm_password:
            QtWidgets.QMessageBox.warning(self, '错误', '两次输入的密码不一致')
            return

        if register_user(username, password):
            QtWidgets.QMessageBox.information(self, '成功', '注册成功，请登录')
            self.back()
        else:
            QtWidgets.QMessageBox.warning(self, '错误', '注册失败，用户名已存在')

    def back(self):
        self.parent().setCurrentIndex(0)

class FunctionSelectionWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()

        self.schedule_button = QtWidgets.QPushButton("排班表生成")
        self.ranking_button = QtWidgets.QPushButton("排名表生成")
        self.show_employee_photos_button = QtWidgets.QPushButton('生成员工展示图')
        
        layout.addWidget(self.schedule_button)
        layout.addWidget(self.ranking_button)
        layout.addWidget(self.show_employee_photos_button)

        self.setLayout(layout)

class RankingWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()

        self.status_label = QtWidgets.QLabel('正在生成排名表...')
        self.ok_button = QtWidgets.QPushButton('确定')
        self.ok_button.hide()

        layout.addWidget(self.status_label)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

        self.ok_button.clicked.connect(QtWidgets.qApp.quit)

    def generate_ranking(self):
        try:
            # 指定表格文件夹路径
            folder_path = '表格'

            # 获取表格文件夹下所有文件的文件名（包含后缀）
            file_names = os.listdir(folder_path)

            # 过滤出所有以 .xlsx 结尾的文件名，并将它们按照修改时间排序
            xlsx_files = [f for f in file_names if f.endswith('.xlsx')]
            xlsx_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder_path, f)), reverse=True)

            if not xlsx_files:
                self.status_label.setText("表格文件夹下不存在任何表格文件！")
                return

            # 打开 Excel 文件
            workbook = openpyxl.load_workbook(os.path.join(folder_path, xlsx_files[0]))

            # 选择工作表
            worksheet = workbook.active
            data = []
            for row in worksheet.iter_rows(min_row=2, max_col=2):
                employee_name = row[0].value
                if employee_name is None:
                    continue
                quantity = row[1].value
                # total_price = row[2].value
                data.append((employee_name, quantity))
                print(employee_name, quantity)

            # 按总价降序排序
            data.sort(key=lambda x: x[1], reverse=True)

            rank = data[:10]
            print(rank)

            basename, extension = os.path.splitext(xlsx_files[0])
            month_string, remaining = basename.split("月", 1)
            month = month_string[-2:] + "月"
            rank_image = generate_rank_image(rank, month)
            if not os.path.exists("./桃花榜"):
                os.makedirs("./桃花榜")

            output_path = os.path.join("./桃花榜", month + "桃花榜.png")
            rank_image.save(output_path)
            # 在这里添加将头像合成排名表的代码

            self.status_label.setText("排名表生成完毕")
            self.ok_button.show()

        except Exception as e:
            self.status_label.setText(f"生成排名表时出现错误：{str(e)}")
            print(f"生成排名表时出现错误：{str(e)}")

class ScheduleWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        # 创建文本编辑框并添加到布局中
        self.text_edit = QtWidgets.QTextEdit()
        layout.addWidget(self.text_edit)

        # 创建等待生成按钮并添加到布局中
        self.generate_button = QtWidgets.QPushButton('等待生成')
        self.generate_button.setEnabled(False)  # 初始状态设为不可按
        layout.addWidget(self.generate_button)

        # 将布局设置为窗口的布局
        self.setLayout(layout)

        # 连接信号和槽
        self.text_edit.textChanged.connect(self.update_button_state)
        self.generate_button.clicked.connect(self.process_input)

    def update_button_state(self):
        # 如果输入框不为空，按钮设为可按
        if self.text_edit.toPlainText().strip():
            self.generate_button.setEnabled(True)
        else:
            self.generate_button.setEnabled(False)

    def process_input(self):
        # 处理文本输入
        input_text = self.text_edit.toPlainText()
        processed_text = word_processing.parse_schedule_text(input_text, "照片")  # 假设 word_processing.py 有一个叫做 process 的函数
        return processed_text
    
class EmployeePhotoWindow(QtWidgets.QWidget):
    def __init__(self, employees):
        super().__init__()

        self.employees = employees
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # 创建名册
        self.create_employee_roster()

        # 文本提示
        self.text_prompt = QtWidgets.QLabel("请检查名册，填写分级，如果检查全部正确，请点击生成图片按钮开始生成")
        layout.addWidget(self.text_prompt)

        # 按钮
        self.open_roster_btn = QtWidgets.QPushButton("打开名册")
        self.open_roster_btn.clicked.connect(self.open_employee_roster)
        layout.addWidget(self.open_roster_btn)

        self.generate_pic_btn = QtWidgets.QPushButton("生成图片")
        self.generate_pic_btn.clicked.connect(self.on_generate_pic_clicked)
        layout.addWidget(self.generate_pic_btn)

        self.confirm_btn = QtWidgets.QPushButton("确认")
        self.confirm_btn.clicked.connect(self.on_confirm_clicked)
        layout.addWidget(self.confirm_btn)
        self.confirm_btn.hide()

        self.setLayout(layout)

    def create_employee_roster(self):
        avatars_folder = "./照片"
        roster_filename = "女仆名册.txt"

        # 检查文件是否存在，如果不存在则创建
        if not os.path.exists(roster_filename):
            with open(roster_filename, "w", encoding="utf-8") as roster_file:
                for employee in self.employees:
                    roster_file.write(f"{employee}:\n")
        else:
            print(f"文件 {roster_filename} 已存在，不会覆盖编辑过的内容。")

    def open_employee_roster(self):
        roster_filename = "女仆名册.txt"
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', roster_filename))
        elif os.name == 'nt':
            os.startfile(roster_filename)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', roster_filename))
        else:
            print("未知操作系统，无法自动打开文件。请手动打开：", roster_filename)


    def read_employee_roster(self,roster_filename):
        employee_rankings = {}
        with open(roster_filename, "r", encoding="utf-8") as roster_file:
            for line in roster_file:
                employee, ranking = line.strip().split(":")
                employee_rankings[employee] = ranking

        return employee_rankings

    def prepare_employee_data(self):
        roster_filename = "女仆名册.txt"
        employee_rankings = self.read_employee_roster(roster_filename)

        employees_by_ranking = {}
        for employee, ranking in employee_rankings.items():
            if ranking not in employees_by_ranking:
                employees_by_ranking[ranking] = []
            employees_by_ranking[ranking].append(employee)

        return employees_by_ranking

    def generate_show_pic(self):
        employees_by_ranking = self.prepare_employee_data()
        generate_show_image(employees_by_ranking)
        self.text_prompt.setText("图片生成完成")
        self.open_roster_btn.hide()
        self.generate_pic_btn.hide()
        self.confirm_btn.show()

    def on_generate_pic_clicked(self):
        print("Generate button clicked, checking rankings...")
        employees_without_rankings = self.check_employee_rankings()
        if employees_without_rankings:
            print(f"Employees without rankings found: {', '.join(employees_without_rankings)}")
            self.text_prompt.setText("以下员工没有被分级：\n" + "\n".join(employees_without_rankings))
            return

        print("All employees have rankings, generating picture...")
        self.generate_show_pic()

    def check_employee_rankings(self):
        roster_filename = "女仆名册.txt"
        avatars_folder = "./照片"

        # 从名册文件中获取已经分级的员工
        ranked_employees = self.read_employee_roster(roster_filename).keys()
        print(f"Ranked employees: {', '.join(ranked_employees)}")

        # 从照片文件夹获取所有员工
        all_employees = [f.replace('.jpg', '').replace('.jpeg', '') 
                        for f in os.listdir(avatars_folder) if f.endswith('.jpg') or f.endswith('.jpeg')]
        print(f"All employees: {', '.join(all_employees)}")

        # 查找没有分级的员工
        employees_without_rankings = [employee for employee in all_employees if employee not in ranked_employees]
        print(f"Employees without rankings: {', '.join(employees_without_rankings)}")

        return employees_without_rankings
    
    def on_confirm_clicked(self):
        print("Confirm button clicked, closing application...")
        QtWidgets.qApp.quit()
    
class GenerateScheduleWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        self.status_label = QtWidgets.QLabel('正在生成排班表...')
        self.ok_button = QtWidgets.QPushButton('确定')
        self.ok_button.hide()

        # 将控件添加到布局中
        layout.addWidget(self.status_label)
        layout.addWidget(self.ok_button)

        # 设置布局
        self.setLayout(layout)

        # 连接信号和槽
        self.ok_button.clicked.connect(QtWidgets.qApp.quit)

    def generation_finished(self):
        self.status_label.setText('排班表生成完毕')
        self.ok_button.show()

    def generate_schedule_image(self, schedule_data):
        # 调用 generate_schedule_image 函数并传入排班数据
        schedule_image = generate_schedule_image(schedule_data)

        # 将生成的排班表图片保存在程序根目录下，命名为当前时间
        current_time = datetime.now().strftime('%m月%d日%H时%M分%S秒')
        output_path = f"排班表/{current_time}.png"
        schedule_image.save(output_path)

        # 调用generation_finished方法，更新状态并显示ok_button
        self.generation_finished()

    def setImage(self, image_path):
        self.image_path = image_path

class GenerateScheduleThread(QThread):
    generation_finished = pyqtSignal(str)

    def __init__(self, generate_schedule_image, selected_employees):
        super().__init__()
        self.generate_schedule_image = generate_schedule_image
        self.selected_employees = selected_employees

    def run(self):
        image_path = self.generate_schedule_image(self.selected_employees)
        self.generation_finished.emit(image_path)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建堆栈窗口部件
        self.stack = QtWidgets.QStackedWidget()

        # 创建登录、注册和排班窗口
        self.login_window = LoginWindow()
        self.register_window = RegisterWindow()
        self.week_days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        avatars_folder = "./照片"
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        self.employees = [os.path.splitext(filename)[0] for filename in os.listdir(avatars_folder) if os.path.splitext(filename)[1].lower() in image_extensions]

        # 创建 ScheduleWindow 并传递员工列表
        self.schedule_window = ScheduleWindow()
        self.show_schedule_window()

        self.generate_schedule_window = GenerateScheduleWindow()
        self.function_selection_window = FunctionSelectionWindow()
        self.ranking_window = RankingWindow()
        self.employee_photo_window = EmployeePhotoWindow(self.employees)

        # 将窗口添加到堆栈部件中
        self.stack.addWidget(self.login_window)
        self.stack.addWidget(self.register_window)
        self.stack.addWidget(self.schedule_window)
        self.stack.addWidget(self.generate_schedule_window)
        self.stack.addWidget(self.function_selection_window)
        self.stack.addWidget(self.ranking_window)
        self.stack.addWidget(self.employee_photo_window)

        # 设置堆栈窗口部件为中心部件
        self.setCentralWidget(self.stack)

        # 连接信号和槽
        self.login_window.login_success.connect(self.show_function_selection_window)
        self.login_window.register_button.clicked.connect(self.show_register_window)
        self.register_window.back_button.clicked.connect(self.show_login_window)
        self.schedule_window.generate_button.clicked.connect(self.show_generate_schedule_window)
        self.function_selection_window.schedule_button.clicked.connect(self.show_schedule_window)
        self.function_selection_window.ranking_button.clicked.connect(self.show_ranking_window)
        self.function_selection_window.show_employee_photos_button.clicked.connect(self.show_employee_photo_window)

    def show_login_window(self):
        self.stack.setCurrentIndex(0)

    def show_register_window(self):
        self.stack.setCurrentIndex(1)

    def show_schedule_window(self):
        self.stack.setCurrentIndex(2)

    def show_generate_schedule_window(self):
        self.stack.setCurrentIndex(3)
        # 获取并处理当前的排班信息
        processed_schedule = self.schedule_window.process_input()

        # 创建新线程用于处理耗时操作
        self.generate_schedule_thread = GenerateScheduleThread(self.generate_schedule_window.generate_schedule_image, processed_schedule)
        self.generate_schedule_thread.generation_finished.connect(self.on_generation_finished)
        self.generate_schedule_thread.start()
        
    def show_function_selection_window(self):
        self.stack.setCurrentIndex(4)

    def show_ranking_window(self):
        self.stack.setCurrentIndex(5)
        self.ranking_window.generate_ranking()

    def show_employee_photo_window(self):
        self.stack.setCurrentIndex(6)

    def on_generation_finished(self):
        # 在 ScheduleWindow 上去掉显示等待中，显示已完成
        self.generate_schedule_window.generation_finished()

    def save_schedule(self):
        # Call the update_schedule function here to save the schedule to the database
        user_id = 1  # Assuming the user_id is 1, replace it with the actual user_id after implementing user login
        for week_day in range(1, 8):
            # Get employee checkboxes for each week day
            employee_checkboxes = self.schedule_window.get_employee_checkboxes_for_week_day(week_day)
            selected_employees = [employee.text() for employee in employee_checkboxes if employee.isChecked()]
            update_schedule(user_id, week_day, selected_employees)

if __name__ == '__main__':
    init_database()
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
