#!/usr/bin/env python3
"""
AI Friend - 二次元桌面助手
直接运行入口文件 (避免相对导入问题)
"""
import sys
from pathlib import Path

# 获取项目根目录（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    project_root = Path(sys._MEIPASS)
else:
    # 正常开发环境
    project_root = Path(__file__).parent

# 添加 src 到路径
sys.path.insert(0, str(project_root / "src"))

# 导入并运行真正的 main 函数
from main import main

if __name__ == "__main__":
    sys.exit(main())
