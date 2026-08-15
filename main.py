import json
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit

from balance_api import BalanceApi
from balance_window import BalanceWindow

CONFIG_FILE = Path(__file__).parent / "config.json"
REFRESH_SECONDS = 300


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(config: dict):
    try:
        CONFIG_FILE.write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        print(f"保存配置失败: {e}")


def prompt_api_key() -> str:
    text, ok = QInputDialog.getText(
        None,
        "DeepSeek API Key",
        "请输入 DeepSeek API Key（platform.deepseek.com 获取）：",
        QLineEdit.EchoMode.Password,
    )
    return text.strip() if ok else ""


class App:
    def __init__(self):
        self.config = load_config()
        self.api = BalanceApi()
        self.api.finished.connect(self._on_result)

        self.window = BalanceWindow(
            on_refresh=self.refresh,
            on_quit=self.quit,
            refresh_seconds=REFRESH_SECONDS,
        )
        self.window.show()

        self.timer = QTimer()
        self.timer.setInterval(REFRESH_SECONDS * 1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

        if not self.config.get("api_key"):
            self._ask_key()
        else:
            self.refresh()

    def _ask_key(self):
        key = prompt_api_key()
        if key:
            self.config["api_key"] = key
            save_config(self.config)
            self.refresh()
        else:
            self.window._show_error("未配置 API Key（右键可重试）")

    def refresh(self):
        key = self.config.get("api_key")
        if not key:
            self._ask_key()
            return
        self.window.show_loading()
        self.api.fetch(key)

    def _on_result(self, result):
        self.window.show_result(result)

    def quit(self):
        self.window._save_state()
        QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    App()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
