import json
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit

from balance_api import BalanceApi
from balance_window import BalanceWindow

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_REFRESH_SECONDS = 300


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


def load_keys(config: dict) -> dict:
    keys = config.get("api_keys")
    if isinstance(keys, dict) and keys:
        return dict(keys)
    return {}


class App:
    def __init__(self):
        self.config = load_config()
        self.refresh_seconds = int(
            self.config.get("refresh_seconds", DEFAULT_REFRESH_SECONDS)
        )
        self.keys = load_keys(self.config)
        self.api = BalanceApi()
        self.api.finished.connect(self._on_result)

        self.window = BalanceWindow(
            on_refresh=self.refresh,
            on_quit=self.quit,
            on_open_config=self.open_config,
            on_reload_config=self.reload_config,
            on_set_interval=self.set_refresh_interval,
            refresh_seconds=self.refresh_seconds,
        )
        self.window.show()

        self.timer = QTimer()
        self.timer.setInterval(self.refresh_seconds * 1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

        if not self.keys:
            self._ask_key()
        else:
            self.refresh()

    def _ask_key(self):
        key = prompt_api_key()
        if key:
            self.config.setdefault("api_keys", {})["默认"] = key
            save_config(self.config)
            self.keys = load_keys(self.config)
            self.refresh()
        else:
            self.window._show_error("未配置 API Key（右键可重试）")

    def refresh(self):
        if not self.keys:
            self._ask_key()
            return
        self.window.show_loading()
        self._results = {}
        for name, key in self.keys.items():
            self.api.fetch(key, name)

    def _on_result(self, result):
        self._results[result.name] = result
        if len(self._results) == len(self.keys):
            self.window.show_results(self._results)

    def open_config(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(CONFIG_FILE)))

    def reload_config(self):
        self.config = load_config()
        self.refresh_seconds = int(
            self.config.get("refresh_seconds", self.refresh_seconds)
        )
        self.timer.setInterval(self.refresh_seconds * 1000)
        self.keys = load_keys(self.config)
        self.refresh()

    def set_refresh_interval(self, seconds: int):
        self.refresh_seconds = seconds
        self.config["refresh_seconds"] = seconds
        save_config(self.config)
        self.timer.setInterval(seconds * 1000)
        self.refresh()

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
