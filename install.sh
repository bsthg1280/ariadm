#!/usr/bin/env bash
set -e

echo "🚀 Đang cài đặt AriaDM CLI..."

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chmod +x "$SCRIPT_DIR/cli/ariadm.py"
chmod +x "$SCRIPT_DIR/cli/sniffer_engine.py"
chmod +x "$SCRIPT_DIR/daemon/server.py"
chmod +x "$SCRIPT_DIR/gui/ariadm_gui.py"

ln -sf "$SCRIPT_DIR/cli/ariadm.py" "$INSTALL_DIR/ariadm"
ln -sf "$SCRIPT_DIR/gui/ariadm_gui.py" "$INSTALL_DIR/ariadm-gui"

# Cài đặt Desktop Entry
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat << EOF > "$DESKTOP_DIR/ariadm-gui.desktop"
[Desktop Entry]
Type=Application
Name=AriaDM
GenericName=Download Manager
Comment=Trình quản lý tải xuống đa luồng và Video Grabber (macOS Dark Edition)
Exec=$INSTALL_DIR/ariadm-gui
Icon=download
Terminal=false
Categories=Network;FileTransfer;AudioVideo;
Keywords=ariadm;idm;aria2;download;video;grabber;torrent;
StartupWMClass=AriaDM
EOF
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "✅ Cài đặt thành công!"
echo "👉 Dùng CLI: ariadm <URL_video>"
echo "👉 Dùng GUI: ariadm-gui (hoặc tìm AriaDM trong Menu ứng dụng)"
echo "🌐 Để cài Extension: Mở brave://extensions hoặc chrome://extensions -> Load unpacked -> chọn thư mục: $SCRIPT_DIR/extension"
