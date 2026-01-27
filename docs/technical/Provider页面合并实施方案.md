Provider 页面合并实施方案
文档信息
创建日期: 2026-01-27
文件位置: D:\opcdcfg\opencode_config_manager_fluent.py
涉及行数: 6379-8879 (约2500行)
任务类型: 大型重构 - UI合并
预计工作量: 4-6小时
风险等级: 中等（大量代码重构，但逻辑不变）
一、项目背景
1.1 当前状态
ProviderPage (行 6379-7446): 管理自定义 Provider，约1067行
功能：添加/编辑/删除自定义Provider、拉取模型、导出CLI、查询余额
依赖：ModelFetchService (模型拉取服务)
NativeProviderPage (行 7447-8879): 管理原生 Provider，约1432行
功能：配置/测试/删除原生Provider、检测已配置、查询余额
依赖：AuthManager (认证管理)、EnvVarDetector (环境变量检测)
问题：两个页面功能独立，在导航菜单中占用两个入口，用户需要切换页面
1.2 合并目标
将两个页面合并为一个统一的 ProviderPage
使用 Pivot 标签页切换自定义/原生 Provider
保留所有原有功能，不丢失任何特性
优化导航菜单，减少菜单项数量
提升用户体验，无需切换页面即可管理所有Provider
1.3 参考实现
PluginPage (行 19802): 已成功合并插件管理和 Oh My OpenCode 管理
PermissionPage (行 11609): 已成功合并权限设置和上下文压缩
使用 Pivot + QStackedWidget 模式
每个标签页内容在独立的 _create_xxx_widget() 方法中创建
二、架构设计
2.1 类结构设计
class ProviderPage(BasePage):
    """Provider 管理页面 - 统一管理自定义和原生Provider"""
    
    # ========== 核心属性 ==========
    main_window: MainWindow          # 主窗口引用
    auth_manager: AuthManager        # 认证管理器 (原生Provider需要)
    env_detector: EnvVarDetector     # 环境变量检测器 (原生Provider需要)
    
    # ========== UI组件 ==========
    pivot: Pivot                     # 标签页切换器
    stack: QStackedWidget            # 内容切换器
    custom_widget: QWidget           # 自定义Provider页面
    native_widget: QWidget           # 原生Provider页面
    
    # ========== 自定义Provider组件 (custom_前缀) ==========
    custom_table: TableWidget                    # 自定义Provider列表
    custom_add_btn: PrimaryPushButton           # 添加按钮
    custom_edit_btn: PushButton                 # 编辑按钮
    custom_delete_btn: PushButton               # 删除按钮
    custom_fetch_models_btn: PushButton         # 拉取模型按钮
    custom_export_cli_btn: PushButton           # 导出CLI按钮
    custom_query_balance_btn: PushButton        # 查询余额按钮
    _model_fetch_service: ModelFetchService     # 模型拉取服务
    
    # ========== 原生Provider组件 (native_前缀) ==========
    native_table: TableWidget                    # 原生Provider列表
    native_config_btn: PrimaryPushButton        # 配置按钮
    native_detect_btn: PushButton               # 检测已配置按钮
    native_test_btn: PushButton                 # 测试连接按钮
    native_delete_btn: PushButton               # 删除配置按钮
    native_query_balance_btn: PushButton        # 查询余额按钮
