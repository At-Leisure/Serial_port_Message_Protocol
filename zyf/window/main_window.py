import os
import re
import sys
import attr
import yaml
import shutil
import pathlib
import inspect
import pprint
import serial
import serial.serialutil
import serial.tools.list_ports
from typing import Literal
from icecream import ic
from functools import partial, wraps
from zyf.window.turntable import Turntable
from zyf.console import Console, Orders
from zyf.window.setting_window import SettingWindow
from zyf.window.bubble import MessageBubbleFrame, MessageBubbleUnit
from zyf.window.code_preview import CodeWindow
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6 import uic

MAIN_UI = './assets/ui/main-manager.ui'  # 主窗口的UI文件
MAIN_ICO = './assets/ico/usb1.png'  # 主窗口的图标文件

BAUDRATES = (300, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200)  # 右键菜单的波特率


def text2html(text: str) -> str:
    """ 将纯文本翻译为html """
    replace_dict = {
        '<': '&lt;',
        '>': '&gt;',
        '\n': '<br>'
    }
    for k, v in replace_dict.items():
        text = text.replace(k, v)
    return text


class ShortcutUnit(QWidget):
    """ 快捷指令(历史回顾)单元

    每个单元有`编辑`和`发送`两个按钮，编辑按钮用来修改后再发送，发送按钮则直接发送信息"""

    def __init__(self, mw: 'MainWindow', title: str, alias: str, define: str, id_: int, parent=None, *args, **kwargs):
        self.title = title
        self.alias = alias
        self.define = define
        self.id = id_
        self.mw = mw
        super().__init__(parent, *args, **kwargs)
        uic.loadUi('./assets/ui/shortcut_unit.ui', self)
        self.setToolTip(define)
        self.edit_btn.clicked.connect(self._edit_event)
        self.send_btn.clicked.connect(self._send_event)
        self.main_label.setText(f'{self.id}.{title}: {alias}')

    @property
    def order(self) -> str:
        c_args = re.findall(r'(?<==)\d+', self.define)  # 获取默认位置参数
        return f'[{self.id}:{",".join(c_args)}]'  # [指令id : 参数1, 参数2, ...]

    def _edit_event(self):
        order, e = self.mw.console.make_normal_order(self.order, do_send=False)
        self.mw.send_textEdit.setText(order)

    def _send_event(self):
        order, e = self.mw.console.make_normal_order(self.order)

        if e is None:
            self.mw.subBubbleFrame.add_message(title=self.title)
            self.mw.append_send_recv_info(self.title, 'tips')
            self.mw.append_send_recv_info_signal.emit(order, 'send')
        elif isinstance(e, serial.PortNotOpenError):
            self.mw.subBubbleFrame.add_message(type_='warn', title='串口未打开')
            self.mw.append_send_recv_info(f'"<< {order}" 发送无效', 'tips')


class ShortcutAndHistory(QDialog):
    """ 快捷指令和历史回顾的对话框 

    该对话框的两侧分别是快捷指令和发送历史"""

    def __init__(self, console: Console, parent: 'MainWindow' = None, *args, **kwargs):
        self.console = console
        self.mw = parent
        super().__init__(parent, *args, **kwargs)
        uic.loadUi('./assets/ui/shortcut_or_history.ui', self)
        self.update_btn.clicked.connect(self._update_shortcut)
        self.ok_btn.clicked.connect(self.close)
        self.end_btn.clicked.connect(self.close)
        self.shortcut_area_widget: QWidget
        self.shortcut_list = []

        self._update_shortcut()

    def _update_shortcut(self):
        """ 根据yaml更新 """
        for w in self.shortcut_list:
            self.shortcut_area_widget.layout().removeWidget(w)
            del w
        self.shortcut_list = []
        shortcuts = self.console.data['shortcut']
        if shortcuts is None:
            return
        for sc in reversed(shortcuts):
            newsc = ShortcutUnit(self.mw, sc['title'], sc['alias'], sc['define'], shortcuts.index(sc), self)
            self.shortcut_area_widget.layout().insertWidget(1, newsc)
            self.shortcut_list.append(newsc)


