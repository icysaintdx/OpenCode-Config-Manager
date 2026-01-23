# macOS 构建脚本验证清单

## 检查日期
2026-01-23

## 新增文件验证

### 1. entitlements.plist ✅
- **位置**: 项目根目录
- **Git 状态**: 已跟踪
- **构建脚本引用**: 第170行
  ```yaml
  codesign --force --deep --sign - --entitlements entitlements.plist dist/OCCM.app
  ```
- **验证**: ✅ 文件存在，构建时会被使用

### 2. install_update.sh ✅
- **位置**: 项目根目录
- **Git 状态**: 已跟踪
- **构建脚本引用**: 第195-196行
  ```yaml
  cp install_update.sh dmg_contents/
  chmod +x dmg_contents/install_update.sh
  ```
- **验证**: ✅ 文件存在，会被复制到 DMG 中

### 3. diagnose_macos.sh ✅
- **位置**: 项目根目录
- **Git 状态**: 已跟踪
- **构建脚本引用**: 第199-200行
  ```yaml
  cp diagnose_macos.sh dmg_contents/
  chmod +x dmg_contents/diagnose_macos.sh
  ```
- **验证**: ✅ 文件存在，会被复制到 DMG 中

## 构建流程验证

### macOS 构建步骤 (build-macos job)

#### 步骤 1-4: 环境准备 ✅
- 拉取源码 (包含所有新文件)
- 配置 Python 3.10
- 安装依赖
- PyInstaller 打包

#### 步骤 5: 代码签名 ✅
```yaml
# 使用 entitlements.plist 进行签名
codesign --force --deep --sign - --entitlements entitlements.plist dist/OCCM.app
```
- **依赖文件**: `entitlements.plist`
- **状态**: ✅ 文件已提交，构建时可用

#### 步骤 6: 打包 DMG ✅
```yaml
# 创建 DMG 内容目录
mkdir -p dmg_contents

# 复制 .app
cp -R "dist/OCCM.app" dmg_contents/

# 创建安装脚本启动器
cat > dmg_contents/安装.command << 'EOFINSTALL'
#!/bin/bash
cd "$(dirname "$0")"
./install_update.sh
EOFINSTALL
chmod +x dmg_contents/安装.command

# 复制安装脚本
cp install_update.sh dmg_contents/
chmod +x dmg_contents/install_update.sh

# 复制诊断脚本
cp diagnose_macos.sh dmg_contents/
chmod +x dmg_contents/diagnose_macos.sh

# 创建 README
cat > dmg_contents/README.txt << 'EOFREADME'
...
EOFREADME

# 生成 DMG
create-dmg ... "dist/OCCM.dmg" "dmg_contents/"
```
- **依赖文件**: `install_update.sh`, `diagnose_macos.sh`
- **状态**: ✅ 所有文件已提交，构建时可用

#### 步骤 7-9: 签名和打包 ✅
- 签名 DMG 文件
- 打包 ZIP 版本
- 上传构建产物

## DMG 内容结构验证

构建后的 DMG 将包含:
```
OCCM.dmg
├── OCCM.app                    # 主应用
├── 安装.command                # 安装启动器 (新增)
├── install_update.sh           # 安装脚本 (新增)
├── diagnose_macos.sh           # 诊断工具 (新增)
└── README.txt                  # 使用说明 (新增)
```

## 潜在问题检查

### ❓ 问题 1: 文件权限
**检查**: shell 脚本是否有执行权限？
```bash
ls -la diagnose_macos.sh install_update.sh
```
**结果**:
```
-rwxr-xr-x diagnose_macos.sh
-rwxr-xr-x install_update.sh
```
**状态**: ✅ 已有执行权限

### ❓ 问题 2: 文件编码
**检查**: shell 脚本是否使用 LF 换行符？
**状态**: ✅ 在 Linux/macOS 上创建，默认 LF

### ❓ 问题 3: 路径引用
**检查**: 构建脚本中的文件路径是否正确？
- `entitlements.plist` - 相对路径 ✅
- `install_update.sh` - 相对路径 ✅
- `diagnose_macos.sh` - 相对路径 ✅
**状态**: ✅ 所有路径正确

## 构建测试建议

### 本地测试 (如果有 macOS 设备)
```bash
# 1. 检查文件存在
ls -la entitlements.plist install_update.sh diagnose_macos.sh

# 2. 测试代码签名
codesign --force --deep --sign - --entitlements entitlements.plist /path/to/OCCM.app

# 3. 测试脚本执行
./install_update.sh
./diagnose_macos.sh
```

### GitHub Actions 测试
1. **推送到分支**: 触发构建
2. **检查构建日志**: 确认文件被正确复制
3. **下载构建产物**: 验证 DMG 内容
4. **在 macOS 设备上测试**: 验证功能

## 预期构建结果

### 成功标志
- ✅ macOS 构建 job 成功完成
- ✅ DMG 文件生成成功
- ✅ DMG 包含所有新文件
- ✅ 代码签名验证通过

### 失败可能性
- ❌ 文件未找到错误 → 检查文件是否提交
- ❌ 权限错误 → 检查 chmod 命令
- ❌ 签名失败 → 检查 entitlements.plist 格式

## 结论

✅ **所有新文件已正确集成到构建脚本中**
✅ **构建脚本引用正确**
✅ **文件已提交到 git**
✅ **预期构建会成功**

## 下一步

1. **推送到远程分支**:
   ```bash
   git push origin backup-1.5.0-wip
   ```

2. **触发构建**:
   - 推送会自动触发 GitHub Actions
   - 或手动触发 workflow_dispatch

3. **验证构建**:
   - 查看 Actions 页面
   - 检查 macOS 构建日志
   - 下载并测试 DMG

4. **如果构建失败**:
   - 检查错误日志
   - 确认文件路径
   - 验证文件内容

## 相关文件

- `.github/workflows/build.yml` - 构建配置
- `entitlements.plist` - macOS 权限
- `install_update.sh` - 安装脚本
- `diagnose_macos.sh` - 诊断工具
- `macos_fixes_summary.md` - 修复总结
