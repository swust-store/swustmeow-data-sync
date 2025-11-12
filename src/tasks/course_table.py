from __future__ import annotations
from playwright.sync_api import BrowserContext, Page
import hashlib
from .resource_loader import read_js

COURSE_TABLE_URL = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:courseTable"
OPTIONAL_TABLE_URL = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=chooseCourse:courseTable"


def _parse_course_table(page: Page) -> dict | None:
    js_code = read_js("parse_course_table.js")
    data = page.evaluate(f"(() => {{\n{js_code}\nreturn parseCourseTable();\n}})()")
    if not data or not data.get("term"):
        return None
    return data


def _fetch_one(ctx: BrowserContext, page: Page, url: str) -> dict | None:
    page.goto(url)
    page.wait_for_selector("table.UICourseTable", timeout=30000)
    return _parse_course_table(page)


def fetch_course_table(ctx: BrowserContext, page: Page) -> list[dict]:
    containers: list[dict] = []

    normal = _fetch_one(ctx, page, COURSE_TABLE_URL)
    if normal and normal.get("term"):
        term = normal["term"]
        cid = hashlib.sha1(f"NORMAL{term}".encode("utf-8")).hexdigest()
        containers.append(
            {
                "id": cid,
                "type": "NORMAL",
                "term": term,
                "entries": normal.get("entries", []),
            }
        )

    optional = _fetch_one(ctx, page, OPTIONAL_TABLE_URL)
    if optional and optional.get("term"):
        term = optional["term"]
        cid = hashlib.sha1(f"OPTIONAL{term}".encode("utf-8")).hexdigest()
        containers.append(
            {
                "id": cid,
                "type": "OPTIONAL",
                "term": term,
                "entries": optional.get("entries", []),
            }
        )

    return list({d["term"]: d for d in reversed(containers)}.values())[::-1]
