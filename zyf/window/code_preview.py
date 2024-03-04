import os
from pprint import pprint
from copy import deepcopy
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from typing import Literal
from PyQt6.QtCore import *
from PyQt6 import uic
from zyf.console import CodingFileNames, Console

CODE_PREVIEW_UI = './assets/ui/code_preview.ui'


class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlight_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(255, 162, 67))  # orange
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel", "atomic_commit",
                    "atomic_noexcept", "auto", "bitand", "bitor", "bool", "break", "case", "catch",
                    "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept", "const",
                    "consteval", "constexpr", "const_cast", "continue", "co_await", "co_return",
                    "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast",
                    "else", "enum", "explicit", "export", "extern", "false", "float", "for",
                    "friend", "goto", "if", "inline", "int", "long", "mutable", "namespace", "new",
                    "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
                    "protected", "public", "reflexpr", "register", "reinterpret_cast", "requires",
                    "return", "short", "signed", "sizeof", "static", "static_assert", "static_cast",
                    "struct", "switch", "synchronized", "template", "this", "thread_local", "throw",
                    "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
                    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq"]
        for word in keywords:
            pattern = QRegularExpression(r'\b{}\b'.format(word))
            self.highlight_rules.append((pattern, keyword_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor(107, 138, 234))  # function
        pattern = QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()')
        self.highlight_rules.append((pattern, function_format))

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor(166, 172, 175))  # gray
        pattern = QRegularExpression('//[^\n]*')
        self.highlight_rules.append((pattern, single_line_comment_format))

        multi_line_comment_format = QTextCharFormat()
        multi_line_comment_format.setForeground(QColor(166, 172, 175))  # gray
        pattern = QRegularExpression('/\*[\s\S]*?\*/')
        self.highlight_rules.append((pattern, multi_line_comment_format))

        precompile_format = QTextCharFormat()
        precompile_format.setForeground(QColor(231, 0, 0))  # precompile
        pattern = QRegularExpression('^#\w+')
        self.highlight_rules.append((pattern, precompile_format))

        quotation_format = QTextCharFormat()
        quotation_format.setForeground(QColor(92, 192, 174))  # string
        pattern = QRegularExpression('"(?:(?!")[^"\\\\]|\\\\.)*"')
        self.highlight_rules.append((pattern, quotation_format))

        # # include pragma define
        # package_format = QTextCharFormat()
        # package_format.setForeground(QColor(0, 200, 0))
        # pattern = QRegularExpression('(?<=#include)\s*<.*>')
        # self.highlight_rules.append((pattern, package_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlight_rules:
            expression = QRegularExpression(pattern)
            matched = expression.match(text)
            self.setFormat(matched.capturedStart(0), matched.capturedLength(), format)


class CodeWindow(QDialog):

    def __init__(self, w: Literal['QWidget', 'QDialog'], console: Console, parent=None, *args, **kwargs):
        if w == 'QWidget':
            QWidget.__init__(self, parent, *args, **kwargs)
        elif w == 'QDialog':
            QDialog.__init__(self, parent, *args, **kwargs)

        self.console = console
        uic.loadUi(CODE_PREVIEW_UI, self)
        self.setWindowTitle('高亮代码预览')
        self.mainBrowser: QTextBrowser = self.textBrowser
        self.funcBrowser: QTextBrowser = self.textBrowser_2
        self.headBrowser: QTextBrowser = self.textBrowser_3
        self.highlighter1 = CppHighlighter(self.mainBrowser.document())
        self.highlighter2 = CppHighlighter(self.funcBrowser.document())
        self.highlighter3 = CppHighlighter(self.headBrowser.document())

        self.save_pushButton.clicked.connect(self.console.save_codings)
        self.pushButton_2.clicked.connect(self.close)

    def exec(self):
        self.Update_Coding()
        super().exec()

    def show(self):
        self.Update_Coding()
        super().show()

    def Update_Coding(self):
        self.mainBrowser.setText(self.console.coding('main.c'))
        self.funcBrowser.setText(self.console.coding('serial_order.c'))
        self.headBrowser.setText(self.console.coding('serial_order.h'))
        