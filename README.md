# deepseek-balance

基于 PySide6 的 DeepSeek API 余额查询桌面小组件（X11 环境）。

## 功能

- 悬浮卡片显示余额 + 可用状态（绿/红状态点）
- 支持多个 API Key，右键菜单「切换 Key」手动切换显示
- 自动刷新间隔可配置：右键菜单选择 30s/60s/300s/600s/1800s，写入配置并即时生效
- 右键菜单：立即刷新、打开配置文件、刷新配置文件、切换 Key、退出
- 窗口位置自动持久化到 `state.json`

## 配置（`config.json`，明文 API Key，已 gitignore）

```json
{
  "api_keys": { "主账号": "sk-xxx", "备用": "sk-yyy" },
  "refresh_seconds": 300
}
```

- `api_keys`：名称 → key 的映射，支持多 key
- `refresh_seconds`：可选，默认 300 秒
- 首次运行无配置时弹出输入框引导；也可通过右键「打开配置文件」直接编辑，「刷新配置文件」热重载

## 启动

```bash
uv run python main.py
```

## 打包（PyInstaller onefile）

```bash
uv add --dev pyinstaller
uv run pyinstaller --noconfirm --clean --onefile --windowed \
  --add-data "assets/icon.png:assets" --name deepseek-balance main.py
```

产物为 `dist/deepseek-balance`（仅 Linux x86_64）。注意：打包程序读取 `dist/` 目录下的 `config.json` / `state.json`（非项目目录），首次打包后需将二者复制到 `dist/`。

### Dock 启动（GNOME）

- 桌面入口 `~/.local/share/applications/deepseek-balance.desktop` 指向 `dist/deepseek-balance` 与 `assets/icon.png`
- 应用列表搜索「DeepSeek 余额」即可启动，右键可固定到 Dock

## 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 包管理器
- X11 桌面环境
