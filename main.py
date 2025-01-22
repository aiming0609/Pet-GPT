"""
桌面宠物主程序
实现了一个基于PyQt5的桌面宠物应用，包含以下主要功能：
1. 可拖拽的透明窗口
2. 支持GIF动画显示
3. 右键菜单交互
4. 聊天对话功能
5. 状态显示
6. 系统托盘支持
"""

import os; os.environ['no_proxy'] = '*' # 避免代理网络产生意外污染

def main():
    #桌面宠物的类
    #导入桌宠界面
    import sys
    from PyQt5.QtCore import Qt, QPoint, QTimer, QSize, QObject, QSharedMemory, QCoreApplication, QPropertyAnimation, QRect, QEasingCurve
    from PyQt5.QtGui import  QMovie, QKeySequence, QIcon
    from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QLabel, QGraphicsDropShadowEffect, QFileDialog, QDialog, QVBoxLayout, \
        QPushButton, QLineEdit, QHBoxLayout, QInputDialog, QDesktopWidget, QCheckBox, QKeySequenceEdit, QSystemTrayIcon
    import configparser
    import random
    import codecs
    from chat_model.chat_main_windows import ChatWindow
    import configparser
    #全局快捷键
    import keyboard
    import threading

    class DesktopPet(QWidget, QObject):
        """
        桌面宠物主类
        继承自QWidget用于GUI显示，QObject用于信号槽机制
        
        属性:
            config: 配置对象，存储宠物的各种设置
            chat_window_open: 聊天窗口是否打开
            direction: 移动方向(-1:左, 0:停止, 1:右)
            pet_width: 宠物显示宽度
            pet_height: 宠物显示高度
        """

        def __init__(self, config):
            self.shared_memory = QSharedMemory("DesktopPetSharedMemory")
            if not self.shared_memory.create(1):  # 尝试创建共享内存
                print("应用程序已经在运行。")
                QCoreApplication.exit(1)  # 退出程序
                return

            super().__init__()
            self.config = config
            
            # 初始化昵称（移到前面）
            self.nickname = self.config.get("Pet", "NICKNAME", fallback="桌面宠物")
            
            # 创建系统托盘图标（移到前面）
            self.create_tray_icon()
            
            self.init_ui()

            self.chat_window_state_changed = False

            # 监听全局快捷键的线程
            keyboard_listener_thread = threading.Thread(target=self._run_keyboard_listener, daemon=True)
            keyboard_listener_thread.start()
            # pet自由移动
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_position)
            self.toggle_walk(self.config.getboolean("Pet", "RANDOM_WALK"))

            # 获取最大屏幕
            desktop = QDesktopWidget().availableGeometry()
            self.max_x = desktop.width() - self.width()
            self.max_y = desktop.height() - self.height()

            self.direction = random.choice([-1, 1])  # 初始化移动方向
            # 停止和移动判断
            self.stop_timer = QTimer()
            self.stop_timer.timeout.connect(self.restart_movement)
            self.movement_timer = QTimer()
            self.movement_timer.timeout.connect(self.stop_movement)
            
            # 根据配置设置是否随机提问
            if self.config.getboolean("Pet", "RANDOM_CHAT"):
                self.set_new_timers()  # 初始化停止时间和移动时间
            #快捷键监听
            self.chat_window_open = False

        #初始化界面
        def init_ui(self):
            """
            初始化用户界面
            设置窗口属性、创建布局、添加组件等
            
            主要组件:
            1. 顶部聊天区域(默认隐藏)
                - 对话气泡
                - 聊天输入框
            2. 宠物显示区域
                - GIF动画显示
                - 状态标签
            3. 右键菜单
                - 主菜单项(角色、互动、设置)
                - 子菜单
            4. 功能按钮(默认隐藏)
            """
            #父容器
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.pet_width = self.config.getint("Pet", "WIDTH")
            self.pet_height = self.config.getint("Pet", "HEIGHT")
            self.setFixedSize(self.pet_width+20, self.pet_height+200)  # 增加高度以容纳输入框
            screen_geometry = QApplication.desktop().availableGeometry()
            self.move(screen_geometry.width() - self.width()-500, screen_geometry.height() - self.height()-100)

            # 创建主布局
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # 顶部聊天区域
            self.top_widget = QWidget()
            self.top_widget.setFixedHeight(100)
            top_layout = QVBoxLayout(self.top_widget)
            top_layout.setContentsMargins(10, 5, 10, 5)

            # 对话气泡
            self.chat_bubble = QLabel()
            self.chat_bubble.setStyleSheet("""
                QLabel {
                    background-color: rgba(45, 45, 45, 180);
                    color: white;
                    border-radius: 10px;
                    padding: 8px;
                }
            """)
            self.chat_bubble.setWordWrap(True)
            self.chat_bubble.hide()
            top_layout.addWidget(self.chat_bubble)

            # 聊天输入框
            input_widget = QWidget()
            input_layout = QHBoxLayout(input_widget)
            input_layout.setContentsMargins(0, 0, 0, 0)

            self.chat_input = QLineEdit()
            self.chat_input.setPlaceholderText("请输入文字...")
            self.chat_input.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(45, 45, 45, 180);
                    color: white;
                    border-radius: 15px;
                    padding: 5px 10px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    background-color: rgba(60, 60, 60, 180);
                }
            """)
            self.chat_input.returnPressed.connect(self.send_chat_message)
            input_layout.addWidget(self.chat_input)

            top_layout.addWidget(input_widget)
            main_layout.addWidget(self.top_widget)
            self.top_widget.hide()  # 默认隐藏输入框

            # 宠物显示区域
            pet_widget = QWidget()
            pet_layout = QVBoxLayout(pet_widget)
            pet_layout.setContentsMargins(0, 0, 0, 0)

            #宠物信息
            self.pet_movie = QMovie(self.config["Pet"]["PET_ICON"])
            self.pet_movie.setScaledSize(QSize(self.pet_width, self.pet_height))
            self.pet_label = QLabel()
            self.pet_label.setMovie(self.pet_movie)
            self.pet_movie.start()

            # 状态显示（等级和电量）
            self.status_label = QLabel()
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(45, 45, 45, 180);
                    color: white;
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
            self.status_label.setText(f"电量: 185\n亲密: Lv.1")
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.hide()  # 默认隐藏状态显示

            pet_layout.addWidget(self.pet_label, alignment=Qt.AlignCenter)
            pet_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
            main_layout.addWidget(pet_widget)

            # 右键菜单
            self.menu = QMenu(self)
            self.menu.setStyleSheet("""
                QMenu {
                    background-color: rgba(0, 0, 0, 200);
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                    min-width: 100px;
                }
                QMenu::item {
                    color: white;
                    background-color: transparent;
                    padding: 8px 20px;
                    margin: 0px;
                }
                QMenu::item:selected {
                    background-color: rgba(255, 255, 255, 30);
                }
                QMenu::separator {
                    height: 1px;
                    background: rgba(255, 255, 255, 30);
                    margin: 4px 0px;
                }
                QMenu::right-arrow {
                    image: none;
                    width: 0px;
                }
            """)

            # 创建主菜单项
            character_action = QAction("角色 ▶", self)
            character_action.triggered.connect(self.show_character_dialog)
            
            interact_action = QAction("互动 ▶", self)
            interact_action.triggered.connect(self.show_interact_menu)
            
            settings_action = QAction("设置 ▶", self)
            settings_action.triggered.connect(self.show_settings_menu)

            # 添加主菜单项和退出选项
            self.menu.addAction(character_action)
            self.menu.addAction(interact_action)
            self.menu.addAction(settings_action)
            self.menu.addSeparator()
            
            minimize_action = QAction("最小化", self)
            minimize_action.triggered.connect(self.hide)
            self.menu.addAction(minimize_action)

            # 创建子菜单
            self.character_menu = QMenu(self)
            self.character_menu.setStyleSheet(self.menu.styleSheet())
            
            self.interact_menu = QMenu(self)
            self.interact_menu.setStyleSheet(self.menu.styleSheet())
            
            self.settings_menu = QMenu(self)
            self.settings_menu.setStyleSheet(self.menu.styleSheet())

            # 创建功能按钮
            self.buttons = []
            button_icons = ['👤', '💝', '⚙️']  # 减少按钮数量，只保留主要功能
            button_positions = [
                (-1, 0),   # 左
                (1, 0),    # 右
                (0, 1)     # 下
            ]
            
            for icon, pos in zip(button_icons, button_positions):
                btn = QPushButton(icon, self)
                btn.setFixedSize(35, 35)  # 稍微减小按钮尺寸
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(30, 30, 30, 220);
                        color: white;
                        border-radius: 17px;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: rgba(61, 61, 61, 220);
                    }
                """)
                btn.hide()  # 初始状态隐藏
                self.buttons.append((btn, pos))

            self.show()

        def send_chat_message(self):
            """
            处理聊天消息发送
            1. 获取输入框文本
            2. 显示对话气泡
            3. 将消息发送到聊天系统处理
            """
            message = self.chat_input.text().strip()
            if message:
                self.chat_input.clear()
                self.show_chat_bubble("system", message)
                # 调用现有的聊天功能处理消息
                self.chat_dialog_body.add_message("system", message)
                self.chat_dialog_body.context_history[2].append(message)
                self.chat_dialog_body.flowise.prompt_queue.put((message, self.chat_dialog_body.context_history, message, False))

        def show_chat_bubble(self, role, text):
            """
            显示对话气泡
            
            参数:
                role: 发送者角色
                text: 显示文本
            
            行为:
                显示文本3秒后自动隐藏
            """
            self.chat_bubble.setText(text)
            self.chat_bubble.adjustSize()
            self.chat_bubble.show()
            # 3秒后自动隐藏
            QTimer.singleShot(3000, self.chat_bubble.hide)

        # 快捷键启动窗口
        def toggle_chat_window(self):
            """
            切换聊天窗口显示状态
            如果窗口打开则关闭，如果关闭则打开
            """
            if self.chat_window_open:
                self.chat_window.close()
                self.chat_window_open = False
                self.chat_window = None
                self.chat_window_state_changed = True
                self.chat_bubble.hide()  # 隐藏气泡框
            else:
                self.chat_window = ChatWindow(self, self.config)
                self.chat_window.show()
                self.chat_window_open = True
                self.chat_window_state_changed = True

        #修改昵称
        def change_nickname(self):
            """
            修改宠物昵称
            1. 弹出输入对话框
            2. 更新配置
            3. 保存到配置文件
            """
            new_nickname, ok = QInputDialog.getText(self, "改昵称", "请输入新的昵称：", QLineEdit.Normal, self.nickname)
            if ok and new_nickname != '':
                self.nickname = new_nickname
                # 修改配置项
                self.config.set('Pet', 'NICKNAME', new_nickname)
                # 保存修改后的配置文件
                self.save_config()
        
        #根据鼠标更新对话框位置
        def update_chat_dialog_position(self):
            """
            更新对话框位置
            根据宠物当前位置调整对话框显示位置
            """
            if hasattr(self, 'chat_dialog') and self.chat_dialog.isVisible():
                dialog_position = self.mapToGlobal(QPoint(self.pet_pixmap.width() // 2, -self.chat_dialog.height()))
                self.chat_dialog.move(dialog_position)

        def mousePressEvent(self, event):
            """
            鼠标按下事件处理
            左键: 开始拖拽，隐藏菜单
            右键: 显示菜单
            """
            if event.button() == Qt.LeftButton:
                self.hide_menu_buttons()
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            elif event.button() == Qt.RightButton:
                self.show_menu_buttons()
            event.accept()

        def show_menu_buttons(self):
            """
            显示功能按钮和输入框
            1. 显示顶部输入框
            2. 显示状态标签
            3. 使用动画显示功能按钮
            """
            # 显示输入框
            self.top_widget.show()
            
            # 显示状态标签
            self.status_label.show()
            
            # 显示功能按钮
            center_x = self.pet_width // 2
            center_y = self.pet_height // 2
            radius = 60  # 减小按钮分布半径
            
            for btn, (dx, dy) in self.buttons:
                # 计算按钮位置
                x = center_x + dx * radius - 17  # 17是按钮尺寸的一半
                y = center_y + dy * radius - 17
                
                # 创建动画
                anim = QPropertyAnimation(btn, b"geometry")
                anim.setDuration(150)  # 减少动画时间
                anim.setStartValue(QRect(center_x - 17, center_y - 17, 35, 35))
                anim.setEndValue(QRect(int(x), int(y), 35, 35))
                anim.setEasingCurve(QEasingCurve.OutQuad)  # 使用更平滑的动画曲线
                
                btn.show()
                anim.start()

        def hide_menu_buttons(self):
            """
            隐藏功能按钮和输入框
            隐藏所有UI元素，返回到只显示宠物的状态
            """
            # 隐藏输入框
            self.top_widget.hide()
            
            # 隐藏状态标签
            self.status_label.hide()
            
            # 隐藏功能按钮
            for btn, _ in self.buttons:
                btn.hide()

        def mouseMoveEvent(self, event):
            """
            鼠标移动事件处理
            实现宠物窗口的拖拽功能
            """
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_position)
                self.update_chat_dialog_position()

        def contextMenuEvent(self, event):
            """
            右键菜单事件处理
            根据选择的菜单项显示对应的子菜单
            """
            action = self.menu.exec_(event.globalPos())
            if action:
                pos = event.globalPos()
                if "角色" in action.text():
                    self.show_character_menu(pos)
                elif "互动" in action.text():
                    self.show_interact_menu(pos)
                elif "设置" in action.text():
                    self.show_settings_menu(pos)

        # 修改图标路径
        def change_icon(self):
            """
            更换宠物图标
            1. 打开文件选择对话框
            2. 更新动画
            3. 保存配置
            """
            # 请在此处添加选择图标的逻辑，可以使用 QFileDialog 获取文件路径
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            new_icon_path, _ = QFileDialog.getOpenFileName(self, "选择新图标", "", "Images (*.png *.xpm *.jpg *.bmp, *.gif);;All Files (*)", options=options)
            if new_icon_path:
                self.pet_movie.stop()  # 停止动画
                # 替换影片
                self.pet_movie.setFileName(new_icon_path)
                # 获取图片尺寸
                self.pet_movie.setScaledSize(QSize(self.pet_width, self.pet_height))
                # 开始播放影片
                self.pet_movie.start()
                # 修改配置项
                self.config.set('Pet', 'PET_ICON', new_icon_path)
                # 保存修改后的配置文件
                self.save_config()

        def set_new_timers(self):
            """
            设置新的定时器
            为随机移动和停止设置随机时间间隔
            """
            stop_time = random.randint(10000, 20000)  # 生成一个2~5秒的随机数，作为移动时间
            self.stop_timer.start(stop_time)

            movement_time = random.randint(10000, 20000)  # 生成一个2~5秒的随机数，作为移动时间
            self.movement_timer.start(movement_time)

            # 如果停止时间到了，则展示一句话
            QTimer.singleShot(stop_time, self.random_speak)

        def restart_movement(self):
            """
            重新开始移动
            随机选择新的移动方向并重置定时器
            """
            self.stop_timer.stop()
            self.movement_timer.stop()
            self.direction = random.choice([-1, 1])  # 随机选择一个方向
            self.set_new_timers()

        def stop_movement(self):
            """
            停止移动
            停止当前移动并设置新的定时器
            """
            self.stop_timer.stop()
            self.movement_timer.stop()
            self.direction = 0  # 停止移动
            self.set_new_timers()  # 重新设置停止时间和移动时间

        def update_position(self):
            """
            更新宠物位置
            根据当前方向移动宠物，到达边界时改变方向
            """
            if self.direction == 0:  # 如果宠物停止了移动
                return  # 不执行任何移动操作
            if self.direction != 0:
                current_pos = self.pos()
                if self.direction == 1:  # 向右移动
                    new_pos = QPoint(current_pos.x() + 1, current_pos.y())
                    if new_pos.x() >= self.max_x:
                        self.direction = -1  # 碰到右边界，掉头向左
                else:  # 向左移动
                    new_pos = QPoint(current_pos.x() - 1, current_pos.y())
                    if new_pos.x() <= 0:
                        self.direction = 1  # 碰到左边界，掉头向右
                self.move(new_pos)
            else:  # 停止移动
                self.stop_timer.stop()
                self.movement_timer.stop()
                stop_time = random.randint(2000, 5000)  # 生成一个2~5秒的随机数，作为移动时间
                self.stop_timer.start(stop_time)
            
        def random_speak(self):
            """
            随机说话功能
            从预设对话列表中随机选择一句话显示
            """
            if not self.isVisible():  # 检查窗口是否可见
                return
            dialogues = ["我好无聊啊", "你想听个笑话吗？", "你有什么好玩的事情吗？", "你觉得我可爱吗？"]
            selected_dialogue = random.choice(dialogues)
            self.show_chat_bubble("system", selected_dialogue)

        #设置界面
        def show_settings_dialog(self):
            """
            显示设置对话框
            包含走动、提问、大小、API设置等选项
            """
            settings_dialog = QDialog(self)
            settings_dialog.setWindowTitle("设置")
            settings_dialog.setFixedSize(400, 200)

            screen_geometry = QApplication.desktop().availableGeometry()
            screen_center = screen_geometry.center()
            settings_dialog.move(screen_center.x() - settings_dialog.width() // 2, screen_center.y() - settings_dialog.height() // 2)

            layout = QVBoxLayout()

            self.walk_checkbox = QCheckBox("是否自由走动", self)
            self.walk_checkbox.setChecked(self.timer.isActive())
            self.walk_checkbox.stateChanged.connect(self.toggle_walk)
            layout.addWidget(self.walk_checkbox)

            self.random_question_checkbox = QCheckBox("是否随机提问", self)
            self.random_question_checkbox.setChecked(self.stop_timer.isActive())
            self.random_question_checkbox.stateChanged.connect(self.toggle_random_question)
            layout.addWidget(self.random_question_checkbox)

            change_size_button = QPushButton("调整大小", self)
            change_size_button.clicked.connect(self.change_size)
            layout.addWidget(change_size_button)

            # Flowise 设置
            flowise_key_layout = QHBoxLayout()
            flowise_key_label = QLabel("Flowise API Key:")
            self.flowise_key_input = QLineEdit()
            self.flowise_key_input.setText(self.config.get("Flowise", "flowise_api_key"))
            flowise_key_layout.addWidget(flowise_key_label)
            flowise_key_layout.addWidget(self.flowise_key_input)
            layout.addLayout(flowise_key_layout)

            flowise_url_layout = QHBoxLayout()
            flowise_url_label = QLabel("Flowise URL:")
            self.flowise_url_input = QLineEdit()
            self.flowise_url_input.setText(self.config.get("Flowise", "flowise_url"))
            flowise_url_layout.addWidget(flowise_url_label)
            flowise_url_layout.addWidget(self.flowise_url_input)
            layout.addLayout(flowise_url_layout)

            chat_window_shortcut_layout = QHBoxLayout()
            chat_window_shortcut_label = QLabel("本地聊天框快捷键:")
            self.chat_window_shortcut_input = QKeySequenceEdit()
            self.chat_window_shortcut_input.setKeySequence(QKeySequence(self.config.get("Pet", "Shortcuts_CHAT_WINDOW")))
            chat_window_shortcut_layout.addWidget(chat_window_shortcut_label)
            chat_window_shortcut_layout.addWidget(self.chat_window_shortcut_input)
            layout.addLayout(chat_window_shortcut_layout)

            ok_button = QPushButton("确定", self)
            ok_button.clicked.connect(lambda: self.save_all_config(
                self.walk_checkbox.isChecked(),
                self.random_question_checkbox.isChecked(),
                self.flowise_key_input.text(),
                self.flowise_url_input.text(),
                self.chat_window_shortcut_input.keySequence().toString()
            ))
            ok_button.clicked.connect(settings_dialog.accept)
            layout.addWidget(ok_button)

            settings_dialog.setLayout(layout)
            settings_dialog.exec_()

        def save_all_config(self, random_walk, random_chat, flowise_key, flowise_url, chat_window_shortcut):
            self.config.set('Pet', 'RANDOM_WALK', str(random_walk))
            self.config.set('Pet', 'RANDOM_CHAT', str(random_chat))
            self.config.set("Flowise", "flowise_api_key", flowise_key)
            self.config.set("Flowise", "flowise_url", flowise_url)
            self.config.set("Pet", "Shortcuts_CHAT_WINDOW", chat_window_shortcut)
            self.save_config()

        def toggle_random_question(self, state):
            if state == Qt.Checked and not self.isHidden():
                self.stop_timer.start()
            else:
                self.stop_timer.stop()

        def _run_keyboard_listener(self):
            chat_window_shortcut = self.config.get("Pet", "Shortcuts_CHAT_WINDOW")
            keyboard.add_hotkey(chat_window_shortcut, lambda: QTimer.singleShot(0, pet.toggle_chat_window))
            keyboard.wait()

        def set_chat_window_closed(self):
            self.chat_window_open = False

        # 控制宠物自由走动和随机提问功能
        def toggle_walk(self, state):
            if state:
                self.timer.start(50)
            else:
                self.timer.stop()
        
        def change_size(self):
            """
            修改宠物大小
            分别设置宽度和高度，并更新配置
            """
            flags = Qt.WindowSystemMenuHint | Qt.WindowTitleHint

            # 宽度输入框
            width_input_dialog = QInputDialog(self, flags)
            width_input_dialog.setWindowTitle("调整宽度")
            width_input_dialog.setLabelText("请输入新的宽度：")
            width_input_dialog.setIntRange(10, 500)
            width_input_dialog.setIntValue(self.pet_width)
            width_input_dialog.finished.connect(lambda: width_input_dialog.deleteLater())

            screen_geometry = QApplication.desktop().availableGeometry()
            screen_center = screen_geometry.center()
            width_input_dialog.move(screen_center.x() - width_input_dialog.width() // 2, screen_center.y() - width_input_dialog.height() // 2)

            result = width_input_dialog.exec_()
            if result == QInputDialog.Accepted:
                new_width = width_input_dialog.intValue()
                self.pet_width = new_width
                self.config.set("Pet", "WIDTH", str(new_width))

            # 高度输入框
            height_input_dialog = QInputDialog(self, flags)
            height_input_dialog.setWindowTitle("调整高度")
            height_input_dialog.setLabelText("请输入新的高度：")
            height_input_dialog.setIntRange(10, 500)
            height_input_dialog.setIntValue(self.pet_height)
            height_input_dialog.finished.connect(lambda: height_input_dialog.deleteLater())

            height_input_dialog.move(screen_center.x() - height_input_dialog.width() // 2, screen_center.y() - height_input_dialog.height() // 2)

            result = height_input_dialog.exec_()
            if result == QInputDialog.Accepted:
                new_height = height_input_dialog.intValue()
                self.pet_height = new_height
                self.config.set("Pet", "HEIGHT", str(new_height))

            self.pet_movie.setScaledSize(QSize(self.pet_width, self.pet_height))

            # 保存修改后的配置文件
            self.save_config()

        def show_pet(self):
            """显示宠物和对话气泡"""
            if self.stop_timer.isActive():
                self.chat_bubble.show()

        def hide_pet(self):
            """隐藏宠物的对话气泡"""
            self.chat_bubble.hide()

        def save_config(self):
            """保存配置到文件"""
            with codecs.open(config_path, 'w', 'utf-8') as f:
                self.config.write(f) 

        def closeEvent(self, event):
            """
            重写关闭事件
            点击关闭按钮时最小化到托盘而不是退出
            """
            if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                event.ignore()  # 忽略关闭事件
                self.hide()  # 隐藏窗口
            else:
                self.quit_application()  # 如果没有托盘图标，则完全退出

        def show_character_dialog(self):
            # TODO: 实现角色切换对话框
            pass

        def show_character_info(self):
            # TODO: 实现角色信息显示
            pass

        def touch_action(self):
            # TODO: 实现抚摸动作
            pass

        def dance_action(self):
            # TODO: 实现跳舞动作
            pass

        def show_character_menu(self, pos):
            """显示角色子菜单"""
            self.character_menu.clear()
            self.character_menu.addAction("切换角色")
            self.character_menu.addAction("角色信息")
            self.character_menu.exec_(pos)

        def show_interact_menu(self, pos):
            """显示互动子菜单"""
            self.interact_menu.clear()
            self.interact_menu.addAction("抚摸")
            self.interact_menu.addAction("跳舞")
            self.interact_menu.exec_(pos)

        def show_settings_menu(self, pos):
            """显示设置子菜单"""
            self.settings_menu.clear()
            self.settings_menu.addAction("更换形象")
            self.settings_menu.addAction("更改昵称")
            self.settings_menu.addAction("高级设置")
            self.settings_menu.exec_(pos)

        def quit_application(self):
            """
            最小化到系统托盘
            """
            if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                self.hide()  # 隐藏窗口
            else:
                # 如果没有托盘图标，则完全退出
                # 保存配置
                self.save_config()
                
                # 停止所有计时器
                self.timer.stop()
                self.stop_timer.stop()
                self.movement_timer.stop()
                
                # 释放共享内存
                if self.shared_memory is not None:
                    self.shared_memory.detach()
                
                # 退出应用
                QApplication.quit()

        def create_tray_icon(self):
            """
            创建系统托盘图标
            设置图标、提示文本和右键菜单
            """
            try:
                # 确保只创建一次
                if hasattr(self, 'tray_icon'):
                    if self.tray_icon.isVisible():
                        print("托盘图标已存在且可见")
                        return
                    else:
                        print("托盘图标存在但不可见，尝试重新显示")
                        self.tray_icon.show()
                        return
                
                print("开始创建托盘图标...")
                self.tray_icon = QSystemTrayIcon(self)
                
                # 使用 avatar_user.png 作为系统托盘图标
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pet_image', 'avatar_user.png')
                print(f"尝试加载图标: {icon_path}")
                
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        print("成功加载图标")
                        self.tray_icon.setIcon(icon)
                    else:
                        print(f"警告: 无法加载图标文件 {icon_path}")
                        self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
                else:
                    print(f"警告: 找不到图标文件 {icon_path}")
                    self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
                
                # 设置工具提示
                tooltip_text = f"{getattr(self, 'nickname', '桌面宠物')} - 桌面宠物"
                self.tray_icon.setToolTip(tooltip_text)
                
                # 创建托盘菜单
                tray_menu = QMenu()
                tray_menu.setStyleSheet("""
                    QMenu {
                        background-color: rgba(0, 0, 0, 200);
                        border: none;
                        border-radius: 4px;
                        padding: 4px;
                    }
                    QMenu::item {
                        color: white;
                        background-color: transparent;
                        padding: 8px 20px;
                    }
                    QMenu::item:selected {
                        background-color: rgba(255, 255, 255, 30);
                    }
                    QMenu::separator {
                        height: 1px;
                        background: rgba(255, 255, 255, 30);
                        margin: 4px 0px;
                    }
                """)
                
                show_action = QAction("显示", self)
                show_action.triggered.connect(self.show)
                
                hide_action = QAction("隐藏", self)
                hide_action.triggered.connect(self.hide)
                
                quit_action = QAction("退出", self)
                quit_action.triggered.connect(QApplication.quit)
                
                tray_menu.addAction(show_action)
                tray_menu.addAction(hide_action)
                tray_menu.addSeparator()
                tray_menu.addAction(quit_action)
                
                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.activated.connect(self.tray_icon_activated)
                
                # 显示托盘图标
                print("尝试显示托盘图标...")
                self.tray_icon.show()
                
                # 检查托盘图标是否真的显示了
                if not self.tray_icon.isVisible():
                    print("警告: 系统托盘图标未能显示，尝试延迟显示")
                    QTimer.singleShot(1000, lambda: self._retry_show_tray_icon(3))
                
            except Exception as e:
                print(f"创建托盘图标时出错: {str(e)}")

        def _retry_show_tray_icon(self, retries):
            """
            重试显示托盘图标
            
            Args:
                retries: 剩余重试次数
            """
            if not hasattr(self, 'tray_icon') or not self.tray_icon.isVisible():
                print(f"重试显示托盘图标 (剩余尝试次数: {retries})")
                self.tray_icon.show()
                if retries > 0 and not self.tray_icon.isVisible():
                    QTimer.singleShot(1000, lambda: self._retry_show_tray_icon(retries - 1))
            else:
                print("托盘图标显示成功")

        def tray_icon_activated(self, reason):
            """
            处理托盘图标的激活事件
            双击时切换显示/隐藏状态
            """
            if reason == QSystemTrayIcon.DoubleClick:
                if self.isVisible():
                    self.hide()
                else:
                    self.show()
                    self.activateWindow()  # 激活窗口
                    
        def hide(self):
            """
            重写hide方法，确保最小化时显示托盘图标
            """
            if not hasattr(self, 'tray_icon'):
                self.create_tray_icon()
            if not self.tray_icon.isVisible():
                self.tray_icon.show()
            super().hide()

    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        base_path = sys._MEIPASS
    else:
        # 如果是源代码
        base_path = os.path.dirname(__file__)

    config_path = os.path.join(base_path, 'pet_config_private.ini')
    app = QApplication(sys.argv)
    config = configparser.ConfigParser()
    with codecs.open(config_path, 'r', 'utf-8') as f:
        # 读取配置文件内容
        config = configparser.ConfigParser()
        config.read_file(f)
    pet = DesktopPet(config)
    sys.exit(app.exec_())  # 确保退出时关闭所有进程

if __name__ == "__main__":
    main()