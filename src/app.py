from __future__ import annotations
import json
import logging
import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime
import urllib.request

from playwright.sync_api import sync_playwright

from ui import StatusWindow, QRWindow
from qr_utils import make_qr_pil_images_from_output
from tasks import (
    ensure_logged_in,
    goto_portal,
    fetch_course_table,
    fetch_exams,
    fetch_scores_points,
    fetch_experiment_course_containers,
)

logger = logging.getLogger(__name__)


def _app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        try:
            return Path(sys.executable).resolve().parent
        except Exception:
            return Path.cwd()
    return Path.cwd()


OUTPUT_DIR = _app_base_dir() / "output"
OUTPUT_JSON = OUTPUT_DIR / "output.json"


def ensure_output() -> None:
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _post_export(window: StatusWindow, out_path: Path, elapsed: float) -> None:
    def on_cloud() -> None:
        window.set_status("正在上传数据")

        def _upload():
            try:
                payload = json.loads(Path(out_path).read_text(encoding="utf-8"))
            except Exception as e:
                logger.exception(f"读取输出数据失败: {e}")
                window.root.after(0, lambda: window.set_status("读取数据失败"))
                return

            try:
                url = "https://next.meowhope.com/api/data_sync/new"
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    resp_text = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                logger.exception(f"上传失败: {e}")
                window.root.after(0, lambda: window.set_status("上传失败"))
                return

            try:
                data = json.loads(resp_text)
                import_code = None
                if isinstance(data, dict) and data.get("code") == 200:
                    inner = data.get("data") or {}
                    import_code = inner.get("code")
                if import_code:

                    def _show():
                        window.set_status("导入码已生成")
                        try:
                            window.show_import_code_modal(import_code)
                        except Exception:
                            pass

                    window.root.after(0, _show)
                else:
                    logger.warning(f"云端返回异常: {data}")
                    window.root.after(0, lambda: window.set_status("云端返回异常"))
            except Exception as e:
                logger.exception(f"解析响应失败: {e}")
                window.root.after(0, lambda: window.set_status("解析响应失败"))

        threading.Thread(target=_upload, daemon=True).start()

    def on_offline() -> None:
        window.set_status("正在生成离线导入二维码")

        def _gen_and_show():
            try:
                is_multi, pil_images = make_qr_pil_images_from_output(out_path)
            except Exception as e:
                logger.exception(f"生成二维码失败: {e}")
                window.root.after(
                    0,
                    lambda: (
                        window.set_status("生成二维码失败"),
                        window.on_done(elapsed),
                    ),
                )
                return

            # output/qrcodes/<timestamp>/
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = OUTPUT_DIR / "qrcodes" / ts
            try:
                save_dir.mkdir(parents=True, exist_ok=True)
                if is_multi:
                    total = len(pil_images)
                    for i, img in enumerate(pil_images, start=1):
                        fname = save_dir / f"frame_{i:03d}_of_{total:03d}.png"
                        try:
                            img.save(fname)
                        except Exception:
                            pass
                else:
                    try:
                        pil_images[0].save(save_dir / "single.png")
                    except Exception:
                        pass
                logger.info(f"二维码已保存到 {save_dir}")
            except Exception as e:
                logger.warning(f"保存二维码失败: {e}")

            def _open():
                try:
                    QRWindow(
                        window.root,
                        pil_images,
                        is_multi,
                        on_done=window._on_close,
                        interval_ms=1000,
                    )
                    window.set_status("请使用导入功能扫描二维码")
                except Exception as e:
                    logger.exception(f"显示二维码失败: {e}")
                    window.set_status("显示二维码失败")
                    window.on_done(elapsed)

            window.root.after(0, _open)

        threading.Thread(target=_gen_and_show, daemon=True).start()

    def _show():
        window.set_status("请选择后续操作")
        window.show_actions(on_cloud, on_offline)
        window.ask_choice_modal(
            "请选择后续操作",
            "请选择后续操作",
            [("上传云端并获取导入码", on_cloud), ("生成离线导入二维码", on_offline)],
        )

    window.root.after(0, _show)


