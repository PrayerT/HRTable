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
        DEBUG = False
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
        process_all_images("./照片", "./照片改","./头像","./原头像", False)

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
        self.generate_avatars_button = QtWidgets.QPushButton('头像有误，重新生成')

        layout.addWidget(self.schedule_button)
        layout.addWidget(self.ranking_button)
        layout.addWidget(self.show_employee_photos_button)
        layout.addWidget(self.generate_avatars_button)

        self.avatar_processing_thread = AvatarProcessingThread()
        self.avatar_processing_thread.processingStarted.connect(self.on_avatar_processing_started)
        self.avatar_processing_thread.processingFinished.connect(self.on_avatar_processing_finished)
        self.generate_avatars_button.clicked.connect(self.on_generate_avatars_button_clicked)

        self.setLayout(layout)

    def on_avatar_processing_started(self):
        self.schedule_button.setEnabled(False)
        self.ranking_button.setEnabled(False)
        self.show_employee_photos_button.setEnabled(False)
        self.generate_avatars_button.setEnabled(False)

    def on_avatar_processing_finished(self):
        self.schedule_button.setEnabled(True)
        self.ranking_button.setEnabled(True)
        self.show_employee_photos_button.setEnabled(True)
        self.generate_avatars_button.setEnabled(True)
        self.generate_avatars_button.setText("处理完毕，点击再次处理")

    def on_generate_avatars_button_clicked(self):
        self.generate_avatars_button.setText("正在处理……")
        self.avatar_processing_thread.start()

class AvatarProcessingThread(QThread):
    processingStarted = pyqtSignal()
    processingFinished = pyqtSignal()

    def run(self):
        self.processingStarted.emit()
        process_all_images("./照片", "./照片改","./头像","./原头像", True)
        self.processingFinished.emit()

