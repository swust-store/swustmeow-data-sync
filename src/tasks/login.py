from __future__ import annotations
from playwright.sync_api import BrowserContext, Page
import re
import time
import logging

LOGIN_URL = "https://cas.swust.edu.cn/authserver/login?service=http%3A%2F%2Fsoa.swust.edu.cn%2Fsys%2Fportal%2Fpage.jsp"


def ensure_logged_in(ctx: BrowserContext) -> Page:
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    already_logged_in = False

    try:
        page.goto(LOGIN_URL)
    except Exception as e:
        msg = str(e)
        if "ERR_TOO_MANY_REDIRECTS" in msg or "Too many redirects" in msg:
            logger.info("Detected TOO_MANY_REDIRECTS, may be already logged in")
            already_logged_in = True
        else:
            raise

    if not already_logged_in:
        try:
            page.wait_for_load_state("networkidle")
        except Exception:
            try:
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass

        try:
            with ctx.expect_page(timeout=5000) as popup_info:
                page.click("#passLogin > div > .fl", timeout=5000)
            qr_page = popup_info.value
            logger.info("Opened WeChat login page in new window")
            try:
                qr_page.wait_for_url(
                    re.compile(r"^https://open\.weixin\.qq\.com/.*"), timeout=10000
                )
            except Exception:
                pass
        except Exception:
            try:
                page.click("#passLogin > div > .fl", timeout=5000)
                try:
                    page.wait_for_url(
                        re.compile(r"^https://open\.weixin\.qq\.com/.*"), timeout=10000
                    )
                except Exception:
                    pass
                logger.info("Navigated to WeChat login page in current window")
            except Exception as e2:
                logger.warning(f"Click login entry failed: {e2}")

        deadline = time.time() + 180
        while time.time() < deadline:
            for p in ctx.pages:
                try:
                    url = p.url or ""
                except Exception:
                    url = ""
                if (
                    url.startswith("https://soa.swust.edu.cn")
                    or url == "chrome-error://chromewebdata/"  # TOO_MANY_REDIRECTS?
                ):
                    logger.info("Successfully logged in")
                    return p
            try:
                page.wait_for_timeout(500)
            except Exception:
                time.sleep(0.5)

    return page


logger = logging.getLogger(__name__)
