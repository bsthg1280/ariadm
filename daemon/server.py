#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AriaDM Local Daemon Server
Cung cấp API REST cục bộ cổng 1001 cho WebExtension và GUI/CLI điều khiển tác vụ tải đa luồng.
"""

import sys
import os
import json
import time
import re
import shutil
import subprocess
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 1001
TASKS = {}    # task_id -> task info
STREAMS = {}  # referer -> list of streams
_lock = threading.Lock()


def format_bytes(b):
    if not b or b <= 0:
        return "--"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} PB"


def run_download_task(task_id, url, referer="", filename=""):
    task = TASKS[task_id]
    video_dir = os.path.expanduser("~/Downloads")
    os.makedirs(video_dir, exist_ok=True)
    ytdlp = shutil.which("yt-dlp") or os.path.expanduser("~/.local/bin/yt-dlp")
    aria2 = shutil.which("aria2c")

    cmd = [ytdlp, "--newline", "--no-mtime", "-P", video_dir]
    if aria2:
        cmd.extend([
            "--downloader", "aria2c",
            "--downloader-args", "aria2c:-j 16 -x 16 -s 16 -k 1M --file-allocation=none"
        ])
    if referer:
        cmd.extend(["--referer", referer])

    if filename and not filename.startswith("http"):
        clean_fn = re.sub(r'[\\/*?:"<>|]', "", filename).strip()[:80]
        cmd.extend(["-o", f"{clean_fn}.%(ext)s"])
    else:
        cmd.extend(["-o", "%(title)s.%(ext)s"])

    cmd.append(url)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True
        )
        task["proc"] = proc
        task["status"] = "downloading"

        re_prog = re.compile(r'\[download\]\s+([\d\.]+)%\s+of\s+~?\s*([\d\.]+\w+)\s+at\s+([\d\.]+\w+/s)\s+ETA\s+([\d:]+)')
        re_dest = re.compile(r'\[download\]\s+Destination:\s+(.+)')

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            m_prog = re_prog.search(line)
            if m_prog:
                task["progress"] = float(m_prog.group(1))
                task["size"] = m_prog.group(2)
                task["speed"] = m_prog.group(3)
                task["eta"] = m_prog.group(4)
                continue

            m_dest = re_dest.search(line)
            if m_dest:
                task["file_path"] = m_dest.group(1).strip()
                if not task.get("title") or task["title"] == "Video Download":
                    task["title"] = os.path.basename(task["file_path"])
                continue

            if "[ffmpeg]" in line or "Merging" in line or "hlsnative" in line:
                task["speed"] = "Ghép video (ffmpeg)..."

        proc.wait()
        if proc.returncode == 0:
            task["progress"] = 100.0
            task["status"] = "completed"
            task["speed"] = "Hoàn thành"
            if shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "-i", "dialog-information", "AriaDM Downloader", f"Đã tải xong: {task.get('title', '')}"])
        else:
            if task.get("status") != "cancelled":
                task["status"] = "error"
                task["speed"] = "Lỗi tải xuống"
    except Exception as e:
        task["status"] = "error"
        task["speed"] = str(e)


class AriaDMHandler(BaseHTTPRequestHandler):
    def _send_cors(self, code=200, content_type="application/json"):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._send_cors(200)

    def do_GET(self):
        if self.path.startswith("/api/streams"):
            self._send_cors(200)
            all_streams = []
            with _lock:
                for ref, lst in STREAMS.items():
                    for s in lst:
                        all_streams.append({
                            "url": s["url"],
                            "kind": s["kind"],
                            "fn": s["fn"],
                            "ref": s["ref"],
                            "resolution": s.get("resolution", "--"),
                            "size": s.get("size", "--"),
                            "t": s["t"]
                        })
            self.wfile.write(json.dumps({"streams": all_streams[-50:]}).encode("utf-8"))
            return

        if self.path.startswith("/api/tasks"):
            self._send_cors(200)
            task_list = []
            with _lock:
                for tid, t in list(TASKS.items()):
                    task_list.append({
                        "id": tid,
                        "url": t.get("url", ""),
                        "title": t.get("title", ""),
                        "progress": t.get("progress", 0.0),
                        "size": t.get("size", "--"),
                        "speed": t.get("speed", "--"),
                        "eta": t.get("eta", "--"),
                        "status": t.get("status", "pending"),
                        "file_path": t.get("file_path", "")
                    })
            self.wfile.write(json.dumps({"tasks": task_list}).encode("utf-8"))
            return

        self._send_cors(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="ignore")

        if self.path == "/download":
            try:
                data = json.loads(body)
                url = data.get("url", "")
                referer = data.get("referer", "")
                filename = data.get("filename", "")
                task_id = str(int(time.time() * 1000))[-8:]
                with _lock:
                    TASKS[task_id] = {
                        "id": task_id,
                        "url": url,
                        "title": filename or "Video Download",
                        "progress": 0.0,
                        "size": "--",
                        "speed": "Đang khởi tạo...",
                        "eta": "--",
                        "status": "starting",
                        "file_path": ""
                    }
                threading.Thread(target=run_download_task, args=(task_id, url, referer, filename), daemon=True).start()
                self._send_cors(200)
                self.wfile.write(json.dumps({"status": "ok", "task_id": task_id}).encode("utf-8"))
            except Exception as e:
                self._send_cors(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/register_stream":
            try:
                data = json.loads(body)
                url = data.get("url", "")
                ref = (data.get("referer", "") or "").split("#")[0]
                fn = data.get("filename", "")
                kind = "video"
                if ".m3u8" in url or ".vl" in url:
                    kind = "hls"
                elif "youtube.com" in url or "youtu.be" in url:
                    kind = "youtube"

                with _lock:
                    lst = STREAMS.setdefault(ref, [])
                    if not any(s["url"] == url for s in lst):
                        entry = {
                            "url": url,
                            "ref": ref,
                            "fn": fn,
                            "kind": kind,
                            "resolution": "1080p",
                            "size": "--",
                            "t": time.time()
                        }
                        lst.append(entry)
                        del lst[:-30]
                self._send_cors(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self._send_cors(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/cancel_task":
            try:
                data = json.loads(body)
                task_id = data.get("task_id", "")
                with _lock:
                    task = TASKS.get(task_id)
                    if task and "proc" in task and task["proc"].poll() is None:
                        task["proc"].terminate()
                        task["status"] = "cancelled"
                        task["speed"] = "Đã huỷ"
                self._send_cors(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self._send_cors(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/clear_streams":
            try:
                with _lock:
                    STREAMS.clear()
                self._send_cors(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self._send_cors(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/clear_tasks":
            try:
                data = json.loads(body) if body else {}
                all_clear = data.get("all", False)
                with _lock:
                    if all_clear:
                        for t in TASKS.values():
                            if "proc" in t and t["proc"].poll() is None:
                                try:
                                    t["proc"].terminate()
                                except:
                                    pass
                        TASKS.clear()
                    else:
                        for tid in list(TASKS.keys()):
                            if TASKS[tid].get("status") in ("completed", "cancelled", "error"):
                                del TASKS[tid]
                self._send_cors(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self._send_cors(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/delete_task":
            try:
                data = json.loads(body)
                task_id = data.get("task_id", "")
                delete_file = data.get("delete_file", False)
                with _lock:
                    task = TASKS.get(task_id)
                    if task:
                        if "proc" in task and task["proc"].poll() is None:
                            try:
                                task["proc"].terminate()
                            except:
                                pass
                        if delete_file and task.get("file_path") and os.path.exists(task["file_path"]):
                            try:
                                os.remove(task["file_path"])
                            except:
                                pass
                        del TASKS[task_id]
                self._send_cors(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self._send_cors(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self._send_cors(404)


def main():
    server = HTTPServer(("127.0.0.1", PORT), AriaDMHandler)
    print(f"🚀 AriaDM Daemon đang lắng nghe tại http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng AriaDM Daemon.")


if __name__ == "__main__":
    main()
