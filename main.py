""" 
zyf.console 提供数据交互 - 后端
zyf.window 提供可视界面 - 前端
"""

import os
import sys
import pathlib
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from zyf.window.main_window import MainWindow
from zyf.console import Console,Config


if __name__ == '__main__':
    root_path = pathlib.Path('./')
    with open(root_path/'start.bat','w',encoding='gbk') as f:
        f.write(f'{sys.executable} {(root_path/"main.py").absolute()} #非首次启动')
    app = QApplication(sys.argv)
    console = Console()
    console.load_from_history(-1,from_path=True) # 默认打开上次的文件
    win = MainWindow(console)
    win.show()
    app.exec()
    sys.exit()
