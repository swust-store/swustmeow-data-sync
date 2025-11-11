from __future__ import annotations
import logging
import queue
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Callable, Optional

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


class QueueLogHandler(logging.Handler):
    def __init__(self, q: "queue.Queue[logging.LogRecord]") -> None:
        super().__init__()
        self.q = q

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.q.put(record, block=False)
        except Exception:
            pass


class StatusWindow:
    def __init__(self, title: str = "西科喵数据同步工具") -> None:
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("820x480")

        top = ttk.Frame(self.root, padding=(14, 12))
        top.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="当前状态: 启动中")
        self.status_label = ttk.Label(
            top, textvariable=self.status_var, font=("Segoe UI", 12, "bold")
        )
        self.status_label.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(top, mode="indeterminate", length=160)
        self.progress.pack(side=tk.RIGHT)
        self.progress.start(20)

        self.banner = ttk.Frame(self.root, padding=(14, 8))
        self.banner.pack(fill=tk.X)
        self.banner.configure(style="Info.TFrame")

        self.banner_text = tk.StringVar(value="")
        self.banner_label = ttk.Label(
            self.banner, textvariable=self.banner_text, font=("Segoe UI", 10)
        )
        self.banner_label.pack(side=tk.LEFT)
        self.banner.pack_forget()

        mid = ttk.Frame(self.root, padding=(12, 8))
        mid.pack(fill=tk.BOTH, expand=True)
        self.log_widget = ScrolledText(
            mid, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10)
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(self.root, padding=(12, 10))
        bottom.pack(fill=tk.X)
        self.elapsed_var = tk.StringVar(value="")
        self.elapsed_label = ttk.Label(bottom, textvariable=self.elapsed_var)
        self.elapsed_label.pack(side=tk.LEFT)

        self.close_btn = ttk.Button(bottom, text="关闭", command=self._on_close)
        self.close_btn.pack(side=tk.RIGHT)
        self.close_btn.state(["disabled"])

        self.actions: Optional[ttk.Frame] = None
        self._on_cloud: Optional[Callable[[], None]] = None
        self._on_offline: Optional[Callable[[], None]] = None

        style = ttk.Style(self.root)
        try:
            style.theme_use(style.theme_use())
        except Exception:
            pass
        style.configure("Info.TFrame", background="#e6f2ff")
        style.configure("Info.TLabel", background="#e6f2ff")

        self._log_q: "queue.Queue[logging.LogRecord]" = queue.Queue()
        self._queue_handler = QueueLogHandler(self._log_q)
        self._queue_handler.setLevel(logging.INFO)
        self._queue_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        self._cleanup: Optional[Callable[[], None]] = None
        self._finished = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._drain_logs()

        self._choice_frame: Optional[ttk.Frame] = None
        self._modal: Optional[tk.Toplevel] = None

    def attach_logger(self) -> None:
        logging.getLogger().addHandler(self._queue_handler)

    def set_status(self, text: str) -> None:
        self.status_var.set(f"当前状态: {text}")

    def show_actions(
        self, on_cloud: Callable[[], None], on_offline: Callable[[], None]
    ) -> None:
        if self.actions is None:
            frm = ttk.Frame(self.root, padding=(12, 8))
            label = ttk.Label(frm, text="选择后续操作")
            label.pack(side=tk.LEFT, padx=(0, 12))
            btn_cloud = ttk.Button(
                frm, text="上传云端并获取导入码", command=lambda: self._do_cloud()
            )
            btn_cloud.pack(side=tk.LEFT, padx=(0, 8))
            btn_off = ttk.Button(
                frm, text="生成离线导入二维码", command=lambda: self._do_offline()
            )
            btn_off.pack(side=tk.LEFT)
            self.actions = frm
        self._on_cloud = on_cloud
        self._on_offline = on_offline
        self.actions.pack(fill=tk.X)

    def hide_actions(self) -> None:
        if self.actions is not None:
            self.actions.pack_forget()

    def _do_cloud(self) -> None:
        cb = self._on_cloud
        if cb:
            cb()

    def _do_offline(self) -> None:
        cb = self._on_offline
        if cb:
            cb()

    def show_login_prompt(self, visible: bool) -> None:
        if visible:
            self.banner_text.set("请在浏览器中扫描微信二维码完成登录")
            self.banner.pack(fill=tk.X)
        else:
            self.banner.pack_forget()

    def append_log(self, line: str) -> None:
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, line + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state=tk.DISABLED)

    def on_done(self, elapsed_seconds: float) -> None:
        self._finished = True
        self.progress.stop()
        self.set_status("已完成")
        self.elapsed_var.set(f"耗时 {elapsed_seconds:.2f}s")
        self.close_btn.state(["!disabled"])

    def set_cleanup(self, fn: Optional[Callable[[], None]]) -> None:
        self._cleanup = fn

    def _drain_logs(self) -> None:
        try:
            while True:
                record = self._log_q.get_nowait()
                try:
                    msg = self._queue_handler.format(record)
                except Exception:
                    msg = record.getMessage()
                self.append_log(msg)
        except queue.Empty:
            pass
        self.root.after(80, self._drain_logs)

    def _on_close(self) -> None:
        try:
            if self._cleanup is not None:
                self._cleanup()
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()

    def start(self) -> None:
        self.root.mainloop()

    def show_choice(
        self, label_text: str, options: list[tuple[str, Callable[[], None]]]
    ) -> None:
        if self._choice_frame is None:
            frm = ttk.Frame(self.root, padding=(12, 8))
            self._choice_label = ttk.Label(frm, text=label_text)
            self._choice_label.pack(side=tk.LEFT, padx=(0, 12))
            self._choice_buttons: list[ttk.Button] = []
            self._choice_frame = frm
        else:
            # Reset
            for b in getattr(self, "_choice_buttons", []):
                try:
                    b.destroy()
                except Exception:
                    pass
            self._choice_buttons = []
            self._choice_label.configure(text=label_text)

        for text, cb in options:
            btn = ttk.Button(self._choice_frame, text=text, command=cb)
            btn.pack(side=tk.LEFT, padx=(0, 8))
            self._choice_buttons.append(btn)
        self._choice_frame.pack(fill=tk.X)

    def hide_choice(self) -> None:
        if self._choice_frame is not None:
            self._choice_frame.pack_forget()

    def ask_choice_modal(
        self, title: str, label_text: str, options: list[tuple[str, Callable[[], None]]]
    ) -> None:
        top = tk.Toplevel(self.root)
        top.title(title)
        top.transient(self.root)
        try:
            top.grab_set()
        except Exception:
            pass
        frm = ttk.Frame(top, padding=(16, 12))
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text=label_text).pack(anchor=tk.W, pady=(0, 8))
        btns = ttk.Frame(frm)
        btns.pack(anchor=tk.W)

        def _wrap(cb: Callable[[], None]):
            def _inner():
                try:
                    try:
                        top.grab_release()
                    except Exception:
                        pass
                    cb()
                finally:
                    try:
                        top.destroy()
                    except Exception:
                        pass

            return _inner

        for text, cb in options:
            ttk.Button(btns, text=text, command=_wrap(cb)).pack(
                side=tk.LEFT, padx=(0, 8)
            )
        try:
            self.root.update_idletasks()
            top.update_idletasks()
            pw = self.root.winfo_width() or self.root.winfo_reqwidth()
            ph = self.root.winfo_height() or self.root.winfo_reqheight()
            px = self.root.winfo_rootx()
            py = self.root.winfo_rooty()
            tw = top.winfo_width() or top.winfo_reqwidth()
            th = top.winfo_height() or top.winfo_reqheight()
            x = int(px + (pw - tw) / 2)
            y = int(py + (ph - th) / 2)
            top.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        def _on_modal_close():
            try:
                top.grab_release()
            except Exception:
                pass
            self._on_close()

        try:
            top.protocol("WM_DELETE_WINDOW", _on_modal_close)
        except Exception:
            pass

        self._modal = top

    def show_import_code_modal(self, import_code: str) -> None:
        top = tk.Toplevel(self.root)
        top.title("导入码")
        top.transient(self.root)
        try:
            top.grab_set()
        except Exception:
            pass
        frm = ttk.Frame(top, padding=(20, 18))
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="导入码").pack(anchor=tk.CENTER)
        code_lbl = ttk.Label(frm, text=import_code, font=("Consolas", 26, "bold"))
        code_lbl.pack(anchor=tk.CENTER, pady=(6, 10))
        ttk.Label(
            frm, text="请进入西科喵->我的->导入数据->使用导入码，输入此导入码完成导入"
        ).pack(anchor=tk.CENTER, pady=(0, 10))

        btns = ttk.Frame(frm)
        btns.pack(anchor=tk.CENTER)

        def _copy():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(import_code)
            except Exception:
                pass

        ttk.Button(btns, text="复制导入码", command=_copy).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btns, text="已输入 退出", command=self._on_close).pack(side=tk.LEFT)

        try:
            self.root.update_idletasks()
            top.update_idletasks()
            pw = self.root.winfo_width() or self.root.winfo_reqwidth()
            ph = self.root.winfo_height() or self.root.winfo_reqheight()
            px = self.root.winfo_rootx()
            py = self.root.winfo_rooty()
            tw = top.winfo_width() or top.winfo_reqwidth()
            th = top.winfo_height() or top.winfo_reqheight()
            x = int(px + (pw - tw) / 2)
            y = int(py + (ph - th) / 2)
            top.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        def _on_close_modal():
            try:
                top.grab_release()
            except Exception:
                pass
            self._on_close()

        try:
            top.protocol("WM_DELETE_WINDOW", _on_close_modal)
        except Exception:
            pass


