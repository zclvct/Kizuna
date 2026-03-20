# Live2D Widget
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from live2d.motion_controller import MotionController
from utils import get_character_manager, get_logger

logger = get_logger()


class Live2DWidget(QFrame):
    """Live2D 控件"""

    clicked = Signal()
    motion_played = Signal(str)  # 播放动作信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_manager = get_character_manager()
        self.motion_controller = MotionController()
        self._current_motion = "idle"
        self._setup_ui()
        self._setup_idle_timer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 角色展示区
        self.character_label = QLabel()
        self.character_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_character_display()
        layout.addWidget(self.character_label)

        # 心情指示器
        self.mood_label = QLabel()
        self.mood_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mood_label.setFont(QFont("Arial", 10))
        self._update_mood_display()
        layout.addWidget(self.mood_label)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 255, 220);
                border-radius: 16px;
            }
        """)
        self.setFixedSize(300, 400)

    def _setup_idle_timer(self):
        """设置空闲动画计时器"""
        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._on_idle)
        self._idle_timer.start(5000)  # 每5秒触发一次空闲动作

    def _update_character_display(self):
        """更新角色显示"""
        persona = self.character_manager.persona
        display_text = f"🎨 {persona.name}\n\n(点击互动)"
        self.character_label.setText(display_text)
        self.character_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #666;
                padding: 20px;
            }
        """)

    def _update_mood_display(self):
        """更新心情显示"""
        state = self.character_manager.state
        mood_emojis = {
            "happy": "😊 开心",
            "excited": "🥳 兴奋",
            "normal": "😐 平静",
            "tired": "😴 疲惫",
            "sad": "😢 难过",
            "angry": "😠 生气",
            "shy": "😊 害羞",
            "thinking": "🤔 思考",
        }
        mood_text = mood_emojis.get(state.current_mood, f"😐 {state.current_mood}")
        self.mood_label.setText(mood_text)
        self.mood_label.setStyleSheet("""
            QLabel {
                color: #888;
                padding: 5px;
            }
        """)

    def _on_idle(self):
        """空闲动作"""
        self.play_motion("idle")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            self._on_click()

    def _on_click(self):
        """点击互动"""
        # 随机播放一个互动动作
        import random
        interactive_motions = ["tap_head", "tap_shoulder", "wave"]
        motion = random.choice(interactive_motions)
        self.play_motion(motion)

        # 稍微改变心情
        state = self.character_manager.state
        if state.current_mood == "normal":
            state.current_mood = "happy"
            self._update_mood_display()

    def play_motion(self, motion_id: str, mood: str = None):
        """播放动作"""
        self._current_motion = motion_id
        logger.info(f"Playing motion: {motion_id}")

        # 更新显示
        persona = self.character_manager.persona
        motion_text = f"🎨 {persona.name}\n\n动作: {motion_id}"
        self.character_label.setText(motion_text)

        # 如果有心情变化
        if mood:
            state = self.character_manager.state
            state.current_mood = mood
            self._update_mood_display()

        # 发送信号
        self.motion_played.emit(motion_id)

        # 2秒后恢复显示
        QTimer.singleShot(2000, self._update_character_display)

    def update_mood(self, mood: str):
        """更新心情"""
        state = self.character_manager.state
        state.current_mood = mood
        self._update_mood_display()

        # 根据心情播放对应动作
        motion = self.motion_controller.get_motion_for_mood(mood)
        if motion:
            self.play_motion(motion)

