from PyQt5 import QtWidgets, QtGui, QtCore
from image_processing import process_all_images, remove_deleted_images, generate_schedule_image
from database import register_user, login_user, update_schedule, get_schedule, init_database
from PyQt5.QtWidgets import QVBoxLayout
import os
import time

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
        layout.addWidget(self.register_button)

        # 设置布局
        self.setLayout(layout)

        # 连接信号和槽
        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
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
        process_all_images("./照片","./头像")

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

class ScheduleWindow(QtWidgets.QWidget):
    def __init__(self, employees):
        super().__init__()
        self.employees = employees

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        self.week_days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.tab_widget = QtWidgets.QTabWidget()

        self.tabs = []
        employee_chunks = [self.employees[i:i + 10] for i in range(0, len(self.employees), 10)]
        for i in range(7):
            tab = self.create_employee_tab(employee_chunks[i % len(employee_chunks)])
            self.tabs.append(tab)
            self.tab_widget.addTab(tab, self.week_days[i])

        layout.addWidget(self.tab_widget)

        button_layout = QtWidgets.QHBoxLayout()
        self.wait_button = QtWidgets.QPushButton('等待生成')
        button_layout.addWidget(self.wait_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

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
    
    def get_current_employee_checkboxes(self, tab):
        layout = tab.layout()
        employee_checkboxes = [layout.itemAt(i).widget() for i in range(layout.count()) if isinstance(layout.itemAt(i).widget(), QtWidgets.QCheckBox)]
        return employee_checkboxes
    
    def get_selected_employees(self):
        selected_employees = {}
        for i, tab in enumerate(self.tabs):
            checkboxes = self.get_current_employee_checkboxes(tab)
            selected = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]
            selected_employees[self.week_days[i]] = selected
        return selected_employees


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

        # 将生成的排班表图片保存在程序根目录下，命名为当前时间戳
        timestamp = str(int(time.time()))
        output_path = f"{timestamp}.png"
        schedule_image.save(output_path)

        # 调用generation_finished方法，更新状态并显示ok_button
        self.generation_finished()

    def setImage(self, image_path):
        self.image_path = image_path

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

# 创建堆栈窗口部件
        self.stack = QtWidgets.QStackedWidget()

        # 创建登录、注册和排班窗口
        self.login_window = LoginWindow()
        self.register_window = RegisterWindow()

        avatars_folder = "./照片"
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        self.employees = [os.path.splitext(filename)[0] for filename in os.listdir(avatars_folder) if os.path.splitext(filename)[1].lower() in image_extensions]

        # 创建 ScheduleWindow 并传递员工列表
        self.schedule_window = ScheduleWindow(self.employees)

        self.generate_schedule_window = GenerateScheduleWindow()

        # 将窗口添加到堆栈部件中
        self.stack.addWidget(self.login_window)
        self.stack.addWidget(self.register_window)
        self.stack.addWidget(self.schedule_window)
        self.stack.addWidget(self.generate_schedule_window)

        # 设置堆栈窗口部件为中心部件
        self.setCentralWidget(self.stack)

        # 连接信号和槽
        self.login_window.login_success.connect(self.show_schedule_window)
        self.login_window.register_button.clicked.connect(self.show_register_window)
        self.register_window.back_button.clicked.connect(self.show_login_window)
        self.schedule_window.wait_button.clicked.connect(self.show_generate_schedule_window)


    def show_login_window(self):
        self.stack.setCurrentIndex(0)

    def show_register_window(self):
        self.stack.setCurrentIndex(1)

    def show_schedule_window(self):
        self.stack.setCurrentIndex(2)

    def show_generate_schedule_window(self):
        self.stack.setCurrentIndex(3)
        # 获取选定的员工数据
        selected_employees = self.schedule_window.get_selected_employees()

        # 调用 generate_schedule_image 方法并传入选定的员工数据
        image_path = self.generate_schedule_window.generate_schedule_image(selected_employees)

        # 在 ScheduleWindow 上去掉显示等待中，显示已完成
        self.generate_schedule_window.generation_finished()

    def delete_images(self):
        # Call the remove_deleted_images function here
        input_folder = "./照片"
        output_folder = "./头像"
        remove_deleted_images(input_folder, output_folder)

    def save_schedule(self):
        # Call the update_schedule function here to save the schedule to the database
        user_id = 1  # Assuming the user_id is 1, replace it with the actual user_id after implementing user login
        for week_day in range(1, 8):
            # Assuming employee_checkboxes is a list of lists containing the employee checkboxes for each week day
            selected_employees = [employee for employee in self.schedule_window.employee_checkboxes[week_day - 1] if employee.isChecked()]
            update_schedule(user_id, week_day, selected_employees)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