class ParamUnit(QWidget):
    """ 参数列表单元

    每行分别代表各自的参数信息，其从左到右依次是 标题,化名,数值,写入 四个列。可以通过更改数值然后点击‘写入’按钮进行更改实际值"""

    def __init__(self, console: Console, id_: int, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        uic.loadUi('./assets/ui/param_unit.ui', self)
        self.console = console
        self.id = id_
        self.parent_: MainWindow = parent  # 直接引用
        self.param = self.console.data['parameter', 'infos', id_]
        self.label.setText(self.param['title'])
        self.label_2.setText(self.param['alias'])
        self.lineEdit: QLineEdit
        values = self.console.data['parameter', 'values', self.console.group_index, 'details', id_]
        self.lineEdit.setText(str(values))
        self.pushButton.clicked.connect(self._write)
        
    @property
    def order(self) -> str | None:
        try:
            v = float(self.lineEdit.text())
        except:
            self.parent_.subBubbleFrame.add_message(
                type_='warn', title='数值类型不合规', info=f'{self.param["alias"]}的值({v})类型错误')
            return None
        return f'[0:{self.id},{v}]'

    def _write(self):
        """ 按钮的事件 """
        try:
            v = float(self.lineEdit.text())
            order, e = self.console.make_param_order(self.param["alias"],v)  # 发送指令并获取发送的指令的详细文本信息
        except Exception as e:
            pass
        
        if e is None:
            # self.parent_.subBubbleFrame.add_message(
            #     title='发送调参信息', info=f'{self.param["title"]} {self.param["alias"]}={v}\n{order}')
            self.parent_.subBubbleFrame.add_message(
                 title='发送调参信息', info=f'{order}')
            self.parent_.append_send_recv_info(f'设置{order}', 'tips')
            self.parent_.append_send_recv_info_signal.emit(order, 'send')
        elif isinstance(e, serial.PortNotOpenError):
            self.parent_.subBubbleFrame.add_message(type_='warn', title='串口未打开')
            self.parent_.append_send_recv_info(f'"<< {order}" 发送无效', 'tips')
        self.parent_.reload_from_yaml()  # 刷新


class SerialInfoHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlight_rules = []

        quotation_format = QTextCharFormat()
        quotation_format.setForeground(QColor(231, 0, 0))  # send
        pattern = QRegularExpression(r'^<<.*')
        self.highlight_rules.append((pattern, quotation_format))

        # quotation_format = QTextCharFormat()
        # quotation_format.setForeground(QColor(0, 200, 0))  # recv
        # pattern = QRegularExpression(r'^>>.*')
        # self.highlight_rules.append((pattern, quotation_format))

        quotation_format = QTextCharFormat()
        quotation_format.setForeground(QColor(128, 128, 128))  # tips
        pattern = QRegularExpression(r'^#.*')
        self.highlight_rules.append((pattern, quotation_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlight_rules:
            expression = QRegularExpression(pattern)
            matched = expression.match(text)
            self.setFormat(matched.capturedStart(0), matched.capturedLength(), format)


class MainWindow(QMainWindow):
    """ 主窗口(前端)，只进行显示和调用后端接口 

    需要传入对应的`Console`对象供以调用后端数据"""

    append_send_recv_info_signal = pyqtSignal(str, str)

    def __init__(self, console: Console, *args, **kwargs):
        """ ## Parameter
        `console`后端控制台，所有后端接口从这里调用"""
        super().__init__(*args, **kwargs)
        uic.loadUi(MAIN_UI, self)
        self.setWindowIcon(QIcon(MAIN_ICO))
        self.setWindowTitle('功能调参窗口 - v2')
        self.console = console
        self.data_path = pathlib.Path('./data')  # 配置文件存储路径
        self.project_btns = []  # 存放对应按键的引用

        # <sub window> 创建子窗口
        self.subBubbleFrame = MessageBubbleFrame(self)
        self.action_msg.triggered.connect(self.subBubbleFrame.add_message)
        self.settingWindow = SettingWindow(self.console, self)
        self.action_6.triggered.connect(self.settingWindow.exec)

        self.shortcut_window = ShortcutAndHistory(self.console, self)
        self.code_preview = CodeWindow('QDialog', self.console, self)
        self.code_widget = CodeWindow('QWidget', self.console, self)
        self.code_widget.pushButton_2.setEnabled(False)
        self.code_frame.layout().addWidget(self.code_widget)

        # <define> 定义控件和属性
        self.scroll_project_browsing: QWidget
        self.treeView: QTreeView
        self.yaml_histories_menu: QMenu
        self.param_adjust_stackArea: QStackedWidget = self.stackedWidget
        # list
        self.param_adjust_srocllWidget: QWidget = self.scrollAreaWidgetContents
        self.param_adjust_list = []
        # wheel
        self.param_adjust_wheel = Turntable(self, n_items=9)
        self.groupBox_5.layout().addWidget(self.param_adjust_wheel)
        # tree
        self._tree_model = QStandardItemModel()  # 创建 QStandardItemModel 对象
        self.treeView.setModel(self._tree_model)  # 将模型设置为 QTreeView 的数据源

        self.serial_textBrowser: QTextBrowser
        # 高亮显示
        self.hlter = SerialInfoHighlighter(self.serial_textBrowser.document())
        self._last_serial_type = None
        self.hlter_text = ''
        self.append_send_recv_info('注释', 'tips')
        self.append_send_recv_info('发送', 'send')
        self.append_send_recv_info('接收1', 'recv')
        self.append_send_recv_info('接收2', 'recv')

        # 串口设置
        self._serial_init()

        # <connect> 绑定事件
        self.action_1.triggered.connect(partial(self.param_adjust_stackArea.setCurrentIndex, 0))  # 切换为轮盘模式
        self.action_14.triggered.connect(partial(self.param_adjust_stackArea.setCurrentIndex, 1))  # 切换为列表模式
        self.action_C.triggered.connect(self.code_preview.exec)  # 生成C代码预览
        self.action_N.triggered.connect(self.make_new_file)  # 创建新文件
        self.pushButton.clicked.connect(self.make_new_file)  # 创建新文件
        self.pushButton_8.clicked.connect(self.reload_from_yaml)
        self.pushButton_17.clicked.connect(self.shortcut_window.exec)  # 调用快捷指令的模态窗口
        self.pushButton_20.clicked.connect(self.shortcut_window.exec)
        self.append_send_recv_info_signal.connect(self.append_send_recv_info)

        # <initial> 其他初始化
        # 设置定时器，自动刷新后端数据，刷线显示信息
        self._reload_timer = QTimer(self)
        self._reload_timer.timeout.connect(self.reload_from_yaml)
        # self._reload_timer.start(10000)  # 每隔1000ms刷新
        self.reload_from_yaml()

        # 接收串口信息
        self._reader = QTimer(self)

        def _read_serial():
            if not self.console.serial.is_open:
                return
            bytes = self.console.serial.read_all()
            if bytes:
                text = bytes.decode(self.console.dct['read encoding'])
                self.append_send_recv_info(text, 'recv')
        self._reader.timeout.connect(_read_serial)
        self._reader.start(100)  # 100ms读取一次

        # disable
        self.comboBox_8.setEnabled(False)
        self.comboBox_9.setEnabled(False)
        self.comboBox_10.setEnabled(False)
        self.checkBox.setEnabled(False)
        self.checkBox_2.setEnabled(False)
        self.checkBox_3.setEnabled(False)
        self.checkBox_4.setEnabled(False)
        self.checkBox_5.setEnabled(False)
        self.pushButton_14.setEnabled(False)
        self.pushButton_15.setEnabled(False)

    def _serial_init(self):
        """  """
        self.ser_port: QComboBox  # 串口号下拉框

        def _wrap(this: QComboBox):
            """ 修饰后，展开自动检测可用值 """
            this.clear()
            ports = serial.tools.list_ports.comports()
            if ports:
                for port in ports:
                    this.addItem(port.name)
            QComboBox.showPopup(this)
        self.ser_port.showPopup = partial(_wrap, self.ser_port)

        self.baudrate_menu = QMenu(self)
        self.ser_baud: QLineEdit
        for b in BAUDRATES:
            action = QAction(str(b), self)
            action.triggered.connect(partial(self.ser_baud.setText, str(b)))
            self.baudrate_menu.addAction(action)

        def show_menu():
            x = QCursor.pos().x()
            y = QCursor.pos().y()
            self.baudrate_menu.move(x, y)
            self.baudrate_menu.exec()

        self.pushButton_12.clicked.connect(show_menu)  # 波特率右键预选

        self.ser_wrtie_encoding: QComboBox
        self.ser_read_encoding: QComboBox

        self.ser_port.activated.connect(self._update_serial_config)
        self.ser_baud.textChanged.connect(self._update_serial_config)
        self.ser_wrtie_encoding.activated.connect(self._update_serial_config)
        self.ser_read_encoding.activated.connect(self._update_serial_config)

        #
        self.open_serial: QPushButton
        self.open_serial.clicked.connect(self.open_close_serial)
        self.btn_default_style = self.open_serial.styleSheet()

        self.send_textEdit: QTextEdit
        self.send_btn.clicked.connect(self._send_from_sendingTextEdit)

        self._update_serial_config()

    def _send_from_sendingTextEdit(self):
        order = self.send_textEdit.toPlainText()
        if order == '':
            return
        o, e = self.console.make_normal_order(order)
        if e is None:
            self.subBubbleFrame.add_message(
                title='发送串口信息', info=order)
            self.append_send_recv_info('普通信息', 'tips')
            self.append_send_recv_info_signal.emit(order, 'send')
            self.send_textEdit.setText('')  # 发送成功后清空发送文本框
        elif isinstance(e, serial.PortNotOpenError):
            self.subBubbleFrame.add_message(type_='warn', title='串口未打开')
            self.append_send_recv_info(f'"<< {o}" 发送无效', 'tips')

    def open_close_serial(self):
        """ 开启或者关闭串口 """
        if self.console.serial.is_open:  # open -> close
            self.console.serial.close()
            self.open_serial.setText('启用串口')
            self.open_serial.setStyleSheet(self.btn_default_style)
            self.subBubbleFrame.add_message(title='串口已关闭')
        else:  # close -> open
            try:
                self.console.serial.open()
                self.open_serial.setText('关闭串口')
                self.open_serial.setStyleSheet("background-color: #1dd46c;")
                self.subBubbleFrame.add_message(title='串口已打开')
            except serial.serialutil.SerialException as e:
                print(e.args)
                self.subBubbleFrame.add_message(type_='warn', title='串口开启失败', info=e.args[0])

    def _update_serial_config(self):
        """ 更改串口配置后触发，同步更新console配置 """
        self.console.set_serial({
            'port': self.ser_port.currentText(),
            'baudrate': int(self.ser_baud.text()),
            #
            'write encoding': self.ser_wrtie_encoding.currentText(),
            'read encoding': self.ser_read_encoding.currentText()
        })

    def append_send_recv_info(self, info: str, type_: Literal['send', 'recv', 'tips']):  # SerialInfoType):
        """ 显示收发信息 """
        match type_:
            case 'send':
                prefix = '\n<< '
            case 'recv':
                if type_ == self._last_serial_type:
                    prefix = ''
                else:
                    prefix = '\n>> '
            case 'tips':
                prefix = '\n# '
            case _:
                raise ValueError()
        if self._last_serial_type is None:
            prefix = prefix.lstrip()
        self.hlter_text += f'{prefix}{info}'
        self.serial_textBrowser.setText(self.hlter_text)

        self._last_serial_type = type_

    def reload_from_yaml(self, yaml_path: str | pathlib.Path = None):
        """ 重新加载相关数据，刷新显示的数据信息 """
        if yaml_path:
            if os.path.isfile(yaml_path):
                self.console.load(yaml_path if isinstance(yaml_path, str) else yaml_path.absolute())
            else:
                print(f'[警告]文件{yaml_path}不存在')
        # 更新[项目浏览]按钮
        layout = self.scroll_project_browsing.layout()
        for btn in self.project_btns:
            layout.removeWidget(btn)
            del btn
        self.project_btns = []
        for fn in [fn for fn in os.listdir(self.data_path) if fn.split('.')[-1] == 'yaml']:
            btn = QPushButton(self)
            btn.clicked.connect(partial(self.reload_from_yaml, self.data_path / fn))
            btn.setIcon(QIcon('./assets/ico/v.png'))
            btn.setProperty('is_project_btn', True)
            btn.setText(fn)
            # 高亮当前文件
            if (self.data_path / fn).samefile(self.console.current_loading):
                btn.setStyleSheet('''*{
                    color: green;
                    font-weight: bold;
                    text-align: left;
                }''')
            self.project_btns.append(btn)
            layout.insertWidget(0, btn)

        # 更新[查看大纲]树
        # 创建根节点
        root_item = self._tree_model.invisibleRootItem()
        # 删除旧节点
        for row in range(root_item.rowCount()):
            root_item.removeRow(0)
        # 添加子节点
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        for value in self.console.data['parameter', 'values']:
            value_item = QStandardItem(value['title'])
            root_item.appendRow(value_item)
            for info, v in zip(self.console.data['parameter', 'infos'], value['details']):
                v_item = QStandardItem(f'{info["alias"]}\t{v}')
                v_item.setFont(font)
                value_item.appendRow(v_item)
        self.treeView.expandAll()
        self.subBubbleFrame.add_message(type_='debug', title='更新数据显示', info=str(self.console.yaml_path))

        # 更新使用的yaml历史
        for action in self.yaml_histories_menu.actions():
            self.yaml_histories_menu.removeAction(action)
        for yaml_path in self.console.loading_histories[::-1]:
            action = QAction(self)
            action.setText(yaml_path)
            action.triggered.connect(partial(self.reload_from_yaml, yaml_path))
            self.yaml_histories_menu.addAction(action)

        # <更新参数列表>
        # 删除旧的字段
        for w in self.param_adjust_list:
            self.param_adjust_srocllWidget.layout().removeWidget(w)
            del w
        self.param_adjust_list = []
        # 增加新的字段
        for i in reversed(range(len(self.console.data['parameter', 'infos']))):
            w = ParamUnit(self.console, i, self)
            self.param_adjust_list.append(w)
            self.param_adjust_srocllWidget.layout().insertWidget(1, w)

        # TODO 更新参数轮盘

        self.code_widget.Update_Coding()  # 更新代码显示

    def make_new_file(self):
        """ 新建文件 """
        folder = pathlib.Path('./data')
        file = folder / f'new.yaml'
        i = 0
        while file.is_file():
            i += 1
            file = folder / f'new_{i}.yaml'
        shutil.copyfile("./assets/docs/empty.yaml", file)
        self.subBubbleFrame.add_message(title='新建文件', info=f'{file}')
        print(f'新文件在{file}')

# class MainWindow(QMainWindow):

#     def __init__(self, config: Config, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         uic.loadUi(MAIN_UI, self)
#         self.setWindowIcon(QIcon(MAIN_ICO))
#         self.config = config
#         # 更新轮盘的值
#         self.parameters = config.parameters
#         assert isinstance(self.parameters, dict)
#         #
#         self.turntable_frame: QFrame
#         layout = QVBoxLayout()
#         texts = [f'{k} {v}' for k, v in self.parameters.items()]
#         self.turntable = Turntable(texts)
#         layout.addWidget(self.turntable)
#         self.turntable_frame.setLayout(layout)
#         self.turntable.signal.connect(self.Turntable_Driving)

#         # 更新列表的值
#         self.form_anchors: QComboBox = self.combobox
#         self.form_anchors.addItems(self.parameters.keys())
#         self.form_anchors.currentIndexChanged.connect(self.Turntable_Follow)
#         # 绑定修改参数的行编辑器的事件
#         self.anchor_editor: QLineEdit = self.lineEdit_2
#         self.anchor_editor_button: QPushButton = self.pushButton_3
#         self.anchor_editor.returnPressed.connect(self.Modify_Enter)
#         self.anchor_editor_button.clicked.connect(self.Modify_Enter)

#         self.message_browser: QTextBrowser = self.textBrowser
#         self.preview_label: QLabel

#         # 顶部菜单
#         self.pin_action: QAction = self.action_13
#         self.unpin_action: QAction = self.action_14
#         # self.unpin_action.triggered.connect(self.Unpin_Window)
#         # self.action_13.triggered.connect(self.Pin_Window)
#         # print(bin(int(self.windowFlags())), bin(Qt.WindowStaysOnTopHint))
#         # print(bin(int(self.windowFlags() & ~Qt.WindowStaysOnTopHint)))
#         self.action.triggered.connect(self.Open_Config)
#         self.action_11.triggered.connect(self.SaveAs_Config)
#         self.action_12.triggered.connect(self.close)
#         self.action_5.triggered.connect(self.Help_Usage)
#         self.action_4.triggered.connect(self.Help_About)

#         # init
#         self.Turntable_Driving(self.turntable.anchor)
#         #self.Pin_Window()  # 默认置顶窗口

#     @property
#     def order_string(self) -> str:
#         k = self.form_anchors.currentText()
#         v = self.anchor_editor.text()
#         head = self.config.settings['send']['frame head']
#         tail = self.config.settings['send']['frame tail']
#         return f"{head}{k},{v}{tail}"

#     def nohtml(self, text: str):
#         for s, t in (
#             ('<', '&lt;'),
#             ('>', '&gt;')
#         ):
#             text = text.replace(s, t)
#         return text

#     def Turntable_Driving(self, anchor: int):
#         """ 列表跟随轮盘转动而改变 """
#         self.form_anchors.setCurrentIndex(anchor)
#         self.anchor_editor.setText(str(self.parameters[self.form_anchors.currentText()]))
#         self.preview_label.setText(self.nohtml(self.order_string))

#     def Turntable_Follow(self, anchor: int):
#         self.turntable.moveItem(anchor)
#         self.anchor_editor.setText(str(self.parameters[self.form_anchors.currentText()]))
#         self.preview_label.setText(self.nohtml(self.order_string))

#     def Modify_Enter(self):
#         k = self.form_anchors.currentText()
#         v = eval(self.anchor_editor.text())
#         self.parameters[k] = v
#         self.turntable.names[self.turntable.anchor] = f'{k} {v}'
#         self.turntable.moveItem()
#         order = self.order_string
#         self.preview_label.setText(f'{self.nohtml(order)}')
#         self.message_browser.append(f'<p style="color: blue;">[send]:{self.nohtml(order)}</p>')  # pink#ff557f
#         print(order)

#     def Pin_Window(self):
#         # 设置窗口置顶标志
#         self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

#     def Unpin_Window(self):
#         # 关闭窗口置顶标志
#         self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)

#     def Update_Settings(self):
#         self.preview_label.setText(self.nohtml(self.order_string))

#     def Open_Config(self):
#         f, _ = QFileDialog.getOpenFileName(self, '选择配置文件', './', 'Yaml (*.yaml *.yml)')
#         if f:
#             self.config.load(f)

#     # def Save_Config(self):
#     #     self.config.dump(f)

#     def SaveAs_Config(self):
#         f, _ = QFileDialog.getSaveFileName(self, '将配置另存为', './', 'Yaml (*.yaml *.yml)')
#         if f:
#             self.config.dump(f)

#     def Help_Usage(self):
#         about = """版本: 1.85.2 (user setup)
# 提交: 8b3775030ed1a69b13e4f4c628c612102e30a681
# 日期: 2024-01-18T06:40:10.514Z
# Electron: 25.9.7
# ElectronBuildId: 26354273
# Chromium: 114.0.5735.289
# Node.js: 18.15.0
# V8: 11.4.183.29-electron.0
# OS: Windows_NT x64 10.0.19045"""
#         QMessageBox.information(self,'关于 VS Code',about,QMessageBox.StandardButton.Yes)

#     def Help_About(self):
#         about = """版本: 1.85.2 (user setup)
# 提交: 8b3775030ed1a69b13e4f4c628c612102e30a681
# 日期: 2024-01-18T06:40:10.514Z
# Electron: 25.9.7
# ElectronBuildId: 26354273
# Chromium: 114.0.5735.289
# Node.js: 18.15.0
# V8: 11.4.183.29-electron.0
# OS: Windows_NT x64 10.0.19045"""
#         QMessageBox.information(self,'关于 VS Code',about,QMessageBox.StandardButton.Yes)


# if __name__ == '__main__':
#     import rich.traceback
#     import sys
#     import string
#     rich.traceback.install()
#     app = QApplication(sys.argv)
#     win = MainWindow()
#     win.setWindowTitle('参数轮盘')
#     win.show()
#     app.exec()
#     sys.exit()
