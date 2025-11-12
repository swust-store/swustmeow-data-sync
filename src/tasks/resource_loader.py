from __future__ import annotations
import os
import sys
from pathlib import Path


def read_js(name: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        cand = os.path.join(base, "tasks", "js", name)
        if os.path.isfile(cand):
            with open(cand, "r", encoding="utf-8") as f:
                return f.read()

    here = Path(__file__).resolve().parent
    p = here / "js" / name
    if p.is_file():
        return p.read_text(encoding="utf-8")

    p2 = Path("tasks") / "js" / name
    if p2.is_file():
        return p2.read_text(encoding="utf-8")

    raise FileNotFoundError(f"JS resource not found: {name}")
