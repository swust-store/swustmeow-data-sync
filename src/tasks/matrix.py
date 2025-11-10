from __future__ import annotations
from playwright.sync_api import BrowserContext, Page
import logging

PORTAL_URL = "https://matrix.dean.swust.edu.cn/acadmicManager/index.cfm?event=studentPortal:DEFAULT_EVENT"


def goto_portal(ctx: BrowserContext, page: Page) -> Page:
    page.goto(PORTAL_URL)
    try:
        page.wait_for_load_state("networkidle")
    except Exception:
        pass
    logger.info("Successfully navigated to the matrix")
    return page
logger = logging.getLogger(__name__)
