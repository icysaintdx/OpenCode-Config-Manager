# macOS 启动失败修复总结

## 修复日期
2026-01-23

## 问题描述
- **硬件**: M4 芯片 (Apple Silicon)
- **系统**: macOS 15.5
- **症状**:
  - DMG版本: 图标在Dock中弹跳两次后消失
  - ZIP版本: 提示需要外部应用权限,然后无反应

## 已实施的修复

### 1. 添加 entitlements.plist ✅
**文件**: `entitlements.plist`

添加了macOS 15.5 + M4芯片所需的权限:
- `com.apple.security.cs.allow-unsigned-executable-memory` - 允许PyQt5使用未签名的可执行内存
- `com.apple.security.cs.disable-library-validation` - 允许加载第三方库
- `com.apple.security.cs.allow-jit` - 允许JIT编译 (Python需要)
- `com.apple.security.cs.allow-dyld-environment-variables` - 允许DYLD环境变量

### 2. 改进代码签名流程 ✅
**文件**: `.github/workflows/build.yml` (第165-173行)

**修改前**:
```bash
codesign --force --deep --options runtime --sign - dist/OCCM.app
```

**修改后**:
```bash
codesign --force --deep --sign - --entitlements entitlements.plist dist/OCCM.app
```

### 3. 添加自动安装脚本 ✅
**文件**: `install_update.sh`

功能:
- 自动检测已安装的旧版本
- 显示版本号对比
- 备份旧版本 (带时间戳)
- 自动复制新版本到 /Applications/
- 自动移除隔离属性
- 提供详细的安装反馈

### 4. 添加诊断工具 ✅
**文件**: `diagnose_macos.sh`

功能:
- 检查应用是否安装
- 检查并移除隔离属性
- 验证代码签名
- 检查应用架构 (ARM64/x86_64)
- 检查系统架构
- 尝试启动应用并捕获错误
- 提供系统日志查看命令

### 5. 优化 DMG 打包流程 ✅
**文件**: `.github/workflows/build.yml` (第175-236行)

**新增内容**:
- 创建 `dmg_contents/` 目录结构
- 包含 `安装.command` 启动器 (双击即可自动安装)
- 包含 `install_update.sh` 安装脚本
- 包含 `diagnose_macos.sh` 诊断脚本
- 包含 `README.txt` 使用说明

**DMG 内容结构**:
```
OCCM.dmg
├── OCCM.app
├── 安装.command (双击自动安装)
├── install_update.sh
├── diagnose_macos.sh
└── README.txt
```

### 6. 添加崩溃日志收集 ✅
**文件**: `opencode_config_manager_fluent.py` (第1-90行)

功能:
- 捕获所有未处理的异常
- 保存详细的崩溃日志到 `~/Library/Logs/OCCM/`
- 记录系统信息 (macOS版本, CPU架构, Python版本)
- 显示用户友好的错误对话框
- 提供GitHub Issues链接

**崩溃日志位置**: `~/Library/Logs/OCCM/crash_<timestamp>.log`

## 修改的文件

1. **新增文件**:
   - `entitlements.plist` - macOS权限配置
   - `install_update.sh` - 自动安装脚本
   - `diagnose_macos.sh` - 诊断工具
   - `macos_fix_plan.md` - 详细修复方案文档

2. **修改文件**:
   - `.github/workflows/build.yml`:
     - 第165-173行: 改进代码签名 (使用entitlements)
     - 第175-236行: 优化DMG打包 (包含安装脚本和诊断工具)
   - `opencode_config_manager_fluent.py`:
     - 第1-90行: 添加macOS崩溃处理器

## 用户使用指南

### 方法 1: 使用自动安装脚本 (推荐)
1. 打开 DMG 文件
2. 双击 `安装.command`
3. 按提示操作

### 方法 2: 手动安装
1. 打开 DMG 文件
2. 拖拽 OCCM.app 到应用程序文件夹
3. 如果遇到"应用已损坏"错误:
   ```bash
   xattr -cr /Applications/OCCM.app
   ```

### 方法 3: 使用诊断工具
如果应用无法启动:
1. 打开 DMG 文件
2. 双击 `diagnose_macos.sh`
3. 查看诊断结果
4. 将崩溃日志发送给开发者

## 预期效果

修复后应该解决:
- ✅ M4 芯片兼容性问题
- ✅ macOS 15.5 Gatekeeper 限制
- ✅ 代码签名被拒绝的问题
- ✅ 更新时需要手动删除旧版本的问题
- ✅ 缺少错误日志导致无法调试的问题

## 测试建议

### 在 macOS 设备上测试 (需要 M4 芯片 + macOS 15.5)

1. **测试自动安装**:
   ```bash
   # 打开 DMG
   open OCCM_v1.5.0.dmg
   # 双击 安装.command
   ```

2. **测试诊断工具**:
   ```bash
   # 运行诊断
   ./diagnose_macos.sh
   ```

3. **测试崩溃日志**:
   ```bash
   # 查看崩溃日志
   ls -la ~/Library/Logs/OCCM/
   cat ~/Library/Logs/OCCM/crash_*.log
   ```

4. **测试代码签名**:
   ```bash
   # 验证签名
   codesign -vvv /Applications/OCCM.app
   # 检查权限
   codesign -d --entitlements - /Applications/OCCM.app
   ```

## 后续优化建议

### 短期 (无需 macOS 设备)
- ✅ 已完成所有立即可行的修复

### 中期 (需要 macOS 设备测试)
- [ ] 创建 .spec 文件优化 PyInstaller 配置
- [ ] 测试 ARM64 原生构建
- [ ] 验证所有修复在真实设备上的效果

### 长期 (需要开发者账号)
- [ ] 申请 Apple Developer 账号
- [ ] 使用正式证书签名
- [ ] 提交公证 (Notarization)
- [ ] 实现应用内自动更新

## 相关资源

- **GitHub Issues**: https://github.com/icysaintdx/OpenCode-Config-Manager/issues
- **macOS 代码签名文档**: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- **PyInstaller macOS 文档**: https://pyinstaller.org/en/stable/usage.html#macos-specific-options
- **Entitlements 参考**: https://developer.apple.com/documentation/bundleresources/entitlements

## 提交信息

```
修复macOS启动失败 + 优化更新流程 (M4芯片 + macOS 15.5)

- 添加 entitlements.plist 支持 macOS 15.5 + M4 芯片
- 改进代码签名流程 (使用 entitlements)
- 添加自动安装脚本 (install_update.sh)
- 添加诊断工具 (diagnose_macos.sh)
- 优化 DMG 打包 (包含安装脚本和诊断工具)
- 添加 macOS 崩溃日志收集
- DMG 安装现在可以自动替换旧版本

修复问题:
- M4 芯片兼容性
- macOS 15.5 Gatekeeper 限制
- 代码签名被拒绝
- 更新流程需要手动删除旧版本
- 缺少错误日志无法调试
```
