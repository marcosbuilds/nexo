"""Browser execution boundary. Real browser operations are injectable and recoverable."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol


class BrowserAdapter(Protocol):
    def start(self) -> None: ...
    def goto(self, url: str) -> None: ...
    def read(self) -> str: ...
    def click(self, selector: str) -> None: ...
    def type(self, selector: str, text: str) -> None: ...
    def press(self, selector: str, key: str) -> None: ...
    def screenshot(self, path: str) -> str: ...
    def close(self) -> None: ...


@dataclass
class BrowserResult:
    status: str
    message: str
    data: dict[str, Any] | None = None


class PlaywrightBrowser:
    """Optional Playwright implementation; import is delayed so core works without it."""
    def __init__(self, profile_dir: str, *, headless: bool = False):
        self.profile_dir = profile_dir
        self.headless = headless
        self._playwright = None
        self._context = None
        self._page = None

    def start(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Browser capability unavailable: Playwright cannot be imported.") from exc
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            self.profile_dir,
            headless=self.headless,
            viewport={"width": 1440, "height": 900},
            args=["--disable-notifications"],
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()

    def _ensure(self):
        if self._page is None:
            raise RuntimeError("browser_not_started")
        return self._page

    def goto(self, url: str) -> None:
        self._ensure().goto(url, wait_until="domcontentloaded")

    def read(self) -> str:
        return self._ensure().inner_text("body")

    def click(self, selector: str) -> None:
        self._ensure().locator(selector).click()

    def type(self, selector: str, text: str) -> None:
        self._ensure().locator(selector).fill(text)

    def press(self, selector: str, key: str) -> None:
        self._ensure().locator(selector).press(key)

    def screenshot(self, path: str) -> str:
        self._ensure().screenshot(path=path, full_page=True)
        return path

    def close(self) -> None:
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        self._context = None
        self._page = None
        self._playwright = None


def classify_manual_intervention(page_text: str, url: str = "") -> dict[str, Any]:
    text = (page_text or "").lower()
    signals = {
        "captcha": ["captcha", "recaptcha", "hcaptcha", "verify you are human"],
        "otp": ["verification code", "one-time code", "otp"],
        "identity": ["identity verification", "verify your identity", "document verification", "verifique sua identidade"],
        "security": ["suspicious activity", "security check", "atividade suspeita"],
    }
    for kind, needles in signals.items():
        if any(n in text for n in needles):
            return {"manual_required": True, "blocker": kind, "url": url}
    return {"manual_required": False}
