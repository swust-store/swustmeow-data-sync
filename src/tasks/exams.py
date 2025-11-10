from __future__ import annotations
from playwright.sync_api import BrowserContext, Page
import pathlib

EXAM_TABLE_URL = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:examTable"


def fetch_exams(ctx: BrowserContext, page: Page) -> dict:
    page.goto(EXAM_TABLE_URL)
    import re, time

    deadline = time.time() + 30
    patt = re.compile(r"\b\d{4}-\d{4}-\d\b\s*学期.*?考试")
    while time.time() < deadline:
        titles = page.locator("h3").all_text_contents()
        if any(patt.search(t or "") for t in titles):
            break
        try:
            page.wait_for_timeout(300)
        except Exception:
            pass

    js_path = pathlib.Path(__file__).parent / "js" / "parse_exams.js"
    js_code = js_path.read_text(encoding="utf-8")
    data = page.evaluate(f"(() => {{\n{js_code}\nreturn parseExams();\n}})()")
    return data
