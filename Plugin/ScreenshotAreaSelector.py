import pyautogui
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint ,pyqtSignal

class ScreenshotAreaSelector(QWidget):
    """截屏区域选择器（子窗口）：拖拽选框，返回截屏结果"""
       # 作用：携带两个任意类型的数据（PIL图像、区域坐标），用于传递截屏结果
    screenshot_finished = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_dragging = False
        self.captured_screenshot = None  # 最终截屏结果（PIL格式）
        self.captured_region = None      # 截屏区域坐标 (x, y, width, height)
        self._setup_mask_window()

    def _setup_mask_window(self):
        """配置截屏遮罩窗口样式（子窗口）"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |    # 无标题栏、无边框
            Qt.WindowStaysOnTopHint |   # 置顶，不被其他窗口遮挡
            Qt.Window
            #Qt.SubWindow                # 标记为子窗口，依赖顶级窗口
        )
        # 覆盖整个屏幕
        self.setGeometry(QApplication.desktop().screenGeometry())
        # 半透明灰色遮罩
        self.setWindowOpacity(0.3)
        self.setStyleSheet("background-color: gray;")
        # 十字光标，提示用户可拖拽
        self.setCursor(QCursor(Qt.CrossCursor))

    def mousePressEvent(self, event):
        """鼠标按下：记录起始点，开始拖拽"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.is_dragging = True

    def mouseMoveEvent(self, event):
        """鼠标移动：实时更新结束点，触发重绘选框"""
        if self.is_dragging:
            self.end_point = event.pos()
            self.update()  # 触发paintEvent，绘制选框

    def mouseReleaseEvent(self, event):
        """鼠标松开：结束拖拽，计算区域，截取屏幕"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.end_point = event.pos()

        try:  # 新增：捕获所有异常，避免闪退
            rect = QRect(self.start_point, self.end_point).normalized()
            x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()

            if width > 10 and height > 10:
                self.captured_region = (x, y, width, height)
                # 新增：pyautogui截图前校验区域有效性，避免越界
                screen_rect = QApplication.desktop().screenGeometry()
                if (x >= 0 and y >= 0 and 
                    x + width <= screen_rect.width() and 
                    y + height <= screen_rect.height()):
                    self.captured_screenshot = pyautogui.screenshot(region=self.captured_region)
                else:
                    self.captured_screenshot = None
                    self.captured_region = None
                    print("❌ 截图区域超出屏幕范围，无效！")
            else:
                self.captured_screenshot = None
                self.captured_region = None
                print("❌ 截图区域过小（小于10x10像素），无效！")

            # 确保信号发射不抛异常（即使参数为None）
            self.screenshot_finished.emit(self.captured_screenshot, self.captured_region)
            # 强制关闭蒙版窗口（核心：无论是否出错，都关闭蒙版）
            self.close()

        except Exception as e:
            # 控制台输出具体报错，方便排查
            print(f"❌ 截图时发生异常：{type(e).__name__} - {str(e)}")
            # 异常时仍发射空信号，关闭蒙版
            self.screenshot_finished.emit(None, None)
            self.close()  # 关键：确保蒙版一定关闭

    def paintEvent(self, event):
        """绘制红色选框 + 蓝色半透明填充"""
        if self.is_dragging:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)

            # 选框边框：红色、2像素、实线
            pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
            painter.setPen(pen)

            # 选框填充：蓝色、半透明（不遮挡屏幕内容）
            brush = QColor(0, 0, 255, 50)
            painter.setBrush(brush)

            # 绘制归一化后的矩形选框
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)
