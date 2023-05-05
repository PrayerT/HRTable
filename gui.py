from PyQt5 import QtWidgets, QtGui, QtCore
from image_processing import generate_rank_image, process_all_images, remove_deleted_images, generate_schedule_image
from database import init_database, register_user, login_user, update_schedule, get_schedule, isRegistered
from PyQt5.QtWidgets import QVBoxLayout, QScrollArea
import os
import openpyxl
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

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
        process_all_images("./照片","./头像","./原头像")

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

        layout.addWidget(self.schedule_button)
        layout.addWidget(self.ranking_button)

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
            for row in worksheet.iter_rows(min_row=3, max_col=3):
                employee_name = row[0].value
                if employee_name is None:
                    continue
                quantity = row[1].value
                total_price = row[2].value
                data.append((employee_name, quantity, total_price))
                print(employee_name, quantity, total_price)

            # 按总价降序排序
            data.sort(key=lambda x: x[2], reverse=True)

            rank = [x[0] for x in data[:10]]
            print(rank)

            #TODO: 生成排名表
            generate_rank_image(rank)
            # 在这里添加将头像合成排名表的代码

            self.status_label.setText("排名表生成完毕")
            self.ok_button.show()

        except Exception as e:
            self.status_label.setText(f"生成排名表时出现错误：{str(e)}")
            print(f"生成排名表时出现错误：{str(e)}")

