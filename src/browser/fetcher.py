"""Единый клиент для загрузки HTML через браузер или requests."""

from __future__ import annotations

import time
from typing import Protocol

import requests

from browser.config import load_browser_config

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class PageFetcher(Protocol):
    def fetch(self, url: str) -> str: ...
    def close(self) -> None: ...


class RequestsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "ru-RU,ru;q=0.9",
        })

    def fetch(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def close(self) -> None:
        self.session.close()


class CamoufoxFetcher:
    def __init__(self, headless: bool = True, delay_seconds: float = 1.0):
        self.headless = headless
        self.delay_seconds = delay_seconds
        self._ctx = None
        self._browser = None
        self._page = None

    def _ensure(self) -> None:
        if self._page:
            return
        from camoufox.sync_api import Camoufox

        self._ctx = Camoufox(headless=self.headless)
        self._browser = self._ctx.__enter__()
        self._page = self._browser.new_page()

    def fetch(self, url: str) -> str:
        self._ensure()
        assert self._page is not None
        self._page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(self.delay_seconds)
        return self._page.content()

    def close(self) -> None:
        if self._ctx:
            self._ctx.__exit__(None, None, None)
            self._ctx = None
            self._browser = None
            self._page = None


class DrissionFetcher:
    def __init__(
        self,
        headless: bool | None = None,
        delay_seconds: float = 1.0,
        config_path: str | None = None,
    ):
        self.delay_seconds = delay_seconds
        self._page = None
        self._browser_cfg = load_browser_config(config_path)
        cfg_headless = self._browser_cfg.get("headless")
        self.headless = headless if headless is not None else bool(cfg_headless)

    def _ensure(self) -> None:
        if self._page:
            return
        from DrissionPage import ChromiumOptions, ChromiumPage

        options = ChromiumOptions()
        browser_path = self._browser_cfg.get("browser_path")
        if browser_path:
            options.set_browser_path(browser_path)
        if self.headless:
            options.headless()
        for arg in self._browser_cfg.get("arguments", []):
            if arg.startswith("--user-agent="):
                options.set_user_agent(arg.split("=", 1)[1])
            else:
                options.set_argument(arg)
        if not self._browser_cfg.get("arguments"):
            options.set_argument("--no-sandbox")
            options.set_argument("--disable-gpu")
        self._page = ChromiumPage(options)

    def fetch(self, url: str) -> str:
        self._ensure()
        assert self._page is not None
        self._page.get(url, timeout=60)
        time.sleep(self.delay_seconds)
        return self._page.html

    def close(self) -> None:
        if self._page:
            try:
                self._page.quit()
            except Exception:
                pass
            self._page = None


def create_fetcher(engine: str = "auto", headless: bool = True, delay_seconds: float = 1.0) -> PageFetcher:
    engine = (engine or "auto").lower()

    if engine == "requests":
        return RequestsFetcher()

    if engine == "camoufox":
        return CamoufoxFetcher(headless=headless, delay_seconds=delay_seconds)

    if engine == "drission":
        return DrissionFetcher(headless=headless, delay_seconds=delay_seconds)

    # auto: drission → camoufox → requests (Chrome проверен у пользователя)
    for factory in (
        lambda: DrissionFetcher(headless=headless, delay_seconds=delay_seconds),
        lambda: CamoufoxFetcher(headless=headless, delay_seconds=delay_seconds),
        lambda: RequestsFetcher(),
    ):
        try:
            fetcher = factory()
            html = fetcher.fetch("https://hh.ru/")
            if len(html) > 1000:
                return fetcher
            fetcher.close()
        except Exception:
            continue

    return RequestsFetcher()
