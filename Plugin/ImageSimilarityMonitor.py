import sys
import io
import numpy as np
import pyautogui
from PIL import Image
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow, 
                             QPushButton, QVBoxLayout, QLabel)
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor, QPixmap
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer, QObject
class ImageSimilarityMonitor(QObject):
    """
    独立的图像相似度循环监控类
    功能：接收基准图和监控区域，循环截图对比，达到阈值触发pp回调
    不依赖任何截屏窗口代码，仅负责核心对比逻辑
    """
    # 自定义信号：向外部传递监控状态（解耦UI）
    signal_monitor_running = pyqtSignal(float)  # 监控中，传递当前相似度（0-1）
    signal_monitor_finished = pyqtSignal(float) # 监控完成（达到阈值），传递最终相似度
    signal_monitor_stopped = pyqtSignal()       # 监控被停止

    def __init__(self):
        super().__init__()
        # 内部初始化（仅保存核心参数，不涉及UI）
        self.base_image = None          # 基准图（PIL Image）
        self.monitor_region = None      # 监控区域 (x, y, w, h)
        self.similarity_threshold = 0.90# 相似度阈值（95%）
        self.check_interval = 500      # 循环间隔（毫秒）
        self.monitor_timer = QTimer(self)# 循环定时器
        self.is_monitoring = False      # 监控状态标记

        # 绑定定时器超时事件
        self.monitor_timer.timeout.connect(self._check_similarity_once)

    def set_config(self, base_image, monitor_region, threshold=0.95, interval=1000):
        """
        设置监控配置（外部调用，传递必要参数）
        :param base_image: 基准图（PIL Image）
        :param monitor_region: 监控区域 (x, y, w, h)
        :param threshold: 相似度阈值（默认0.95）
        :param interval: 循环间隔（默认1000毫秒）
        """
        self.base_image = base_image
        self.monitor_region = monitor_region
        self.similarity_threshold = threshold
        self.check_interval = interval

        # 更新定时器间隔
        self.monitor_timer.setInterval(self.check_interval)

    def start_monitor(self):
        """启动循环监控（外部调用）"""
        # 参数校验
        if not self.base_image or not self.monitor_region:
            raise ValueError("监控配置未完成！请先调用 set_config 设置基准图和监控区域")
        if self.is_monitoring:
            return

        # 标记状态，启动定时器
        self.is_monitoring = True
        self.monitor_timer.start()
        print("\n" + "="*60)
        print("✅ 图像相似度监控已启动")
        print(f"🎯 相似度阈值：{self.similarity_threshold*100}%")
        print(f"⏱  循环间隔：{self.check_interval/1000}秒")
        print("="*60 + "\n")

    def stop_monitor(self):
        """停止循环监控（外部调用）"""
        if not self.is_monitoring:
            return

        # 标记状态，停止定时器
        self.is_monitoring = False
        self.monitor_timer.stop()

        # 发送停止信号给外部
        self.signal_monitor_stopped.emit()
        print("\n" + "="*60)
        print("⏹ 图像相似度监控已停止")
        print("="*60 + "\n")

    def _calculate_similarity(self, img1, img2):
        """内部方法：计算两张PIL图片的相似度（返回0-1）"""
        if img1 is None or img2 is None:
            return 0.0

        # 尺寸对齐
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        # 转换为灰度图并转为numpy数组
        img1_gray = np.array(img1.convert("L"), dtype=np.float32)
        img2_gray = np.array(img2.convert("L"), dtype=np.float32)

        # 计算像素差值平均值和相似度
        diff = np.abs(img1_gray - img2_gray)
        diff_avg = np.mean(diff)
        similarity = 1.0 - (diff_avg / 255.0)

        return similarity

    def _check_similarity_once(self):
        """内部方法：单次相似度检查（定时器触发）"""
        if not self.is_monitoring:
            return

        # 1. 截取当前监控区域图片
        current_image = pyautogui.screenshot(region=self.monitor_region)

        # 2. 计算相似度
        similarity = self._calculate_similarity(self.base_image, current_image)
        similarity_percent = round(similarity * 100, 2)

        # 3. 发送监控中信号给外部（更新UI）
        self.signal_monitor_running.emit(similarity)

        # 4. 打印内部日志
        print(f"🔍 当前相似度：{similarity_percent}%（阈值：{self.similarity_threshold*100}%）")

        # 5. 判断是否达到阈值
        if similarity >= self.similarity_threshold:
            # 停止监控
            self.stop_monitor()

            # 发送完成信号给外部
            self.signal_monitor_finished.emit(similarity)
            print("\n" + "="*60)
            print(f"🎉 达到相似度阈值！最终相似度：{similarity_percent}%")
            print("="*60 + "\n")