import os
import sys
import shutil
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


def get_resource_path(relative_path):
    """获取资源文件路径，兼容 PyInstaller 打包。"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def find_ffmpeg():
    """返回 ffmpeg 可执行文件完整路径，找不到返回 None。"""
    bundled = get_resource_path("ffmpeg/ffmpeg-win-x86_64-v7.1.exe")
    if os.path.isfile(bundled):
        return bundled
    if imageio_ffmpeg is not None:
        try:
            p = imageio_ffmpeg.get_ffmpeg_exe()
            if p and os.path.isfile(p):
                return p
        except Exception:
            pass
    found = shutil.which("ffmpeg")
    if found:
        return found
    return None


def find_deno():
    """返回 deno 可执行文件完整路径，找不到返回 None。"""
    bundled = get_resource_path("deno/deno.exe")
    if os.path.isfile(bundled):
        return bundled
    found = shutil.which("deno")
    if found:
        return found
    return None


class YoutubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 视频下载器")
        self.root.geometry("680x520")
        self.root.minsize(600, 450)

        self.msg_queue = queue.Queue()
        self.download_thread = None
        self.ydl = None

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="视频 URL:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(4, 8))
        self.url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.url_var, font=("Consolas", 10)).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        ttk.Label(main_frame, text="输出目录:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=(4, 8))
        self.output_var = tk.StringVar(value=os.path.abspath("."))
        ttk.Entry(output_frame, textvariable=self.output_var, font=("Consolas", 10)).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(output_frame, text="浏览", command=self._browse_output, width=8).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding=10)
        options_frame.pack(fill=tk.X, pady=(4, 8))

        ttk.Label(options_frame, text="视频质量:").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
        self.quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(
            options_frame,
            textvariable=self.quality_var,
            values=["best", "1080p", "720p", "480p", "360p"],
            state="readonly",
            width=12,
        )
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        self.audio_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, text="仅下载音频 (MP3)", variable=self.audio_only_var
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 20))

        self.merge_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="合并音视频 (需要 FFmpeg)", variable=self.merge_var
        ).grid(row=0, column=3, sticky=tk.W)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(4, 8))
        self.download_btn = ttk.Button(
            button_frame, text="开始下载", command=self._start_download, width=16
        )
        self.download_btn.pack(side=tk.LEFT)

        ttk.Button(
            button_frame, text="查看可用格式", command=self._list_formats, width=16
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(main_frame, text="下载进度:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(4, 4))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="0%", width=6)
        self.progress_label.pack(side=tk.RIGHT, padx=(8, 0))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var, foreground="#555").pack(
            anchor=tk.W, pady=(0, 8)
        )

        ttk.Label(main_frame, text="日志:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(
            main_frame, height=12, font=("Consolas", 9), wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.log_text.config(state=tk.DISABLED)

    def _browse_output(self):
        path = filedialog.askdirectory(
            title="选择输出目录", initialdir=self.output_var.get()
        )
        if path:
            self.output_var.set(path)

    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _poll_queue(self):
        try:
            while True:
                action, data = self.msg_queue.get_nowait()
                if action == "log":
                    self._log(data)
                elif action == "status":
                    self.status_var.set(data)
                elif action == "progress":
                    self.progress_var.set(data)
                    self.progress_label.config(text=f"{data:.1f}%")
                elif action == "done":
                    self._on_download_done(data)
                elif action == "error":
                    self._on_download_error(data)
        except queue.Empty:
            pass
        self.root.after(150, self._poll_queue)

    def _install_ffmpeg(self):
        self.status_var.set("正在安装 FFmpeg...")
        self.download_btn.config(state=tk.DISABLED)

        def install_worker():
            import subprocess

            try:
                self.msg_queue.put(("log", "正在安装 imageio-ffmpeg..."))
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "imageio-ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    self.msg_queue.put(("log", "安装成功！"))
                    global imageio_ffmpeg
                    try:
                        import importlib

                        importlib.reload(imageio_ffmpeg)
                    except Exception:
                        pass
                    try:
                        import imageio_ffmpeg as new_ffmpeg

                        imageio_ffmpeg = new_ffmpeg
                    except ImportError:
                        pass
                    self.msg_queue.put(("status", "安装完成，准备下载..."))
                    self.root.after(1000, self._start_download)
                else:
                    err = result.stderr or result.stdout
                    self.msg_queue.put(("error", f"安装失败:\n{err[:500]}"))
            except subprocess.TimeoutExpired:
                self.msg_queue.put(("error", "安装超时，请重试"))
            except Exception as e:
                self.msg_queue.put(("error", f"安装异常: {e}"))

        threading.Thread(target=install_worker, daemon=True).start()

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频 URL")
            return
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showinfo("提示", "正在下载中，请稍候")
            return

        audio_only = self.audio_only_var.get()
        merge = self.merge_var.get()

        if (audio_only or merge) and not find_ffmpeg():
            result = messagebox.askyesno(
                "缺少 FFmpeg",
                "此操作需要 FFmpeg 但系统未找到。\n\n"
                "是否立即安装？（将自动安装 imageio-ffmpeg 包）",
            )
            if not result:
                return
            self._install_ffmpeg()
            return

        self.progress_var.set(0)
        self.download_btn.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.status_var.set("准备中...")

        output_dir = self.output_var.get().strip() or "."
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                messagebox.showerror("错误", f"无法创建目录: {e}")
                self.download_btn.config(state=tk.NORMAL)
                return

        self.download_thread = threading.Thread(
            target=self._download_worker,
            args=(
                url,
                output_dir,
                self.quality_var.get(),
                self.audio_only_var.get(),
                self.merge_var.get(),
            ),
            daemon=True,
        )
        self.download_thread.start()

    def _progress_hook(self, d):
        status = d.get("status", "")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                percent = downloaded / total * 100
                self.msg_queue.put(("progress", percent))
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")
            filename = d.get("filename", "")
            if filename:
                name = os.path.basename(filename)
                self.msg_queue.put(
                    ("status", f"下载中: {name[:40]}... {speed} ETA: {eta}")
                )
        elif status == "finished":
            self.msg_queue.put(("status", "下载完成，处理中..."))
            self.msg_queue.put(("progress", 100))

    def _download_worker(self, url, output_dir, quality, audio_only, merge):
        output_path = os.path.join(output_dir, "%(title)s.%(ext)s")

        ffmpeg_path = find_ffmpeg()
        deno_path = find_deno()

        ydl_opts = {
            "outtmpl": output_path,
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [self._progress_hook],
            "logger": self._YdlLogger(self.msg_queue),
        }
        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path
        if deno_path:
            ydl_opts["postprocessor_args"] = {
                "default": ["--js-runtime", deno_path]
            }

        if audio_only:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        else:
            if merge:
                ydl_opts["format"] = (
                    f"bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                )
                ydl_opts["merge_output_format"] = "mp4"
            else:
                ydl_opts["format"] = f"{quality}[ext=mp4]/best[ext=mp4]/best"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.ydl = ydl
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "unknown")
                self.msg_queue.put(("done", title))
        except yt_dlp.DownloadError as e:
            self.msg_queue.put(("error", str(e)))
        except Exception as e:
            self.msg_queue.put(("error", f"未知错误: {e}"))
        finally:
            self.ydl = None

    def _on_download_done(self, title):
        self.status_var.set(f"下载完成: {title[:50]}...")
        self.progress_var.set(100)
        self.download_btn.config(state=tk.NORMAL)
        self._log(f"\n下载完成: {title}")
        messagebox.showinfo("完成", f"下载完成:\n{title}")

    def _on_download_error(self, err):
        self.status_var.set("下载失败")
        self.download_btn.config(state=tk.NORMAL)
        self._log(f"\n错误: {err}")
        messagebox.showerror("下载失败", str(err))

    def _list_formats(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频 URL")
            return

        self.status_var.set("正在获取格式列表...")

        def worker():
            try:
                with yt_dlp.YoutubeDL(
                    {"listformats": True, "quiet": True}
                ) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get("formats", [])
                    lines = []
                    for f in formats:
                        fid = f.get("format_id", "")
                        ext = f.get("ext", "")
                        note = f.get("format_note", "")
                        res = f.get("resolution", "")
                        size = f.get("filesize", 0) or f.get("filesize_approx", 0)
                        size_str = f"{size / 1024 / 1024:.1f} MB" if size else "?"
                        lines.append(
                            f"ID: {fid:<10}  格式: {ext:<5}  质量: {note:<12}  "
                            f"分辨率: {res:<12}  大小: {size_str}"
                        )
                    self.msg_queue.put(("log", "\n".join(lines)))
                    self.msg_queue.put(("status", "格式列表已生成"))
            except Exception as e:
                self.msg_queue.put(("error", f"获取格式失败: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    class _YdlLogger:
        def __init__(self, q):
            self.q = q

        def debug(self, msg):
            if msg.startswith("[download]"):
                return
            self.q.put(("log", msg))

        def info(self, msg):
            self.q.put(("log", msg))

        def warning(self, msg):
            self.q.put(("log", "[警告] " + msg))

        def error(self, msg):
            self.q.put(("log", "[错误] " + msg))


def main():
    root = tk.Tk()
    app = YoutubeDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