2.2 方法命名规则（完整映射表）
功能分类	原方法名	自定义Provider	原生Provider
初始化	__init__()	统一的 __init__()	-
UI创建	_setup_ui()	统一的 _setup_ui()	-
-	_create_custom_provider_widget()	_create_native_provider_widget()
数据加载	_load_data()	_load_custom_data()	_load_native_data()
添加	_on_add()	_on_custom_add()	-
编辑	_on_edit()	_on_custom_edit()	-
删除	_on_delete()	_on_custom_delete()	_on_native_delete()
配置	_on_config()	-	_on_native_config()
测试	_on_test()	-	_on_native_test()
拉取模型	_on_fetch_models()	_on_custom_fetch_models()	-
_fetch_models_for_provider()	_custom_fetch_models_for_provider()	-
_on_models_fetched()	_on_custom_models_fetched()	-
_add_models()	_custom_add_models()	-
_resolve_model_category()	_custom_resolve_model_category()	-
_get_preset_for_category()	_custom_get_preset_for_category()	-
_apply_batch_config()	_custom_apply_batch_config()	-
导出CLI	_on_export_to_cli()	_on_custom_export_to_cli()	-
查询余额	_on_query_balance()	_on_custom_query_balance()	_on_native_query_balance()
_query_provider_usage()	_custom_query_provider_usage()	-
_query_newapi_usage()	_custom_query_newapi_usage()	-
_query_openai_usage()	_custom_query_openai_usage()	-
_show_balance_result()	_custom_show_balance_result()	-
_show_balance_error()	_custom_show_balance_error()	-
检测配置	_on_detect_configured()	-	_on_native_detect_configured()
获取选中项	_get_selected_provider()	-	_get_selected_native_provider()
配置变更	_on_config_changed()	统一的 _on_config_changed()	-
标签页切换	-	_on_tab_changed()	-
2.3 UI布局结构
ProviderPage
├── Pivot (标签页切换器)
│   ├── Tab: "自定义 Provider"
│   └── Tab: "原生 Provider"
└── QStackedWidget (内容切换器)
    ├── Index 0: custom_widget
    │   ├── Toolbar (工具栏)
    │   │   ├── 添加 Provider
    │   │   ├── 编辑
    │   │   ├── 删除
    │   │   ├── 拉取模型
    │   │   ├── 导出到CLI
    │   │   └── 查询余额
    │   └── TableWidget (自定义Provider列表)
    │       └── 列: 名称 | 显示名称 | SDK | API地址 | 模型数
    └── Index 1: native_widget
        ├── Toolbar (工具栏)
        │   ├── 配置 Provider
        │   ├── 检测已配置
        │   ├── 测试连接
        │   ├── 删除配置
        │   └── 查询余额
        └── TableWidget (原生Provider列表)
            └── 列: Provider | SDK | 状态 | 环境变量
三、详细实施步骤
步骤 1: 修改 __init__ 方法
位置: 行 6382-6388

原代码:

def __init__(self, main_window, parent=None):
    super().__init__(tr("provider.title"), parent)
    self.main_window = main_window
    self._setup_ui()
    self._load_data()
    # 连接配置变更信号
    self.main_window.config_changed.connect(self._on_config_changed)
修改后:

def __init__(self, main_window, parent=None):
    super().__init__(tr("provider.title"), parent)
    self.main_window = main_window
    
    # 初始化原生Provider需要的管理器
    self.auth_manager = AuthManager()
    self.env_detector = EnvVarDetector()
    
    # 初始化UI
    self._setup_ui()
    
    # 加载数据
    self._load_custom_data()
    self._load_native_data()
    
    # 连接配置变更信号
    self.main_window.config_changed.connect(self._on_config_changed)
关键变更:

添加 self.auth_manager = AuthManager() - 原生Provider认证管理
添加 self.env_detector = EnvVarDetector() - 环境变量检测
_load_data() 拆分为 _load_custom_data() 和 _load_native_data()
步骤 2: 重写 _setup_ui 方法
位置: 行 6590-6649

完整新代码:

def _setup_ui(self):
    """初始化UI - 使用Pivot标签页"""
    # Pivot 标签页
    self.pivot = Pivot(self)
    self.pivot.addItem(routeKey="custom", text=tr("provider.custom_provider"))
    self.pivot.addItem(routeKey="native", text=tr("provider.native_provider"))
    self.pivot.setCurrentItem("custom")
    self.pivot.currentItemChanged.connect(self._on_tab_changed)
    self._layout.addWidget(self.pivot)
    
    # QStackedWidget
    self.stack = QStackedWidget(self)
    
    # 自定义 Provider 页面
    self.custom_widget = self._create_custom_provider_widget()
    self.stack.addWidget(self.custom_widget)
    
    # 原生 Provider 页面
    self.native_widget = self._create_native_provider_widget()
    self.stack.addWidget(self.native_widget)
    
    self._layout.addWidget(self.stack, 1)

def _on_tab_changed(self, route_key: str):
    """切换标签页"""
    if route_key == "custom":
        self.stack.setCurrentIndex(0)
    else:
        self.stack.setCurrentIndex(1)

def _on_config_changed(self):
    """配置变更时刷新两个标签页的数据"""
    self._load_custom_data()
    self._load_native_data()
关键点:

