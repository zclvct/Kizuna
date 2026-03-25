@echo off
chcp 65001 >nul
REM Kizuna - Windows 自动打包脚本
REM 使用方法: build_win.bat [--clean]

setlocal EnableDelayedExpansion

echo ================================
echo   Kizuna - Windows 打包脚本
echo ================================

REM 项目根目录
cd /d "%~dp0"
set PROJECT_ROOT=%cd%

REM 解析参数
set CLEAN=false
:parse_args
if "%~1"=="" goto :end_parse
if /i "%~1"=="--clean" set CLEAN=true
shift
goto :parse_args
:end_parse

REM 清理旧的构建文件
if "%CLEAN%"=="true" (
    echo 清理旧的构建文件...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    echo 清理完成
)

REM 检查 Python
echo 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM 检查 PyInstaller
echo 检查 PyInstaller...
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 未安装，正在安装...
    pip install pyinstaller
)

REM 创建 .ico 图标（如果 ImageMagick 可用）
echo 检查图标文件...
set ICON_SRC=%PROJECT_ROOT%\assets\images\AI助手.png
set ICON_ICO=%PROJECT_ROOT%\assets\images\icon.ico

if exist "%ICON_SRC%" (
    if not exist "%ICON_ICO%" (
        echo 尝试创建 ico 图标...
        REM 尝试使用 magick (ImageMagick)
        magick --version >nul 2>&1
        if not errorlevel 1 (
            magick convert "%ICON_SRC%" -define icon:auto-resize=256,128,64,48,32,16 "%ICON_ICO%"
            echo 图标创建完成: %ICON_ICO%
        ) else (
            echo [提示] ImageMagick 未安装，跳过图标创建
            echo        可以手动将 PNG 转换为 ICO 格式
        )
    ) else (
        echo 图标文件已存在: %ICON_ICO%
    )
) else (
    echo [警告] 源图标文件不存在: %ICON_SRC%
)

REM 更新 spec 文件中的图标路径
if exist "%ICON_ICO%" (
    powershell -Command "(gc kizuna.spec) -replace 'icon=None', 'icon=r\"%ICON_ICO:\=\\%\"' | Out-File -encoding UTF8 kizuna.spec.tmp"
    move /y kizuna.spec.tmp kizuna.spec >nul
)

REM 执行打包
echo 开始打包...
pyinstaller kizuna.spec --noconfirm

REM 检查打包结果
set APP_PATH=%PROJECT_ROOT%\dist\Kizuna
if exist "%APP_PATH%" (
    echo.
    echo ================================
    echo   打包成功！
    echo ================================
    
    REM 显示应用大小
    for /f "tokens=3" %%a in ('dir /s /-c "%APP_PATH%" ^| findstr /c:"个文件"') do set SIZE=%%a
    echo 应用位置: %APP_PATH%
    echo 文件大小: !SIZE! 字节
    
    REM 创建 ZIP 压缩包
    echo.
    echo 创建 ZIP 压缩包...
    set ZIP_PATH=%PROJECT_ROOT%\dist\Kizuna_Windows.zip
    powershell -Command "Compress-Archive -Path '%APP_PATH%' -DestinationPath '%ZIP_PATH%' -Force"
    echo ZIP 创建完成: %ZIP_PATH%
    
    echo.
    echo [提示] 可以将 dist\Kizuna 文件夹分发，或使用安装包制作工具
    echo        推荐工具: Inno Setup, NSIS, WiX Toolset
    echo.
) else (
    echo.
    echo ================================
    echo   打包失败！
    echo ================================
    echo 请检查上方错误信息
)

pause
