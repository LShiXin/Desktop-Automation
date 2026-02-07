from Plugin.ScreenshotAreaSelector import ScreenshotAreaSelector
from Plugin.ImageSimilarityMonitor import ImageSimilarityMonitor
import sys
import io
import os
import pyautogui
from PIL import Image
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor, QPixmap
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
class MainWindow(QMainWindow):
    """顶级测试窗口：用于唤起截屏子窗口，展示截屏结果"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("截屏展示 + 独立循环对比")
        self.setGeometry(100, 100, 800, 750)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.base_screenshot = None  # 截屏得到的基准图
        self.monitor_region = None   # 截屏得到的监控区域
        self.similarity_monitor = ImageSimilarityMonitor()  # 实例化独立对比类

        # 初始化UI控件
        self._init_ui()

        # 绑定独立对比类的信号（接收监控状态）
        self._bind_monitor_signals()

    def _init_ui(self):
        """初始化UI：截屏按钮 → 图片展示 → 开始对比按钮 → 停止对比按钮"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)

        # 1. 状态标签（显示当前流程状态）
        self.status_label = QLabel("状态：未截屏，请先选择截屏区域", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 25px; color: #333333;")
        layout.addWidget(self.status_label)

        # 2. 图片展示标签（显示截屏后的基准图）
        self.image_show_label = QLabel("未截屏，暂无图片", self)
        self.image_show_label.setFixedSize(700, 400)
        self.image_show_label.setStyleSheet("border: 2px solid #cccccc;")
        self.image_show_label.setAlignment(Qt.AlignCenter)
        self.image_show_label.setScaledContents(False)
        layout.addWidget(self.image_show_label)

        # 3. 功能按钮组
        # 3.1 截屏按钮（选择区域并展示）
        self.screenshot_btn = QPushButton("📸 选择截屏区域", self)
        self.screenshot_btn.setFixedSize(250, 50)
        self.screenshot_btn.clicked.connect(self.on_call_screenshot)
        layout.addWidget(self.screenshot_btn)

        # 3.2 开始对比按钮（初始禁用，截屏后启用）
        self.start_compare_btn = QPushButton("🚀 开始循环对比", self)
        self.start_compare_btn.setFixedSize(250, 50)
        self.start_compare_btn.setEnabled(False)  # 初始禁用
        self.start_compare_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.start_compare_btn.clicked.connect(self.on_start_compare)
        layout.addWidget(self.start_compare_btn)

        # 3.3 停止对比按钮（初始禁用，监控中启用）
        self.stop_compare_btn = QPushButton("⏹ 停止循环对比", self)
        self.stop_compare_btn.setFixedSize(250, 50)
        self.stop_compare_btn.setEnabled(False)
        self.stop_compare_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_compare_btn.clicked.connect(self.on_stop_compare)
        layout.addWidget(self.stop_compare_btn)


    def _bind_monitor_signals(self):
        """绑定独立对比类的信号，更新UI状态"""
        # 监控中：更新当前相似度
        self.similarity_monitor.signal_monitor_running.connect(self._on_monitor_running)

        # 监控完成：更新完成状态
        self.similarity_monitor.signal_monitor_finished.connect(self._on_monitor_finished)

        # 监控停止：更新停止状态
        self.similarity_monitor.signal_monitor_stopped.connect(self._on_monitor_stopped)


    def on_call_screenshot(self):
        """点击按钮：创建并显示截屏子窗口"""
        # 1. 创建截屏子窗口，指定父窗口为当前顶级窗口（建立父子关系）,指定父窗口时窗口大小会被限制，截屏插件不指定窗口
        self.screenshot_selector = ScreenshotAreaSelector()
        # 2. 绑定子窗口的信号与顶级窗口的槽函数（接收截屏结果）
        self.screenshot_selector.screenshot_finished.connect(self.on_screenshot_result)
        # 3. 显示截屏子窗口（非阻塞，顶级窗口仍可响应操作）
        self.screenshot_selector.show()

    def _on_screenshot_finished(self, base_screenshot, monitor_region):
        """截屏完成，展示图片并启用「开始对比按钮」"""
        # 1. 验证截屏结果
        if not base_screenshot or not monitor_region:
            self.status_label.setText("状态：截屏失败，无法展示图片")
            return

        # 2. 保存基准图和监控区域
        self.base_screenshot = base_screenshot
        self.monitor_region = monitor_region

        # 3. 展示基准图到UI
        qpixmap = self.pil_to_qpixmap(self.base_screenshot)
        if qpixmap is not None:
            scaled_qpixmap = qpixmap.scaled(
                self.image_show_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_show_label.setPixmap(scaled_qpixmap)
            self.image_show_label.setText("")

        # 4. 更新UI状态和按钮（启用开始对比按钮）
        self.status_label.setText("状态：截屏完成，可点击「开始循环对比」启动监控")
        self.start_compare_btn.setEnabled(True)
        self.stop_compare_btn.setEnabled(False)

        # 5. 打印日志
        print("\n" + "="*60)
        print("✅ 截屏完成，图片已展示")
        print(f"📌 截屏区域：{self.monitor_region}")
        print(f"📏 图片尺寸：{self.base_screenshot.size}")
        print("="*60 + "\n")

    def pil_to_qpixmap(self, pil_image):
        """辅助方法：将 PIL 图像转换为 PyQt5 支持的 QPixmap（核心转换逻辑）"""
        if pil_image is None:
            return None
        # 1. 创建字节流缓冲区
        buffer = io.BytesIO()
        # 2. 将 PIL 图像保存到字节流中（格式为 PNG，无压缩，保真）
        pil_image.save(buffer, format='PNG')
        # 3. 从字节流中读取数据，创建 QPixmap
        qpixmap = QPixmap()
        qpixmap.loadFromData(buffer.getvalue())
        # 4. 返回转换后的 QPixmap
        return qpixmap

    def on_start_compare(self):
        """点击「开始对比按钮」，启动独立类的循环监控"""
        # 1. 配置独立对比类的参数
        print("开始对比")
        self.similarity_monitor.set_config(
            base_image=self.base_screenshot,
            monitor_region=self.monitor_region,
            threshold=0.90,
            interval=500
        )

        # 2. 启动监控
        try:
            self.similarity_monitor.start_monitor()

            # 3. 更新UI状态和按钮
            self.status_label.setText("状态：监控中，正在循环对比相似度...")
            self.start_compare_btn.setEnabled(False)
            self.stop_compare_btn.setEnabled(True)
        except ValueError as e:
            self.status_label.setText(f"状态：启动监控失败 → {str(e)}")

    def on_stop_compare(self):
        """点击「停止对比按钮」，停止独立类的循环监控"""
        self.similarity_monitor.stop_monitor()

    def _on_monitor_running(self, similarity):
        """接收监控中信号，更新当前相似度UI"""
        similarity_percent = round(similarity * 100, 2)
        self.status_label.setText(f"状态：监控中 → 当前相似度：{similarity_percent}%（阈值：90%）")

    def _on_monitor_finished(self, similarity):
        """接收监控完成信号，更新完成状态"""
        similarity_percent = round(similarity * 100, 2)
        self.status_label.setText(f"状态：监控完成 → 最终相似度：{similarity_percent}%（≥90%）")

        # 保存稳定截图（可选业务逻辑）
        final_screenshot = pyautogui.screenshot(region=self.monitor_region)
        final_screenshot.save("Images/stable_screenshot.png")
        print("💾 稳定区域截图已保存为：stable_screenshot.png")

    def _on_monitor_stopped(self):
        """接收监控停止信号，更新停止状态"""
        self.status_label.setText("状态：监控已停止")
        self.start_compare_btn.setEnabled(True)
        self.stop_compare_btn.setEnabled(False)

    def on_screenshot_result(self, screenshot, region):
        """槽函数：接收截屏子窗口的结果，处理并展示,截图完毕后，将信息导入到_on_screenshot_finished方法，开启对比按钮"""
        print("\n" + "="*50)

        if screenshot and region:
            # 截屏成功：打印结果
            print("✅ 截屏成功！")
            print(f"📌 截屏区域坐标：{region}")
            print(f"📏 截图尺寸：{screenshot.size}")
            

             # 在保存截图前，先创建Images文件夹
            save_dir = "Images"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)  # 如果文件夹不存在，就创建它
            # 保存截图到Images文件夹
             # 可选：保存截图到本地（验证结果）
            screenshot.save(os.path.join(save_dir, "test_screenshot_from_main.png"))
            print("💾 截图已保存为：test_screenshot_from_main.png")

             # 3. 核心：将 PIL 截图转换为 QPixmap
            qpixmap = self.pil_to_qpixmap(screenshot)
            if qpixmap is not None:
                # 4. 调整 QPixmap 大小，自适应图片显示标签（保持比例，不变形）
                scaled_qpixmap = qpixmap.scaled(
                    self.image_show_label.size(),  # 目标大小（标签大小）
                    Qt.KeepAspectRatio,             # 保持图片宽高比，避免变形
                    Qt.SmoothTransformation         # 平滑缩放，提升图片显示质量
                )
                # 5. 将缩放后的 QPixmap 设置到标签上，展示图片
                self.image_show_label.setPixmap(scaled_qpixmap)
                # 6. 清除标签的默认文本（可选，设置 pixmap 后文本会被覆盖）
                self.image_show_label.setText("")
            #截图完毕后，启用对比按钮，
            self._on_screenshot_finished(screenshot,region)

        else:
            # 截屏失败：提示无效区域
            print("❌ 截屏失败！未选择有效区域（请拖拽大于 10x10 像素的区域）")
        print("="*60 + "\n")
       