import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from zyf.window.main_window import MainWindow
from zyf.window.setting_window import SettingWindow
from zyf.window.newconfig import NewconfigWindow
from zyf.assist.config_struct import Config
from zyf.window.code_preview import CodeWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = Config('./config/template.yaml')
    win = MainWindow(config)
    setwin = SettingWindow(config, win)
    codewin = CodeWindow(config, win)
    filewin = NewconfigWindow(win)

    win.action_2.triggered.connect(filewin.exec)  # 模态窗口win.exec()，非模态窗口win.show()
    win.action_3.triggered.connect(setwin.exec)
    win.action_8.triggered.connect(codewin.exec)
    win.action_6.triggered.connect(config.show)
    win.pushButton_4.clicked.connect(setwin.exec)
    setwin.apply_signal.connect(win.Update_Settings)
    win.show()
    app.exec()
    sys.exit()