class RankingWindow(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()
        self.main_window = main_window

        self.status_label = QtWidgets.QLabel('正在生成排名表...')
        self.ok_button = QtWidgets.QPushButton('回到功能选择')
        self.ok_button.hide()

        layout.addWidget(self.status_label)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

        self.ok_button.clicked.connect(self.on_back_button_clicked)

    def generate_ranking(self):
        # try:
        # 指定表格文件夹路径
        folder_path = '表格'

        # 获取表格文件夹下所有文件的文件名（包含后缀）
        file_names = os.listdir(folder_path)

        # 过滤出所有以 .xlsx 结尾的文件名，并将它们按照修改时间排序
        # 过滤出所有以 .xlsx 结尾，且不以 '~$' 开头的文件名，并将它们按照修改时间排序
        xlsx_files = [f for f in file_names if f.endswith('.xlsx') and not f.startswith('~$')]
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

        # except Exception as e:
        #     self.status_label.setText(f"生成排名表时出现错误：{str(e)}")
        #     print(f"生成排名表时出现错误：{str(e)}")

    def on_back_button_clicked(self):
        # 返回功能选择页面
        self.main_window.switch_to_function_selection_window()

class ScheduleWindow(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()
        self.main_window = main_window

        # 创建文本编辑框并添加到布局中
        self.text_edit = QtWidgets.QTextEdit()
        layout.addWidget(self.text_edit)

        # 创建等待生成按钮并添加到布局中
        self.generate_button = QtWidgets.QPushButton('等待生成')
        self.generate_button.setEnabled(False)  # 初始状态设为不可按
        layout.addWidget(self.generate_button)

        # 添加返回按钮
        self.back_button = QtWidgets.QPushButton('返回')
        self.back_button.clicked.connect(self.on_back_button_clicked)
        layout.addWidget(self.back_button)

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
        processed_text = word_processing.parse_schedule_text(input_text, "照片")
        return processed_text
    
    def on_back_button_clicked(self):
        # 返回功能选择页面
        self.main_window.switch_to_function_selection_window()
    
class EmployeePhotoWindow(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # 文本提示
        self.text_prompt = QtWidgets.QLabel("请检查压缩包是否正确，如果检查全部正确，请点击生成图片按钮开始生成")
        layout.addWidget(self.text_prompt)

        # 按钮
        self.generate_pic_btn = QtWidgets.QPushButton("生成图片")
        self.generate_pic_btn.clicked.connect(self.on_generate_pic_clicked)
        layout.addWidget(self.generate_pic_btn)

        self.confirm_btn = QtWidgets.QPushButton("回到功能选择")
        self.confirm_btn.clicked.connect(self.on_back_button_clicked)
        layout.addWidget(self.confirm_btn)
        self.confirm_btn.hide()

        self.setLayout(layout)

    def on_back_button_clicked(self):
        self.reset_window()
        # 返回功能选择页面
        self.main_window.switch_to_function_selection_window()

    def get_employee_data_from_folders(self):
        base_folder = "助教"
        rankings = ['A级', 'R级', 'S级']

        employees_by_ranking = {}
        for ranking in rankings:
            ranking_folder = os.path.join(base_folder, ranking)
            if os.path.exists(ranking_folder):
                employees = [f.replace('.jpg', '') for f in os.listdir(ranking_folder) if f.endswith('.jpg')]
                employees_by_ranking[ranking] = employees

        return employees_by_ranking

    def prepare_employee_data(self):
        employees_by_ranking = self.get_employee_data_from_folders()

        # 将 R 级别的员工放在 A 级别和 S 级别之间
        if 'R' in employees_by_ranking:
            R_ranking_employees = employees_by_ranking.pop('R')
            new_employee_ranking = {}
            for ranking, employees in employees_by_ranking.items():
                if ranking == 'A':
                    new_employee_ranking['R'] = R_ranking_employees
                new_employee_ranking[ranking] = employees
            employees_by_ranking = new_employee_ranking

        return employees_by_ranking

    def generate_show_pic(self):
        employees_by_ranking = self.prepare_employee_data()
        generate_show_image(employees_by_ranking)
        self.text_prompt.setText("图片生成完成")
        self.generate_pic_btn.hide()
        self.confirm_btn.show()

    def on_generate_pic_clicked(self):
        self.generate_show_pic()

    def reset_window(self):
        self.text_prompt.setText("请检查分级，如果检查全部正确，请点击生成图片按钮开始生成")
        self.generate_pic_btn.show()
        self.confirm_btn.hide()
        
class GenerateScheduleWindow(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()
        self.main_window = main_window

        self.status_label = QtWidgets.QLabel('正在生成排班表...')
        self.ok_button = QtWidgets.QPushButton('返回功能选择')
        self.ok_button.hide()

        # 将控件添加到布局中
        layout.addWidget(self.status_label)
        layout.addWidget(self.ok_button)

        # 设置布局
        self.setLayout(layout)

        # 连接信号和槽
        self.ok_button.clicked.connect(self.on_back_button_clicked)

    def on_back_button_clicked(self):
        self.reset_window()
        # 返回功能选择页面
        self.main_window.switch_to_function_selection_window()

    
    def reset_window(self):
        # 重置状态标签和确认按钮
        self.status_label.setText('正在生成排班表...')
        self.ok_button.hide()

    def generation_finished(self, image_path):
        self.setImage(image_path)
        self.status_label.setText('排班表生成完毕')
        self.ok_button.show()

    def generate_schedule_image(self, schedule_data):
        # 调用 generate_schedule_image 函数并传入排班数据
        schedule_image = generate_schedule_image(schedule_data)

        # 将生成的排班表图片保存在程序根目录下，命名为当前时间
        current_time = datetime.now().strftime('%m月%d日%H时%M分%S秒')
        output_path = f"排班表/{current_time}.png"
        schedule_image.save(output_path)

        return output_path

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

        avatars_folder = "照片"
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        self.employees = [os.path.splitext(filename)[0] for filename in os.listdir(avatars_folder) if os.path.splitext(filename)[1].lower() in image_extensions]

        # 创建 ScheduleWindow 并传递员工列表
        self.schedule_window = ScheduleWindow(self)
        self.show_schedule_window()

        self.generate_schedule_window = GenerateScheduleWindow(self)
        self.function_selection_window = FunctionSelectionWindow()
        self.ranking_window = RankingWindow(self)
        self.employee_photo_window = EmployeePhotoWindow(self)

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
        self.function_selection_window.generate_avatars_button.clicked.connect(
            self.function_selection_window.on_generate_avatars_button_clicked)


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
        self.generate_schedule_thread.generation_finished.connect(self.generate_schedule_window.generation_finished)
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

    def switch_to_function_selection_window(self):
        # 假设功能选择页面的索引是0
        self.stack.setCurrentIndex(4)

if __name__ == '__main__':
    init_database()
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
