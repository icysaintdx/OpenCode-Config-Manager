# MCP 对话框和模型管理界面修复总结

## 修复时间
2026-01-23

## 修复的问题

### 1. 模型管理界面批量模型下拉框 ✅

#### 问题描述
- 模型管理界面不应该包含批量模型下拉框
- 批量模型功能应该只在 Oh My Agent 页面

#### 修复内容
- 移除了模型管理页面（ModelPage）中的批量模型下拉框
- 删除了以下代码：
  ```python
  self.bulk_model_label = BodyLabel(tr("model.bulk_model"), self)
  toolbar.addWidget(self.bulk_model_label)
  self.bulk_model_combo = ComboBox(self)
  self.bulk_model_combo.setMinimumWidth(220)
  toolbar.addWidget(self.bulk_model_combo)
  ```

### 2. MCP 对话框语言切换问题 ✅

#### 问题描述
- 添加和编辑 MCP 对话框中的以下字段切换语言后仍显示英文：
  - "Additional Information (Click to Expand/Collapse)" - 附加信息
  - "Full JSON Preview" - JSON 预览
  - "Full MCP Configuration Preview" - MCP 配置预览
  - "Include mcpServers Wrapper" - 包含 mcpServers 包装器

#### 根本原因
- QGroupBox 和 CheckBox 在初始化时使用 `tr()` 设置了文本
- 但这些控件在语言切换后不会自动更新文本
- 需要手动监听语言切换事件并更新控件文本

#### 修复内容

1. **添加语言切换监听**
   ```python
   # 在 __init__ 方法中添加
   _lang_manager.language_changed.connect(self._on_language_changed)
   ```

2. **添加语言切换处理方法**
   ```python
   def _on_language_changed(self, lang_code: str) -> None:
       """处理语言切换事件"""
       # 更新窗口标题
       if self.is_edit:
           self.setWindowTitle(tr("mcp.dialog.edit_title"))
       else:
           title = (
               tr("mcp.dialog.add_local_title")
               if self.mcp_type == "local"
               else tr("mcp.dialog.add_remote_title")
           )
           self.setWindowTitle(title)
       
       # 更新 QGroupBox 标题
       self.extra_group.setTitle(tr("mcp.additional_info"))
       self.preview_group.setTitle(tr("mcp.full_json_preview"))
       
       # 更新 CheckBox 文本
       self.preview_wrap_check.setText(tr("mcp.include_wrapper"))
       self.enabled_check.setText(tr("mcp.dialog.enable_checkbox"))
       
       # 更新按钮文本
       self.cancel_btn.setText(tr("common.cancel"))
       self.save_btn.setText(tr("common.save"))
       self.format_btn.setText(tr("cli_export.format_json"))
   ```

3. **涉及的翻译键**
   - `mcp.additional_info` - "附加信息（点击展开/折叠）"
   - `mcp.full_json_preview` - "完整 JSON 预览"
   - `mcp.full_mcp_config_preview` - "完整 MCP 配置预览"
   - `mcp.include_wrapper` - "包含 mcpServers 包装器"
   - `mcp.dialog.enable_checkbox` - "启用此 MCP 服务器"
   - `mcp.dialog.edit_title` - "编辑 MCP 服务器"
   - `mcp.dialog.add_local_title` - "添加本地 MCP 服务器"
   - `mcp.dialog.add_remote_title` - "添加远程 MCP 服务器"

## 技术细节

### 语言切换机制

1. **全局语言管理器**
   - `LanguageManager` 类管理所有翻译
   - 提供 `language_changed` 信号
   - 当语言切换时，发出信号通知所有监听者

2. **对话框语言切换处理**
   - 对话框需要手动监听 `language_changed` 信号
   - 在信号处理方法中更新所有控件的文本
   - 包括：窗口标题、QGroupBox 标题、CheckBox 文本、按钮文本等

3. **为什么需要手动处理**
   - Qt 的控件在创建时设置文本后，不会自动更新
   - `tr()` 函数只在调用时返回当前语言的翻译
   - 需要在语言切换时重新调用 `tr()` 并更新控件

### 批量模型功能说明

- **Oh My Agent 页面**：需要批量模型功能，因为可以批量设置多个 Agent 的模型
- **Model 管理页面**：不需要批量模型功能，因为是直接管理单个模型

## 测试验证

### MCP 对话框
- ✅ 打开 MCP 对话框，切换语言
- ✅ 验证"附加信息"标题更新
- ✅ 验证"JSON 预览"标题更新
- ✅ 验证"包含 mcpServers 包装器"复选框文本更新
- ✅ 验证按钮文本更新

### 模型管理页面
- ✅ 打开模型管理页面
- ✅ 验证工具栏中没有批量模型下拉框
- ✅ 验证页面功能正常

## 相关文件

### 修改的文件
1. `opencode_config_manager_fluent.py`
   - ModelPage 类 - 移除批量模型下拉框
   - MCPDialog 类 - 添加语言切换处理

### 涉及的翻译文件
1. `locales/en_US.json` - 英文翻译（已存在）
2. `locales/zh_CN.json` - 中文翻译（已存在）

## 后续建议

1. **其他对话框检查**
   - 检查其他对话框是否也需要语言切换处理
   - 确保所有对话框都能正确响应语言切换

2. **统一处理机制**
   - 考虑创建一个基类对话框，自动处理语言切换
   - 减少重复代码

3. **测试覆盖**
   - 测试所有对话框的语言切换功能
   - 确保没有遗漏的硬编码文本

## 参考资料

- Qt 信号与槽机制：https://doc.qt.io/qt-5/signalsandslots.html
- PyQt5 国际化：https://doc.qt.io/qt-5/internationalization.html
