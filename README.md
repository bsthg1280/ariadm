# 🚀 AriaDM — Multi-threaded Video & Media Downloader

<p align="center">
  <b>Bộ công cụ bóc tách luồng & tăng tốc tải video đa luồng mã nguồn mở, tối ưu cho Linux Desktop (và đa nền tảng).</b><br>
  <i>Hội tụ sức mạnh từ <code>aria2c</code> (16–32 luồng song song + BitTorrent) + <code>yt-dlp</code> + <code>ffmpeg</code>.</i>
</p>

---

## 📌 Giới thiệu dự án

**AriaDM** hiện tại là một dự án **chuyên biệt về tải video (Video Downloader & Stream Sniffer)** mã nguồn mở, được xây dựng nhằm mang lại trải nghiệm tải video mượt mà, tốc độ cao trên Linux mà không cần phải chạy IDM Windows qua Wine/Proton.

Hệ thống tự động giải quyết các bài toán tải media phức tạp:
- **Tải đa luồng kịch trần băng thông:** Tận dụng `aria2c` chia nhỏ file thành 16–32 kết nối song song.
- **Tự động bóc tách luồng HLS/DASH ngầm:** Bắt và ghép các playlist `.m3u8`, `.vl`, `.mpd`, trích xuất video Full HD/4K từ YouTube, TikTok, Facebook và các trang web phim.
- **Tính toán trước Độ phân giải & Dung lượng:** Hiển thị rõ ràng độ phân giải (1080p, 720p, 480p...) và dung lượng dự kiến (MB/GB) trước khi bấm tải.
- **🧲 Hỗ trợ BitTorrent & Magnet Link:** Tích hợp engine P2P có sẵn của `aria2c`, hỗ trợ tải file `.torrent` và link `magnet:` siêu nhẹ.

---

## 🧩 Các thành phần cốt lõi

### 1. AriaDM CLI (`ariadm`)
Công cụ dòng lệnh thông minh. Bạn chỉ cần paste link trang web, `ariadm` sẽ tự động phân tích cấu trúc trang, tìm ra luồng video ngầm và tải về:

```bash
# Phân tích thông tin (độ phân giải & dung lượng) mà không tải:
ariadm --info "https://www.youtube.com/watch?v=..."

# Phân tích và tải ngay chất lượng cao nhất (16 luồng):
ariadm "https://motchillve.im/..."

# Chỉ định độ phân giải cụ thể:
ariadm "https://vlxx.net/..." -q 1080p

# Tăng lên 32 luồng song song và lưu vào thư mục khác:
ariadm "https://..." -c 32 -d ~/Videos -o "Phim.mp4"

# Tải link Magnet / BitTorrent:
ariadm "magnet:?xt=urn:btih:..."
```

### 2. AriaDM WebExtension (Manifest V3)
Tiện ích mở rộng độc lập cho trình duyệt (Brave, Chrome, Edge, Cốc Cốc, Firefox):
- Tự động bắt mọi luồng media khi bạn xem phim hoặc xem video.
- Popup hiện đại phong cách Cốc Cốc hiển thị: **Độ phân giải**, **Dung lượng dự kiến**, **Định dạng**.
- Nút bấm `[ ⚡ Tải Aria2c (16 luồng) ]` và nút `[ 💻 Copy CLI ]` để chuyển sang terminal.

### 3. AriaDM Desktop GUI (`ariadm-gui`)
Giao diện đồ hoạ PySide6 hiện đại kết hợp tinh hoa giữa **IDM cổ điển** và **AriaNg**, tối ưu đồng bộ với theme **macOS Dark (MacTahoe / WhiteSur)**:
- **Thanh công cụ Toolbar phong cách IDM**: ➕ Thêm URL, ▶ Tiếp tục, ⏸ Tạm dừng, ⏹ Dừng tất cả, 🗑 Xoá bài, và **🧹 Xoá lịch sử tải** tiện lợi.
- **Sidebar phân loại danh mục (Categories)**: Tất cả bài tải, Đang tải, Tạm dừng, Hoàn thành, Lỗi/Huỷ, BitTorrent/Magnet và **Video Grabber**.
- **Tab Video Grabber tích hợp**: Gom toàn bộ luồng video bắt được từ trình duyệt web với độ phân giải và dung lượng ước tính.
- **Menu chuột phải phong phú**: Mở file, Mở thư mục chứa, Tải lại, Xoá khỏi danh sách, Xoá cả file trên đĩa.
- **Khởi chạy cực nhanh**: Gõ `ariadm-gui` trên terminal hoặc mở biểu tượng **AriaDM** từ Menu ứng dụng desktop.

