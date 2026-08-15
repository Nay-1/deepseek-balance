# AGENTS.md

PySide6 桌面小组件，查询 DeepSeek API 余额（浮窗，仅 X11）。

## 运行与验证

- 启动：`uv run python main.py`（依赖用 uv 管理，勿用 pip；Python 3.12+）
- GUI 应用：需要 X11 显示器，headless/SSH 环境无法运行；无测试、无 lint/CI，唯一验证方式是运行它
- 无 formatter/typecheck 配置

## 结构

- `main.py` — 入口：配置读写、定时刷新（间隔可配置，默认 300s）、多 key 并发查询、打包路径解析（`app_dir()`）
- `balance_api.py` — 异步请求 `https://api.deepseek.com/user/balance`，用 `QNetworkAccessManager` + `finished` 信号返回 `BalanceResult`（勿改成 requests，会卡 UI）；多 key 并发，结果带 `name` 标识
- `balance_window.py` — 无边框浮窗 UI、拖拽、右键菜单（切换 Key、刷新间隔选择）
- `assets/icon.png` — 程序与 Dock 图标

## 注意

- `config.json` 存明文 API Key（`api_keys` 映射：名称 → key，不再兼容旧 `api_key` 字段）、`state.json` 存窗口位置，两者均已 gitignore，改路径时勿解开
- 路径解析：源码运行时配置在项目目录；打包（PyInstaller onefile）后 `app_dir()` 返回 `sys.executable` 所在目录（`dist/`），配置要放在可执行文件旁，勿用 `__file__`（打包后指向临时解压目录）
- 打包命令与 Dock 入口见 README
- UI 文案为中文，新增文案沿用中文
- 错误提示约定：401 → "API Key 无效"，402 → "余额不足"
- 未经用户明确要求，不得 `git commit` / `git push`