class ScheduleWindow(QtWidgets.QWidget):
    def __init__(self, employees):
        super().__init__()
        self.employees = employees

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        self.week_days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.tab_widget = QtWidgets.QTabWidget()

        self.tabs = []
        employee_chunks = [self.employees]
        self.employee_checkboxes = {}  # 初始化 employee_checkboxes 字典
        for i in range(7):
            tab = self.create_employee_tab(employee_chunks[i % len(employee_chunks)])
            self.tabs.append(tab)
            self.tab_widget.addTab(tab, self.week_days[i])

        layout.addWidget(self.tab_widget)

        button_layout = QtWidgets.QHBoxLayout()
        self.select_all_button = QtWidgets.QPushButton('全选')
        self.select_inverse_button = QtWidgets.QPushButton('反选')
        self.clear_selection_button = QtWidgets.QPushButton('清空')
        self.wait_button = QtWidgets.QPushButton('等待生成')
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.select_inverse_button)
        button_layout.addWidget(self.clear_selection_button)
        button_layout.addWidget(self.wait_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

        # 连接信号和槽
        self.select_all_button.clicked.connect(self.select_all)
        self.select_inverse_button.clicked.connect(self.select_inverse)
        self.clear_selection_button.clicked.connect(self.clear_selection)

    def get_active_tab_employee_checkboxes(self):
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index < 0 or current_tab_index >= len(self.tabs):
            return []
        current_tab = self.tabs[current_tab_index]
        return self.get_current_employee_checkboxes(current_tab)
    
    def select_inverse(self):
        # 实现反选功能
        employee_checkboxes = self.get_active_tab_employee_checkboxes()
        for employee_checkbox in employee_checkboxes:
            employee_checkbox.setChecked(not employee_checkbox.isChecked())

    def select_all(self):
        # 实现全选功能
        employee_checkboxes = self.get_active_tab_employee_checkboxes()
        for employee_checkbox in employee_checkboxes:
            employee_checkbox.setChecked(True)

    def clear_selection(self):
        # 实现清空功能
        employee_checkboxes = self.get_active_tab_employee_checkboxes()
        for employee_checkbox in employee_checkboxes:
            employee_checkbox.setChecked(False)

    def create_employee_tab(self, employees):
        # 创建一个新的选项卡
        tab = QtWidgets.QWidget()
        
        # 为选项卡创建一个 QVBoxLayout
        layout = QVBoxLayout()
        
        # 将员工复选框添加到布局中
        for employee in employees:
            checkbox = QtWidgets.QCheckBox(employee)
            layout.addWidget(checkbox)
        
        # 将布局添加到选项卡中
        tab.setLayout(layout)
        
        return tab
    
    def load_schedule(self, schedule_data):
        print(f"Loading schedule data: {schedule_data}")
        for i, tab in enumerate(self.tabs):
            employee_checkboxes = self.get_current_employee_checkboxes(tab)
            for checkbox in employee_checkboxes:
                if checkbox.text() in schedule_data[self.week_days[i]]:
                    checkbox.setChecked(True)
    
    def get_current_employee_checkboxes(self, tab):
        layout = tab.layout()
        employee_checkboxes = [layout.itemAt(i).widget() for i in range(layout.count()) if isinstance(layout.itemAt(i).widget(), QtWidgets.QCheckBox)]
        return employee_checkboxes
    
    def get_selected_employees(self):
        selected_employees = {}
        for i, tab in enumerate(self.tabs):
            checkboxes = self.get_current_employee_checkboxes(tab)
            selected = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]
            print(f"Selected employees on {self.week_days[i]}: {selected}")  # 添加 log 输出
            selected_employees[self.week_days[i]] = selected
        print(f"Selected employees: {selected_employees}")  # 添加 log 输出
        return selected_employees
    
    def get_employee_checkboxes_for_week_day(self, week_day):
        # Get the employee checkboxes for a specific week_day
        if 1 <= week_day <= len(self.tabs):
            tab = self.tabs[week_day - 1]
            return self.get_current_employee_checkboxes(tab)
        return []



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
        self.schedule_window = ScheduleWindow(self.employees)
        self.show_schedule_window()

        self.generate_schedule_window = GenerateScheduleWindow()
        self.function_selection_window = FunctionSelectionWindow()
        self.ranking_window = RankingWindow()

        # 将窗口添加到堆栈部件中
        self.stack.addWidget(self.login_window)
        self.stack.addWidget(self.register_window)
        self.stack.addWidget(self.schedule_window)
        self.stack.addWidget(self.generate_schedule_window)
        self.stack.addWidget(self.function_selection_window)
        self.stack.addWidget(self.ranking_window)

        # 设置堆栈窗口部件为中心部件
        self.setCentralWidget(self.stack)

        # 连接信号和槽
        self.login_window.login_success.connect(self.show_function_selection_window)
        self.login_window.register_button.clicked.connect(self.show_register_window)
        self.register_window.back_button.clicked.connect(self.show_login_window)
        self.schedule_window.wait_button.clicked.connect(self.show_generate_schedule_window)
        self.function_selection_window.schedule_button.clicked.connect(self.show_schedule_window)
        self.function_selection_window.ranking_button.clicked.connect(self.show_ranking_window)


    def show_login_window(self):
        self.stack.setCurrentIndex(0)

    def show_register_window(self):
        self.stack.setCurrentIndex(1)

    def show_schedule_window(self, load_schedule=True):
        if load_schedule:
            user_id = 1  # Assuming the user_id is 1, replace it with the actual user_id after implementing user login
            schedule_data = {self.week_days[week_day - 1]: get_schedule(user_id, week_day) for week_day in range(1, 8)}
            self.schedule_window.load_schedule(schedule_data)
        self.stack.setCurrentIndex(2)

    def show_generate_schedule_window(self):
        self.stack.setCurrentIndex(3)
        # 获取当前选定的员工数据
        selected_employees = self.schedule_window.get_selected_employees()
        self.save_schedule()

        # 创建新线程用于处理耗时操作
        self.generate_schedule_thread = GenerateScheduleThread(self.generate_schedule_window.generate_schedule_image, selected_employees)
        self.generate_schedule_thread.generation_finished.connect(self.on_generation_finished)
        self.generate_schedule_thread.start()

    def show_function_selection_window(self):
        self.stack.setCurrentIndex(4)

    def show_ranking_window(self):
        self.stack.setCurrentIndex(5)
        self.ranking_window.generate_ranking()

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
