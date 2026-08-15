# AGENTS.md

PySide6 桌面小组件，查询 DeepSeek API 余额（浮窗，仅 X11）。

## 运行与验证

- 启动：`uv run python main.py`（依赖用 uv 管理，勿用 pip；Python 3.12+）
- GUI 应用：需要 X11 显示器，headless/SSH 环境无法运行；无测试、无 lint/CI，唯一验证方式是运行它
- 无 formatter/typecheck 配置

## 结构

- `main.py` — 入口：配置读写、定时刷新（`REFRESH_SECONDS = 300`）
- `balance_api.py` — 异步请求 `https://api.deepseek.com/user/balance`，用 `QNetworkAccessManager` + `finished` 信号返回 `BalanceResult`（勿改成 requests，会卡 UI）
- `balance_window.py` — 无边框浮窗 UI、拖拽、右键菜单

## 注意

- `config.json` 存明文 API Key、`state.json` 存窗口位置，两者均已 gitignore，改路径时勿解开
- UI 文案为中文，新增文案沿用中文
- 错误提示约定：401 → "API Key 无效"，402 → "余额不足"
