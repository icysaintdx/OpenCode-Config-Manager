#!/bin/bash
# OCCM macOS 启动诊断脚本

echo "=========================================="
echo "OCCM macOS 启动诊断工具"
echo "=========================================="

APP_PATH="/Applications/OCCM.app"

# 1. 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "❌ 应用未安装在 /Applications/"
    echo "请将 OCCM.app 拖入应用程序文件夹"
    exit 1
fi

echo "✓ 应用已安装"

# 2. 检查隔离属性
echo ""
echo "检查隔离属性..."
QUARANTINE=$(xattr -l "$APP_PATH" | grep com.apple.quarantine)
if [ -n "$QUARANTINE" ]; then
    echo "⚠️  检测到隔离属性"
    echo "正在移除..."
    xattr -dr com.apple.quarantine "$APP_PATH"
    echo "✓ 隔离属性已移除"
else
    echo "✓ 无隔离属性"
fi

# 3. 检查代码签名
echo ""
echo "检查代码签名..."
codesign -vvv "$APP_PATH" 2>&1 | head -5

# 4. 检查架构
echo ""
echo "检查应用架构..."
file "$APP_PATH/Contents/MacOS"/*

# 5. 检查系统架构
echo ""
echo "检查系统架构..."
echo "CPU: $(uname -m)"
echo "macOS: $(sw_vers -productVersion)"

# 6. 尝试启动并捕获错误
echo ""
echo "尝试启动应用..."
echo "如果应用无法启动,请查看下方错误信息:"
echo ""
"$APP_PATH/Contents/MacOS"/* 2>&1 &
APP_PID=$!

sleep 3

if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✓ 应用启动成功 (PID: $APP_PID)"
else
    echo "❌ 应用启动失败"
    echo ""
    echo "请查看系统日志获取详细错误:"
    echo "  log show --predicate 'process == \"OCCM\"' --last 1m"
    echo ""
    echo "或查看崩溃日志:"
    echo "  ~/Library/Logs/OCCM/"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
