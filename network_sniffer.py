# network_sniffer.py
import json
import os
import time
from pathlib import Path
from typing import Iterable, Optional

class NetworkSniffer:
    """
    用于 Playwright 页面网络抓包：
    - request
    - response
    - requestfailed
    - console
    - pageerror

    使用方式：
        sniffer = NetworkSniffer(page, "logs", keywords=["voice", "audio", "answer"])
        sniffer.start()
        ...
        sniffer.stop()
    """

    def __init__(
        self,
        page,
        log_dir: str = "logs",
        keywords: Optional[Iterable[str]] = None,
        body_max_len: int = 3000,
        response_max_len: int = 5000,
    ):
        self.page = page
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.keywords = [k.lower() for k in (keywords or [])]
        self.body_max_len = body_max_len
        self.response_max_len = response_max_len

        ts = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"network_{ts}.jsonl"
        self.text_file = self.log_dir / f"network_{ts}.txt"

        self._handlers = []

    def _match(self, text: str) -> bool:
        if not self.keywords:
            return True
        t = (text or "").lower()
        return any(k in t for k in self.keywords)

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
            if not self._match(url):
                return

            post_data = None
            try:
                post_data = request.post_data
            except Exception:
                post_data = None

            item = {
                "type": "request",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "method": request.method,
                "url": url,
                "resource_type": request.resource_type,
                "headers": request.headers,
                "post_data": post_data[: self.body_max_len] if post_data else None,
            }
            self._write_jsonl(item)

        # 响应
        def on_response(response):
            url = response.url
            if not self._match(url):
                return

            body_text = None
            try:
                ct = response.headers.get("content-type", "")
                if "text" in ct or "json" in ct or "javascript" in ct or "xml" in ct:
                    body_text = response.text()
                    if body_text is not None and len(body_text) > self.response_max_len:
                        body_text = body_text[: self.response_max_len] + "...<truncated>"
            except Exception as e:
                body_text = f"<failed to read body: {e}>"

            item = {
                "type": "response",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": response.status,
                "url": url,
                "headers": response.headers,
                "body": body_text,
            }
            self._write_jsonl(item)

        # 请求失败
        def on_request_failed(request):
            url = request.url
            if not self._match(url):
                return

            failure = None
            try:
                failure = request.failure
            except Exception:
                failure = None

            item = {
                "type": "requestfailed",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "method": request.method,
                "url": url,
                "failure": failure,
            }
            self._write_jsonl(item)

        # console
        def on_console(msg):
            try:
                text = msg.text
            except Exception:
                text = str(msg)

            item = {
                "type": "console",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "level": msg.type,
                "text": text,
            }
            self._write_jsonl(item)

        # page error
        def on_page_error(err):
            item = {
                "type": "pageerror",
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(err),
            }
            self._write_jsonl(item)

        self.page.on("request", on_request)
        self.page.on("response", on_response)
        self.page.on("requestfailed", on_request_failed)
        self.page.on("console", on_console)
        self.page.on("pageerror", on_page_error)

        self._handlers = [
            ("request", on_request),
            ("response", on_response),
            ("requestfailed", on_request_failed),
            ("console", on_console),
            ("pageerror", on_page_error),
        ]

        self._write_text(f"[START] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_text(f"keywords={self.keywords}")

    def stop(self):
        # Playwright sync API 没有特别优雅的 off，这里尽量解绑
        for event_name, handler in self._handlers:
            try:
                self.page.off(event_name, handler)
            except Exception:
                pass
        self._write_text(f"[STOP] {time.strftime('%Y-%m-%d %H:%M:%S')}")