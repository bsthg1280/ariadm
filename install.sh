#!/usr/bin/env bash
set -e

echo "🚀 Đang cài đặt AriaDM CLI..."

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chmod +x "$SCRIPT_DIR/cli/ariadm.py"
chmod +x "$SCRIPT_DIR/cli/sniffer_engine.py"
chmod +x "$SCRIPT_DIR/daemon/server.py"

ln -sf "$SCRIPT_DIR/cli/ariadm.py" "$INSTALL_DIR/ariadm"

echo "✅ Cài đặt thành công!"
echo "👉 Bạn có thể chạy lệnh: ariadm <URL_video>"
echo "🌐 Để cài Extension: Mở brave://extensions hoặc chrome://extensions -> Load unpacked -> chọn thư mục: $SCRIPT_DIR/extension"
