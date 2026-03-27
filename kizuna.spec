# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置文件
# 使用 --onedir 模式（目录形式），启动更快

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# 项目根目录
project_root = Path(SPECPATH)

# 图标路径（按平台选择，避免 Windows 使用 .icns 报错）
if sys.platform == 'darwin':
    icon_path = project_root / 'assets' / 'images' / 'icon.icns'
elif sys.platform == 'win32':
    icon_path = project_root / 'assets' / 'images' / 'icon.ico'
else:
    icon_path = None

if icon_path is not None and not icon_path.exists():
    print(f"Warning: icon file not found: {icon_path}, fallback to default icon")
    icon_path = None

# 收集所有数据文件
datas = [
    ('assets', 'assets'),
    ('data', 'data'),
]

# 收集 live2d-web 资源（WebEngine 方案）
try:
    live2d_web_path = project_root / 'assets' / 'live2d_web'
    if live2d_web_path.exists():
        datas.append((str(live2d_web_path), str(Path('assets') / 'live2d_web')))
        print(f"Added live2d_web assets: {live2d_web_path}")
    else:
        print("Warning: assets/live2d_web not found")
except Exception as e:
    print(f"Warning: Error collecting live2d_web assets: {e}")

# 显式收集 PySide6 动态库，避免 macOS 下 Qt 模块运行时缺失
binaries = collect_dynamic_libs('PySide6')

# 隐式导入（PyInstaller 无法自动检测的模块）
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebChannel',
    'PySide6.QtNetwork',
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
    icon=str(icon_path) if icon_path else None,
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
        icon=str(icon_path) if icon_path else None,
        bundle_identifier='com.kizuna.desktop',
        version='1.0.0',
        info_plist={
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13',
            'LSUIElement': True,
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2024 Kizuna',
        },
    )
