from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

BALANCE_URL = "https://api.deepseek.com/user/balance"


class BalanceResult:
    def __init__(self, ok=False, error="", is_available=False, infos=None, name=""):
        self.ok = ok
        self.error = error
        self.is_available = is_available
        self.infos = infos or []
        self.name = name

    @property
    def primary(self) -> dict | None:
        if self.infos:
            return self.infos[0]
        return None


class BalanceApi(QObject):
    finished = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nam = QNetworkAccessManager(self)

    def fetch(self, api_key: str, name: str = ""):
        req = QNetworkRequest(QUrl(BALANCE_URL))
        req.setRawHeader(b"Authorization", f"Bearer {api_key}".encode())
        req.setTransferTimeout(15000)
        reply = self.nam.get(req)
        reply.setProperty("key_name", name)
        reply.finished.connect(lambda: self._on_finished(reply))

    def _on_finished(self, reply: QNetworkReply):
        name = reply.property("key_name") or ""
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        if reply.error() != QNetworkReply.NetworkError.NoError:
            if status == 401:
                self.finished.emit(BalanceResult(error="API Key 无效 (401)", name=name))
            elif status == 402:
                self.finished.emit(BalanceResult(error="余额不足 (402)", name=name))
            else:
                self.finished.emit(
                    BalanceResult(error=f"网络错误: {reply.errorString()}", name=name)
                )
            reply.deleteLater()
            return
        try:
            data = reply.readAll().data().decode("utf-8")
            import json

            payload = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            reply.deleteLater()
            self.finished.emit(BalanceResult(error="响应解析失败", name=name))
            return
        reply.deleteLater()
        if status != 200:
            self.finished.emit(
                BalanceResult(
                    error=f"HTTP {status}: {payload.get('error', {}).get('message', '')}",
                    name=name,
                )
            )
            return
        infos = []
        for b in payload.get("balance_infos", []):
            infos.append(
                {
                    "currency": b.get("currency", "CNY"),
                    "total": b.get("total_balance", "0"),
                    "granted": b.get("granted_balance", "0"),
                    "topped_up": b.get("topped_up_balance", "0"),
                }
            )
        self.finished.emit(
            BalanceResult(
                ok=True,
                is_available=bool(payload.get("is_available")),
                infos=infos,
                name=name,
            )
        )
