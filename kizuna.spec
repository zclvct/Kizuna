# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置文件
# 使用 --onedir 模式（目录形式），启动更快

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
project_root = Path(SPECPATH)

# 图标路径
icon_path = project_root / 'assets' / 'images' / 'icon.icns'

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

# 排除不必要的模块以减小体积（关键优化！）
excludes = [
    # GUI 框架（只保留 PySide6）
    'tkinter',
    'PyQt5',
    'PyQt6',
    'PyQt4',
    'PySide',
    'PySide2',
    
    # 数据科学（项目不需要）
    'matplotlib',
    'numpy.f2py',
    'scipy',
    'pandas',
    'statsmodels',
    'sympy',
    
    # 开发工具
    'pytest',
    'sphinx',
    'docutils',
    'IPython',
    'jupyter',
    'notebook',
    'jupyter_client',
    'jupyter_core',
    'nbconvert',
    'nbformat',
    
    # 网络相关 - 不排除核心模块，requests/urllib3/langchain 依赖它们
    # html.parser - langchain 用于解析 HTML
    # certifi - requests 用于 HTTPS 证书验证
    # charset_normalizer - requests 用于编码检测
    # idna - requests 用于国际化域名
    
    # 其他工具
    'tqdm',
    'PIL',
    'pillow',
    'cv2',
    'opencv',
    'sklearn',
    'torch',
    'tensorflow',
    'keras',
    
    # PySide6 不常用的模块
    'PySide6.QtBluetooth',
    'PySide6.QtCharts',
    'PySide6.QtDataVisualization',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtLocation',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtNfc',
    'PySide6.QtPositioning',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects',
    'PySide6.QtScript',
    'PySide6.QtScxml',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtSql',
    'PySide6.QtSvg',
    'PySide6.QtTest',
    'PySide6.QtTextToSpeech',
    'PySide6.QtWebChannel',
    'PySide6.QtWebEngine',
    'PySide6.QtWebSockets',
    'PySide6.QtXml',
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 使用目录模式（--onedir），启动更快
exe = EXE(
    pyz,
    a.scripts,
    [],  # 空列表，目录模式
    exclude_binaries=True,  # 排除二进制文件，目录模式必需
    name='Kizuna',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # macOS 上 UPX 可能导致问题，禁用
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path),
)

# 收集所有文件到目录
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # macOS 上 UPX 可能导致问题，禁用
    upx_exclude=[],
    name='Kizuna',
)

# macOS 应用包配置
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Kizuna.app',
        icon=str(icon_path),
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
