# network_sniffer.py
import json
import time
from pathlib import Path

class NetworkSniffer:
    """用于 Playwright 页面网络抓包：记录所有响应"""

    def __init__(
        self,
        page,
        log_dir: str = "logs",
        response_max_len: int = 5000,
    ):
        self.page = page
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.response_max_len = response_max_len

        ts = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"network_{ts}.jsonl"
        self.text_file = self.log_dir / f"network_{ts}.txt"

        self._handlers = []

    def _write_jsonl(self, obj: dict):
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _write_text(self, text: str):
        with self.text_file.open("a", encoding="utf-8") as f:
            f.write(text + "\n")

    def start(self):
        # 请求
        def on_request(request):
            url = request.url

            post_data = None
            try:
                post_data = request.post_data
            except Exception:
                pass

            item = {
                "type": "request",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "method": request.method,
                "url": url,
                "resource_type": request.resource_type,
                "headers": dict(request.headers),
                "post_data": post_data,
            }

            self._write_jsonl(item)
            print(f"[请求] {request.method} {url}")

        # 响应
        def on_response(response):
            url = response.url
            status = response.status
            body_text = None

            try:
                ct = response.headers.get("content-type", "")
                if "text" in ct or "json" in ct or "javascript" in ct or "xml" in ct:
                    body_text = response.text()
                    if body_text and len(body_text) > self.response_max_len:
                        body_text = body_text[:self.response_max_len]
            except Exception as e:
                body_text = f"<failed to read body: {e}>"

            item = {
                "type": "response",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
                "url": url,
                "body": body_text,
            }

            self._write_jsonl(item)
            print(f"[响应] [{status}] {url}")

        self.page.on("request", on_request)
        self.page.on("response", on_response)

        self._handlers = [
            ("request", on_request),
            ("response", on_response),
        ]

        self._write_text(f"[START] {time.strftime('%Y-%m-%d %H:%M:%S')}")

    def stop(self):
        # Playwright sync API 没有特别优雅的 off，这里尽量解绑
        for event_name, handler in self._handlers:
            try:
                self.page.off(event_name, handler)
            except Exception:
                pass
        self._write_text(f"[STOP] {time.strftime('%Y-%m-%d %H:%M:%S')}")