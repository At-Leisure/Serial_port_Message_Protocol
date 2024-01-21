from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import string


class Turntable(QWidget):

    signal = pyqtSignal(int)

    def __init__(self, names: tuple[str] = None, n_items: str = 7, *args, **kwargs):
        super().__init__(*args, **kwargs)
        names = names if not names is None else [string.ascii_uppercase[i:i+3] for i in range(0, 25, 3)]
        self.names = names
        self.n_items = n_items
        self._anchor = n_items // 2
        assert n_items % 2 == 1
        self.labels = []

        layout = QVBoxLayout()
        for i in range(n_items):
            l = QLabel()
            self.labels.append(l)
            layout.addWidget(l, n_items-abs(n_items//2-i))

            font = QFont()
            if (i+1)*2 - self.n_items == 1:
                font.setBold(True)
                font.setPointSize(12)
                font.setFamily('Consolas')
            else:
                font.setPointSize(12 - 2 - abs(n_items//2-i))
            l.setFont(font)

        self.setLayout(layout)
        self.moveItem()

    @property
    def anchor(self):
        return self._anchor

    @anchor.setter
    def anchor(self, x: int):
        self._anchor = x % len(self.names)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 20:
            self.anchor -= 1
        if event.angleDelta().y() < 20:
            self.anchor += 1
        self.moveItem()
        # print(self.anchor_word)
        self.signal.emit(self.anchor)

    def moveItem(self, index: int = None):
        if not index is None:
            self.anchor = index
        names = self.names*3
        names = names[len(self.names)+self.anchor-self.n_items//2:len(self.names)+self.anchor+self.n_items//2+1]
        c = self.labels
        for i in range(len(c)):
            l: QLabel = c[i]
            s = '-' if i >= len(names) else names[i]
            if (i+1)*2 - self.n_items == 1:
                s = '>'+s
            else:
                s = '  '+s
            l.setText(s)


if __name__ == '__main__':
    import rich.traceback
    import sys
    rich.traceback.install()
    app = QApplication(sys.argv)
    win = Turntable()
    win.setWindowTitle('参数轮盘')
    win.show()
    sys.exit(app.exec())
