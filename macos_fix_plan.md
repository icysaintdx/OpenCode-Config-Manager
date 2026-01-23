# macOS 启动失败修复方案

## 问题分析

### 用户报告的问题
- **硬件**: M4 芯片 (Apple Silicon)
- **系统**: macOS 15.5
- **症状**:
  - DMG版本: 图标在Dock中弹跳两次后消失
  - ZIP版本: 提示需要外部应用权限,然后无反应

### 根本原因分析

#### 1. 代码签名问题 (最可能)
- macOS 15.5 的 Gatekeeper 更严格
- 当前构建使用 `--sign -` (临时签名),在 macOS 15+ 可能被拒绝
- 需要使用 `ad-hoc` 签名或正式的开发者证书

#### 2. Apple Silicon 兼容性
- 当前构建在 `macos-latest` (可能是 Intel 或 Universal)
- M4 芯片需要 ARM64 原生支持
- PyQt5 和 qfluentwidgets 需要正确的 ARM64 构建

#### 3. 权限问题
- macOS 15.5 对未公证的应用限制更严
- 需要添加 `com.apple.security.cs.allow-unsigned-executable-memory` 权限
- 需要添加 `com.apple.security.cs.disable-library-validation` 权限

#### 4. 依赖库问题
- PyQt5 在 Apple Silicon 上可能缺少某些动态库
- qfluentwidgets 从源码安装可能不完整

## 修复方案

### 方案 1: 改进代码签名 (立即可行)

#### 1.1 使用 ad-hoc 签名替代临时签名
```bash
# 当前 (第165-173行)
codesign --force --deep --options runtime --sign - dist/OCCM.app

# 修复后
codesign --force --deep --sign - --entitlements entitlements.plist dist/OCCM.app
```

#### 1.2 创建 entitlements.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- 允许未签名的可执行内存 (PyQt5 需要) -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <!-- 禁用库验证 (允许加载第三方库) -->
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <!-- 允许 JIT 编译 (Python 需要) -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <!-- 允许 DYLD 环境变量 -->
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
</dict>
</plist>
```

### 方案 2: 优化 PyInstaller 配置

#### 2.1 添加 macOS 特定的 spec 文件
创建 `opencode_config_manager_macos.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['opencode_config_manager_fluent.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'qfluentwidgets',
        'qfluentwidgets.widgets',
        'qfluentwidgets.components',
        'qfluentwidgets.common',
        'qfluentwidgets.window',
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5.QtBluetooth',
        'PyQt5.QtNfc',
        'PyQt5.QtPositioning',
        'PyQt5.QtGamepad',
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
    [],
    exclude_binaries=True,
    name='OCCM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # 强制 ARM64
    codesign_identity='-',  # ad-hoc 签名
    entitlements_file='entitlements.plist',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name='OCCM',
)

app = BUNDLE(
    coll,
    name='OCCM.app',
    icon='assets/icon.icns',
    bundle_identifier='com.icysaint.occm',
    version='1.5.0',
    info_plist={
        'CFBundleName': 'OCCM',
        'CFBundleDisplayName': 'OpenCode Config Manager',
        'CFBundleShortVersionString': '1.5.0',
        'CFBundleVersion': '1.5.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSRequiresAquaSystemAppearance': False,
        'NSPrincipalClass': 'NSApplication',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
    },
)
```

### 方案 3: 添加启动诊断脚本

创建 `diagnose_macos.sh` 帮助用户诊断问题:

```bash
#!/bin/bash
# macOS 启动诊断脚本

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
file "$APP_PATH/Contents/MacOS/OCCM"

# 5. 检查系统架构
echo ""
echo "检查系统架构..."
uname -m

# 6. 尝试启动并捕获错误
echo ""
echo "尝试启动应用..."
echo "如果应用无法启动,请查看下方错误信息:"
echo ""
"$APP_PATH/Contents/MacOS/OCCM" 2>&1 &
APP_PID=$!

sleep 3

if ps -p $APP_PID > /dev/null; then
    echo "✓ 应用启动成功 (PID: $APP_PID)"
else
    echo "❌ 应用启动失败"
    echo ""
    echo "请查看系统日志获取详细错误:"
    echo "  log show --predicate 'process == \"OCCM\"' --last 1m"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
```

### 方案 4: 优化更新流程

#### 4.1 创建自动更新脚本 (包含在 DMG 中)

创建 `install_update.sh`:

```bash
#!/bin/bash
# OCCM 自动更新安装脚本

set -e

APP_NAME="OCCM.app"
INSTALL_DIR="/Applications"
OLD_APP="$INSTALL_DIR/$APP_NAME"
NEW_APP="$(dirname "$0")/$APP_NAME"

echo "=========================================="
echo "OCCM 安装/更新工具"
echo "=========================================="

