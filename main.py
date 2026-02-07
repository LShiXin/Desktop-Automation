from Windows.MainWindow import MainWindow
import sys
import pyautogui
from Plugin.ScreenshotAreaSelector import ScreenshotAreaSelector
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QPushButton, QLabel)
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
if __name__ == "__main__":
    # 1. 初始化PyQt5应用（全局唯一）
    app = QApplication(sys.argv)

    # 2. 创建并显示顶级测试窗口
    main_window = MainWindow()
    main_window.show()

    # 3. 启动全局事件循环（由顶级窗口掌控，关闭顶级窗口才会退出）
    sys.exit(app.exec_())