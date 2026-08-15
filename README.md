# deepseek-balance

基于 PySide6 的 DeepSeek API 余额查询桌面小组件（X11 环境）。

## 功能

- 悬浮卡片显示总余额 + 赠送/充值明细 + 可用状态
- 每 5 分钟自动刷新，点 ⟳ 按钮或右键菜单立即刷新
- 首次运行引导输入 API Key（存 `config.json`，已 gitignore）
- 窗口位置自动持久化到 `state.json`

## 启动

```bash
uv run python main.py
```

## 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 包管理器
- X11 桌面环境