class QRWindow:
    def __init__(
        self,
        parent: tk.Tk,
        pil_images: list,
        is_multi: bool,
        on_done: Callable[[], None],
        interval_ms: int = 500,
    ) -> None:
        if ImageTk is None:
            raise RuntimeError("缺少 Pillow 库，无法显示二维码")
        self.top = tk.Toplevel(parent)
        self.top.title("离线导入二维码")
        self.top.geometry("720x820")
        self.on_done = on_done
        self.is_multi = is_multi
        self.interval_ms = interval_ms

        self.pil_images = pil_images
        self.tk_image = None

        wrap = ttk.Frame(self.top, padding=(12, 12))
        wrap.pack(fill=tk.BOTH, expand=True)
        self.label = ttk.Label(wrap)
        self.label.pack(expand=True)

        ttk.Label(
            wrap, text="请进入西科喵->我的->导入数据->扫描二维码，扫描此二维码完成导入"
        ).pack(anchor=tk.CENTER, pady=(0, 10))

        bottom = ttk.Frame(wrap)
        bottom.pack(fill=tk.X, pady=(8, 0))
        hint = ttk.Label(bottom, text=("多帧将自动轮播" if is_multi else "单帧二维码"))
        hint.pack(side=tk.LEFT)

        self.counter_var = tk.StringVar(value=f"1/{len(self.pil_images)}")
        self.counter_label = ttk.Label(bottom, textvariable=self.counter_var)
        self.counter_label.pack(side=tk.LEFT, padx=(12, 0))
        btn = ttk.Button(bottom, text="已扫描 退出", command=self._done)
        btn.pack(side=tk.RIGHT)

        self._idx = 0
        self._play_job = None
        self._resize_job = None
        try:
            self.top.bind("<Configure>", lambda e: self._schedule_resize())
        except Exception:
            pass

        self._render_image()
        if self.is_multi:
            self._start_playback()

    def _render_image(self) -> None:
        try:
            max_w, max_h = self._max_render_size()
        except Exception:
            max_w, max_h = 640, 640

        img = self.pil_images[self._idx]
        if Image is not None:
            src_w, src_h = getattr(img, "size", (max_w, max_h))
            scale = min(max_w / src_w, max_h / src_h, 1.0)
            if scale < 1.0:
                new_size = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                disp = img.resize(new_size, Image.NEAREST)
            else:
                disp = img
        else:
            disp = img
        self.tk_image = ImageTk.PhotoImage(disp)
        self.label.configure(image=self.tk_image)
        self.label.image = self.tk_image
        self.counter_var.set(f"{self._idx + 1}/{len(self.pil_images)}")

    def _start_playback(self) -> None:
        self._cancel_playback()
        self._play_job = self.top.after(self.interval_ms, self._tick)

    def _cancel_playback(self) -> None:
        try:
            if self._play_job is not None:
                self.top.after_cancel(self._play_job)
        except Exception:
            pass
        self._play_job = None

    def _tick(self) -> None:
        self._idx = (self._idx + 1) % len(self.pil_images)
        self._render_image()
        self._play_job = self.top.after(self.interval_ms, self._tick)

    def _max_render_size(self) -> tuple[int, int]:
        self.top.update_idletasks()
        w = self.top.winfo_width()
        h = self.top.winfo_height()
        max_w = max(120, w - 48)
        max_h = max(160, h - 200)
        return max_w, max_h

    def _schedule_resize(self) -> None:
        try:
            if self._resize_job is not None:
                self.top.after_cancel(self._resize_job)
        except Exception:
            pass
        self._resize_job = self.top.after(80, self._render_image)

    def _done(self) -> None:
        try:
            self._cancel_playback()
        except Exception:
            pass
        try:
            if self._resize_job is not None:
                self.top.after_cancel(self._resize_job)
        except Exception:
            pass
        try:
            self.top.destroy()
        except Exception:
            pass
        try:
            self.on_done()
        except Exception:
            pass
