import json
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from balance_api import BalanceResult

HEADER_HEIGHT = 26
MIN_W = 260
MIN_H = 100
STATE_FILE = Path(__file__).parent / "state.json"
INTERVAL_OPTIONS = [30, 60, 300, 600, 1800]
MENU_STYLE = (
    "QMenu { background: rgba(255, 255, 255, 0.96); border: 1px solid rgba(15, 23, 42, 0.12);"
    " border-radius: 8px; padding: 6px; }"
    "QMenu::item { color: #0f172a; font-size: 13px; padding: 6px 18px; border-radius: 5px; }"
    "QMenu::item:selected { background: rgba(16, 185, 129, 0.12); color: #047857; }"
    "QMenu::item:disabled { color: #94a3b8; }"
    "QMenu::separator { height: 1px; background: rgba(15, 23, 42, 0.08); margin: 5px 8px; }"
)


def currency_symbol(currency: str) -> str:
    return "$" if currency == "USD" else "¥"


def draw_dot(color: QColor, size: int = 10) -> QLabel:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(color, 2))
    painter.setBrush(color)
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    label = QLabel()
    label.setPixmap(pm)
    label.setFixedSize(size, size)
    return label


class BalanceWindow(QWidget):
    def __init__(self, on_refresh, on_quit, on_open_config, on_reload_config, on_set_interval, refresh_seconds: int, parent=None):
        super().__init__(parent)
        self.on_refresh = on_refresh
        self.on_quit = on_quit
        self.on_open_config = on_open_config
        self.on_reload_config = on_reload_config
        self.on_set_interval = on_set_interval
        self.refresh_seconds = refresh_seconds
        self._drag_offset: QPoint | None = None
        self._results: dict = {}
        self._current = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))

        card = QFrame(self)
        card.setObjectName("balanceCard")
        card.setGraphicsEffect(shadow)
        card.setStyleSheet(
            "#balanceCard { background: rgba(16, 185, 129, 0.10);"
            " border: 1px solid rgba(16, 185, 129, 0.35);"
            " border-radius: 12px; }"
        )
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 6, 14, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(6)

        self.status_dot = draw_dot(QColor(160, 160, 160))
        header.addWidget(self.status_dot)

        self.title_label = QLabel("DeepSeek 余额")
        self.title_label.setStyleSheet(
            "color: #0e7490; font-size: 14px; font-weight: bold; background: transparent;"
        )
        header.addWidget(self.title_label)
        header.addStretch(1)

        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(22, 22)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setToolTip("立即刷新")
        self.refresh_btn.clicked.connect(lambda: self.on_refresh())
        self.refresh_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent;"
            " color: #0e7490; font-size: 15px; font-weight: bold; }"
            "QPushButton:hover { color: #155e75; }"
        )
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.total_label = QLabel("--")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_label.setStyleSheet(
            "color: #0f172a; font-size: 30px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(self.total_label)
        layout.addStretch(1)

        self.setFixedWidth(MIN_W)
        self.setMinimumHeight(MIN_H)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._load_state()

    # ---- data display ----
    def show_loading(self):
        self.total_label.setText("查询中…")
        self.total_label.setStyleSheet(
            "color: #64748b; font-size: 20px; font-weight: bold; background: transparent;"
        )
        self._set_dot(QColor(160, 160, 160))

    def show_results(self, results: dict):
        self._results = dict(results)
        if self._current not in self._results:
            self._current = next(iter(self._results))
        self._show_current()

    def _show_current(self):
        if len(self._results) > 1:
            self.title_label.setText(f"DeepSeek 余额 · {self._current}")
        else:
            self.title_label.setText("DeepSeek 余额")
        self.show_result(self._results[self._current])

    def show_result(self, result: BalanceResult):
        if not result.ok:
            self._show_error(result.error)
            return
        info = result.primary
        symbol = currency_symbol(info["currency"]) if info else "¥"
        self.total_label.setText(f"{symbol} {info['total']}")
        self.total_label.setStyleSheet(
            "color: #0f172a; font-size: 30px; font-weight: bold; background: transparent;"
        )
        if result.is_available:
            self._set_dot(QColor(34, 197, 94))
        else:
            self._set_dot(QColor(239, 68, 68))

    def _show_error(self, error: str):
        self.total_label.setText("⚠")
        self.total_label.setStyleSheet(
            "color: #dc2626; font-size: 30px; font-weight: bold; background: transparent;"
        )
        self._set_dot(QColor(239, 68, 68))

    def _set_dot(self, color: QColor):
        self.status_dot.setPixmap(draw_dot(color).pixmap())

    # ---- drag ----
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() <= HEADER_HEIGHT + 14:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._drag_offset is not None:
            self._drag_offset = None
            self._save_state()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ---- persistence ----
    def _save_state(self):
        try:
            STATE_FILE.write_text(
                json.dumps({"x": self.x(), "y": self.y()}), encoding="utf-8"
            )
        except OSError:
            pass

    def _load_state(self):
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            self.move(int(state["x"]), int(state["y"]))
        except (OSError, KeyError, ValueError):
            self.move(40, 40)

    # ---- menu ----
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        refresh = QAction("⟳ 立即刷新", menu)
        refresh.triggered.connect(self.on_refresh)
        menu.addAction(refresh)

        open_cfg = QAction("⚙ 打开配置文件", menu)
        open_cfg.triggered.connect(self.on_open_config)
        menu.addAction(open_cfg)

        reload_cfg = QAction("↻ 刷新配置文件", menu)
        reload_cfg.triggered.connect(self.on_reload_config)
        menu.addAction(reload_cfg)

        menu.addSeparator()

        interval_menu = QMenu("自动刷新间隔", menu)
        interval_menu.setStyleSheet(MENU_STYLE)
        group = QActionGroup(interval_menu)
        for seconds in INTERVAL_OPTIONS:
            action = QAction(f"{seconds}s", interval_menu)
            action.setCheckable(True)
            action.setChecked(seconds == self.refresh_seconds)
            action.triggered.connect(
                lambda checked=False, s=seconds: self._choose_interval(s)
            )
            group.addAction(action)
            interval_menu.addAction(action)
        menu.addMenu(interval_menu)

        if len(self._results) > 1:
            menu.addSeparator()
            key_menu = QMenu("切换 Key", menu)
            key_menu.setStyleSheet(MENU_STYLE)
            key_group = QActionGroup(key_menu)
            for name in self._results:
                action = QAction(name, key_menu)
                action.setCheckable(True)
                action.setChecked(name == self._current)
                action.triggered.connect(
                    lambda checked=False, n=name: self._choose_key(n)
                )
                key_group.addAction(action)
                key_menu.addAction(action)
            menu.addMenu(key_menu)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.on_quit)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    def _choose_interval(self, seconds: int):
        if seconds == self.refresh_seconds:
            return
        self.refresh_seconds = seconds
        self.on_set_interval(seconds)

    def _choose_key(self, name: str):
        if name == self._current:
            return
        self._current = name
        self._show_current()