Pivot 的 routeKey 使用 "custom" 和 "native"
默认显示 "custom" 标签页
_on_tab_changed 根据 routeKey 切换 QStackedWidget 的索引
_on_config_changed 同时刷新两个标签页
步骤 3: 创建自定义Provider标签页
新增方法: _create_custom_provider_widget()

完整代码 (插入到 _setup_ui 方法之后):

def _create_custom_provider_widget(self) -> QWidget:
    """创建自定义Provider管理部件"""
    widget = QWidget(self)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 8, 0, 0)
    layout.setSpacing(8)
    
    # 工具栏
    toolbar = QHBoxLayout()
    
    self.custom_add_btn = PrimaryPushButton(FIF.ADD, tr("provider.add_provider"), widget)
    self.custom_add_btn.clicked.connect(self._on_custom_add)
    toolbar.addWidget(self.custom_add_btn)
    
    self.custom_edit_btn = PushButton(FIF.EDIT, tr("common.edit"), widget)
    self.custom_edit_btn.clicked.connect(self._on_custom_edit)
    toolbar.addWidget(self.custom_edit_btn)
    
    self.custom_delete_btn = PushButton(FIF.DELETE, tr("common.delete"), widget)
    self.custom_delete_btn.clicked.connect(self._on_custom_delete)
    toolbar.addWidget(self.custom_delete_btn)
    
    self.custom_fetch_models_btn = PushButton(FIF.SYNC, tr("provider.fetch_models"), widget)
    self.custom_fetch_models_btn.clicked.connect(self._on_custom_fetch_models)
    toolbar.addWidget(self.custom_fetch_models_btn)
    
    self.custom_export_cli_btn = PushButton(FIF.SEND, tr("provider.export_to_cli"), widget)
    self.custom_export_cli_btn.clicked.connect(self._on_custom_export_to_cli)
    toolbar.addWidget(self.custom_export_cli_btn)
    
    self.custom_query_balance_btn = PushButton(FIF.MARKET, tr("provider.query_balance"), widget)
    self.custom_query_balance_btn.clicked.connect(self._on_custom_query_balance)
    toolbar.addWidget(self.custom_query_balance_btn)
    
    toolbar.addStretch()
    layout.addLayout(toolbar)
    
    # Provider 列表表格
    self.custom_table = TableWidget(widget)
    self.custom_table.setColumnCount(5)
    self.custom_table.setHorizontalHeaderLabels([
        tr("common.name"),
        tr("provider.display_name"),
        tr("provider.sdk_type"),
        tr("provider.api_address"),
        tr("provider.model_count"),
    ])
    
    # 表格配置
    header = self.custom_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.Fixed)
    header.resizeSection(0, 120)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Fixed)
    header.resizeSection(2, 180)
    header.setSectionResizeMode(3, QHeaderView.Stretch)
    header.setSectionResizeMode(4, QHeaderView.Fixed)
    header.resizeSection(4, 60)
    
    self.custom_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.custom_table.setSelectionMode(QAbstractItemView.SingleSelection)
    self.custom_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self.custom_table.doubleClicked.connect(self._on_custom_edit)
    
    layout.addWidget(self.custom_table)
    
    return widget
步骤 4: 创建原生Provider标签页
新增方法: _create_native_provider_widget()

完整代码 (插入到 _create_custom_provider_widget 方法之后):

