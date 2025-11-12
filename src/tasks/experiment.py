from __future__ import annotations
import logging
import re
from typing import List, Dict
from playwright.sync_api import BrowserContext, Page
from typing import Tuple
from .resource_loader import read_js

logger = logging.getLogger(__name__)

EXP_HOME_URL = "https://sjjx.dean.swust.edu.cn/swust"


def goto_experiment_portal(ctx: BrowserContext, page: Page) -> Page:
    try:
        page.goto(EXP_HOME_URL)
        try:
            page.wait_for_load_state("networkidle")
        except Exception:
            pass
    except Exception:
        pass
    return page


def _to_fixed_term(term: str) -> str | None:
    m = re.match(r"^(\d{4}-\d{4})[-/]?([上下])$", term)
    if not m:
        return None
    year, suf = m.group(1), m.group(2)
    n = "1" if suf == "上" else "2"
    return f"{year}-{n}"


def _term_output_name(term: str) -> str:
    m = re.match(r"^(\d{4}-\d{4})[-/]?([上下])$", term)
    if not m:
        return term
    year, suf = m.group(1), m.group(2)
    return f"{year}-{suf}学期"


def _load_js() -> str:
    return read_js("parse_experiment.js")


def _fetch_page(page: Page, js: str, url: str) -> Dict:
    return page.evaluate(
        "(p)=>{ const {code,url}=p; eval(code); return fetchExpPage(url); }",
        {"code": js, "url": url},
    )


def _is_error(page: Page, js: str, html: str) -> bool:
    return bool(
        page.evaluate(
            "(p)=>{ const {code,html}=p; eval(code); return detectErrorFromHTML(html); }",
            {"code": js, "html": html},
        )
    )


def _total_pages(page: Page, js: str, html: str) -> int:
    n = page.evaluate(
        "(p)=>{ const {code,html}=p; eval(code); return extractTotalPagesFromHTML(html); }",
        {"code": js, "html": html},
    )
    return int(n or 1)


def _parse_entries(page: Page, js: str, html: str) -> List[Dict]:
    data = page.evaluate(
        "(p)=>{ const {code,html}=p; eval(code); return parseExpEntriesFromHTML(html); }",
        {"code": js, "html": html},
    )
    return data or []


def _build_urls(ft: str, total: int) -> List[str]:
    return [
        f"https://sjjx.dean.swust.edu.cn/teachn/teachnAction/index.action?page.pageNum={p}&currTeachCourseCode=%25&currWeek=%25&currYearterm={ft}"
        for p in range(2, total + 1)
    ]


def fetch_experiment_course_containers(
    page: Page, normal_terms: List[str]
) -> List[Dict]:
    goto_experiment_portal(None, page)

    pairs = []
    for t in normal_terms:
        ft = _to_fixed_term(t)
        if ft:
            pairs.append((ft, _term_output_name(t)))

    seen = set()
    uniq: List[Tuple[str, str]] = []
    for ft, out_term in pairs:
        if ft in seen:
            continue
        seen.add(ft)
        uniq.append((ft, out_term))

    total_terms = len(uniq)
    logger.info("开始获取实验课表")

    js = _load_js()
    containers: List[Dict] = []

    for idx, (ft, out_term) in enumerate(uniq, start=1):
        logger.info(f"进度 {idx}/{total_terms}")
        url1 = (
            f"https://sjjx.dean.swust.edu.cn/teachn/teachnAction/index.action"
            f"?page.pageNum=1&currTeachCourseCode=%25&currWeek=%25&currYearterm={ft}"
        )
        resp1 = _fetch_page(page, js, url1)
        html1 = resp1.get("text") if isinstance(resp1, dict) else ""
        if not html1 or _is_error(page, js, html1):
            logger.warning(
                f"term={out_term} 第1页获取失败 status={resp1.get('status')}"
            )
            containers.append({"term": out_term.strip("学期"), "entries": []})
            continue

        total = _total_pages(page, js, html1)
        entries = _parse_entries(page, js, html1)
        if total > 1:
            urls = _build_urls(ft, total)
            resps = (
                page.evaluate(
                    "(p)=>{ const {code,urls}=p; eval(code); return fetchMany(urls); }",
                    {"code": js, "urls": urls},
                )
                or []
            )
            for r in resps:
                h = r.get("text") if isinstance(r, dict) else ""
                if not h or _is_error(page, js, h):
                    logger.warning("分页获取失败")
                    continue
                entries.extend(_parse_entries(page, js, h))
        containers.append({"term": out_term.strip("学期"), "entries": entries})

    logger.info("实验课表获取完成")
    return containers
