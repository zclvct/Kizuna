#!/bin/bash
# Kizuna - macOS 自动打包脚本
# 使用方法: ./build_mac.sh [--clean] [--sign]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Kizuna - macOS 打包脚本${NC}"
echo -e "${BLUE}================================${NC}"

# 解析参数
CLEAN=false
SIGN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --sign)
            SIGN=true
            shift
            ;;
        *)
            echo -e "${YELLOW}未知参数: $1${NC}"
            shift
            ;;
    esac
done

# 清理旧的构建文件
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}清理旧的构建文件...${NC}"
    rm -rf build dist
    echo -e "${GREEN}清理完成${NC}"
fi

# 检查 PyInstaller
echo -e "${BLUE}检查依赖...${NC}"
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${YELLOW}PyInstaller 未安装，正在安装...${NC}"
    pip install pyinstaller
fi

# 创建 .icns 图标
echo -e "${BLUE}创建应用图标...${NC}"
ICON_SRC="$PROJECT_ROOT/assets/images/AI助手.png"
ICON_ICNS="$PROJECT_ROOT/assets/images/icon.icns"

if [ -f "$ICON_SRC" ]; then
    # 创建临时目录存放 iconset
    ICONSET_DIR="$PROJECT_ROOT/assets/images/icon.iconset"
    mkdir -p "$ICONSET_DIR"
    
    # 生成各种尺寸的图标
    sips -z 16 16     "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16.png"
    sips -z 32 32     "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16@2x.png"
    sips -z 32 32     "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32.png"
    sips -z 64 64     "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32@2x.png"
    sips -z 128 128   "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128.png"
    sips -z 256 256   "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128@2x.png"
    sips -z 256 256   "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256.png"
    sips -z 512 512   "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256@2x.png"
    sips -z 512 512   "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512.png"
    sips -z 1024 1024 "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512@2x.png"
    
    # 转换为 icns
    iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"
    rm -rf "$ICONSET_DIR"
    
    echo -e "${GREEN}图标创建完成: $ICON_ICNS${NC}"
else
    echo -e "${YELLOW}源图标文件不存在: $ICON_SRC${NC}"
fi

# 更新 spec 文件中的图标路径
if [ -f "$ICON_ICNS" ]; then
    sed -i '' "s|icon=None|icon='$ICON_ICNS'|g" "$PROJECT_ROOT/kizuna.spec"
fi

# 执行打包
echo -e "${BLUE}开始打包...${NC}"
pyinstaller kizuna.spec --noconfirm

# 检查打包结果
APP_PATH="$PROJECT_ROOT/dist/Kizuna.app"
if [ -d "$APP_PATH" ]; then
    echo -e "${GREEN}打包成功: $APP_PATH${NC}"
    
    # 移除隔离属性（解决"无法验证开发者"问题）
    echo -e "${BLUE}移除隔离属性...${NC}"
    xattr -cr "$APP_PATH"
    
    # 代码签名（可选）
    if [ "$SIGN" = true ]; then
        echo -e "${BLUE}进行代码签名...${NC}"
        # 获取签名身份
        SIGN_IDENTITY=$(security find-identity -v -p codesigning | head -n 1 | awk -F'"' '{print $2}')
        if [ -n "$SIGN_IDENTITY" ]; then
            codesign --deep --force --verify --verbose --sign "$SIGN_IDENTITY" "$APP_PATH"
            echo -e "${GREEN}签名完成: $SIGN_IDENTITY${NC}"
        else
            echo -e "${YELLOW}未找到代码签名证书，跳过签名${NC}"
        fi
    fi
    
    # 显示应用大小
    APP_SIZE=$(du -sh "$APP_PATH" | awk '{print $1}')
    echo -e "${GREEN}应用大小: $APP_SIZE${NC}"
    
    # 分析体积占用
    echo -e "${BLUE}分析应用体积...${NC}"
    echo -e "${YELLOW}主要模块大小:${NC}"
    du -sh "$APP_PATH/Contents/MacOS/Kizuna"/*.pyd 2>/dev/null | sort -hr | head -5
    du -sh "$APP_PATH/Contents/MacOS/Kizuna"/PySide6 2>/dev/null
    du -sh "$APP_PATH/Contents/MacOS/Kizuna"/langchain* 2>/dev/null
    
    # 创建 DMG（可选）
    echo -e "${BLUE}创建 DMG 安装包...${NC}"
    DMG_PATH="$PROJECT_ROOT/dist/Kizuna.dmg"
    hdiutil create -volname "Kizuna" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
    DMG_SIZE=$(du -sh "$DMG_PATH" | awk '{print $1}')
    echo -e "${GREEN}DMG 创建完成: $DMG_PATH ($DMG_SIZE)${NC}"
    
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  打包完成！${NC}"
    echo -e "${GREEN}================================${NC}"
    echo -e "应用位置: ${BLUE}$APP_PATH${NC}"
    echo -e "安装包: ${BLUE}$DMG_PATH${NC}"
else
    echo -e "${RED}打包失败！${NC}"
    exit 1
fi
