# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置文件

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
project_root = Path(SPECPATH)

# 收集所有数据文件
datas = [
    ('assets', 'assets'),
    ('data', 'data'),
]

# 收集 live2d-py 包（包含动态库）
try:
    import live2d
    live2d_path = Path(live2d.__file__).parent
    datas.append((str(live2d_path), 'live2d'))
    print(f"Added live2d package to datas: {live2d_path}")
except ImportError:
    print("Warning: live2d not found")

# 收集 live2d-py 动态库（备用）
binaries = []
try:
    import live2d
    live2d_path = Path(live2d.__file__).parent
    print(f"live2d module path: {live2d_path}")
    # 收集 live2d 的所有动态库
    for f in live2d_path.rglob('*'):
        if f.suffix in ['.so', '.dylib', '.pyd', '.dll']:
            # 保持相对路径结构
            rel_path = f.relative_to(live2d_path)
            binaries.append((str(f), str(live2d_path.name / rel_path.parent)))
            print(f"Found live2d binary: {f} -> {rel_path}")
except ImportError:
    print("Warning: live2d not found, skipping binary collection")
except Exception as e:
    print(f"Warning: Error collecting live2d binaries: {e}")

# 隐式导入（PyInstaller 无法自动检测的模块）
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'OpenGL',
    'OpenGL.GL',
    'live2d',
    'live2d.v3',
    'live2d.v4',
    'langchain',
    'langchain_core',
    'langchain_community',
    'langchain_openai',
    'langchain_ollama',
    'langchain_mcp_adapters',
    'apscheduler',
    'apscheduler.schedulers.background',
    'apscheduler.triggers.cron',
    'apscheduler.triggers.interval',
    'pydantic',
    'pydantic_settings',
    'requests',
    'psutil',
    'pyperclip',
    'dotenv',
]

# macOS 特定导入
if sys.platform == 'darwin':
    hiddenimports.extend([
        'objc',
        'Foundation',
        'AppKit',
        'Cocoa',
    ])

# Windows 特定导入  
if sys.platform == 'win32':
    hiddenimports.extend([
        'pywin32',
        'win32api',
        'win32con',
    ])

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy.f2py',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Kizuna',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可设置图标路径
)

# macOS 应用包配置
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Kizuna.app',
        icon=None,  # 可设置 .icns 图标路径
        bundle_identifier='com.kizuna.desktop',
        version='1.0.0',
        info_plist={
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2024 Kizuna',
        },
    )
