#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AriaDM — Modern Internet Download Manager (macOS Dark Edition)
Giao diện GUI đồ hoạ chuẩn macOS Dark đồng bộ với theme Manjaro (MacTahoe-Dark / WhiteSurDark).
Tích hợp phong cách IDM cổ điển + AriaNg hiện đại, tăng tốc đa luồng aria2c 16 luồng & Video Grabber.
"""

import sys
import os
import json
import shutil
import urllib.request
import urllib.parse
import subprocess
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QCheckBox, QMessageBox, QTabWidget, QProgressBar, QInputDialog,
    QSplitter, QListWidget, QListWidgetItem, QLineEdit, QMenu,
    QDialog, QFileDialog, QSpinBox, QStackedWidget, QFrame
)
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QAction, QKeySequence, QClipboard

SERVER_URL = "http://127.0.0.1:1001"


def get_free_space_gb():
    try:
        stat = shutil.disk_usage(os.path.expanduser("~/Downloads"))
        return f"{stat.free / (1024**3):.1f} GB"
    except Exception:
        return "-- GB"


def get_file_icon(name):
    ext = os.path.splitext(name)[1].lower()
    if ext in ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.ts', '.m3u8'):
        return "🎬"
    elif ext in ('.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg'):
        return "🎵"
    elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'):
        return "📦"
    elif ext in ('.iso', '.img', '.dmg', '.bin'):
        return "💿"
    elif ext in ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'):
        return "📄"
    elif ext in ('.torrent',) or name.startswith("magnet:"):
        return "🧲"
    elif ext in ('.exe', '.msi', '.deb', '.rpm', '.pkg', '.apk'):
        return "⚙️"
    return "📁"


class AddDownloadDialog(QDialog):
    """Hộp thoại thêm liên kết tải xuống phong cách modal macOS."""
    def __init__(self, parent=None, initial_url="", initial_fn="", initial_ref=""):
        super().__init__(parent)
        self.setWindowTitle("Thêm liên kết tải xuống — AriaDM")
        self.setFixedSize(540, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        lbl_title = QLabel("➕ Thêm URL tải mới")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #fff;")
        layout.addWidget(lbl_title)

        # URL Input
        layout.addWidget(QLabel("Địa chỉ URL (Hỗ trợ YouTube, Phim, Direct, HLS, DASH, Magnet):"))
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://... hoặc magnet:?xt=...")
        self.txt_url.setText(initial_url)
        layout.addWidget(self.txt_url)

        # Filename Input
        layout.addWidget(QLabel("Tên tệp lưu (Tuỳ chọn, để trống sẽ tự động lấy theo nguồn):"))
        self.txt_fn = QLineEdit()
        self.txt_fn.setPlaceholderText("Ví dụ: Video_Full_HD.mp4")
        self.txt_fn.setText(initial_fn)
        layout.addWidget(self.txt_fn)

        # Save Directory
        layout.addWidget(QLabel("Thư mục lưu trữ:"))
        dir_layout = QHBoxLayout()
        self.txt_dir = QLineEdit(os.path.expanduser("~/Downloads"))
        self.txt_dir.setReadOnly(True)
        dir_layout.addWidget(self.txt_dir)
        btn_browse = QPushButton("Chọn...")
        btn_browse.setStyleSheet("background: #2a2a32; padding: 6px 12px;")
        btn_browse.clicked.connect(self.browse_dir)
        dir_layout.addWidget(btn_browse)
        layout.addLayout(dir_layout)

        # Thread / Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Gia tốc đa luồng:"))
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 32)
        self.spin_threads.setValue(16)
        mode_layout.addWidget(self.spin_threads)
        mode_layout.addWidget(QLabel("luồng song song (aria2c)"))
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        layout.addSpacing(10)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Huỷ bỏ")
        btn_cancel.setStyleSheet("background: #2a2a32; color: #8e8e93; border: 1px solid rgba(255,255,255,0.1);")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_download = QPushButton("🚀 Bắt đầu tải ngay")
        self.btn_download.setStyleSheet("background: #0a84ff; color: #fff; font-weight: bold; padding: 6px 16px;")
        self.btn_download.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_download)

        layout.addLayout(btn_box)

        # Auto paste clipboard if URL
        if not initial_url:
            clip = QApplication.clipboard().text().strip()
            if clip.startswith("http://") or clip.startswith("https://") or clip.startswith("magnet:"):
                self.txt_url.setText(clip)

    def browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu trữ", self.txt_dir.text())
        if d:
            self.txt_dir.setText(d)

    def get_data(self):
        return {
            "url": self.txt_url.text().strip(),
            "filename": self.txt_fn.text().strip(),
            "dir": self.txt_dir.text().strip(),
            "threads": self.spin_threads.value()
        }


class AriaDMMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AriaDM — Internet Download Manager")
        self.resize(1000, 620)
        self.setMinimumSize(840, 500)

        self.known_stream_urls = set()
        self.current_filter = "all"  # all, downloading, paused, completed, error, grabber, torrents
        self.search_keyword = ""

        # Central Widget & Layout
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Header Bar (macOS Window Title & Global Info)
        self.setup_header_bar(root_layout)

        # 2. Modern IDM Toolbar
        self.setup_toolbar(root_layout)

        # 3. Main Splitter (Left Sidebar + Right Content Stack)
        self.setup_body(root_layout)

        # 4. Bottom Status Bar
        self.setup_status_bar(root_layout)

        # Áp dụng bộ giao diện macOS Dark Theme cao cấp
        self.apply_theme()

        # Polling Timer (1.2 giây)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_updates)
        self.timer.start(1200)

        self.poll_updates()

    def setup_header_bar(self, parent_layout):
        hdr = QFrame()
        hdr.setObjectName("HeaderBar")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(16, 10, 16, 10)
        hdr_layout.setSpacing(12)

        # Logo & App Title
        logo_lbl = QLabel("🚀 AriaDM")
        logo_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #fff;")
        hdr_layout.addWidget(logo_lbl)

        badge_lbl = QLabel("v1.2")
        badge_lbl.setStyleSheet("background: #0a84ff30; color: #0a84ff; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;")
        hdr_layout.addWidget(badge_lbl)

        hdr_layout.addSpacing(16)

        # Search Bar (Filter Realtime)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Tìm bài tải, URL hoặc video...")
        self.txt_search.setObjectName("SearchBar")
        self.txt_search.setFixedWidth(280)
        self.txt_search.textChanged.connect(self.on_search_changed)
        hdr_layout.addWidget(self.txt_search)

        hdr_layout.addStretch()

        # Always on top checkbox
        self.cb_ontop = QCheckBox("📌 Luôn nổi")
        self.cb_ontop.stateChanged.connect(self.toggle_always_on_top)
        hdr_layout.addWidget(self.cb_ontop)

        # Daemon Status Pill
        self.daemon_status_pill = QLabel("● Sẵn sàng (1001)")
        self.daemon_status_pill.setStyleSheet("background: #30d15820; color: #30d158; border: 1px solid #30d15840; border-radius: 10px; padding: 3px 10px; font-size: 11px; font-weight: bold;")
        hdr_layout.addWidget(self.daemon_status_pill)

        parent_layout.addWidget(hdr)

    def setup_toolbar(self, parent_layout):
        tbar = QFrame()
        tbar.setObjectName("ToolBar")
        tbar_layout = QHBoxLayout(tbar)
        tbar_layout.setContentsMargins(14, 6, 14, 8)
        tbar_layout.setSpacing(6)

        # Button 1: Thêm URL
        self.btn_add = QPushButton("➕ Thêm URL")
        self.btn_add.setObjectName("BtnPrimary")
        self.btn_add.clicked.connect(self.open_add_dialog)
        tbar_layout.addWidget(self.btn_add)

        # Button 2: Tiếp tục
        self.btn_resume = QPushButton("▶ Tiếp tục")
        self.btn_resume.clicked.connect(self.action_resume_selected)
        tbar_layout.addWidget(self.btn_resume)

        # Button 3: Tạm dừng
        self.btn_pause = QPushButton("⏸ Tạm dừng")
        self.btn_pause.clicked.connect(self.action_pause_selected)
        tbar_layout.addWidget(self.btn_pause)

        # Button 4: Dừng tất cả
        self.btn_stop_all = QPushButton("⏹ Dừng tất cả")
        self.btn_stop_all.clicked.connect(self.action_stop_all)
        tbar_layout.addWidget(self.btn_stop_all)

        tbar_layout.addSpacing(8)

        # Button 5: Xoá bài tải
        self.btn_delete = QPushButton("🗑 Xoá bài")
        self.btn_delete.clicked.connect(self.action_delete_selected)
        tbar_layout.addWidget(self.btn_delete)

        # Button 6: Xoá lịch sử tải (Người dùng yêu cầu)
        self.btn_clear_history = QPushButton("🧹 Xoá lịch sử tải")
        self.btn_clear_history.setObjectName("BtnClearHistory")
        self.btn_clear_history.setToolTip("Xoá toàn bộ các bài đã hoàn tất và bài lỗi khỏi danh sách")
        self.btn_clear_history.clicked.connect(self.action_clear_history)
        tbar_layout.addWidget(self.btn_clear_history)

        tbar_layout.addSpacing(8)

        # Button 7: Video Grabber
        self.btn_grabber = QPushButton("🎬 Video Grabber")
        self.btn_grabber.setObjectName("BtnGrabber")
        self.btn_grabber.clicked.connect(lambda: self.set_sidebar_category("grabber"))
        tbar_layout.addWidget(self.btn_grabber)

        tbar_layout.addStretch()

        # Button 8: Mở thư mục Downloads
        self.btn_open_downloads = QPushButton("📂 Mở ~/Downloads")
        self.btn_open_downloads.clicked.connect(self.open_download_dir)
        tbar_layout.addWidget(self.btn_open_downloads)

        parent_layout.addWidget(tbar)

    def setup_body(self, parent_layout):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("MainSplitter")

        # --- Sidebar Trái ---
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("SidebarWidget")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 12, 10, 12)
        sidebar_layout.setSpacing(6)

        lbl_cat_title = QLabel("DANH MỤC TẢI")
        lbl_cat_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #636366; padding-left: 6px;")
        sidebar_layout.addWidget(lbl_cat_title)

        self.list_sidebar = QListWidget()
        self.list_sidebar.setObjectName("SidebarList")
        self.list_sidebar.setSpacing(2)

        # Thêm các danh mục
        self.sidebar_items = {
            "all": QListWidgetItem("📥 Tất cả bài tải (0)"),
            "downloading": QListWidgetItem("⚡ Đang tải (0)"),
            "paused": QListWidgetItem("⏸ Tạm dừng (0)"),
            "completed": QListWidgetItem("✅ Đã hoàn thành (0)"),
            "error": QListWidgetItem("❌ Lỗi / Đã huỷ (0)"),
            "grabber": QListWidgetItem("🎬 Video Bắt Được (0)"),
            "torrents": QListWidgetItem("🧲 BitTorrent / Magnet (0)")
        }

        for key, item in self.sidebar_items.items():
            item.setData(Qt.UserRole, key)
            self.list_sidebar.addItem(item)

        self.list_sidebar.setCurrentRow(0)
        self.list_sidebar.currentItemChanged.connect(self.on_sidebar_item_changed)
        sidebar_layout.addWidget(self.list_sidebar)

        # Chân Sidebar: Nút dọn dẹp phụ
        sidebar_footer = QVBoxLayout()
        sidebar_footer.setSpacing(6)

        btn_side_clear_hist = QPushButton("🧹 Dọn lịch sử đã tải")
        btn_side_clear_hist.setObjectName("BtnSubtle")
        btn_side_clear_hist.clicked.connect(self.action_clear_history)
        sidebar_footer.addWidget(btn_side_clear_hist)

        btn_side_clear_streams = QPushButton("🗑 Xoá video bắt được")
        btn_side_clear_streams.setObjectName("BtnSubtle")
        btn_side_clear_streams.clicked.connect(self.action_clear_streams)
        sidebar_footer.addWidget(btn_side_clear_streams)

        sidebar_layout.addLayout(sidebar_footer)
        splitter.addWidget(sidebar_widget)
        splitter.setStretchFactor(0, 0)

        # --- Content Phải (QStackedWidget) ---
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")

        # Page 0: Bảng bài tải (Downloads Table)
        page_tasks = QWidget()
        layout_tasks = QVBoxLayout(page_tasks)
        layout_tasks.setContentsMargins(12, 10, 12, 10)
        layout_tasks.setSpacing(8)

        self.table_tasks = QTableWidget(0, 7)
        self.table_tasks.setHorizontalHeaderLabels([
            "Tập tin", "Dung lượng", "Tiến trình", "Tốc độ", "Còn lại (ETA)", "Trạng thái", "Thao tác"
        ])
        self.table_tasks.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table_tasks.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_tasks.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_tasks.setColumnWidth(0, 240)
        self.table_tasks.verticalHeader().setVisible(False)
        self.table_tasks.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_tasks.setAlternatingRowColors(True)
        self.table_tasks.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_tasks.customContextMenuRequested.connect(self.on_tasks_context_menu)
        self.table_tasks.cellDoubleClicked.connect(self.on_task_double_clicked)
        layout_tasks.addWidget(self.table_tasks)

        self.content_stack.addWidget(page_tasks)

        # Page 1: Bảng Video Grabber (Streams Table)
        page_streams = QWidget()
        layout_streams = QVBoxLayout(page_streams)
        layout_streams.setContentsMargins(12, 10, 12, 10)
        layout_streams.setSpacing(8)

        grab_hdr = QHBoxLayout()
        lbl_grab_info = QLabel("🎬 Danh sách luồng video tự động bắt từ Brave / Chrome / Cốc Cốc:")
        lbl_grab_info.setStyleSheet("color: #ff9f0a; font-weight: bold; font-size: 13px;")
        grab_hdr.addWidget(lbl_grab_info)
        grab_hdr.addStretch()

        btn_clear_st = QPushButton("🗑 Xoá danh sách video")
        btn_clear_st.setStyleSheet("background: #3a2024; color: #ff453a; border: 1px solid #ff453a40; font-weight: bold;")
        btn_clear_st.clicked.connect(self.action_clear_streams)
        grab_hdr.addWidget(btn_clear_st)
        layout_streams.addLayout(grab_hdr)

        self.table_streams = QTableWidget(0, 6)
        self.table_streams.setHorizontalHeaderLabels([
            "Nguồn", "Định dạng", "Tiêu đề video", "Độ phân giải", "Dung lượng", "Thao tác"
        ])
        self.table_streams.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_streams.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_streams.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_streams.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_streams.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_streams.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_streams.verticalHeader().setVisible(False)
        self.table_streams.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_streams.setAlternatingRowColors(True)
        layout_streams.addWidget(self.table_streams)

        self.content_stack.addWidget(page_streams)

        splitter.addWidget(self.content_stack)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([210, 790])

        parent_layout.addWidget(splitter)

    def setup_status_bar(self, parent_layout):
        stat = QFrame()
        stat.setObjectName("StatusBar")
        stat_layout = QHBoxLayout(stat)
        stat_layout.setContentsMargins(16, 6, 16, 6)
        stat_layout.setSpacing(16)

        self.lbl_stat_engine = QLabel("⚡ Engine: yt-dlp + aria2c (16 luồng)")
        self.lbl_stat_engine.setStyleSheet("color: #0a84ff; font-weight: 600; font-size: 11px;")
        stat_layout.addWidget(self.lbl_stat_engine)

        stat_layout.addStretch()

        self.lbl_stat_speed = QLabel("⬇ Tốc độ tổng: 0 KB/s")
        self.lbl_stat_speed.setStyleSheet("color: #30d158; font-weight: bold; font-size: 11px;")
        stat_layout.addWidget(self.lbl_stat_speed)

        self.lbl_stat_space = QLabel(f"💾 Trống: {get_free_space_gb()}")
        self.lbl_stat_space.setStyleSheet("color: #8e8e93; font-size: 11px;")
        stat_layout.addWidget(self.lbl_stat_space)

        parent_layout.addWidget(stat)

    def apply_theme(self):
        """macOS Dark Theme phong cách MacTahoe-Dark / WhiteSurDark."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #16161a;
            }
            QWidget {
                color: #e5e5ea;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
                font-size: 13px;
            }
            #HeaderBar {
                background-color: #1a1a20;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            #ToolBar {
                background-color: #1f1f26;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            #SearchBar {
                background-color: #121215;
                color: #fff;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 12px;
            }
            #SearchBar:focus {
                border: 1px solid #0a84ff;
            }
            #SidebarWidget {
                background-color: #141417;
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }
            #SidebarList {
                background-color: transparent;
                border: none;
                outline: none;
            }
            #SidebarList::item {
                padding: 8px 10px;
                border-radius: 6px;
                color: #c7c7cc;
                font-weight: 500;
            }
            #SidebarList::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #fff;
            }
            #SidebarList::item:selected {
                background-color: #0a84ff25;
                color: #0a84ff;
                font-weight: bold;
                border-left: 3px solid #0a84ff;
            }
            QTableWidget {
                background-color: #1c1c22;
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.05);
                alternate-background-color: #17171d;
                selection-background-color: rgba(10, 132, 255, 0.25);
                selection-color: #fff;
            }
            QHeaderView::section {
                background-color: #24242c;
                color: #a1a1aa;
                padding: 8px 6px;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton {
                background-color: #2a2a32;
                color: #f2f2f7;
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #383844;
            }
            QPushButton:pressed {
                background-color: #22222a;
            }
            #BtnPrimary {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: bold;
                border: none;
            }
            #BtnPrimary:hover {
                background-color: #0071e3;
            }
            #BtnClearHistory {
                background-color: #3a2024;
                color: #ff453a;
                border: 1px solid rgba(255, 69, 58, 0.35);
                font-weight: bold;
            }
            #BtnClearHistory:hover {
                background-color: #4a252a;
            }
            #BtnGrabber {
                background-color: #332512;
                color: #ff9f0a;
                border: 1px solid rgba(255, 159, 10, 0.35);
                font-weight: bold;
            }
            #BtnGrabber:hover {
                background-color: #423015;
            }
            #BtnSubtle {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: #8e8e93;
                font-size: 11px;
                padding: 5px;
            }
            #BtnSubtle:hover {
                background-color: rgba(255, 255, 255, 0.06);
                color: #ff453a;
            }
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 5px;
                text-align: center;
                background-color: #121215;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a84ff, stop:1 #5ac8fa);
                border-radius: 4px;
            }
            #StatusBar {
                background-color: #141418;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            }
            QCheckBox {
                color: #a1a1aa;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: #1e1e24;
            }
            QCheckBox::indicator:checked {
                background: #0a84ff;
                border-color: #0a84ff;
            }
            QMenu {
                background-color: #24242c;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
                color: #fff;
            }
            QMenu::item:selected {
                background-color: #0a84ff;
            }
            QScrollBar:vertical {
                border: none;
                background: #141418;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #383842;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4e4e5a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def toggle_always_on_top(self, state):
        if state == Qt.Checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def open_download_dir(self):
        video_dir = os.path.expanduser("~/Downloads")
        subprocess.Popen(["xdg-open", video_dir])

    def open_add_dialog(self, initial_url="", initial_fn=""):
        dlg = AddDownloadDialog(self, initial_url, initial_fn)
        if dlg.exec():
            data = dlg.get_data()
            url = data["url"]
            fn = data["filename"]
            if url:
                self.start_download(url, "", fn, "aria2")

    def on_sidebar_item_changed(self, current, previous):
        if not current:
            return
        cat = current.data(Qt.UserRole)
        self.current_filter = cat
        if cat == "grabber":
            self.content_stack.setCurrentIndex(1)
            self.fetch_streams()
        else:
            self.content_stack.setCurrentIndex(0)
            self.fetch_tasks()

    def set_sidebar_category(self, cat):
        for idx in range(self.list_sidebar.count()):
            item = self.list_sidebar.item(idx)
            if item.data(Qt.UserRole) == cat:
                self.list_sidebar.setCurrentRow(idx)
                break

    def on_search_changed(self, text):
        self.search_keyword = text.strip().lower()
        self.fetch_tasks()
        if self.current_filter == "grabber":
            self.fetch_streams()

    def action_resume_selected(self):
        # Tải lại task được chọn
        row = self.table_tasks.currentRow()
        if row >= 0:
            item = self.table_tasks.item(row, 0)
            url = item.data(Qt.UserRole + 1)
            fn = item.text().strip()
            if url:
                self.start_download(url, "", fn, "aria2")

    def action_pause_selected(self):
        row = self.table_tasks.currentRow()
        if row >= 0:
            tid = self.table_tasks.item(row, 0).data(Qt.UserRole)
            if tid:
                self.cancel_task(tid)

    def action_stop_all(self):
        reply = QMessageBox.question(self, "Dừng tất cả", "Bạn có chắc chắn muốn dừng toàn bộ tác vụ đang tải?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                req = urllib.request.Request(f"{SERVER_URL}/api/tasks")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    tasks = json.loads(resp.read().decode("utf-8")).get("tasks", [])
                    for t in tasks:
                        if t.get("status") == "downloading":
                            self.cancel_task(t["id"])
            except Exception:
                pass

    def action_delete_selected(self):
        row = self.table_tasks.currentRow()
        if row < 0:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn một bài tải trong bảng để xoá.")
            return

        item = self.table_tasks.item(row, 0)
        tid = item.data(Qt.UserRole)
        title = item.text()

        reply = QMessageBox.question(
            self, "Xoá bài tải",
            f"Bạn có muốn xoá bài '{title}' khỏi danh sách?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.delete_task(tid, delete_file=False)

    def action_clear_history(self):
        """Xoá sạch toàn bộ lịch sử bài đã tải hoàn thành hoặc lỗi."""
        reply = QMessageBox.question(
            self, "Xoá lịch sử tải",
            "Bạn có chắc muốn xoá toàn bộ lịch sử các bài đã tải xong và bài lỗi không?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                payload = json.dumps({"all": False}).encode("utf-8")
                req = urllib.request.Request(f"{SERVER_URL}/api/clear_tasks", data=payload, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=1.5)
                self.table_tasks.setRowCount(0)
                self.fetch_tasks()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không xoá được lịch sử: {e}")

    def action_clear_streams(self):
        """Xoá sạch toàn bộ video bắt được trong grabber."""
        try:
            req = urllib.request.Request(f"{SERVER_URL}/api/clear_streams", data=b"{}", headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=1.5)
            self.table_streams.setRowCount(0)
            self.known_stream_urls.clear()
            self.sidebar_items["grabber"].setText("🎬 Video Bắt Được (0)")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không xoá được danh sách video: {e}")

    def delete_task(self, task_id, delete_file=False):
        try:
            payload = json.dumps({"task_id": task_id, "delete_file": delete_file}).encode("utf-8")
            req = urllib.request.Request(f"{SERVER_URL}/api/delete_task", data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=1.5)
            self.fetch_tasks()
        except Exception:
            pass

    def start_download(self, url, ref, fn, mode="aria2"):
        payload = json.dumps({"url": url, "referer": ref, "mode": mode, "filename": fn}).encode("utf-8")
        req = urllib.request.Request(f"{SERVER_URL}/download", data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if mode == "idm":
                    QMessageBox.information(self, "IDM", "Đã gửi sang IDM Wine!")
                else:
                    self.set_sidebar_category("all")
                    self.fetch_tasks()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", f"Không bắt đầu tải được: {exc}")

    def cancel_task(self, task_id):
        try:
            payload = json.dumps({"task_id": task_id}).encode("utf-8")
            req = urllib.request.Request(f"{SERVER_URL}/api/cancel_task", data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=1.5)
            self.fetch_tasks()
        except Exception:
            pass

    def poll_updates(self):
        self.fetch_tasks()
        if self.current_filter == "grabber":
            self.fetch_streams()
        self.lbl_stat_space.setText(f"💾 Trống: {get_free_space_gb()}")

    def fetch_tasks(self):
        try:
            req = urllib.request.Request(f"{SERVER_URL}/api/tasks")
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                tasks = data.get("tasks", [])
                self.daemon_status_pill.setText("● Sẵn sàng (1001)")
                self.daemon_status_pill.setStyleSheet("background: #30d15820; color: #30d158; border: 1px solid #30d15840; border-radius: 10px; padding: 3px 10px; font-size: 11px; font-weight: bold;")
                self.update_tasks_display(tasks)
        except Exception:
            self.daemon_status_pill.setText("● Mất kết nối")
            self.daemon_status_pill.setStyleSheet("background: #ff453a20; color: #ff453a; border: 1px solid #ff453a40; border-radius: 10px; padding: 3px 10px; font-size: 11px; font-weight: bold;")

    def update_tasks_display(self, tasks):
        # Đếm thống kê
        total_count = len(tasks)
        down_count = sum(1 for t in tasks if t.get("status") == "downloading")
        paused_count = sum(1 for t in tasks if t.get("status") == "paused")
        comp_count = sum(1 for t in tasks if t.get("status") == "completed")
        err_count = sum(1 for t in tasks if t.get("status") in ("error", "cancelled"))
        torrent_count = sum(1 for t in tasks if "magnet:" in t.get("url", "") or ".torrent" in t.get("title", ""))

        self.sidebar_items["all"].setText(f"📥 Tất cả bài tải ({total_count})")
        self.sidebar_items["downloading"].setText(f"⚡ Đang tải ({down_count})")
        self.sidebar_items["paused"].setText(f"⏸ Tạm dừng ({paused_count})")
        self.sidebar_items["completed"].setText(f"✅ Đã hoàn thành ({comp_count})")
        self.sidebar_items["error"].setText(f"❌ Lỗi / Đã huỷ ({err_count})")
        self.sidebar_items["torrents"].setText(f"🧲 BitTorrent / Magnet ({torrent_count})")

        # Lọc theo sidebar & search
        filtered_tasks = []
        for t in tasks:
            status = t.get("status", "pending")
            title = (t.get("title") or "").lower()
            url = (t.get("url") or "").lower()

            if self.search_keyword and (self.search_keyword not in title and self.search_keyword not in url):
                continue

            if self.current_filter == "downloading" and status != "downloading":
                continue
            elif self.current_filter == "paused" and status != "paused":
                continue
            elif self.current_filter == "completed" and status != "completed":
                continue
            elif self.current_filter == "error" and status not in ("error", "cancelled"):
                continue
            elif self.current_filter == "torrents" and ("magnet:" not in url and ".torrent" not in title):
                continue

            filtered_tasks.append(t)

        # Tính tổng tốc độ
        speeds = [t.get("speed", "") for t in tasks if t.get("status") == "downloading"]
        if speeds:
            self.lbl_stat_speed.setText(f"⬇ Tốc độ: {speeds[0]}")
        else:
            self.lbl_stat_speed.setText("⬇ Tốc độ: 0 KB/s")

        # Render bảng
        self.render_tasks_table(filtered_tasks)

    def render_tasks_table(self, tasks):
        existing_rows = {}
        for r in range(self.table_tasks.rowCount()):
            item0 = self.table_tasks.item(r, 0)
            if item0:
                tid = item0.data(Qt.UserRole)
                if tid:
                    existing_rows[tid] = r

        # Xoá các hàng không còn tồn tại
        active_ids = {t["id"] for t in tasks}
        for tid, r in sorted(existing_rows.items(), key=lambda x: -x[1]):
            if tid not in active_ids:
                self.table_tasks.removeRow(r)

        # Cập nhật hoặc chèn mới
        for t in tasks:
            tid = t["id"]
            title = t.get("title") or "Tệp tải về"
            prog = int(t.get("progress") or 0)
            speed = t.get("speed") or "--"
            size = t.get("size") or "--"
            eta = t.get("eta") or "--"
            status = t.get("status") or "pending"
            file_path = t.get("file_path") or ""
            url = t.get("url") or ""

            icon = get_file_icon(title)
            display_title = f"{icon}  {title}"

            if tid in existing_rows and existing_rows[tid] < self.table_tasks.rowCount():
                row = existing_rows[tid]
                self.table_tasks.item(row, 0).setText(display_title)
                self.table_tasks.item(row, 1).setText(size)

                pbar = self.table_tasks.cellWidget(row, 2)
                if pbar:
                    pbar.setValue(prog)

                self.table_tasks.item(row, 3).setText(speed)
                self.table_tasks.item(row, 4).setText(eta)

                # Status item
                status_item = self.table_tasks.item(row, 5)
                self.apply_status_item(status_item, status)

                # Nút thao tác
                btn_widget = self.table_tasks.cellWidget(row, 6)
                if btn_widget:
                    btn_open = btn_widget.findChild(QPushButton, "btn_open")
                    btn_cancel = btn_widget.findChild(QPushButton, "btn_cancel")
                    if btn_open and btn_cancel:
                        btn_open.setVisible(status == "completed")
                        btn_cancel.setVisible(status == "downloading")
            else:
                row = self.table_tasks.rowCount()
                self.table_tasks.insertRow(row)

                item_title = QTableWidgetItem(display_title)
                item_title.setData(Qt.UserRole, tid)
                item_title.setData(Qt.UserRole + 1, url)
                item_title.setData(Qt.UserRole + 2, file_path)
                self.table_tasks.setItem(row, 0, item_title)

                item_size = QTableWidgetItem(size)
                item_size.setTextAlignment(Qt.AlignCenter)
                self.table_tasks.setItem(row, 1, item_size)

                pbar = QProgressBar()
                pbar.setValue(prog)
                self.table_tasks.setCellWidget(row, 2, pbar)

                item_speed = QTableWidgetItem(speed)
                item_speed.setTextAlignment(Qt.AlignCenter)
                if status == "downloading":
                    item_speed.setForeground(QColor("#30d158"))
                self.table_tasks.setItem(row, 3, item_speed)

                item_eta = QTableWidgetItem(eta)
                item_eta.setTextAlignment(Qt.AlignCenter)
                self.table_tasks.setItem(row, 4, item_eta)

                status_item = QTableWidgetItem()
                self.apply_status_item(status_item, status)
                self.table_tasks.setItem(row, 5, status_item)

                # Action Buttons
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 2, 4, 2)
                btn_layout.setSpacing(4)

                btn_open = QPushButton("▶ Mở")
                btn_open.setObjectName("btn_open")
                btn_open.setStyleSheet("background: #30d158; color: #fff; font-weight: bold; padding: 3px 8px;")
                btn_open.setVisible(status == "completed")
                btn_open.clicked.connect(lambda _, p=file_path: self.open_file_or_dir(p))
                btn_layout.addWidget(btn_open)

                btn_cancel = QPushButton("⏹ Huỷ")
                btn_cancel.setObjectName("btn_cancel")
                btn_cancel.setStyleSheet("background: #ff453a; color: #fff; padding: 3px 8px;")
                btn_cancel.setVisible(status == "downloading")
                btn_cancel.clicked.connect(lambda _, task_id=tid: self.cancel_task(task_id))
                btn_layout.addWidget(btn_cancel)

                btn_del = QPushButton("🗑")
                btn_del.setToolTip("Xoá khỏi danh sách")
                btn_del.setStyleSheet("background: transparent; color: #8e8e93; border: none; padding: 3px 6px;")
                btn_del.clicked.connect(lambda _, task_id=tid: self.delete_task(task_id, False))
                btn_layout.addWidget(btn_del)

                self.table_tasks.setCellWidget(row, 6, btn_widget)

    def apply_status_item(self, item, status):
        item.setTextAlignment(Qt.AlignCenter)
        if status == "downloading":
            item.setText("⚡ Đang tải")
            item.setForeground(QColor("#30d158"))
        elif status == "completed":
            item.setText("✅ Hoàn thành")
            item.setForeground(QColor("#0a84ff"))
        elif status == "error":
            item.setText("❌ Lỗi")
            item.setForeground(QColor("#ff453a"))
        elif status == "cancelled":
            item.setText("⏹ Đã huỷ")
            item.setForeground(QColor("#8e8e93"))
        elif status == "paused":
            item.setText("⏸ Tạm dừng")
            item.setForeground(QColor("#ff9f0a"))
        else:
            item.setText(status)

    def fetch_streams(self):
        try:
            req = urllib.request.Request(f"{SERVER_URL}/api/streams")
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                streams = data.get("streams", [])
                self.sidebar_items["grabber"].setText(f"🎬 Video Bắt Được ({len(streams)})")
                self.render_streams_table(streams)
        except Exception:
            pass

    def render_streams_table(self, streams):
        self.table_streams.setRowCount(0)
        for s in streams:
            url = s.get("url", "")
            fn = s.get("fn") or "Video Stream"
            ref = s.get("ref") or ""
            kind = (s.get("kind") or "HLS").upper()
            res = s.get("resolution") or "1080p"
            size = s.get("size") or "--"

            domain = urllib.parse.urlparse(ref or url).netloc or "Web Stream"

            row = self.table_streams.rowCount()
            self.table_streams.insertRow(row)

            # 0: Nguồn
            item_src = QTableWidgetItem(f"🌐 {domain}")
            self.table_streams.setItem(row, 0, item_src)

            # 1: Định dạng
            item_kind = QTableWidgetItem(f"[{kind}]")
            item_kind.setTextAlignment(Qt.AlignCenter)
            if kind in ("HLS", "DASH"):
                item_kind.setForeground(QColor("#ff9f0a"))
            else:
                item_kind.setForeground(QColor("#0a84ff"))
            self.table_streams.setItem(row, 1, item_kind)

            # 2: Tiêu đề
            item_fn = QTableWidgetItem(fn)
            item_fn.setToolTip(url)
            self.table_streams.setItem(row, 2, item_fn)

            # 3: Độ phân giải
            item_res = QTableWidgetItem(res)
            item_res.setTextAlignment(Qt.AlignCenter)
            item_res.setForeground(QColor("#30d158"))
            self.table_streams.setItem(row, 3, item_res)

            # 4: Dung lượng
            item_sz = QTableWidgetItem(size)
            item_sz.setTextAlignment(Qt.AlignCenter)
            self.table_streams.setItem(row, 4, item_sz)

            # 5: Nút thao tác
            btn_box = QWidget()
            box_layout = QHBoxLayout(btn_box)
            box_layout.setContentsMargins(2, 2, 2, 2)
            box_layout.setSpacing(4)

            btn_dl = QPushButton("⚡ Tải Aria2 (16 luồng)")
            btn_dl.setStyleSheet("background: #0a84ff; color: #fff; font-weight: bold; padding: 4px 10px;")
            btn_dl.clicked.connect(lambda _, u=url, r=ref, f=fn: self.start_download(u, r, f, "aria2"))
            box_layout.addWidget(btn_dl)

            btn_cp = QPushButton("📋")
            btn_cp.setToolTip("Sao chép liên kết URL")
            btn_cp.setStyleSheet("background: #2a2a32; max-width: 28px;")
            btn_cp.clicked.connect(lambda _, u=url: self.copy_to_clipboard(u))
            box_layout.addWidget(btn_cp)

            self.table_streams.setCellWidget(row, 5, btn_box)

    def on_tasks_context_menu(self, pos):
        row = self.table_tasks.rowAt(pos.y())
        if row < 0:
            return

        item0 = self.table_tasks.item(row, 0)
        tid = item0.data(Qt.UserRole)
        url = item0.data(Qt.UserRole + 1)
        file_path = item0.data(Qt.UserRole + 2)

        menu = QMenu(self)

        act_open = QAction("▶ Mở tập tin", self)
        act_open.triggered.connect(lambda: self.open_file_or_dir(file_path))
        menu.addAction(act_open)

        act_folder = QAction("📂 Mở thư mục chứa", self)
        act_folder.triggered.connect(lambda: self.open_folder_for_file(file_path))
        menu.addAction(act_folder)

        menu.addSeparator()

        act_copy = QAction("📋 Sao chép URL tải", self)
        act_copy.triggered.connect(lambda: self.copy_to_clipboard(url))
        menu.addAction(act_copy)

        act_retry = QAction("🔄 Tải lại", self)
        act_retry.triggered.connect(lambda: self.start_download(url, "", item0.text().strip(), "aria2"))
        menu.addAction(act_retry)

        menu.addSeparator()

        act_del = QAction("🗑 Xoá khỏi danh sách", self)
        act_del.triggered.connect(lambda: self.delete_task(tid, delete_file=False))
        menu.addAction(act_del)

        act_del_file = QAction("⚠️ Xoá cả tập tin trên đĩa", self)
        act_del_file.triggered.connect(lambda: self.delete_task(tid, delete_file=True))
        menu.addAction(act_del_file)

        menu.exec(self.table_tasks.viewport().mapToGlobal(pos))

    def on_task_double_clicked(self, row, col):
        item0 = self.table_tasks.item(row, 0)
        if item0:
            file_path = item0.data(Qt.UserRole + 2)
            self.open_file_or_dir(file_path)

    def open_file_or_dir(self, path):
        if path and os.path.exists(path):
            subprocess.Popen(["xdg-open", path])
        else:
            self.open_download_dir()

    def open_folder_for_file(self, path):
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            subprocess.Popen(["xdg-open", folder])
        else:
            self.open_download_dir()

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "AriaDM", "Đã sao chép liên kết vào bộ nhớ tạm (Clipboard)!")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AriaDM")
    win = AriaDMMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
