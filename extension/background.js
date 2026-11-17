// AriaDM WebExtension Background Service Worker (Manifest V3)
// Độc lập 100% — Tự động bắt mọi luồng media & đồng bộ AriaDM Core

const CAPTURED_STREAMS = {}; // tabId -> Array of stream objects
const SERVER_URL = "http://127.0.0.1:1001";

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "--";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return bytes.toFixed(1) + " " + units[i];
}

// Lắng nghe Network Headers để bắt mọi stream video
chrome.webRequest.onHeadersReceived.addListener(
  function(details) {
    try {
      const url = details.url;
      if (!url || !url.startsWith("http")) return;
      const cleanUrl = url.split("?")[0].toLowerCase();
      let isMedia = false;
      let mediaType = "Video";
      let resolution = "--";

      // 1. Kiểm tra theo đuôi mở rộng
      if (cleanUrl.endsWith(".m3u8") || cleanUrl.includes(".m3u8")) {
        isMedia = true;
        mediaType = "HLS Stream";
        if (cleanUrl.includes("1080p")) resolution = "1080p";
        else if (cleanUrl.includes("720p")) resolution = "720p";
        else if (cleanUrl.includes("480p")) resolution = "480p";
      } else if (cleanUrl.endsWith(".vl") || cleanUrl.includes("/manifest")) {
        isMedia = true;
        mediaType = "HLS Stream (.vl)";
        resolution = "1080p";
      } else if (cleanUrl.endsWith(".mpd")) {
        isMedia = true;
        mediaType = "DASH Stream";
      } else if (cleanUrl.endsWith(".mp4")) {
        isMedia = true;
        mediaType = "MP4 Video";
      } else if (cleanUrl.endsWith(".webm")) {
        isMedia = true;
        mediaType = "WebM Video";
      } else if (cleanUrl.endsWith(".mkv")) {
        isMedia = true;
        mediaType = "MKV Video";
      }

      // 2. Kiểm tra theo Content-Type header
      let contentLength = 0;
      if (details.responseHeaders) {
        for (const h of details.responseHeaders) {
          const hn = h.name.toLowerCase();
          if (hn === "content-type") {
            const ct = (h.value || "").toLowerCase();
            if (ct.includes("application/vnd.apple.mpegurl") || ct.includes("application/x-mpegurl")) {
              isMedia = true;
              mediaType = "HLS Stream";
            } else if (ct.includes("application/dash+xml")) {
              isMedia = true;
              mediaType = "DASH Stream";
            } else if (ct.includes("video/mp4")) {
              isMedia = true;
              mediaType = "MP4 Video";
            } else if (ct.includes("video/webm")) {
              isMedia = true;
              mediaType = "WebM Video";
            }
          } else if (hn === "content-length") {
            contentLength = parseInt(h.value, 10) || 0;
          }
        }
      }

      // Bỏ qua các phân mảnh con nhỏ (.ts, .m4s) để tránh làm rối danh sách
      if (isMedia && !cleanUrl.endsWith(".ts") && !cleanUrl.endsWith(".m4s")) {
        const tabId = details.tabId;
        if (tabId >= 0) {
          chrome.tabs.get(tabId).then(tab => {
            if (!tab) return;
            const tabTitle = tab.title || "Video";
            const pageUrl = tab.url || "";

            const list = CAPTURED_STREAMS[tabId] || (CAPTURED_STREAMS[tabId] = []);
            if (!list.some(item => item.url === url)) {
              const entry = {
                url: url,
                type: mediaType,
                title: tabTitle,
                pageUrl: pageUrl,
                resolution: resolution,
                size: contentLength ? formatBytes(contentLength) : "--",
                time: Date.now()
              };
              list.push(entry);

              // Cập nhật huy hiệu trên icon extension
              chrome.action.setBadgeText({ tabId: tabId, text: String(list.length) });
              chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: "#1976D2" });

              // Đồng bộ báo về AriaDM Backend cổng 1001
              fetch(`${SERVER_URL}/api/register_stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  url: url,
                  referer: pageUrl,
                  filename: tabTitle,
                  action: 4
                })
              }).catch(() => {});
            }
          }).catch(() => {});
        }
      }
    } catch (e) {}
  },
  { urls: ["<all_urls>"] },
  ["responseHeaders"]
);

// Lắng nghe chuyển tab / cập nhật URL để tự động bắt YouTube & video platforms
function checkPageUrl(tabId, url, title) {
  if (!url || !url.startsWith("http")) return;
  if (url.includes("youtube.com/watch") || url.includes("youtu.be/")) {
    const list = CAPTURED_STREAMS[tabId] || (CAPTURED_STREAMS[tabId] = []);
    if (!list.some(item => item.url === url)) {
      list.push({
        url: url,
        type: "YouTube Video",
        title: title || "YouTube Video",
        pageUrl: url,
        resolution: "1080p (Full HD)",
        size: "~300 MB",
        time: Date.now()
      });
      chrome.action.setBadgeText({ tabId: tabId, text: String(list.length) });
      chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: "#CC0000" });

      fetch(`${SERVER_URL}/api/register_stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url,
          referer: url,
          filename: title || "YouTube Video",
          action: 4
        })
      }).catch(() => {});
    }
  }
}

chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {
  if (tab && tab.url) {
    checkPageUrl(tabId, tab.url, tab.title);
  }
});

chrome.tabs.onRemoved.addListener(function(tabId) {
  delete CAPTURED_STREAMS[tabId];
});

// Giao tiếp với Popup
chrome.runtime.onMessage.addListener(function(req, sender, sendResponse) {
  if (req.action === "get_media") {
    const list = CAPTURED_STREAMS[req.tabId] || [];
    sendResponse({ media: list });
    return true;
  }
});
