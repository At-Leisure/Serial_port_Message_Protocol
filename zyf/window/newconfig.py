from PyQt6 import uic
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import string
import yaml
from collections import OrderedDict
from zyf.assist.config_struct import Config

PARAMUNIT_UI = './assets/ui/paramuint.ui'
NEWCONFIG_UI = './assets/ui/newconfig.ui'


class ParamUnit(QWidget):

    def __init__(self, parent=None, *agrs, **kwargs):
        super().__init__(parent, *agrs, **kwargs)
        uic.loadUi(PARAMUNIT_UI, self)
        self.label: QLabel
        self.key: QLineEdit = self.lineEdit
        self.value: QLineEdit = self.lineEdit_2


class NewconfigWindow(QDialog):

    def __init__(self, parent=None, *agrs, **kwargs):
        super().__init__(parent, *agrs, **kwargs)
        uic.loadUi(NEWCONFIG_UI, self)
        self.setWindowTitle('新建配置文件')
        self.item_list = []
        self.unitlist: QWidget = self.scrollAreaWidgetContents
        self.additem: QPushButton = self.item_add_btn
        self.popitem: QPushButton = self.pushButton_4
        self.addpath: QPushButton = self.pushButton_3
        self.confirm: QPushButton = self.pushButton_2
        self.cancel: QPushButton = self.pushButton
        self.pathlabel: QLabel = self.label
        self.path: str = None
        #
        self.confirm.clicked.connect(self.Confirm_Save)
        self.cancel.clicked.connect(self.close)
        self.additem.clicked.connect(self.Add_Item)
        self.popitem.clicked.connect(self.Pop_Item)
        self.addpath.clicked.connect(self.Choose_Path)
        #
        for i in range(3):
            self.Add_Item()

    def Choose_Path(self):
        f, _ = QFileDialog.getSaveFileName(self, '新配置保存到', './', 'Yaml (*.yaml *.yml)')
        if f:
            self.path = f
        self.pathlabel.setText('path: '+f)

    def Add_Item(self):
        item = ParamUnit(self)
        item.label.setText(str(len(self.item_list)))
        self.item_list.append(item)
        layout = self.unitlist.layout()
        layout.insertWidget(layout.count()-1, item)

    def Pop_Item(self):
        layout = self.unitlist.layout()
        w = self.item_list[-1]
        layout.removeWidget(w)
        self.item_list.pop()

    @property
    def params(self) -> tuple[str, float]:
        kv = []
        for item in self.item_list:
            item: ParamUnit
            k, v = item.key.text(), item.value.text()
            if k:
                if not v:
                    v = '0'
                try:
                    v = eval(v)
                except:
                    QMessageBox.critical(self.parent(), '语法错误', "值(value)只能是int或float类型！", QMessageBox.StandardButton.Yes)
                    continue
                kv.append([k, v])
        return kv

    def Confirm_Save(self):
        config = Config()
        config.parameters = self.params
        config.show()
        if self.path is None:
            QMessageBox.critical(self.parent(), '路径错误', "进行保存时对应路径不存在！", QMessageBox.StandardButton.Yes)
            self.pathlabel.setText('<p style="color: red;">path: 【警告】先选择路径才能保存配置！</p>')
        else:
            config.dump(self.path)
            QMessageBox.information(self.parent(), '创建成功', f'新文件已保存到"{self.path}"路径下。', QMessageBox.StandardButton.Yes)
            self.close()


if __name__ == '__main__':
    import rich.traceback
    import sys
    rich.traceback.install()
    app = QApplication(sys.argv)
    win = NewconfigWindow()
    win.show()
    app.exec()
    sys.exit()
