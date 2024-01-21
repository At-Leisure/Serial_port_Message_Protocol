from zyf.window.turntable import Turntable
from zyf.assist.config_struct import Config
import yaml
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic

MAIN_UI = './assets/ui/serial.ui'
MAIN_ICO = './assets/ico/v3.png'

class MainWindow(QMainWindow):

    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(MAIN_UI, self)
        self.setWindowIcon(QIcon(MAIN_ICO))
        self.config = config
        # 更新轮盘的值
        self.parameters = config.parameters
        assert isinstance(self.parameters, dict)
        #
        self.turntable_frame: QFrame
        layout = QVBoxLayout()
        texts = [f'{k} {v}' for k, v in self.parameters.items()]
        self.turntable = Turntable(texts)
        layout.addWidget(self.turntable)
        self.turntable_frame.setLayout(layout)
        self.turntable.signal.connect(self.Turntable_Driving)

        # 更新列表的值
        self.form_anchors: QComboBox = self.combobox
        self.form_anchors.addItems(self.parameters.keys())
        self.form_anchors.currentIndexChanged.connect(self.Turntable_Follow)
        # 绑定修改参数的行编辑器的事件
        self.anchor_editor: QLineEdit = self.lineEdit_2
        self.anchor_editor_button: QPushButton = self.pushButton_3
        self.anchor_editor.returnPressed.connect(self.Modify_Enter)
        self.anchor_editor_button.clicked.connect(self.Modify_Enter)

        self.message_browser: QTextBrowser = self.textBrowser
        self.preview_label: QLabel

        # 顶部菜单
        self.pin_action: QAction = self.action_13
        self.unpin_action: QAction = self.action_14
        # self.unpin_action.triggered.connect(self.Unpin_Window)
        # self.action_13.triggered.connect(self.Pin_Window)
        # print(bin(int(self.windowFlags())), bin(Qt.WindowStaysOnTopHint))
        # print(bin(int(self.windowFlags() & ~Qt.WindowStaysOnTopHint)))
        self.action.triggered.connect(self.Open_Config)
        self.action_11.triggered.connect(self.SaveAs_Config)
        self.action_12.triggered.connect(self.close)
        self.action_5.triggered.connect(self.Help_Usage)
        self.action_4.triggered.connect(self.Help_About)

        # init
        self.Turntable_Driving(self.turntable.anchor)
        #self.Pin_Window()  # 默认置顶窗口

    @property
    def order_string(self) -> str:
        k = self.form_anchors.currentText()
        v = self.anchor_editor.text()
        head = self.config.settings['send']['frame head']
        tail = self.config.settings['send']['frame tail']
        return f"{head}{k},{v}{tail}"

    def nohtml(self, text: str):
        for s, t in (
            ('<', '&lt;'),
            ('>', '&gt;')
        ):
            text = text.replace(s, t)
        return text

    def Turntable_Driving(self, anchor: int):
        """ 列表跟随轮盘转动而改变 """
        self.form_anchors.setCurrentIndex(anchor)
        self.anchor_editor.setText(str(self.parameters[self.form_anchors.currentText()]))
        self.preview_label.setText(self.nohtml(self.order_string))

    def Turntable_Follow(self, anchor: int):
        self.turntable.moveItem(anchor)
        self.anchor_editor.setText(str(self.parameters[self.form_anchors.currentText()]))
        self.preview_label.setText(self.nohtml(self.order_string))

    def Modify_Enter(self):
        k = self.form_anchors.currentText()
        v = eval(self.anchor_editor.text())
        self.parameters[k] = v
        self.turntable.names[self.turntable.anchor] = f'{k} {v}'
        self.turntable.moveItem()
        order = self.order_string
        self.preview_label.setText(f'{self.nohtml(order)}')
        self.message_browser.append(f'<p style="color: blue;">[send]:{self.nohtml(order)}</p>')  # pink#ff557f
        print(order)

    def Pin_Window(self):
        # 设置窗口置顶标志
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def Unpin_Window(self):
        # 关闭窗口置顶标志
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)

    def Update_Settings(self):
        self.preview_label.setText(self.nohtml(self.order_string))

    def Open_Config(self):
        f, _ = QFileDialog.getOpenFileName(self, '选择配置文件', './', 'Yaml (*.yaml *.yml)')
        if f:
            self.config.load(f)

    # def Save_Config(self):
    #     self.config.dump(f)

    def SaveAs_Config(self):
        f, _ = QFileDialog.getSaveFileName(self, '将配置另存为', './', 'Yaml (*.yaml *.yml)')
        if f:
            self.config.dump(f)
            
    def Help_Usage(self):        
        about = """版本: 1.85.2 (user setup)
提交: 8b3775030ed1a69b13e4f4c628c612102e30a681
日期: 2024-01-18T06:40:10.514Z
Electron: 25.9.7
ElectronBuildId: 26354273
Chromium: 114.0.5735.289
Node.js: 18.15.0
V8: 11.4.183.29-electron.0
OS: Windows_NT x64 10.0.19045"""
        QMessageBox.information(self,'关于 VS Code',about,QMessageBox.Yes)
            
    def Help_About(self):
        about = """版本: 1.85.2 (user setup)
提交: 8b3775030ed1a69b13e4f4c628c612102e30a681
日期: 2024-01-18T06:40:10.514Z
Electron: 25.9.7
ElectronBuildId: 26354273
Chromium: 114.0.5735.289
Node.js: 18.15.0
V8: 11.4.183.29-electron.0
OS: Windows_NT x64 10.0.19045"""
        QMessageBox.information(self,'关于 VS Code',about,QMessageBox.Yes)



if __name__ == '__main__':
    import rich.traceback
    import sys
    import string
    rich.traceback.install()
    app = QApplication(sys.argv)
    win = MainWindow(Config('config.yaml'))
    win.setWindowTitle('参数轮盘')
    win.show()
    app.exec()
    sys.exit()
