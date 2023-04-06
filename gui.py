from PyQt5 import QtWidgets, QtGui, QtCore
from image_processing import process_employee_images
from database import register_user, login_user, save_schedule, load_schedule

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

        if login_user(username, password):
            self.login_success.emit()
        else:
            QtWidgets.QMessageBox.warning(self, '错误', '用户名或密码错误')

    def register(self):
        self.parent().setCurrentIndex(1)


class RegisterWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

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
    def __init__(self):
        super().__init__()

        # 创建布局和控件
        layout = QtWidgets.QVBoxLayout()

        self.week_days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        self.tab_widget = QtWidgets.QTabWidget()

        self.tabs = []
        for i in range(7):
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout()

            # 在此处创建员工复选框并添加到tab_layout中

            # 创建反选、全选和清空按钮
            btn_layout = QtWidgets.QHBoxLayout()
            btn_select_inverse = QtWidgets.QPushButton('反选')
            btn_select_inverse.clicked.connect(self.select_inverse)
            btn_select_all = QtWidgets.QPushButton('全选')
            btn_select_all.clicked.connect(self.select_all)
            btn_clear = QtWidgets.QPushButton('清空')
            btn_clear.clicked.connect(self.clear_selection)

            btn_layout.addWidget(btn_select_inverse)
            btn_layout.addWidget(btn_select_all)
            btn_layout.addWidget(btn_clear)

            tab_layout.addLayout(btn_layout)
            tab.setLayout(tab_layout)
            self.tab_widget.addTab(tab, self.week_days[i])

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def select_inverse(self):
        # 实现反选功能
        for employee_checkbox in self.employee_checkboxes:
            employee_checkbox.setChecked(not employee_checkbox.isChecked())

    def select_all(self):
        # 实现全选功能
        for employee_checkbox in self.employee_checkboxes:
            employee_checkbox.setChecked(True)

    def clear_selection(self):
        # 实现清空功能
        for employee_checkbox in self.employee_checkboxes:
            employee_checkbox.setChecked(False)


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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('排班表生成器')

        # 创建一个堆叠窗口小部件并将其设置为中心窗口小部件
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # 创建子窗口并将其添加到堆叠窗口小部件中
        self.login_window = LoginWindow()
        self.register_window = RegisterWindow()
        self.schedule_window = ScheduleWindow()
        self.generate_schedule_window = GenerateScheduleWindow()

        self.stack.addWidget(self.login_window)
        self.stack.addWidget(self.register_window)
        self.stack.addWidget(self.schedule_window)
        self.stack.addWidget(self.generate_schedule_window)

        # 连接子窗口的信号和槽
        self.login_window.login_success.connect(self.show_schedule_window)
        self.login_window.register_button.clicked.connect(self.show_register_window)
        self.register_window.back_button.clicked.connect(self.show_login_window)

    def show_schedule_window(self):
        self.stack.setCurrentIndex(2)

    def show_login_window(self):
        self.stack.setCurrentIndex(0)

    def show_register_window(self):
        self.stack.setCurrentIndex(1)

    def show_generate_schedule_window(self):
        self.stack.setCurrentIndex(3)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