---

## 🗺️ Lộ trình Phát triển & Định hướng Đa Nền Tảng (Roadmap)

Dự án được định hướng phát triển thành công cụ quản lý tải xuống toàn diện (All-in-One Download Manager) trên cả 3 nền tảng:

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│     Giai đoạn 1 (Hiện tại)      │ ──> │      Giai đoạn 2 (Sắp tới)      │ ──> │      Giai đoạn 3 (Tương lai)    │
├─────────────────────────────────┤     ├─────────────────────────────────┤     ├─────────────────────────────────┤
│ • Video Sniffer & Downloader    │     │ • Hỗ trợ hoàn chỉnh Torrent/P2P │     │ • Bản cài đặt macOS (.dmg)      │
│ • HLS, DASH, YouTube, Web Phim  │     │ • Bản Portable Windows (.exe)   │     │ • Auto-updater & Cloud Sync     │
│ • Linux CLI & WebExtension MV3  │     │ • Desktop GUI Native (Qt6/Rust) │     │ • Phân loại danh mục tự động    │
└─────────────────────────────────┘     └─────────────────────────────────┘     └─────────────────────────────────┘
```

---

## 📥 Hướng dẫn cài đặt

### Yêu cầu hệ thống (Linux):
- `python3` (>= 3.9)
- `aria2` (`sudo pacman -S aria2` trên Arch/Manjaro hoặc `sudo apt install aria2` trên Ubuntu/Debian)
- `ffmpeg`
- `yt-dlp` (`pipx install yt-dlp` hoặc qua package manager)

### Cài đặt nhanh CLI:
```bash
git clone https://github.com/nguyenthangtran2003-cmyk/ariadm.git
cd ariadm
chmod +x install.sh
./install.sh
```

### Cài đặt WebExtension vào Trình duyệt:
1. Mở Brave/Chrome, truy cập: `chrome://extensions/` (hoặc `brave://extensions/`).
2. Bật công tắc **Developer mode** (Chế độ dành cho nhà phát triển).
3. Bấm **Load unpacked** (Tải tiện ích đã giải nén).
4. Chọn thư mục `extension/` trong repository này.

---

## 🤝 Lời ngỏ & Kêu gọi đóng góp từ Cộng đồng (Call for Contributions)

> [!IMPORTANT]
> **AriaDM hiện tại đang ở giai đoạn đầu tập trung hoàn thiện cho tác vụ VIDEO & STREAMING.**
> 
> Chúng tôi rất hoan nghênh và mong muốn nhận được sự chung tay đóng góp từ cộng đồng mã nguồn mở:
> - 🧩 **Viết thêm Custom Extractors:** Bổ sung bộ bóc tách cho các trang web phim, anime, bài giảng, khoá học, dịch vụ livestream đặc thù trong file `cli/sniffer_engine.py`.
> - 🪟 **Hỗ trợ Windows & macOS (Cross-platform):** Đóng gói bộ bundle standalone cho Windows (`aria2c.exe` + `yt-dlp.exe` + `ffmpeg.exe` + script launcher) và Homebrew Formula cho macOS.
> - 🧲 **Hoàn thiện module BitTorrent:** Mở rộng giao diện quản lý peer, tracker, tốc độ upload/download cho torrent.
> - 🖥️ **Phát triển Desktop GUI Native:** Đóng góp giao diện người dùng native bằng **Qt6 (PySide6 / C++)** hoặc **Rust (Slint / Tauri)**.
> - 📦 **Đóng gói Linux:** Hỗ trợ tạo PKGBUILD (Arch User Repository - AUR), Flatpak, AppImage và DEB/RPM.

Mọi ý tưởng, đóng góp (Pull Request, Issue báo lỗi, gợi ý trang web cần hỗ trợ) đều vô cùng quý giá!

---

## 📄 Giấy phép (License)
Dự án được phát hành theo giấy phép mã nguồn mở **MIT License**.
