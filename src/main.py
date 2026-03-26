#!/usr/bin/env python3
"""
AI Friend - 二次元桌面助手
主入口文件 - 完整整合版
"""
import sys
import asyncio
from pathlib import Path

# 添加 src 到路径（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    project_root = Path(sys._MEIPASS)
else:
    # 正常开发环境
    project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# macOS 上设置应用不在 Dock 中显示（必须在 QApplication 创建之前）
if sys.platform == 'darwin':
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        print("✅ macOS Dock 图标隐藏设置成功")
    except ImportError as e:
        print(f"⚠️ pyobjc 未安装，Dock 图标将显示: {e}")
    except Exception as e:
        print(f"⚠️ 设置 Dock 隐藏失败: {e}")


def main():
    """主函数"""
    # 延迟导入 utils，避免启动时加载过多模块
    import utils
    
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

        # 创建应用（先创建 Qt 应用，尽快显示窗口）
        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("AI Friend")
        qt_app.setQuitOnLastWindowClosed(False)

        # macOS: 在 QApplication 创建后再次设置 Dock 隐藏（Qt 可能会重置）
        if sys.platform == 'darwin':
            try:
                from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
                NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
                print("✅ macOS Dock 图标隐藏已再次确认")
            except Exception as e:
                print(f"⚠️ 再次设置 Dock 隐藏失败: {e}")

        # 延迟导入 UI 模块
        import app
        
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
            # 托盘退出时先调用窗口关闭方法，确保配置保存
            tray.quit_app.connect(window._close_all)
            logger.info("系统托盘已创建")
        except Exception as e:
            logger.warning(f"系统托盘创建失败: {e}，继续运行")

        # 延迟初始化 Agent（在窗口显示后）
        def init_agent():
            """延迟初始化 Agent"""
            try:
                from agent import get_core
                from chat import get_conversation_manager
                
                core = get_core()
                logger.info(f"LangChain Agent 已初始化，工具数: {len(core.get_enabled_tool_names())}")

                # 清空对话历史（每次启动重新开始）
                conversation_manager = get_conversation_manager()
                conversation_manager.clear()
                logger.info("对话历史已清空")
                
                # 初始化 MCP 工具
                async def init_mcp():
                    try:
                        await core.initialize_mcp_tools()
                        logger.info("MCP 工具已初始化")
                    except Exception as e:
                        logger.warning(f"MCP 工具初始化失败: {e}")
                
                # 启动 MCP 初始化
                import threading
                loop = asyncio.new_event_loop()
                
                def run_loop():
                    asyncio.set_event_loop(loop)
                    loop.run_forever()
                
                thread = threading.Thread(target=run_loop, daemon=True)
                thread.start()
                
                asyncio.run_coroutine_threadsafe(init_mcp(), loop)
                
            except Exception as e:
                logger.error(f"Agent 初始化失败: {e}", exc_info=True)

        # 延迟 300ms 初始化 Agent
        QTimer.singleShot(300, init_agent)

        # 延迟启动任务管理器
        def start_task_manager():
            """启动任务管理器"""
            try:
                import scheduler
                task_manager = scheduler.get_task_manager()

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    asyncio.create_task(task_manager.start())
                else:
                    import threading
                    def run_loop():
                        asyncio.set_event_loop(loop)
                        loop.run_forever()

                    thread = threading.Thread(target=run_loop, daemon=True)
                    thread.start()
                    asyncio.run_coroutine_threadsafe(task_manager.start(), loop)

                # 设置任务回调
                async def on_task_execute(task):
                    if task.motion_id:
                        window.live2d_widget.play_motion(task.motion_id)
                    else:
                        window.live2d_widget.update_mood("happy")

                    if window._chat_visible:
                        window.chat_widget._add_message_bubble(
                            f"📋 定时任务: {task.task_name}\n\n{task.action_prompt}",
                            is_user=False
                        )

                task_manager.set_task_executor(on_task_execute)
                logger.info("任务管理器已启动")
            except Exception as e:
                logger.error(f"任务管理器启动失败: {e}")

        QTimer.singleShot(500, start_task_manager)

        logger.info("应用启动完成")

        return qt_app.exec()

    except Exception as e:
        # 延迟导入 logger
        import utils
        logger = utils.get_logger()
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

