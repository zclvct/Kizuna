#!/usr/bin/env python3
"""
AI Friend - 二次元桌面助手
主入口文件 - 完整整合版
"""
import sys
import asyncio
from pathlib import Path

# 添加 src 到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# 直接导入模块，避免相对导入问题
import utils
import app
import assistant
import scheduler


async def start_task_manager():
    """启动任务管理器"""
    task_manager = scheduler.get_task_manager()
    await task_manager.start()
    return task_manager


def setup_task_callbacks(window, task_manager):
    """设置任务回调"""
    async def on_task_execute(task):
        """任务执行回调"""
        # 在主线程中更新 UI
        if task.motion_id:
            window.live2d_widget.play_motion(task.motion_id)
        else:
            window.live2d_widget.update_mood("happy")

        # 如果对话窗口可见，显示消息
        if window._chat_visible:
            window.chat_widget._add_message_bubble(
                f"📋 定时任务: {task.task_name}\n\n{task.action_prompt}",
                is_user=False
            )

    task_manager.set_task_executor(on_task_execute)


def main():
    """主函数"""
    # 初始化日志
    logger = utils.setup_logger()
    logger.info("=" * 50)
    logger.info("AI Friend - 二次元桌面助手")
    logger.info("=" * 50)

    try:
        # 加载配置
        config = utils.get_config()
        logger.info(f"LLM Provider: {config.llm.provider}")
        logger.info(f"LLM Model: {config.llm.model}")

        # 加载角色设定
        char_manager = utils.get_character_manager()
        is_first_run = char_manager.persona.is_first_run()
        logger.info(f"First run: {is_first_run}")

        # 初始化助手工具
        tool_registry = assistant.get_tool_registry()
        logger.info(f"已注册 {len(tool_registry.tools)} 个工具")

        # 创建应用
        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("AI Friend")
        qt_app.setQuitOnLastWindowClosed(False)

        # 创建主窗口
        window = app.MainWindow()
        window.show()
        logger.info("主窗口已显示")

        # 创建系统托盘
        try:
            tray = app.TrayIcon()
            tray.show()

            # 连接托盘信号
            tray.toggle_window.connect(window.setVisible)
            tray.open_settings.connect(window._open_settings)
            tray.quit_app.connect(qt_app.quit)
            logger.info("系统托盘已创建")
        except Exception as e:
            logger.warning(f"系统托盘创建失败: {e}，继续运行")

        # 启动任务管理器（异步）
        task_manager = scheduler.get_task_manager()

        # 使用 QTimer 延迟启动异步任务
        def start_async_tasks():
            """启动异步任务"""
            try:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    asyncio.create_task(task_manager.start())
                else:
                    # 在单独线程中运行事件循环
                    import threading
                    def run_loop():
                        loop.run_forever()

                    thread = threading.Thread(target=run_loop, daemon=True)
                    thread.start()
                    asyncio.run_coroutine_threadsafe(task_manager.start(), loop)

                setup_task_callbacks(window, task_manager)
                logger.info("任务管理器已启动")
            except Exception as e:
                logger.error(f"任务管理器启动失败: {e}")

        QTimer.singleShot(500, start_async_tasks)

        if is_first_run:
            logger.info("第一次运行，显示问候")
            # 第一次运行时自动打开对话窗口
            QTimer.singleShot(1000, window._toggle_chat)

        logger.info("应用启动完成")

        return qt_app.exec()

    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        # 尝试显示错误对话框
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "启动失败",
                f"应用启动失败:\n\n{str(e)}\n\n请检查日志文件了解详情。"
            )
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())