def _create_native_provider_widget(self) -> QWidget:
    """创建原生Provider管理部件"""
    widget = QWidget(self)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 8, 0, 0)
    layout.setSpacing(8)
    
    # 工具栏
    toolbar = QHBoxLayout()
    
    self.native_config_btn = PrimaryPushButton(FIF.SETTING, tr("native_provider.config_provider"), widget)
    self.native_config_btn.clicked.connect(self._on_native_config)
    toolbar.addWidget(self.native_config_btn)
    
    self.native_detect_btn = PushButton(FIF.SEARCH, tr("native_provider.detect_configured"), widget)
    self.native_detect_btn.clicked.connect(self._on_native_detect_configured)
    toolbar.addWidget(self.native_detect_btn)
    
    self.native_test_btn = PushButton(FIF.WIFI, tr("native_provider.test_connection"), widget)
    self.native_test_btn.clicked.connect(self._on_native_test)
    toolbar.addWidget(self.native_test_btn)
    
    self.native_delete_btn = PushButton(FIF.DELETE, tr("native_provider.delete_config"), widget)
    self.native_delete_btn.clicked.connect(self._on_native_delete)
    toolbar.addWidget(self.native_delete_btn)
    
    self.native_query_balance_btn = PushButton(FIF.MARKET, tr("provider.query_balance"), widget)
    self.native_query_balance_btn.clicked.connect(self._on_native_query_balance)
    toolbar.addWidget(self.native_query_balance_btn)
    
    toolbar.addStretch()
    layout.addLayout(toolbar)
    
    # Provider 列表表格
    self.native_table = TableWidget(widget)
    self.native_table.setColumnCount(4)
    self.native_table.setHorizontalHeaderLabels([
        tr("native_provider.provider_name"),
        tr("provider.sdk_type"),
        tr("native_provider.status"),
        tr("native_provider.env_vars"),
    ])
    
    # 表格配置
    header = self.native_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.Fixed)
    header.resizeSection(0, 160)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Fixed)
    header.resizeSection(2, 80)
    header.setSectionResizeMode(3, QHeaderView.Stretch)
    
    self.native_table.setSelectionBehavior(QAbstractItemView.SelectRows)
    self.native_table.setSelectionMode(QAbstractItemView.SingleSelection)
    self.native_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self.native_table.doubleClicked.connect(self._on_native_config)
    
    layout.addWidget(self.native_table)
    
    return widget
步骤 5: 重命名自定义Provider的所有方法
需要重命名的方法列表 (共约15个方法):

_load_data() → _load_custom_data()
_on_add() → _on_custom_add()
_on_edit() → _on_custom_edit()
_on_delete() → _on_custom_delete()
_on_fetch_models() → _on_custom_fetch_models()
_fetch_models_for_provider() → _custom_fetch_models_for_provider()
_on_models_fetched() → _on_custom_models_fetched()
_add_models() → _custom_add_models()
_resolve_model_category() → _custom_resolve_model_category()
_get_preset_for_category() → _custom_get_preset_for_category()
_apply_batch_config() → _custom_apply_batch_config()
_on_export_to_cli() → _on_custom_export_to_cli()
_on_query_balance() → _on_custom_query_balance()
_query_provider_usage() → _custom_query_provider_usage()
_query_newapi_usage() → _custom_query_newapi_usage()
_query_openai_usage() → _custom_query_openai_usage()
_show_balance_result() → _custom_show_balance_result()
_show_balance_error() → _custom_show_balance_error()
重要: 在每个方法内部，所有对 self.table 的引用都需要改为 self.custom_table

示例 (以 _load_data 为例):

# 原方法
def _load_data(self):
    """加载 Provider 数据"""
    self.table.setRowCount(0)
    config = self.main_window.opencode_config or {}
    providers = config.get("provider", {})
    
    for name, data in providers.items():
        if not isinstance(data, dict):
            continue
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        # ...

# 修改后
def _load_custom_data(self):
    """加载自定义Provider数据"""
    self.custom_table.setRowCount(0)
    config = self.main_window.opencode_config or {}
    providers = config.get("provider", {})
    
    for name, data in providers.items():
        if not isinstance(data, dict):
            continue
        row = self.custom_table.rowCount()
        self.custom_table.insertRow(row)
        self.custom_table.setItem(row, 0, QTableWidgetItem(name))
        # ...
步骤 6: 重命名原生Provider的所有方法
需要重命名的方法列表 (共约8个方法):

_load_data() → _load_native_data()
_get_selected_provider() → _get_selected_native_provider()
_on_config() → _on_native_config()
_on_test() → _on_native_test()
_on_delete() → _on_native_delete()
_on_detect_configured() → _on_native_detect_configured()
_on_query_balance() → _on_native_query_balance()
_on_config_changed() → 删除 (已在步骤2中统一实现)
重要: 在每个方法内部，所有对 self.table 的引用都需要改为 self.native_table

示例 (以 _load_data 为例):

# 原方法
def _load_data(self):
    """加载 Provider 数据"""
    self.table.setRowCount(0)
    
    # 读取已配置的认证
    auth_data = {}
    try:
        auth_data = self.auth_manager.read_auth()
    except Exception:
        pass
    
    for provider in NATIVE_PROVIDERS:
        row = self.table.rowCount()
        self.table.insertRow(row)
        # ...

