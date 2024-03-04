import sys
import datetime
from functools import partial, wraps
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic
from typing import Literal
from PyQt6.QtWidgets import QWidget
from rich import traceback


CHAT_WID = 200
CHAR_N = '\n'

IconTypes = Literal['info', 'warn', 'error', 'debug']
bubble_icons = {
    'info': './assets/ico/info.png',
    'warn': './assets/ico/warn.png',
    'error': './assets/ico/error.png',
    'debug': './assets/ico/debug.png'
}


class BasicBubble(QWidget):
    clicked = pyqtSignal()  # 绑定点击事件

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi('./assets/ui/chat-unit.ui', self)
        self.setMaximumWidth(CHAT_WID)
        self.setMinimumWidth(CHAT_WID)
        self.title_label: QLabel = self.label_2
        self.info_label: QLabel = self.label_3
        self.date_label: QLabel = self.label_4
        self.img_label: QLabel
        self.set_message()  # 设置默认消息

    def set_image(self, img: QPixmap):
        """ 设置图标 """
        self.img_label.setPixmap(img)

    def set_message(self, *, title: str = None, info: str = None, date: str = None):
        """ 设置标题和详情 """
        title = title if title else "Message 通知"
        info = info if info else "Information\n信息提示"
        now = datetime.datetime.now()
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        date = date if date else f'周{weekdays[now.weekday()]}  {now.strftime("%Y-%m-%d  %H:%M:%S")}'
        # date = date if date else f'{now.strftime("%Y-%m-%d  %H:%M:%S")}'
        self.title_label.setText(title)
        self.info_label.setText(info.replace(CHAR_N, "<br>"))
        self.date_label.setText(date)

    def mousePressEvent(self, event):
        """ 绑定点击事件 """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()  # 发送clicked信号

    @property
    def info(self) -> str:
        return f'ChatUnit{{title:"{self.title_label.text()}", info:"{self.info_label.text()}", date:"{self.date_label.text()}"}}'


class MessageBubbleUnit(BasicBubble):
    reduce_count = 0

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        MessageBubbleUnit.reduce_count += 1  # 记录是第几个生成的消息
        self.count_n = MessageBubbleUnit.reduce_count


class MessageBubbleFrame(QWidget):
    pop_signal = pyqtSignal(int)

    def __init__(self, parent: QWidget = None, *, debug=False) -> None:
        super().__init__(parent)
        self.is_debug = debug
        uic.loadUi('./assets/ui/chat-frame.ui', self)
        self.scrollWidget: QWidget = self.chat_widget
        self.addBtn: QPushButton = self.pushButton
        self.subBtn: QPushButton = self.pushButton_2
        self.BtnFrame: QFrame = self.BtnFrame
        self.setMaximumWidth(CHAT_WID)
        self.setMinimumWidth(CHAT_WID)

        self.chat_list = []

        # self.setWindowOpacity(0.5)
        # self.scrollArea.setWindowOpacity(0.5)
        # self.scrollWidget.setWindowOpacity(0.5)

        self.pop_signal.connect(self.rm_unit)

        if not debug:
            self.BtnFrame.setVisible(False)
        else:
            self.BtnFrame.setVisible(True)
            self.addBtn.clicked.connect(partial(self._add_unit, None))
            self.subBtn.clicked.connect(partial(self.rm_unit, None))

        # 修饰parent的resize事件
        if self.parent():
            parent.resizeEvent = self._follow_resize(parent.resizeEvent)

    def _follow_resize(self, parent_resizeEvent):
        """ 函数修饰器：跟随parent的resize事件 """
        @wraps(parent_resizeEvent)
        def f2(*args, **kwargs):
            parent_resizeEvent(*args, **kwargs)
            self.move(self.parent().width() - self.width(), 0)
        return f2

    def _add_unit(self, unit: MessageBubbleUnit | None = None):
        if unit is None:
            unit = MessageBubbleUnit()
        layout = self.scrollWidget.layout()
        # print(unit.info)
        self.chat_list.append(unit)
        layout.insertWidget(0, unit)
        self.fit_resize()

        timer = QTimer(self)
        timer.timeout.connect(partial(self.pop_signal.emit, unit.count_n))
        unit.clicked.connect(partial(self.pop_signal.emit, unit.count_n))
        timer.start(5000)

    def add_message(self, *, type_: IconTypes = 'info', title: str = None, info: str = None, just_title=False):
        """ 添加新的通知气泡 

        ## Parameter
        - `type_`信息的性质，共四类['info', 'warn', 'error', 'debug']
        - `title`信息的标题
        - `info`信息的内容
        - `just_title`仅显示标题不显示详情"""
        icon = QPixmap(bubble_icons[type_])
        unit = MessageBubbleUnit(self)
        unit.set_image(icon)
        unit.set_message(title=title, info=info)
        if info is None:
            unit.info_label.setVisible(False)
        self._add_unit(unit)

    def rm_unit(self, count_n: int = None):
        nn = [unit.count_n for unit in self.chat_list]
        if count_n is None:
            index = 0
        elif count_n in nn:
            index = nn.index(count_n)
        else:
            return  # 如果目标已经删除，就不再进行重复删除
        if len(self.chat_list) > 0:
            self.scrollWidget.layout().removeWidget(self.chat_list[index])
            self.chat_list.pop(index)
            # print(f'remove {count_n}')
            self.fit_resize()

    def fit_resize(self):
        # resize
        hei = sum(unit.height() for unit in self.chat_list)
        if self.is_debug:
            hei += 100
        # print(hei)
        wid = self.scrollWidget.width()
        # self.resize(wid,hei)
        self.setMinimumHeight(hei)
        self.setMaximumHeight(hei)