# 检查是否有旧版本
if [ -d "$OLD_APP" ]; then
    echo "检测到已安装的版本"
    
    # 获取旧版本号
    OLD_VERSION=$(defaults read "$OLD_APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "未知")
    NEW_VERSION=$(defaults read "$NEW_APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "未知")
    
    echo "当前版本: $OLD_VERSION"
    echo "新版本: $NEW_VERSION"
    
    # 询问是否替换
    read -p "是否替换旧版本? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "正在备份旧版本..."
        mv "$OLD_APP" "$OLD_APP.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✓ 旧版本已备份"
    else
        echo "取消安装"
        exit 0
    fi
fi

# 复制新版本
echo "正在安装新版本..."
cp -R "$NEW_APP" "$INSTALL_DIR/"

# 移除隔离属性
echo "正在移除隔离属性..."
xattr -dr com.apple.quarantine "$OLD_APP"

echo ""
echo "✓ 安装完成!"
echo ""
echo "您现在可以从启动台或应用程序文件夹启动 OCCM"
echo "=========================================="
```

#### 4.2 修改 DMG 创建流程

在 `build.yml` 第175-193行修改:

```yaml
- name: 6. 打包 DMG 镜像 (包含自动安装脚本)
  run: |
    # 创建临时目录
    mkdir -p dmg_contents
    
    # 复制 .app
    cp -R "dist/OCCM_${{ env.TAG_NAME }}.app" dmg_contents/
    
    # 创建安装脚本
    cat > dmg_contents/安装.command << 'EOF'
    #!/bin/bash
    cd "$(dirname "$0")"
    ./install_update.sh
    EOF
    chmod +x dmg_contents/安装.command
    
    # 复制安装脚本
    cp install_update.sh dmg_contents/
    chmod +x dmg_contents/install_update.sh
    
    # 创建 README
    cat > dmg_contents/README.txt << 'EOF'
    OCCM - OpenCode Config Manager
    
    安装方法:
    1. 双击"安装.command"自动安装 (推荐)
    2. 或手动拖拽 OCCM.app 到应用程序文件夹
    
    如果遇到"应用已损坏"错误:
    1. 打开终端
    2. 运行: xattr -cr /Applications/OCCM.app
    3. 重新启动应用
    
    更多帮助: https://github.com/icysaintdx/OpenCode-Config-Manager
    EOF
    
    # 生成 DMG
    create-dmg \
      --volname "OCCM ${{ env.TAG_NAME }}" \
      --window-size 800 500 \
      --icon-size 100 \
      --icon "OCCM_${{ env.TAG_NAME }}.app" 200 200 \
      --app-drop-link 600 200 \
      --hide-extension "OCCM_${{ env.TAG_NAME }}.app" \
      --volicon "assets/icon.icns" \
      --no-internet-enable \
      "dist/OCCM_${{ env.TAG_NAME }}.dmg" \
      "dmg_contents/"
  shell: /bin/bash -e {0}
```

### 方案 5: 添加崩溃日志收集

在主程序中添加 macOS 特定的错误处理:

```python
# 在 opencode_config_manager_fluent.py 开头添加

import sys
import platform
import traceback
from pathlib import Path

def setup_macos_crash_handler():
    """设置 macOS 崩溃处理器"""
    if platform.system() != "Darwin":
        return
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        """捕获未处理的异常"""
        # 写入崩溃日志
        crash_log_dir = Path.home() / "Library" / "Logs" / "OCCM"
        crash_log_dir.mkdir(parents=True, exist_ok=True)
        
        crash_log_file = crash_log_dir / f"crash_{int(time.time())}.log"
        
        with open(crash_log_file, "w", encoding="utf-8") as f:
            f.write(f"OCCM Crash Report\n")
            f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {platform.platform()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Architecture: {platform.machine()}\n")
            f.write(f"\nException:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        
        # 显示错误对话框
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "OCCM 崩溃",
                f"应用程序遇到错误并需要关闭。\n\n"
                f"错误日志已保存到:\n{crash_log_file}\n\n"
                f"请将此日志文件发送给开发者以帮助修复问题。"
            )
        except:
            pass
        
        # 调用默认处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_handler

# 在 main() 函数开头调用
if __name__ == "__main__":
    setup_macos_crash_handler()
    # ... 原有代码
```

## 实施步骤

### 立即可行的修复 (无需 macOS 设备)

1. **创建 entitlements.plist**
2. **修改 build.yml 的签名步骤**
3. **添加诊断脚本和安装脚本**
4. **添加崩溃日志收集代码**

### 需要 macOS 设备测试的修复

1. **创建并测试 .spec 文件**
2. **验证 ARM64 构建**
3. **测试自动更新流程**

## 用户临时解决方案

在修复版本发布前,用户可以尝试:

```bash
# 方法 1: 移除隔离属性
xattr -cr /Applications/OCCM.app

# 方法 2: 允许任何来源的应用 (macOS 15.5)
sudo spctl --master-disable

# 方法 3: 手动添加到允许列表
sudo spctl --add /Applications/OCCM.app

# 方法 4: 查看崩溃日志
log show --predicate 'process == "OCCM"' --last 1h
```

## 预期效果

修复后:
- ✅ M4 芯片原生支持
- ✅ macOS 15.5 正常启动
- ✅ DMG 安装自动替换旧版本
- ✅ 详细的错误日志便于调试
- ✅ 用户友好的诊断工具
