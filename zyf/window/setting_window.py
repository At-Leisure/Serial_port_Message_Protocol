from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import string
import yaml
from zyf.assist.config_struct import Config

SETTING_UI = './assets/ui/setting.ui'

class SettingWindow(QDialog):
    apply_signal = pyqtSignal()

    def __init__(self, config: Config, parent=None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.config = config
        uic.loadUi(SETTING_UI, self)
        self.setWindowTitle('设置收发配饰')
        self.send_head_Edit: QLineEdit = self.lineEdit
        self.send_tail_Edit: QLineEdit = self.lineEdit_2
        self.recv_head_Edit: QLineEdit = self.lineEdit_3
        self.recv_tail_Edit: QLineEdit = self.lineEdit_4

        self.send_head_Edit.setText(config.settings['send']['frame head'])
        self.send_tail_Edit.setText(config.settings['send']['frame tail'])
        self.recv_head_Edit.setText(config.settings['recv']['frame head'])
        self.recv_tail_Edit.setText(config.settings['recv']['frame tail'])

        self.apply: QPushButton
        self.confirm: QPushButton
        self.cancel: QPushButton

        self.apply.clicked.connect(self.Press_Apply)
        self.confirm.clicked.connect(self.Press_Confirm)
        self.cancel.clicked.connect(self.close)

    @property
    def params(self) -> dict:
        return {
            'send': {
                'frame head': self.send_head_Edit.text(),
                'frame tail': self.send_tail_Edit.text(),
            },
            'recv': {
                'frame head': self.recv_head_Edit.text(),
                'frame tail': self.recv_tail_Edit.text(),
            }
        }

    def Press_Apply(self):
        self.config._configure['settings'] = self.params
        # self.config.show()
        self.apply_signal.emit()

    def Press_Confirm(self):
        self.Press_Apply()
        self.close()

    # def Press_Cancel(self):
    #     self.close()


if __name__ == '__main__':
    import rich.traceback
    import sys
    rich.traceback.install()
    app = QApplication(sys.argv)
    win = SettingWindow(Config('config.yaml'))
    win.setWindowTitle('参数轮盘-setting')
    win.show()
    app.exec()
    sys.exit()
