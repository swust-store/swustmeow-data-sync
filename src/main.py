import pathlib
import logging
import threading
from logging_config import setup_logging
from ui import StatusWindow
from app import worker_fetch, ensure_output, OUTPUT_JSON, start_with_existing


USER_DATA = pathlib.Path("user-data")
logger = logging.getLogger("main")


def main():
    setup_logging(logfile=str(pathlib.Path("output") / "output.log"))
    ensure_output()

    window = StatusWindow()
    window.attach_logger()

    candidates = [
        OUTPUT_JSON,
        pathlib.Path("output.json"),
        pathlib.Path("output") / "output.json",
    ]
    existing_path = next((p for p in candidates if p.exists()), None)

    if existing_path is not None:
        window.set_status("检测到已有数据")

        def use_existing():
            start_with_existing(window, existing_path)

        def fetch_new():
            t = threading.Thread(
                target=worker_fetch, args=(window, USER_DATA), daemon=True
            )
            t.start()

        window.show_choice(
            "发现已有数据 是否使用",
            [
                ("使用已有数据", use_existing),
                ("重新获取数据", fetch_new),
            ],
        )
        window.root.after(
            0,
            lambda: window.ask_choice_modal(
                "是否使用已有数据",
                f"发现 {existing_path} 是否使用",
                [("使用已有数据", use_existing), ("重新获取数据", fetch_new)],
            ),
        )
    else:
        t = threading.Thread(target=worker_fetch, args=(window, USER_DATA), daemon=True)
        t.start()

    window.start()


if __name__ == "__main__":
    main()