# 修改后
def _load_native_data(self):
    """加载原生Provider数据"""
    self.native_table.setRowCount(0)
    
    # 读取已配置的认证
    auth_data = {}
    try:
        auth_data = self.auth_manager.read_auth()
    except Exception:
        pass
    
    for provider in NATIVE_PROVIDERS:
        row = self.native_table.rowCount()
        self.native_table.insertRow(row)
        # ...
步骤 7: 更新翻译文件
文件 1: locales/zh_CN.json

在 provider 部分添加（约行 138-236）:

"provider": {
    "title": "Provider 管理",
    ...
    "custom_provider": "自定义 Provider",
    "native_provider": "原生 Provider",
    ...
}
文件 2: locales/en_US.json

在 provider 部分添加（约行 138-236）:

"provider": {
    "title": "Provider Management",
    ...
    "custom_provider": "Custom Provider",
    "native_provider": "Native Provider",
    ...
}
步骤 8: 更新导航菜单
位置: _init_navigation() 方法，约行 12358-12450

原代码:

# Provider 页面
self.provider_page = ProviderPage(self)
self.addSubInterface(self.provider_page, FIF.PEOPLE, tr("menu.provider"))

# 原生 Provider 页面
self.native_provider_page = NativeProviderPage(self)
self.addSubInterface(
    self.native_provider_page, FIF.GLOBE, tr("menu.native_provider")
)
修改后:

# Provider 页面（已合并自定义和原生Provider）
self.provider_page = ProviderPage(self)
self.addSubInterface(self.provider_page, FIF.PEOPLE, tr("menu.provider"))

# 移除 native_provider_page 的注册
# self.native_provider_page = NativeProviderPage(self)
# self.addSubInterface(
#     self.native_provider_page, FIF.GLOBE, tr("menu.native_provider")
# )
注意:

保留 NativeProviderPage 类的定义（行 7447-8879），不要删除
只是不再在导航菜单中注册它
四、关键注意事项
4.1 变量引用更新
必须更新的引用:

所有 self.table → self.custom_table 或 self.native_table
所有 self.add_btn → self.custom_add_btn 或 self.native_config_btn
所有按钮的 clicked.connect() 信号连接
4.2 保留原类定义
不要删除 NativeProviderPage 类（行 7447-8879），原因：

可能有其他地方引用
便于回滚
便于对比验证
4.3 ModelFetchService 初始化
自定义Provider的模型拉取服务需要保留：

if not hasattr(self, "_model_fetch_service"):
    self._model_fetch_service = ModelFetchService(self)
    self._model_fetch_service.fetch_finished.connect(self._on_custom_models_fetched)
4.4 对话框引用
以下对话框类保持不变，无需修改：

ProviderDialog - 自定义Provider编辑对话框
NativeProviderDialog - 原生Provider配置对话框
BalanceDialog - 余额显示对话框
ModelSelectDialog - 模型选择对话框
4.5 信号连接
确保所有按钮的 clicked 信号连接到正确的方法：

# 自定义Provider
self.custom_add_btn.clicked.connect(self._on_custom_add)
self.custom_edit_btn.clicked.connect(self._on_custom_edit)
# ...

# 原生Provider
self.native_config_btn.clicked.connect(self._on_native_config)
self.native_test_btn.clicked.connect(self._on_native_test)
# ...
五、测试计划
5.1 自定义Provider功能测试
 添加Provider: 点击"添加Provider"按钮，填写信息，保存成功
 编辑Provider: 双击或点击"编辑"按钮，修改信息，保存成功
 删除Provider: 选中Provider，点击"删除"，确认删除成功
 拉取模型: 选中Provider，点击"拉取模型"，成功获取模型列表
 导出到CLI: 选中Provider，点击"导出到CLI"，跳转到CLI导出页面
 查询余额: 选中Provider，点击"查询余额"，显示余额信息
 表格显示: 表格正确显示所有自定义Provider
 双击编辑: 双击表格行，打开编辑对话框
5.2 原生Provider功能测试
 配置Provider: 选中Provider，点击"配置Provider"，填写认证信息，保存成功
 检测已配置: 点击"检测已配置"，正确显示已配置的Provider
 测试连接: 选中已配置的Provider，点击"测试连接"，显示测试结果
 删除配置: 选中已配