from playwright.sync_api import sync_playwright
import pathlib
import json
import logging
from logging_config import setup_logging
from tasks import (
    ensure_logged_in,
    goto_portal,
    fetch_course_table,
    fetch_exams,
    fetch_scores_points,
)

USER_DATA = pathlib.Path("user-data")
logger = logging.getLogger(__name__)


def main():
    setup_logging()
    logger.info("Launching chromium")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            USER_DATA,
            channel="chromium",
            headless=False,
            slow_mo=50,
        )

        logger.info("Ensuring user is logged in")
        page = ensure_logged_in(ctx)

        logger.info("Navigating to matrix")
        page = goto_portal(ctx, page)
        
        logger.info("Fetching course table")
        course_containers = fetch_course_table(ctx, page)
        exams = fetch_exams(ctx, page)

        logger.info("Fetching scores and points")
        scores_points = fetch_scores_points(ctx, page)

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
        logger.info(f"All done! Output saved to {out_path.resolve()}")

        input("Press Enter to exit the program...")
        ctx.close()


if __name__ == "__main__":
    main()
