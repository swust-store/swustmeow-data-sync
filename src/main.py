from playwright.sync_api import sync_playwright
import pathlib
import json
import logging
import threading
import time
from logging_config import setup_logging
from ui import StatusWindow
from tasks import (
    ensure_logged_in,
    goto_portal,
    fetch_course_table,
    fetch_exams,
    fetch_scores_points,
)

USER_DATA = pathlib.Path("user-data")
logger = logging.getLogger("main")


def _worker(window: StatusWindow) -> None:
    start = time.perf_counter()
    logger.info("正在启动浏览器")
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                USER_DATA,
                channel="chromium",
                headless=False,
                slow_mo=50,
            )

            def _cleanup():
                try:
                    ctx.close()
                except Exception:
                    pass

            window.set_cleanup(_cleanup)

            window.set_status("等待用户登录")
            logger.info("正在确认登录状态")
            page = ensure_logged_in(
                ctx,
                on_wait_login=lambda: window.show_login_prompt(True),
                on_login_success=lambda: window.show_login_prompt(False),
            )

            window.set_status("进入教务系统")
            logger.info("进入教务系统")
            page = goto_portal(ctx, page)

            window.set_status("获取课程表")
            logger.info("获取课程表")
            course_containers = fetch_course_table(ctx, page)

            window.set_status("获取考试安排")
            logger.info("获取考试安排")
            exams = fetch_exams(ctx, page)

            window.set_status("获取成绩与绩点")
            logger.info("获取成绩与绩点")
            scores_points = fetch_scores_points(ctx, page)

            window.set_status("正在保存数据")
            output = {
                "courseContainers": course_containers,
                "exams": exams.get("exams", []),
                "scores": scores_points.get("scores", []),
                "points": scores_points.get("points", {}),
            }
            out_path = pathlib.Path("output.json")
            out_path.write_text(
                json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info(f"已保存数据到 {out_path.resolve()}")

            elapsed = time.perf_counter() - start
            window.on_done(elapsed)
    except Exception as e:
        logger.exception(f"致命错误: {e}")
        try:
            window.set_status("发生错误")
        except Exception:
            pass


def main():
    setup_logging()
    window = StatusWindow()
    window.attach_logger()

    t = threading.Thread(target=_worker, args=(window,), daemon=True)
    t.start()
    window.start()


if __name__ == "__main__":
    main()
