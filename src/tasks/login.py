from __future__ import annotations
from playwright.sync_api import BrowserContext, Page
import re
import time
import logging
from typing import Callable, Optional

LOGIN_URL = "https://cas.swust.edu.cn/authserver/login?service=http%3A%2F%2Fsoa.swust.edu.cn%2Fsys%2Fportal%2Fpage.jsp"

logger = logging.getLogger(__name__)


def ensure_logged_in(
    ctx: BrowserContext,
    on_wait_login: Optional[Callable[[], None]] = None,
    on_login_success: Optional[Callable[[], None]] = None,
) -> Page:
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    already_logged_in = False

    try:
        page.goto(LOGIN_URL)
    except Exception as e:
        msg = str(e)
        if "ERR_TOO_MANY_REDIRECTS" in msg or "Too many redirects" in msg:
            logger.info("检测到 TOO_MANY_REDIRECTS，视为已登录")
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
            logger.info("已打开微信扫码登录页")
            if on_wait_login:
                try:
                    on_wait_login()
                except Exception:
                    pass
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
                logger.info("已进入微信扫码登录页")
                if on_wait_login:
                    try:
                        on_wait_login()
                    except Exception:
                        pass
            except Exception as e2:
                logger.warning(f"点击登录入口失败: {e2}")

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
                    logger.info("登录成功")
                    if on_login_success:
                        try:
                            on_login_success()
                        except Exception:
                            pass
                    return p
            try:
                page.wait_for_timeout(500)
            except Exception:
                time.sleep(0.5)

    return page
