import os
from pprint import pprint
from copy import deepcopy
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from zyf.assist.config_struct import Config

CODE_PREVIEW_UI = './assets/ui/code_preview.ui'


class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlight_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(255, 162, 67))  # orange
        keyword_format.setFontWeight(QFont.Bold)
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
            pattern = QRegExp(r'\b{}\b'.format(word))
            self.highlight_rules.append((pattern, keyword_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor(107, 138, 234))  # function
        pattern = QRegExp(r'\b[A-Za-z0-9_]+(?=\()')
        self.highlight_rules.append((pattern, function_format))

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor(166, 172, 175))  # gray
        pattern = QRegExp('//[^\n]*')
        self.highlight_rules.append((pattern, single_line_comment_format))

        multi_line_comment_format = QTextCharFormat()
        multi_line_comment_format.setForeground(QColor(166, 172, 175))  # gray
        pattern = QRegExp('/\*[\s\S]*?\*/')
        self.highlight_rules.append((pattern, multi_line_comment_format))

        precompile_format = QTextCharFormat()
        precompile_format.setForeground(QColor(231, 0, 0))  # precompile
        pattern = QRegExp('^#\w+\s(?=\S)')
        self.highlight_rules.append((pattern, precompile_format))

        quotation_format = QTextCharFormat()
        quotation_format.setForeground(QColor(92, 192, 174))  # string
        pattern = QRegExp('"(?:(?!")[^"\\\\]|\\\\.)*"')
        self.highlight_rules.append((pattern, quotation_format))

        # # include pragma define
        # package_format = QTextCharFormat()
        # package_format.setForeground(QColor(0, 200, 0))
        # pattern = QRegExp('(?<=#include)\s*<.*>')
        # self.highlight_rules.append((pattern, package_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlight_rules:
            expression = QRegExp(pattern)
            i = expression.indexIn(text)
            while i >= 0:
                length = expression.matchedLength()
                self.setFormat(i, length, format)
                i = expression.indexIn(text, i + length)


class CodeWindow(QDialog):

    def __init__(self, config: Config, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        uic.loadUi(CODE_PREVIEW_UI, self)
        self.setWindowTitle('高亮代码预览')
        self.setMinimumSize(1000, 700)
        self.mainBrowser: QTextBrowser = self.textBrowser
        self.funcBrowser: QTextBrowser = self.textBrowser_2
        self.highlighter1 = CppHighlighter(self.mainBrowser.document())
        self.highlighter2 = CppHighlighter(self.funcBrowser.document())

        self.save_pushButton.clicked.connect(self.Save_Building)
        self.pushButton_2.clicked.connect(self.close)

    def exec(self):
        self.Update_Coding()
        super().exec()

    def show(self):
        self.Update_Coding()
        super().show()

    def Update_Coding(self):
        self.mainBrowser.setText(self.main_coding)
        self.funcBrowser.setText(self.func_coding)

    def Save_Building(self):
        folder_path = './build/'+self.config.yaml_path.replace(r'\\', '/').split('/')[-1].rsplit('.', 1)[0]
        main_path = folder_path+'/main.c'
        func_path = folder_path+'/func.c'
        if os.path.exists(main_path):
            os.remove(main_path)
        if os.path.exists(func_path):
            os.remove(func_path)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)  # 如果文件存在则先删除后创建，目录不存在直接创建
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(self.main_coding)
        with open(func_path, 'w', encoding='utf-8') as f:
            f.write(self.func_coding)
        QMessageBox.information(self.parent(), '生成C代码', f'代码已经保存到{os.path.abspath(folder_path)}目录下。', QMessageBox.Yes)
# ------------------------------------------------ main.c ------------------------------------------------ #

    @property
    def main_coding(self) -> str:
        _N = '\n'
        return f"""#include <stdio.h>
#include "stdlib.h"

// 以下是通过宏定义进行引言的全局变量，DEF_XXX是生成代码使用中的别名，where_XXX需要自己进行替换
{ _N.join('#define DEF_'+k+' where_'+k for k in self.config.parameters.keys())}

#define DEF_WIRELESS_recv where_wireless_recv

enum {{{', '.join(self.config.parameters.keys())}}};

int main()
{{
    char s = "Hello World!";
    printf("%s",s);
    return 0;
}}"""

# ------------------------------------------------ func.c ------------------------------------------------ #
    @property
    def func_coding(self) -> str:

        return f"""#include<math.h>
int function(void){{
    return 0; 
}}"""


if __name__ == '__main__':
    import rich.traceback
    import sys
    import string
    rich.traceback.install()
    app = QApplication(sys.argv)
    win = CodeWindow(Config('config.yaml'))
    win.setWindowTitle('参数轮盘')
    win.show()
    app.exec()
    sys.exit()
