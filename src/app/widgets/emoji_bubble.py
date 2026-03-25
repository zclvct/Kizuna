# Emoji Bubble Widget - 表情包气泡控件（漫画风格）
import sys
import math
from pathlib import Path
from typing import Optional

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect,
    QSizePolicy, QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PySide6.QtGui import QPixmap, QMovie, QPainter, QColor, QPainterPath, QPen, QBrush

from utils.logger import get_logger
from utils.constants import resolve_path

logger = get_logger()


class EmojiBubble(QWidget):
    """表情包气泡控件 - 漫画风格云朵气泡
    
    在屏幕上显示表情包图片/GIF，带云朵气泡效果，指向 Live2D 模型头顶
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_movie = None
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)
        
        self._fade_animation = None
        self._opacity_effect = None
        
        # 气泡样式参数
        self._bubble_padding = 12  # 内容区域内边距
        self._bubble_radius = 16   # 圆角半径
        self._tail_height = 20     # 尾部高度（指向模型的部分）
        
        # 图片尺寸
        self._emoji_size = 120
        
        self._setup_ui()
        self.hide()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 主布局 - 留出尾部空间
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self._bubble_padding, 
            self._bubble_padding, 
            self._bubble_padding, 
            self._bubble_padding + self._tail_height
        )
        
        # 图片标签
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background: transparent;")
        self._image_label.setFixedSize(self._emoji_size, self._emoji_size)
        layout.addWidget(self._image_label, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # 透明度效果
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        
        # 设置固定大小
        total_width = self._emoji_size + self._bubble_padding * 2
        total_height = self._emoji_size + self._bubble_padding * 2 + self._tail_height
        self.setFixedSize(total_width, total_height)
    
    def paintEvent(self, event):
        """绘制漫画风格气泡背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 气泡主体区域（不含尾部）
        bubble_rect = self.rect().adjusted(0, 0, 0, -self._tail_height)
        
        # 创建气泡路径
        path = QPainterPath()
        
        # 主体圆角矩形
        path.addRoundedRect(bubble_rect, self._bubble_radius, self._bubble_radius)
        
        # 底部三角形尾巴
        center_x = bubble_rect.center().x()
        tail_top = bubble_rect.bottom()
        tail_bottom = self.rect().bottom()
        
        # 三角形尾巴
        tail_path = QPainterPath()
        tail_width = 16
        tail_height = self._tail_height
        tail_path.moveTo(center_x - tail_width // 2, tail_top)
        tail_path.lineTo(center_x, tail_bottom)
        tail_path.lineTo(center_x + tail_width // 2, tail_top)
        tail_path.closeSubpath()
        path.addPath(tail_path)
        
        # 填充白色背景（半透明）
        painter.fillPath(path, QColor(255, 255, 255, 250))
        
        # 绘制边框
        pen = QPen(QColor(220, 220, 220), 2)
        painter.setPen(pen)
        painter.drawPath(path)
    
    def show_emoji(self, file_path: str, duration: int = 3000, position: Optional[QPoint] = None):
        """显示表情包
        
        Args:
            file_path: 表情包文件路径（相对或绝对）
            duration: 显示时长（毫秒）
            position: Live2D 模型头顶位置（气泡会指向这个位置）
        """
        logger.info(f"EmojiBubble.show_emoji 被调用: {file_path}, duration={duration}")
        
        # 停止之前的动画
        if self._current_movie:
            self._current_movie.stop()
        
        # 使用 resolve_path 解析文件路径（优先用户目录，然后项目目录）
        full_path = resolve_path(file_path)
        
        logger.info(f"表情包完整路径: {full_path}, 存在: {full_path.exists()}")
        
        if not full_path.exists():
            logger.warning(f"表情包文件不存在: {full_path}")
            return
        
        # 根据文件类型加载
        suffix = full_path.suffix.lower()
        
        if suffix == '.gif':
            self._show_gif(full_path)
        else:
            self._show_image(full_path)
        
        # 设置位置 - 气泡在模型上方，尾部指向模型头顶
        if position:
            self._set_position_above_model(position)
        else:
            self._set_auto_position()
        
        # 显示并开始计时
        self._opacity_effect.setOpacity(1.0)
        self.show()
        self.raise_()
        
        logger.info(f"EmojiBubble 已显示, visible={self.isVisible()}, geometry={self.geometry()}")
        
        # 设置自动隐藏
        self._hide_timer.start(duration)
    
    def _show_image(self, path: Path):
        """显示静态图片"""
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logger.warning(f"无法加载图片: {path}")
            return
        
        # 缩放到固定尺寸
        if pixmap.width() > self._emoji_size or pixmap.height() > self._emoji_size:
            pixmap = pixmap.scaled(
                self._emoji_size, self._emoji_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        self._image_label.setPixmap(pixmap)
    
    def _show_gif(self, path: Path):
        """显示 GIF 动图"""
        self._current_movie = QMovie(str(path))
        self._current_movie.setScaledSize(QSize(self._emoji_size, self._emoji_size))
        
        self._image_label.setMovie(self._current_movie)
        self._current_movie.start()
    
    def _set_position_above_model(self, model_head_pos: QPoint):
        """设置气泡位置，使其尾部指向模型头顶"""
        screen = self.screen()
        if not screen:
            screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 气泡底部中央指向模型头顶
        # 所以气泡底部应该在 model_head_pos.y 的位置
        bubble_x = model_head_pos.x() - self.width() // 2
        bubble_y = model_head_pos.y() - self.height()  # 气泡在头顶上方
        
        # 确保不超出屏幕左边界
        if bubble_x < screen_rect.left():
            bubble_x = screen_rect.left()
        # 确保不超出屏幕右边界
        if bubble_x + self.width() > screen_rect.right():
            bubble_x = screen_rect.right() - self.width()
        # 确保不超出屏幕上边界
        if bubble_y < screen_rect.top():
            bubble_y = screen_rect.top()
        
        self.move(bubble_x, bubble_y)
        logger.info(f"气泡位置: ({bubble_x}, {bubble_y}), 指向: {model_head_pos}")
    
    def _set_auto_position(self):
        """自动设置位置（在 Live2D 模型头顶上方）"""
        live2d_widget = self._find_live2d_widget()
        
        if live2d_widget:
            # 获取 Live2D 窗口位置
            live2d_rect = live2d_widget.geometry()
            
            # 计算模型头顶位置（窗口中央偏上）
            model_head_x = live2d_rect.center().x()
            model_head_y = live2d_rect.top() + 50  # 头顶位置（距顶部约50像素）
            
            self._set_position_above_model(QPoint(model_head_x, model_head_y))
        else:
            # 默认在屏幕中央偏上
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                center_x = screen_rect.center().x() - self.width() // 2
                center_y = screen_rect.top() + 100
                self.move(center_x, center_y)
    
    def _find_live2d_widget(self):
        """查找 Live2D 控件"""
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "live2dWidget" or "Live2D" in widget.__class__.__name__:
                return widget
        return None
    
    def _start_fade_out(self):
        """开始淡出动画"""
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(300)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._fade_animation.finished.connect(self.hide)
        self._fade_animation.start()
    
    def hide(self):
        """隐藏"""
        if self._current_movie:
            self._current_movie.stop()
            self._current_movie = None
        super().hide()
    
    def mousePressEvent(self, event):
        """点击关闭"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.hide()
        super().mousePressEvent(event)
