#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AriaDM - Web Video Sniffer & Extractor Engine
Tự động phân tích trang web và bóc tách luồng video chất lượng cao (YouTube, VLXX, Motchill, HLS/DASH/MP4).
"""

import sys
import os
import re
import json
import urllib.request
import urllib.parse
import shutil
import subprocess

DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


def format_bytes(b):
    if not b or b <= 0:
        return "--"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} PB"


class VideoSniffer:
    def __init__(self, ua=DEFAULT_UA):
        self.ua = ua

    def fetch_url(self, url, headers=None, method='GET', data=None, timeout=8):
        h = {'User-Agent': self.ua}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, headers=h, method=method, data=data)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')

    def analyze(self, page_url):
        """Phân tích trang web và trả về thông tin các luồng tải."""
        page_url = page_url.strip()
        u_lower = page_url.lower()

        # 1. YouTube & các nền tảng lớn được hỗ trợ chính quy
        if any(d in u_lower for d in ("youtube.com", "youtu.be", "tiktok.com", "facebook.com", "fb.watch", "twitter.com", "x.com", "bilibili.com", "missav.ws")):
            info = self._analyze_via_ytdlp(page_url)
            if info and info.get("formats"):
                return info

        # 2. Phân tích chuyên biệt: VLXX.net
        if "vlxx.net" in u_lower:
            info = self._analyze_vlxx(page_url)
            if info and info.get("formats"):
                return info

        # 3. Phân tích chuyên biệt: Motchill
        if "motchill" in u_lower:
            info = self._analyze_motchill(page_url)
            if info and info.get("formats"):
                return info

        # 4. Quét Web Tổng Quát (Generic Web Sniffer)
        info = self._analyze_generic_web(page_url)
        if info and info.get("formats"):
            return info

        # 5. Fallback cuối cùng: Thử yt-dlp generic extractor
        fallback = self._analyze_via_ytdlp(page_url)
        if fallback and fallback.get("formats"):
            return fallback

        return {
            "url": page_url,
            "title": "Không tìm thấy luồng",
            "formats": [],
            "error": "Không thể trích xuất luồng video từ trang web này."
        }

    # -------------------------------------------------------------
    # 1. YouTube / Nền tảng video lớn (yt-dlp)
    # -------------------------------------------------------------
    def _analyze_via_ytdlp(self, page_url):
        ytdlp_bin = shutil.which("yt-dlp") or os.path.expanduser("~/.local/bin/yt-dlp")
        if not ytdlp_bin:
            return None

        cmd = [
            ytdlp_bin,
            "--no-download",
            "--dump-json",
            "--no-playlist",
            page_url
        ]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if p.returncode != 0 or not p.stdout.strip():
                return None
            data = json.loads(p.stdout)
            title = data.get("title", "Video")
            formats_raw = data.get("formats", [])

            # Gom các chất lượng video tốt nhất (1080p, 720p, 480p...)
            res_map = {}
            for f in formats_raw:
                vcodec = f.get("vcodec", "none")
                if vcodec == "none":
                    continue
                height = f.get("height")
                if not height:
                    continue
                res_key = f"{height}p"
                sz = f.get("filesize") or f.get("filesize_approx") or 0
                
                # Ưu tiên mp4 hoặc format có bitrate tốt hơn
                if res_key not in res_map or (sz and sz > res_map[res_key]["raw_size"]):
                    res_map[res_key] = {
                        "id": f.get("format_id"),
                        "resolution": f"{height}p ({f.get('width', 0)}x{height})",
                        "height": height,
                        "size": format_bytes(sz) if sz else "--",
                        "raw_size": sz,
                        "ext": "mp4",
                        "stream_url": page_url, # Dùng page_url để yt-dlp tải kèm audio
                        "format_arg": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]",
                        "type": "YTDL"
                    }

            # Sắp xếp từ độ phân giải cao nhất xuống thấp nhất
            sorted_formats = sorted(res_map.values(), key=lambda x: x["height"], reverse=True)
            return {
                "url": page_url,
                "title": title,
                "engine": "yt-dlp",
                "referer": page_url,
                "formats": sorted_formats
            }
        except Exception:
            return None

    # -------------------------------------------------------------
    # 2. VLXX.net Sniffer
    # -------------------------------------------------------------
    def _analyze_vlxx(self, page_url):
        try:
            html = self.fetch_url(page_url)
            # Tìm vid
            m_vid = re.search(r'var\s+vid\s*=\s*(\d+)', html)
            m_title = re.search(r'<title>(.*?)</title>', html, re.I)
            title = m_title.group(1).replace("- VLXX.COM", "").strip() if m_title else "VLXX Video"

            if not m_vid:
                return None
            vid = m_vid.group(1)

            # Gọi POST ajax.php để lấy embed iframe
            post_data = urllib.parse.urlencode({
                'vlxx_server': 1,
                'id': int(vid),
                'server': 1
            }).encode('utf-8')
            ajax_resp = self.fetch_url(
                "https://vlxx.net/ajax.php",
                headers={
                    'Referer': page_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                },
                method='POST',
                data=post_data
            )
            ajax_json = json.loads(ajax_resp)
            player_html = ajax_json.get("player", "")
            m_iframe = re.search(r'src=[\"\']([^\"\']+)[\"\']', player_html)
            if not m_iframe:
                return None
            embed_url = m_iframe.group(1)

            # Tải iframe embed để lấy manifest .vl
            embed_html = self.fetch_url(embed_url, headers={'Referer': 'https://vlxx.net/'})
            m_src = re.search(r'window\.__SRC\s*=\s*(\[.*?\]);', embed_html)
            if not m_src:
                return None
            src_arr = json.loads(m_src.group(1))
            manifest_url = src_arr[0].get("file") if src_arr else None
            if not manifest_url:
                return None

            # Đọc manifest .vl để tính dung lượng & số segments
            manifest_text = self.fetch_url(manifest_url, headers={'Referer': 'https://play.vlstream.net/'})
            durations = [float(x) for x in re.findall(r'#EXTINF:([\d\.]+)', manifest_text)]
            total_duration = sum(durations)
            segments = re.findall(r'^(https?://[^\r\n]+)', manifest_text, re.M)
            est_size_str = "--"
            if segments:
                # Lấy mẫu phân đoạn ở giữa (tránh đoạn intro/cảnh đen tĩnh đầu phim bị lệch bitrate)
                mid_idx = len(segments) // 2
                sample_url = segments[mid_idx]
                try:
                    req_mid = urllib.request.Request(sample_url, headers={'User-Agent': self.ua, 'Referer': 'https://play.vlstream.net/'})
                    with urllib.request.urlopen(req_mid, timeout=4) as sr:
                        sample_bytes = len(sr.read(1024 * 1024 * 10))
                        if sample_bytes > 0:
                            est_bytes = sample_bytes * len(segments)
                            est_size_str = format_bytes(est_bytes)
                except Exception:
                    pass
            if est_size_str == "--" and total_duration > 0:
                # Ước tính theo bitrate Full HD chuẩn 2.8 Mbps
                est_bytes = total_duration * 2.8 * 1000 * 1000 / 8
                est_size_str = format_bytes(est_bytes)

            return {
                "url": page_url,
                "title": title,
                "engine": "vlxx",
                "referer": "https://play.vlstream.net/",
                "formats": [
                    {
                        "id": "1",
                        "resolution": "1080p (Full HD)",
                        "height": 1080,
                        "size": est_size_str,
                        "duration": f"{int(total_duration//60)}:{int(total_duration%60):02d}",
                        "ext": "mp4",
                        "stream_url": manifest_url,
                        "type": "HLS (.vl)"
                    }
                ]
            }
        except Exception as e:
            return None

    # -------------------------------------------------------------
    # 3. Motchill Sniffer
    # -------------------------------------------------------------
    def _analyze_motchill(self, page_url):
        try:
            html = self.fetch_url(page_url)
            m_title = re.search(r'<title>(.*?)</title>', html, re.I)
            title = m_title.group(1).replace("- Motchill", "").strip() if m_title else "Motchill Video"

            # Tìm server VSMov (server chuẩn nhất không bị khóa token)
            m_vsmov = re.search(r'data-source=[\"\']vsmov[\"\'][^>]*data-link=[\"\']([^\"\']+)[\"\']', html)
            if not m_vsmov:
                # Thử tìm link vsmov trực tiếp
                m_vsmov = re.search(r'(https?://[^\s\"\'<>]+streamvsmov\.com/video/[a-zA-Z0-9\-]+)', html)

            if m_vsmov:
                vsmov_url = m_vsmov.group(1)
                video_hash = vsmov_url.split("/")[-1]
                vsmov_host = urllib.parse.urlparse(vsmov_url).netloc
                master_url = f"https://{vsmov_host}/stream/{video_hash}/master.m3u8"
                
                # Thử đọc master.m3u8
                m3u8_text = self.fetch_url(master_url, headers={'Referer': 'https://motchillve.im/'})
                durations = [float(x) for x in re.findall(r'#EXTINF:([\d\.]+)', m3u8_text)]
                est_size = format_bytes(len(durations) * 600 * 1024) if durations else "~450 MB"
                
                return {
                    "url": page_url,
                    "title": title,
                    "engine": "motchill",
                    "referer": "https://motchillve.im/",
                    "formats": [
                        {
                            "id": "1",
                            "resolution": "1080p (Full HD)",
                            "height": 1080,
                            "size": est_size,
                            "ext": "mp4",
                            "stream_url": master_url,
                            "type": "HLS (VSMov)"
                        }
                    ]
                }
        except Exception:
            pass
        return None

    # -------------------------------------------------------------
    # 4. Quét Web Tổng Quát (Generic Web Sniffer)
    # -------------------------------------------------------------
    def _analyze_generic_web(self, page_url):
        try:
            html = self.fetch_url(page_url)
            m_title = re.search(r'<title>(.*?)</title>', html, re.I)
            title = m_title.group(1).strip() if m_title else "Video"

            # Quét các link m3u8, mpd, mp4
            streams_found = re.findall(r'(https?://[^\s\"\'<>]+\.(?:m3u8|mpd|mp4|webm|vl)[^\s\"\'<>]*)', html)
            if not streams_found:
                return None

            formats = []
            idx = 1
            for s_url in list(dict.fromkeys(streams_found))[:5]:
                # Phân tích HLS nếu có
                clean_s = s_url.split("?")[0].lower()
                res = "1080p"
                sz = "--"
                stype = "Video"
                if clean_s.endswith(".m3u8") or ".m3u8" in clean_s or clean_s.endswith(".vl"):
                    stype = "HLS"
                    try:
                        p_text = self.fetch_url(s_url, headers={'Referer': page_url}, timeout=3)
                        res_list = re.findall(r'RESOLUTION=(\d+x\d+)', p_text)
                        if res_list:
                            res = f"{res_list[-1].split('x')[-1]}p"
                        durations = [float(d) for d in re.findall(r'#EXTINF:([\d\.]+)', p_text)]
                        if durations:
                            sz = format_bytes(len(durations) * 500 * 1024)
                    except Exception:
                        pass
                formats.append({
                    "id": str(idx),
                    "resolution": res,
                    "height": 1080 if "1080" in res else 720,
                    "size": sz,
                    "ext": "mp4",
                    "stream_url": s_url,
                    "type": stype
                })
                idx += 1

            if formats:
                return {
                    "url": page_url,
                    "title": title,
                    "engine": "generic_web",
                    "referer": page_url,
                    "formats": formats
                }
        except Exception:
            pass
        return None
