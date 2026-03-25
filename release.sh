#!/bin/bash
# 一键发布脚本 - 自动触发 GitHub Actions 跨平台打包
# 使用方法: ./release.sh [version]
# 示例: ./release.sh 1.0.0

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
cd "$(dirname "$0")"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Kizuna - 一键发布打包${NC}"
echo -e "${BLUE}================================${NC}"

# 检查是否在 git 仓库中
if [ ! -d ".git" ]; then
    echo -e "${RED}错误: 当前目录不是 git 仓库${NC}"
    echo -e "${YELLOW}请先初始化 git 并推送到 GitHub:${NC}"
    echo "  git init"
    echo "  git add ."
    echo "  git commit -m 'Initial commit'"
    echo "  git remote add origin https://github.com/你的用户名/Kizuna.git"
    echo "  git push -u origin main"
    exit 1
fi

# 检查是否有远程仓库
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo -e "${RED}错误: 未配置远程仓库${NC}"
    echo -e "${YELLOW}请先添加远程仓库:${NC}"
    echo "  git remote add origin https://github.com/你的用户名/Kizuna.git"
    exit 1
fi

# 获取版本号
if [ -z "$1" ]; then
    # 自动从 spec 文件或代码中获取版本号
    CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
    CURRENT_VERSION=${CURRENT_VERSION#v}
    
    echo -e "${YELLOW}当前版本: v${CURRENT_VERSION}${NC}"
    echo -n "请输入新版本号 (如 1.0.1): "
    read VERSION
else
    VERSION=$1
fi

# 验证版本号格式
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}错误: 版本号格式不正确，应为 x.x.x 格式${NC}"
    exit 1
fi

echo -e "${GREEN}版本号: v${VERSION}${NC}"

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}检测到未提交的更改，是否先提交? (y/n)${NC}"
    read -r CONFIRM
    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
        git add .
        git commit -m "chore: prepare release v${VERSION}"
        echo -e "${GREEN}更改已提交${NC}"
    else
        echo -e "${RED}请先提交更改后再发布${NC}"
        exit 1
    fi
fi

# 推送到远程
echo -e "${BLUE}推送代码到 GitHub...${NC}"
git push origin main

# 创建并推送 tag
echo -e "${BLUE}创建 tag v${VERSION}...${NC}"
git tag -a "v${VERSION}" -m "Release v${VERSION}"
git push origin "v${VERSION}"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  发布已触发！${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "GitHub Actions 正在打包..."
echo -e "查看进度: ${BLUE}${REMOTE_URL%.git}/actions${NC}"
echo ""
echo -e "打包完成后，可在此下载:"
echo -e "${BLUE}${REMOTE_URL%.git}/releases/tag/v${VERSION}${NC}"
