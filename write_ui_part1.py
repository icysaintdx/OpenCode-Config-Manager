# -*- coding: utf-8 -*-
qfluentwidgets_code = '''

# ==================== 版本检查服务 ====================
class VersionCheckThread(QThread):
    """版本检查线程"""
    versionChecked = pyqtSignal(str, str)  # latest_version, release_url
    
    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={"User-Agent": "OpenCode-Config-Manager"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", tag_name)
                if version_match:
                    latest_version = version_match.group(1)
                    release_url = data.get("html_url", GITHUB_URL + "/releases")
                    self.versionChecked.emit(latest_version, release_url)
        except Exception as e:
            print(f"Version check failed: {e}")


def compare_versions(current: str, latest: str) -> bool:
    """比较版本号，返回 True 如果有新版本"""
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        return latest_parts > current_parts
    except:
        return False


# ==================== 基础页面类 ====================
class BasePage(ScrollArea):
    """所有页面的基类"""
    
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", ""))
        self.setWidgetResizable(True)
        
        # 主容器
        self.scrollWidget = QWidget()
        self.setWidget(self.scrollWidget)
        
        # 主布局
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setSpacing(16)
        
        # 标题
        self.titleLabel = LargeTitleLabel(title, self.scrollWidget)
        self.subtitleLabel = CaptionLabel(subtitle, self.scrollWidget)
        
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addSpacing(16)
        
        # 设置样式
        self.setStyleSheet("""
            BasePage {
                background-color: transparent;
                border: none;
            }
        """)
'''

with open('opencode_config_manager_fluent.py', 'a', encoding='utf-8') as f:
    f.write(qfluentwidgets_code)
print('Part 1 added')
