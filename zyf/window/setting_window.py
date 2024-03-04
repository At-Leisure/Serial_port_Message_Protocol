import os
import attr
import yaml
import pathlib
from icecream import ic
from functools import partial
from zyf.window.turntable import Turntable
from zyf.console import Console
from zyf.window.bubble import MessageBubbleFrame, MessageBubbleUnit
from zyf.window.code_preview import CodeWindow
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6 import uic


class ParamUnit(QWidget):

    def __init__(self, console: Console, parent=None, *args, **kwargs):
        self.console = console
        super().__init__(parent, *args, **kwargs)
        uic.loadUi('./assets/ui/setting_param.ui', self)
        self.title: QLineEdit
        self.alias: QLineEdit
        self.extern_: QLineEdit
        self.define: QLineEdit
        self.description: QLineEdit


class SettingWindow(QDialog):

    def __init__(self, console: Console, parent=None, *args, **kwargs):
        self.console = console
        self.parent_bubble: MessageBubbleFrame = parent.subBubbleFrame  # 用于提示错误信息
        super().__init__(parent, *args, **kwargs)
        uic.loadUi('./assets/ui/setting.ui', self)
        self.setWindowTitle('设置窗口')
        self.paramInfoList = []  # 子控件的引用，方便调用
        self.paramValueList = []

        self.fileTitleEditor: QLineEdit
        self.fileNameEditor: QLineEdit
        self.fileDescriptionEditor: QLineEdit

        self.initCodeEditor: QLineEdit
        self.initHeaderEditor: QLineEdit

        self.paramInfo_toolBox: QToolBox
        self.paramValue_toolBox: QToolBox

        self.update_pushButton: QPushButton
        self.paramCreation: QPushButton
        self.paramDeletion: QPushButton
        self.ok_pushButton: QPushButton

        self.update_pushButton.clicked.connect(self.update_Information)
        self.paramCreation.clicked.connect(partial(self._add_param,
                                                   title='title',
                                                   alias='alias',
                                                   define='define',
                                                   extern='extern',
                                                   description='description'))
        self.paramDeletion.clicked.connect(self._del_param)
        self.ok_pushButton.clicked.connect(self.close)
        self.update_Information()

    def _add_param(self, title, alias, define, extern, description):
        new = ParamUnit(self.console, self.parent())
        new.title.setText(title)
        new.alias.setText(alias)
        new.define.setText(define)
        new.extern_.setText(extern)
        new.description.setText(description)
        self.paramInfoList.append(new)
        self.paramInfo_toolBox.addItem(new, f'{len(self.paramInfoList)}.{title}：{alias}')
        # 设置toolbox的高度，以便让页面完全显示而不用折叠
        hei = len(self.paramInfoList)*30 + self.paramInfoList[0].height()
        self.paramInfo_toolBox.setMinimumHeight(hei)

    def _del_param(self):
        i = self.paramInfo_toolBox.currentIndex()
        

    def update_Information(self):
        """ 根据文件刷新显示 """
        self.fileNameEditor.setText(self.console.current_loading)
        self.fileTitleEditor.setText(self.console.data['file info', 'title'])
        self.fileDescriptionEditor.setText(self.console.data['file info', 'description'])
        self.initHeaderEditor.setText(', '.join(self.console.data['initial', 'includes']))
        self.initCodeEditor.setText(self.console.data['initial', 'coding'])
        self.parent_bubble.add_message(title='在设置中更新显示信息', just_title=True)

        # 删除toolbox的空白页
        for i in range(self.paramInfo_toolBox.count()):
            self.paramInfo_toolBox.removeItem(0)
        # 重置索引
        self.paramInfoList = []
        # 添加更新的页面
        for i in range(self.console.data.n_param_group):
            self._add_param(
                title=self.console.data['parameter', 'infos', i, 'title'],
                alias=self.console.data['parameter', 'infos', i, 'alias'],
                define=self.console.data['parameter', 'infos', i, 'define'],
                extern=self.console.data['parameter', 'infos', i, 'extern'],
                description=self.console.data['parameter', 'infos', i, 'description'])

        for i in range(self.paramValue_toolBox.count()):
            self.paramValue_toolBox.removeItem(0)
        self.paramValueList = []
        for i in range(self.console.data.n_value_group):
            ...
    # def exec(self):
    #     """ 刷新后，开启模态窗口 """

    #     # values
    #     #n_group = self.console.data['parameter', 'values']

    #     super().exec()
