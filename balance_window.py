import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
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
MIN_H = 150
STATE_FILE = Path(__file__).parent / "state.json"


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
    def __init__(self, on_refresh, on_quit, refresh_seconds: int, parent=None):
        super().__init__(parent)
        self.on_refresh = on_refresh
        self.on_quit = on_quit
        self.refresh_seconds = refresh_seconds
        self._drag_offset: QPoint | None = None
        self._last_update = None

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

        title = QLabel("DeepSeek 余额")
        title.setStyleSheet(
            "color: #0e7490; font-size: 14px; font-weight: bold; background: transparent;"
        )
        header.addWidget(title)
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

        detail_box = QFrame()
        detail_box.setStyleSheet(
            "QFrame { background: rgba(255, 255, 255, 0.55); border-radius: 8px; }"
        )
        detail_layout = QVBoxLayout(detail_box)
        detail_layout.setContentsMargins(10, 6, 10, 6)
        detail_layout.setSpacing(2)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(
            "color: #475569; font-size: 12px; background: transparent;"
        )
        detail_layout.addWidget(self.detail_label)

        self.state_label = QLabel("")
        self.state_label.setStyleSheet(
            "color: #94a3b8; font-size: 11px; background: transparent;"
        )
        detail_layout.addWidget(self.state_label)
        layout.addWidget(detail_box)

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
        self.detail_label.setText("")
        self.state_label.setText("")
        self._set_dot(QColor(160, 160, 160))

    def show_result(self, result: BalanceResult):
        self._last_update = datetime.now()
        if not result.ok:
            self._show_error(result.error)
            return
        info = result.primary
        symbol = currency_symbol(info["currency"]) if info else "¥"
        self.total_label.setText(f"{symbol} {info['total']}")
        self.total_label.setStyleSheet(
            "color: #0f172a; font-size: 30px; font-weight: bold; background: transparent;"
        )
        detail_lines = []
        if info:
            detail_lines.append(
                f"赠送 {symbol}{info['granted']}　·　充值 {symbol}{info['topped_up']}"
            )
        if result.is_available:
            self._set_dot(QColor(34, 197, 94))
        else:
            self._set_dot(QColor(239, 68, 68))
        detail_lines.append(
            "可用" if result.is_available else "不可用（余额不足）"
        )
        self.detail_label.setText("　　".join(detail_lines[:1]))
        self.state_label.setText(
            f"上次刷新 {self._last_update.strftime('%H:%M:%S')}"
        )

    def _show_error(self, error: str):
        self.total_label.setText("⚠")
        self.total_label.setStyleSheet(
            "color: #dc2626; font-size: 30px; font-weight: bold; background: transparent;"
        )
        self.detail_label.setText(error)
        self.state_label.setText(f"上次刷新 {self._last_update.strftime('%H:%M:%S') if self._last_update else '—'}")
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
        menu.addAction("⟳ 立即刷新", self.on_refresh)
        menu.addSeparator()
        menu.addAction(f"自动刷新间隔 {self.refresh_seconds}s", lambda: None).setEnabled(False)
        menu.addSeparator()
        menu.addAction("退出", self.on_quit)
        menu.exec(event.globalPos())
