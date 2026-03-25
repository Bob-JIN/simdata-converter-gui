#!/usr/bin/env python3
"""
main.py: CB2016 .ised/.fits文件转换工具主程序入口
"""

import sys

from PyQt5.QtWidgets import QApplication

from gui import ISEDConverterGUI


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ISEDConverterGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
