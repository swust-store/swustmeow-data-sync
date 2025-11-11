import logging
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO, logfile: str = "output.log") -> None:
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(level)

    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter(log_format, datefmt=datefmt))

    try:
        p = Path(logfile)
        if p.parent:
            p.parent.mkdir(parents=True, exist_ok=True)
        logfile = str(p)
    except Exception:
        pass
    file_handler = logging.FileHandler(logfile, mode="w", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=datefmt))

    root.addHandler(stream_handler)
    root.addHandler(file_handler)
