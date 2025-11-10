from __future__ import annotations
from playwright.sync_api import BrowserContext, Page
import time
import pathlib

COURSE_MARK_URL = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentProfile:courseMark"


def fetch_scores_points(ctx: BrowserContext, page: Page) -> dict:
    page.goto(COURSE_MARK_URL, wait_until="domcontentloaded", timeout=15000)
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            ok = page.evaluate(
                "document.getElementById('Plan') || document.getElementById('Summary') ? true : false"
            )
            if ok:
                break
        except Exception:
            pass
        try:
            page.wait_for_timeout(200)
        except Exception:
            pass

    js_path = pathlib.Path(__file__).parent / "js" / "parse_scores_points.js"
    js_code = js_path.read_text(encoding="utf-8")
    data = page.evaluate(f"(() => {{\n{js_code}\nreturn parseScoresPoints();\n}})()")
    return data