def _choose_and_launch_context(p, user_data_dir: Path):
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")
    os.environ.setdefault("PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS", "1")

    preferred = []
    env_ch = os.environ.get("SWUSTMEOW_BROWSER_CHANNEL")
    if env_ch:
        preferred.append(env_ch)
    preferred.extend(["msedge", "chrome", "msedge-beta", "chrome-beta", "chromium"])

    last_err = None
    udd = str(Path(user_data_dir).resolve())

    for ch in preferred:
        try:
            kwargs = dict(user_data_dir=udd, headless=False, slow_mo=50)
            if ch:
                kwargs["channel"] = ch
            return p.chromium.launch_persistent_context(**kwargs)
        except Exception as e:
            logger.warning(f"launch_persistent_context failed for channel={ch}: {e}")
            last_err = e
            continue

    if last_err:
        raise last_err
    raise RuntimeError("No available browser channel found for Playwright")


def worker_fetch(window: StatusWindow, user_data_dir: Path) -> None:
    start = time.perf_counter()
    logger.info("启动 Chromium 持久化上下文")
    ensure_output()
    try:
        with sync_playwright() as p:
            ctx = _choose_and_launch_context(p, user_data_dir)

            def _cleanup() -> None:
                try:
                    ctx.close()
                except Exception:
                    pass

            window.set_cleanup(_cleanup)

            window.root.after(0, lambda: window.set_status("等待用户登录"))
            logger.info("正在确认登录状态")
            page = ensure_logged_in(
                ctx,
                on_wait_login=lambda: window.root.after(
                    0, lambda: window.show_login_prompt(True)
                ),
                on_login_success=lambda: window.root.after(
                    0, lambda: window.show_login_prompt(False)
                ),
            )

            window.root.after(0, lambda: window.set_status("获取课表"))
            logger.info("进入教务系统并获取课表")
            page = goto_portal(ctx, page)
            course_containers = fetch_course_table(ctx, page)

            window.root.after(0, lambda: window.set_status("获取考试安排"))
            logger.info("获取考试安排")
            exams = fetch_exams(ctx, page)

            window.root.after(0, lambda: window.set_status("获取成绩与绩点"))
            logger.info("获取成绩与绩点")
            scores_points = fetch_scores_points(ctx, page)

            normal_terms = []
            for c in course_containers or []:
                t = (c or {}).get("term")
                if t and t not in normal_terms:
                    normal_terms.append(t)
            window.root.after(0, lambda: window.set_status("获取实验课表"))
            logger.info("开始获取完整实验课表")
            exp_containers = fetch_experiment_course_containers(page, normal_terms)

            # 合并实验课表到对应学期的课表容器中
            term_index = {c["term"]: c for c in course_containers}
            for exp in exp_containers:
                term = exp["term"]
                if term in term_index:
                    term_index[term]["entries"].extend(exp["entries"])
                else:
                    course_containers.append(exp)

            window.root.after(0, lambda: window.set_status("写入输出 JSON"))
            output = {
                "courseContainers": course_containers,
                "exams": exams.get("exams", []),
                "scores": scores_points.get("scores", []),
                "points": scores_points.get("points", {}),
            }
            OUTPUT_JSON.write_text(
                json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info(f"已写入输出 JSON 到 {OUTPUT_JSON.resolve()}")

            elapsed = time.perf_counter() - start
            _post_export(window, OUTPUT_JSON, elapsed)
    except Exception as e:
        logger.exception(f"致命错误: {e}")
        try:
            window.set_status("发生错误")
        except Exception:
            pass


def start_with_existing(window: StatusWindow, out_path: Path) -> None:
    ensure_output()
    window.set_status("使用已有数据")
    _post_export(window, out_path, elapsed=0.0)
