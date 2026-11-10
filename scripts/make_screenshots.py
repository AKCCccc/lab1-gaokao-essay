"""启动本地服务并用 Playwright 生成 README 截图。

用法：
    .venv\\Scripts\\python.exe scripts\\make_screenshots.py

依赖 Playwright 与本机 Chrome/Edge，不会自动下载浏览器。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

PROJECT = Path(__file__).resolve().parent.parent
SHOTS = PROJECT / "screenshots"
PORT = 8123
BASE = f"http://127.0.0.1:{PORT}"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    raise SystemExit("未找到 Chrome 或 Edge，请先安装浏览器。")


def wait_for_server(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE}/api/health", timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.4)
    raise SystemExit("服务启动超时。")


def main() -> None:
    SHOTS.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["DEMO_MODE"] = "false"
    log_path = PROJECT / "screenshots" / "_server.log"
    log = log_path.open("w", encoding="utf-8", errors="ignore")
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=PROJECT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )

    try:
        wait_for_server()
        browser_path = find_browser()

        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=browser_path, headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 1000},
                device_scale_factor=1.5,
                locale="zh-CN",
            )
            page = context.new_page()
            page.goto(BASE, wait_until="networkidle")
            page.wait_for_timeout(800)
            page.screenshot(path=str(SHOTS / "01-home.png"))
            print("saved 01-home.png")

            page.locator("#titleChips .chip").first.click()
            page.locator("#outlineBtn").click()
            page.wait_for_function(
                "() => { const el = document.querySelector('#outlineView');"
                " return el && !el.classList.contains('hidden') && el.innerText.trim().length > 200"
                " && document.querySelector('#statusBar').classList.contains('done'); }",
                timeout=120_000,
            )
            page.evaluate(
                "() => window.scrollTo(0, document.querySelector('#workspace').offsetTop - 104)"
            )
            page.evaluate("() => { document.querySelector('#outlineView').scrollTop = 0; }")
            page.wait_for_timeout(600)
            page.screenshot(path=str(SHOTS / "02-outline.png"))
            print("saved 02-outline.png")

            page.locator("#generateBtn").click()
            page.wait_for_function(
                "() => { const el = document.querySelector('#essayView');"
                " return el && el.innerText.trim().length > 500"
                " && document.querySelector('#statusBar').classList.contains('done'); }",
                timeout=180_000,
            )
            page.evaluate(
                "() => window.scrollTo(0, document.querySelector('#workspace').offsetTop - 104)"
            )
            page.evaluate("() => { document.querySelector('#essayView').scrollTop = 0; }")
            page.wait_for_timeout(700)
            page.screenshot(path=str(SHOTS / "03-essay.png"))
            print("saved 03-essay.png")

            page.locator("#reviewBtn").click()
            page.wait_for_function(
                "() => { const el = document.querySelector('#reviewView');"
                " return el && el.innerText.trim().length > 200"
                " && document.querySelector('#statusBar').classList.contains('done'); }",
                timeout=180_000,
            )
            page.evaluate(
                "() => window.scrollTo(0, document.querySelector('#workspace').offsetTop - 104)"
            )
            page.evaluate("() => { document.querySelector('#reviewView').scrollTop = 0; }")
            page.wait_for_timeout(600)
            page.screenshot(path=str(SHOTS / "04-review.png"))
            print("saved 04-review.png")

            mobile = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=2,
                is_mobile=True,
                locale="zh-CN",
            )
            mpage = mobile.new_page()
            mpage.goto(BASE, wait_until="networkidle")
            mpage.wait_for_timeout(900)
            mpage.screenshot(path=str(SHOTS / "05-mobile.png"))
            print("saved 05-mobile.png")

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=8)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


if __name__ == "__main__":
    main()

