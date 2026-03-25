# Motion Controller
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import Optional, List, Callable
import json
import random

from utils import MOTIONS_FILE, DEFAULT_MOTIONS_CONFIG, get_config, get_logger
from utils.constants import resolve_path

logger = get_logger()


class MotionController:
    """动作控制器 - 管理 Live2D 动作播放"""

    def __init__(self, model=None, config_path: Path = MOTIONS_FILE):
        self.model = model
        self.config_path = config_path
        self.config = self._load_config()
        self.current_mood = "normal"
        self._motion_callbacks: List[Callable] = []
        self._model_motions_cache = None  # 缓存模型动作列表

    def _load_config(self) -> dict:
        """加载配置"""
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"加载动作配置失败: {e}")
        # 如果文件不存在，创建默认配置
        self._save_default_config()
        return DEFAULT_MOTIONS_CONFIG

    def _save_default_config(self):
        """保存默认配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(
                json.dumps(DEFAULT_MOTIONS_CONFIG, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.info(f"已创建默认动作配置: {self.config_path}")
        except Exception as e:
            logger.error(f"保存默认动作配置失败: {e}")

    def _save_config(self):
        """保存配置"""
        try:
            self.config_path.write_text(
                json.dumps(self.config, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.info(f"动作配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存动作配置失败: {e}")

    def get_motion_for_mood(self, mood: str) -> Optional[str]:
        """根据心情获取动作"""
        motions = self.config.get("mood_motions", {}).get(mood, [])
        if motions:
            return random.choice(motions)
        return self.config.get("default_motion", "idle_01")

    def get_motion_for_intent(self, intent: str) -> Optional[str]:
        """根据意图获取动作"""
        motions = self.config.get("intent_motions", {}).get(intent, [])
        if motions:
            return random.choice(motions)
        return None

    def add_motion_callback(self, callback: Callable[[str], None]):
        """添加动作回调"""
        if callback not in self._motion_callbacks:
            self._motion_callbacks.append(callback)

    def remove_motion_callback(self, callback: Callable[[str], None]):
        """移除动作回调"""
        if callback in self._motion_callbacks:
            self._motion_callbacks.remove(callback)

    def play_motion(
        self,
        mood: Optional[str] = None,
        intent: Optional[str] = None,
        motion_id: Optional[str] = None,
        new_mood: Optional[str] = None
    ) -> str:
        """
        播放动作

        Args:
            mood: 根据心情选择动作
            intent: 根据意图选择动作
            motion_id: 直接指定动作 ID
            new_mood: 切换到新心情

        Returns:
            播放的动作 ID
        """
        if new_mood:
            self.current_mood = new_mood

        if motion_id:
            final_motion = motion_id
        elif intent:
            final_motion = self.get_motion_for_intent(intent)
            if not final_motion and mood:
                final_motion = self.get_motion_for_mood(mood)
            elif not final_motion:
                final_motion = self.get_motion_for_mood(self.current_mood)
        elif mood:
            final_motion = self.get_motion_for_mood(mood)
        else:
            final_motion = self.get_motion_for_mood(self.current_mood)

        if not final_motion:
            final_motion = self.config.get("default_motion", "idle_01")

        # 执行回调
        for callback in self._motion_callbacks:
            try:
                callback(final_motion)
            except Exception as e:
                logger.error(f"动作回调失败: {e}")

        logger.info(f"Playing motion: {final_motion} (mood: {self.current_mood})")
        return final_motion

    def play_idle(self) -> str:
        """播放空闲动作"""
        motions = self.config.get("idle_motions", ["idle_01"])
        motion = random.choice(motions) if motions else "idle_01"
        return self.play_motion(motion_id=motion)

    def get_available_motions(self) -> List[str]:
        """获取所有可用动作
        
        优先级:
        1. 从模型配置文件动态读取（最准确）
        2. 从配置文件的 available_motions 字段读取
        3. 从心情/意图动作中收集
        """
        # 优先从模型文件读取
        model_motions = self._get_model_motions()
        if model_motions:
            return model_motions
        
        # 使用配置中明确定义的动作列表
        if "available_motions" in self.config:
            return self.config["available_motions"]
        
        # 兼容旧配置：从各处收集
        all_motions = set()

        # 从心情动作中收集
        for motions in self.config.get("mood_motions", {}).values():
            all_motions.update(motions)

        # 从意图动作中收集
        for motions in self.config.get("intent_motions", {}).values():
            all_motions.update(motions)

        # 从空闲动作中收集
        all_motions.update(self.config.get("idle_motions", []))

        return sorted(list(all_motions)) if all_motions else ["idle"]

    def _get_model_motions(self) -> Optional[List[str]]:
        """从模型配置文件读取动作列表"""
        if self._model_motions_cache is not None:
            return self._model_motions_cache
        
        try:
            config = get_config()
            model_path = resolve_path(config.live2d.model_path)
            
            if not model_path.exists():
                logger.warning(f"模型路径不存在: {model_path}")
                return None
            
            # 查找 .model3.json 文件
            model3_files = list(model_path.glob("*.model3.json"))
            if not model3_files:
                logger.warning(f"未找到模型配置文件: {model_path}")
                return None
            
            model_json_path = model3_files[0]
            
            with open(model_json_path, 'r', encoding='utf-8') as f:
                model_config = json.load(f)
            
            motions_config = model_config.get("FileReferences", {}).get("Motions", {})
            motion_names = []
            
            for group_name, motion_list in motions_config.items():
                for motion_entry in motion_list:
                    file_path = motion_entry.get("File", "")
                    if file_path:
                        motion_name = Path(file_path).stem
                        if motion_name.endswith(".motion3"):
                            motion_name = motion_name[:-8]
                        motion_names.append(motion_name)
            
            self._model_motions_cache = motion_names
            logger.info(f"从模型读取到 {len(motion_names)} 个动作: {motion_names}")
            return motion_names
            
        except Exception as e:
            logger.error(f"读取模型动作失败: {e}", exc_info=True)
            return None

    def clear_motions_cache(self):
        """清除动作缓存（切换模型时调用）"""
        self._model_motions_cache = None

    def get_available_moods(self) -> List[str]:
        """获取所有可用心情"""
        return sorted(list(self.config.get("mood_motions", {}).keys()))

