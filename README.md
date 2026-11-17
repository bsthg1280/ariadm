# 🚀 AriaDM — Multi-threaded Video Downloader & Sniffer for Linux

<p align="center">
  <b>Bộ công cụ bóc tách luồng & tăng tốc tải video đa luồng mã nguồn mở, tối ưu cho Linux Desktop.</b><br>
  <i>Hội tụ sức mạnh từ <code>aria2c</code> (16–32 luồng song song) + <code>yt-dlp</code> + <code>ffmpeg</code>.</i>
</p>

---

## 📌 Giới thiệu dự án

**AriaDM** hiện tại là một dự án **chuyên biệt về tải video (Video Downloader & Stream Sniffer)** mã nguồn mở, được xây dựng nhằm mang lại trải nghiệm tải video mượt mà, tốc độ cao trên Linux mà không cần phải chạy IDM Windows qua Wine/Proton.

Hệ thống tự động giải quyết các vấn đề thường gặp trên Linux:
- **Tải đa luồng kịch trần băng thông:** Tận dụng `aria2c` chia nhỏ file thành 16 kết nối song song.
- **Tự động bóc tách luồng HLS/DASH phức tạp:** Bắt và ghép các playlist `.m3u8`, `.vl`, `.mpd`, trích xuất video Full HD/4K từ YouTube, TikTok, Facebook và các trang web phim.
- **Tính toán trước Độ phân giải & Dung lượng:** Hiển thị rõ ràng độ phân giải (1080p, 720p, 480p...) và dung lượng dự kiến (MB/GB) trước khi bấm tải.

---

## 🧩 Các thành phần cốt lõi

Dự án gồm 2 công cụ chính hoạt động độc lập hoặc phối hợp với nhau:

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
```

### 2. AriaDM WebExtension (Manifest V3)
Tiện ích mở rộng độc lập cho trình duyệt (Brave, Chrome, Edge, Cốc Cốc, Firefox):
- Tự động bắt mọi luồng media khi bạn xem phim hoặc xem video.
- Popup hiện đại phong cách Cốc Cốc hiển thị: **Độ phân giải**, **Dung lượng dự kiến**, **Định dạng**.
- Nút bấm `[ ⚡ Tải Aria2c (16 luồng) ]` và nút `[ 💻 Copy CLI ]` để chuyển sang terminal.

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
> **AriaDM hiện tại đang ở giai đoạn đầu tập trung hoàn thiện cho tác vụ VIDEO.**
> 
> Chúng tôi rất hoan nghênh và mong muốn nhận được sự chung tay đóng góp từ cộng đồng mã nguồn mở để phát triển AriaDM ngày một mạnh mẽ hơn:
> - **Viết thêm Custom Extractors:** Bổ sung bộ bóc tách cho các trang web phim, anime, bài giảng, khoá học, dịch vụ livestream đặc thù trong file `cli/sniffer_engine.py`.
> - **Phát triển Desktop GUI Native:** Đóng góp giao diện người dùng bằng **Qt6 (PySide6 / C++)** hoặc **Rust (Slint / Tauri)**.
> - **Tối ưu hóa Engine Tải:** Viết daemon lõi bằng Rust (Tokio) để tối ưu hóa tài nguyên RAM/CPU.
> - **Đóng gói Linux:** Hỗ trợ tạo PKGBUILD (Arch User Repository - AUR), Flatpak, AppImage và DEB/RPM.

Mọi ý tưởng, đóng góp (Pull Request, Issue báo lỗi, gợi ý trang web cần hỗ trợ) đều vô cùng quý giá!

---

## 📄 Giấy phép (License)
Dự án được phát hành theo giấy phép mã nguồn mở **MIT License**.
