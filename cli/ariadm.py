#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AriaDM CLI - Trình Tải Video Đa Luồng & Bóc Tách Web Thông Minh Cho Linux
Sử dụng:
    ariadm <URL_trang_web>
    ariadm <URL> -q 1080p
    ariadm <URL> --info
"""

import sys
import os
import argparse
import subprocess
import shutil
import re

# Thêm đường dẫn hiện tại vào sys.path để import sniffer_engine
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sniffer_engine import VideoSniffer

# ANSI Colors
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def print_banner():
    banner = f"""{CYAN}{BOLD}
╔═══════════════════════════════════════════════════════════════╗
║   🚀 AriaDM CLI — Video Sniffer & Multi-thread Downloader     ║
║   (Engine: yt-dlp + aria2c 16 luồng + ffmpeg)                 ║
╚═══════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


def sanitize_filename(name):
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean[:100] if clean else "video"


def download_stream(target, dest_dir, connections=16, custom_name=None):
    ytdlp_bin = shutil.which("yt-dlp") or os.path.expanduser("~/.local/bin/yt-dlp")
    aria2_bin = shutil.which("aria2c")

    if not ytdlp_bin:
        print(f"{RED}❌ Không tìm thấy `yt-dlp`! Hãy cài đặt bằng: pipx install yt-dlp{RESET}")
        return False

    os.makedirs(dest_dir, exist_ok=True)
    stream_url = target.get("stream_url")
    referer = target.get("referer", "")
    title = target.get("title", "Video")
    format_arg = target.get("format_arg")

    out_tmpl = f"{sanitize_filename(custom_name or title)}.%(ext)s"

    cmd = [
        ytdlp_bin,
        "-P", dest_dir,
        "-o", out_tmpl,
        "--newline",
        "--no-mtime"
    ]

    # Sử dụng aria2c tăng tốc đa luồng nếu có
    if aria2_bin:
        cmd.extend([
            "--downloader", "aria2c",
            "--downloader-args", f"aria2c:-j {connections} -x {connections} -s {connections} -k 1M --file-allocation=none"
        ])

    if referer:
        cmd.extend(["--referer", referer])

    if format_arg:
        cmd.extend(["-f", format_arg])

    cmd.append(stream_url)

    print(f"\n{GREEN}{BOLD}⚡ Bắt đầu tải với aria2c ({connections} luồng song song)...{RESET}")
    print(f"📁 Thư mục lưu: {CYAN}{dest_dir}{RESET}")
    print(f"🎬 Tên file dự kiến: {YELLOW}{out_tmpl}{RESET}\n")

    try:
        proc = subprocess.run(cmd)
        if proc.returncode == 0:
            print(f"\n{GREEN}{BOLD}✅ TẢI XUỐNG HOÀN TẤT THÀNH CÔNG!{RESET}")
            # Gửi thông báo hệ thống desktop
            if shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "-i", "dialog-information", "AriaDM Downloader", f"Đã tải xong: {title}"])
            return True
        else:
            print(f"\n{RED}❌ Quá trình tải gặp lỗi (mã thoát: {proc.returncode}){RESET}")
            return False
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️ Người dùng đã huỷ tác vụ tải.{RESET}")
        return False


def main():
    parser = argparse.ArgumentParser(description="AriaDM - Tự động bóc tách web & tải video đa luồng")
    parser.add_argument("url", nargs="?", help="URL trang web hoặc link video (YouTube, Motchill, VLXX, HLS...)")
    parser.add_argument("-q", "--quality", help="Độ phân giải mong muốn (1080p, 720p, 480p, best)")
    parser.add_argument("-o", "--output", help="Tên file hoặc đường dẫn lưu file")
    parser.add_argument("-d", "--dir", default=os.path.expanduser("~/Downloads"), help="Thư mục tải về (Mặc định: ~/Downloads)")
    parser.add_argument("-c", "--connections", type=int, default=16, help="Số luồng tải aria2c (Mặc định: 16)")
    parser.add_argument("--info", action="store_true", help="Chỉ phân tích và hiển thị thông tin luồng mà không tải")

    args = parser.parse_args()

    print_banner()

    url = args.url
    if not url:
        try:
            url = input(f"{BOLD}🔗 Nhập URL trang web cần tải:{RESET} ").strip()
        except KeyboardInterrupt:
            print("\nThoát.")
            return

    if not url:
        print(f"{RED}❌ Vui lòng cung cấp URL hợp lệ!{RESET}")
        return

    print(f"\n{CYAN}🔍 Đang phân tích trang web: {url}...{RESET}")
    sniffer = VideoSniffer()
    info = sniffer.analyze(url)

    if not info or not info.get("formats"):
        print(f"{RED}❌ {info.get('error', 'Không tìm thấy video nào có thể tải trên trang này!')}{RESET}")
        return

    title = info.get("title", "Video")
    engine = info.get("engine", "generic")
    formats = info.get("formats", [])
    referer = info.get("referer", url)

    print(f"\n{GREEN}{BOLD}🎬 Tiêu đề:{RESET} {title}")
    print(f"{MAGENTA}🌐 Engine nhận diện:{RESET} {engine.upper()} | {len(formats)} lựa chọn chất lượng\n")

    print(f"{BOLD}{'STT':<5} {'ĐỘ PHÂN GIẢI':<22} {'DUNG LƯỢNG':<16} {'LOẠI STREAM':<15}{RESET}")
    print("─" * 62)

    for idx, f in enumerate(formats, 1):
        res = f.get("resolution", "--")
        sz = f.get("size", "--")
        stype = f.get("type", "Video")
        print(f"{CYAN}{idx:<5}{RESET} {GREEN}{res:<22}{RESET} {YELLOW}{sz:<16}{RESET} {stype:<15}")

    print("─" * 62)

    if args.info:
        print(f"\n{YELLOW}ℹ️ Chế độ --info: Đã phân tích xong, không thực hiện tải.{RESET}")
        return

    # Chọn chất lượng để tải
    chosen = None
    if args.quality:
        q_target = args.quality.lower().replace("p", "")
        if q_target == "best":
            chosen = formats[0]
        else:
            for f in formats:
                if q_target in f.get("resolution", "").lower():
                    chosen = f
                    break

    if not chosen:
        if len(formats) == 1:
            chosen = formats[0]
        else:
            try:
                choice = input(f"\n{BOLD}👉 Chọn số thứ tự để tải [1-{len(formats)}] (Mặc định: 1 - Chất lượng tốt nhất):{RESET} ").strip()
                if not choice:
                    chosen = formats[0]
                else:
                    idx = int(choice) - 1
                    if 0 <= idx < len(formats):
                        chosen = formats[idx]
                    else:
                        print(f"{YELLOW}Lựa chọn không hợp lệ, dùng bản cao nhất [1].{RESET}")
                        chosen = formats[0]
            except (ValueError, KeyboardInterrupt):
                print("\nThoát.")
                return

    chosen_target = {
        "stream_url": chosen.get("stream_url"),
        "referer": referer,
        "title": title,
        "format_arg": chosen.get("format_arg")
    }

    download_stream(
        chosen_target,
        dest_dir=args.dir,
        connections=args.connections,
        custom_name=args.output
    )


if __name__ == "__main__":
    main()
