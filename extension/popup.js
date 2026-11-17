// AriaDM Popup Script
const SERVER_URL = "http://127.0.0.1:1001";

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("media-list");
  const countBadge = document.getElementById("count-badge");
  const btnOpenGui = document.getElementById("btn-open-gui");

  if (btnOpenGui) {
    btnOpenGui.addEventListener("click", () => {
      fetch(`${SERVER_URL}/api/open_gui`, { method: "POST" }).catch(() => {});
    });
  }

  // Lấy tab hiện tại
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  // Yêu cầu background gửi danh sách media
  chrome.runtime.sendMessage({ action: "get_media", tabId: tab.id }, (response) => {
    const list = (response && response.media) || [];
    countBadge.textContent = list.length;

    if (list.length === 0) return;

    container.innerHTML = "";
    list.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "media-card";

      const title = item.title || "Video Stream";
      const shortUrl = item.url.length > 55 ? item.url.slice(0, 52) + "..." : item.url;
      const res = item.resolution && item.resolution !== "--" ? item.resolution : "1080p";
      const sz = item.size && item.size !== "--" ? item.size : "--";
      const type = item.type || "Video";

      card.innerHTML = `
        <div class="media-title">${escapeHtml(title)}</div>
        <div class="tags-row">
          <span class="tag tag-res">📺 ${escapeHtml(res)}</span>
          <span class="tag tag-size">💾 ${escapeHtml(sz)}</span>
          <span class="tag tag-type">${escapeHtml(type)}</span>
        </div>
        <div class="media-url" title="${escapeHtml(item.url)}">${escapeHtml(shortUrl)}</div>
        <div class="btn-row">
          <button class="btn-download" data-idx="${index}">
            ⚡ Tải Aria2c (16 luồng)
          </button>
          <button class="btn-copy" data-url="${escapeHtml(item.url)}" title="Copy Link Stream">
            📋 Link
          </button>
          <button class="btn-cli" data-url="${escapeHtml(item.url)}" title="Copy lệnh terminal AriaDM">
            💻 CLI
          </button>
        </div>
      `;

      // Xử lý nút Tải
      const btnDownload = card.querySelector(".btn-download");
      btnDownload.addEventListener("click", () => {
        btnDownload.disabled = true;
        btnDownload.textContent = "⏳ Đang gửi sang Aria2c...";
        btnDownload.style.background = "#ffa000";

        fetch(`${SERVER_URL}/download`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: item.url,
            referer: item.pageUrl || tab.url,
            mode: "aria2",
            filename: title
          })
        })
        .then(r => r.json())
        .then(data => {
          btnDownload.textContent = "🚀 Đang tải với 16 luồng!";
          btnDownload.style.background = "#2e7d32";
          setTimeout(() => {
            btnDownload.disabled = false;
            btnDownload.textContent = "⚡ Tải Lại";
            btnDownload.style.background = "#1976D2";
          }, 3500);
        })
        .catch(err => {
          btnDownload.textContent = "❌ Lỗi kết nối Daemon";
          btnDownload.style.background = "#c62828";
          btnDownload.disabled = false;
        });
      });

      // Xử lý nút Copy Link
      const btnCopy = card.querySelector(".btn-copy");
      btnCopy.addEventListener("click", () => {
        navigator.clipboard.writeText(item.url);
        btnCopy.textContent = "✅ Đã chép";
        setTimeout(() => btnCopy.textContent = "📋 Link", 2000);
      });

      // Xử lý nút Copy Lệnh CLI
      const btnCli = card.querySelector(".btn-cli");
      btnCli.addEventListener("click", () => {
        const cmd = `ariadm "${item.url}"`;
        navigator.clipboard.writeText(cmd);
        btnCli.textContent = "✅ Đã chép";
        setTimeout(() => btnCli.textContent = "💻 CLI", 2000);
      });

      container.appendChild(card);
    });
  });
});

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
