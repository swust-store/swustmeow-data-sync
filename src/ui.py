from __future__ import annotations
import logging
import queue
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Callable, Optional


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

        self.status_var = tk.StringVar(value="当前状态：启动中")
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

    def attach_logger(self) -> None:
        logging.getLogger().addHandler(self._queue_handler)

    def set_status(self, text: str) -> None:
        self.status_var.set(f"当前状态：{text}")

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
