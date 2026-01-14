#!/bin/bash
# ============================================================
# OpenCode Config Manager - Unix Build Script (Linux + macOS)
# v1.0.5 Fluent (PyQt5 + QFluentWidgets)
# ============================================================
# 
# 使用方法:
#   Linux (无头服务器): xvfb-run ./build_unix.sh
#   Linux (有显示器):   ./build_unix.sh
#   macOS:              ./build_unix.sh
#
# 依赖:
#   - Python 3.8+
#   - PyQt5, PyQt5-Fluent-Widgets, PyInstaller
#   - Linux 无头服务器需要: xvfb
#
# ============================================================

set -e

VERSION="1.0.5"
MAIN_SCRIPT="opencode_config_manager_fluent.py"

echo "========================================"
echo "  OpenCode Config Manager - Unix Build"
echo "  v${VERSION} Fluent (PyQt5 + QFluentWidgets)"
echo "========================================"
echo ""

# ==================== 平台检测 ====================
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=macos;;
    *)          PLATFORM=unknown;;
esac

echo "[INFO] Detected platform: ${PLATFORM}"

if [ "${PLATFORM}" = "unknown" ]; then
    echo "[ERROR] Unsupported platform: ${OS}"
    exit 1
fi

# ==================== Python 检测 ====================
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[INFO] Python version: ${PYTHON_VERSION}"

# 检查 Python 版本 >= 3.8
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "${PYTHON_MAJOR}" -lt 3 ] || ([ "${PYTHON_MAJOR}" -eq 3 ] && [ "${PYTHON_MINOR}" -lt 8 ]); then
    echo "[ERROR] Python 3.8+ required, found ${PYTHON_VERSION}"
    exit 1
fi

# ==================== 依赖安装 ====================
echo "[INFO] Checking dependencies..."

# 检测是否在虚拟环境中
if [ -n "${VIRTUAL_ENV}" ]; then
    PIP_CMD="pip"
else
    PIP_CMD="pip3"
fi

# PyQt5
if ! python3 -c "import PyQt5" &> /dev/null; then
    echo "[INFO] Installing PyQt5..."
    ${PIP_CMD} install PyQt5
fi

# QFluentWidgets
if ! python3 -c "import qfluentwidgets" &> /dev/null; then
    echo "[INFO] Installing PyQt5-Fluent-Widgets..."
    ${PIP_CMD} install PyQt5-Fluent-Widgets
fi

# PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "[INFO] Installing PyInstaller..."
    ${PIP_CMD} install pyinstaller
fi

# ==================== Linux 特殊处理 ====================
if [ "${PLATFORM}" = "linux" ]; then
    # 检测是否有显示器
    if [ -z "${DISPLAY}" ]; then
        echo "[WARN] No display detected (headless server)"
        echo "[INFO] Please run with: xvfb-run ./build_unix.sh"
        
        # 检查是否已经在 xvfb-run 下运行
        if [ -z "${XVFB_RUN}" ]; then
            # 检查 xvfb 是否可用
            if command -v xvfb-run &> /dev/null; then
                echo "[INFO] Auto-starting with xvfb-run..."
                export XVFB_RUN=1
                exec xvfb-run -a "$0" "$@"
            else
                echo "[ERROR] xvfb not found. Install with: sudo apt install xvfb"
                exit 1
            fi
        fi
    fi
fi

# ==================== 清理旧构建 ====================
echo "[INFO] Cleaning previous build..."
rm -rf dist build *.spec

# ==================== 构建 ====================
echo "[INFO] Building executable..."
echo "[INFO] This may take a few minutes..."

# 通用 PyInstaller 参数
COMMON_ARGS=(
    --onefile
    --windowed
    --name "OpenCodeConfigManager_v${VERSION}"
    --add-data "assets:assets"
    --collect-data qfluentwidgets
    --collect-submodules qfluentwidgets
    --hidden-import qfluentwidgets
    --hidden-import qfluentwidgets.components
    --hidden-import qfluentwidgets.common
    --hidden-import qfluentwidgets.window
    --exclude-module torch
    --exclude-module tensorflow
    --exclude-module scipy
    --exclude-module matplotlib
    --exclude-module pandas
    --exclude-module numpy
    --exclude-module IPython
    --exclude-module jupyter
    --exclude-module tkinter
)

if [ "${PLATFORM}" = "macos" ]; then
    # macOS: 创建 .app bundle
    pyinstaller "${COMMON_ARGS[@]}" \
        --osx-bundle-identifier "com.opencode.configmanager" \
        --icon "assets/icon.png" \
        "${MAIN_SCRIPT}"

    # 可选: 创建 DMG
    if command -v create-dmg &> /dev/null; then
        echo "[INFO] Creating DMG..."
        create-dmg \
            --volname "OpenCode Config Manager" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --app-drop-link 450 185 \
            "dist/OpenCodeConfigManager_v${VERSION}.dmg" \
            "dist/OpenCodeConfigManager_v${VERSION}.app" 2>/dev/null || true
    fi
    
    OUTPUT_FILE="dist/OpenCodeConfigManager_v${VERSION}.app"
else
    # Linux
    pyinstaller "${COMMON_ARGS[@]}" "${MAIN_SCRIPT}"
    OUTPUT_FILE="dist/OpenCodeConfigManager_v${VERSION}"
fi

# ==================== 构建完成 ====================
echo ""
echo "========================================"
echo "  Build completed successfully!"
echo "========================================"
echo ""
echo "  Platform: ${PLATFORM}"
echo "  Output:   ${OUTPUT_FILE}"
echo ""

# 显示文件大小
if [ -f "${OUTPUT_FILE}" ]; then
    SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)
    echo "  Size:     ${SIZE}"
elif [ -d "${OUTPUT_FILE}" ]; then
    SIZE=$(du -sh "${OUTPUT_FILE}" | cut -f1)
    echo "  Size:     ${SIZE}"
fi

echo ""
echo "========================================"
