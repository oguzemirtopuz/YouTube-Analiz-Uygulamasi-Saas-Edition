/**
 * content.js — YT Analiz Pro | Viral Klonlama Motoru
 *
 * Manifest V3 content script — YouTube sayfasına enjekte edilir.
 * popup.js, chrome.scripting.executeScript ile extractYouTubeData
 * fonksiyonunu doğrudan inject ettiğinden bu dosya pasif bir guard
 * görevi görür ve bağımsız mesaj dinleyicisi olarak da kullanılabilir.
 *
 * STRES TESTİ FIX #5 — YouTube SPA Navigation:
 * YouTube, sayfa yenilemeden (AJAX / History API) video değiştirir.
 * Bu dosya artık URL değişimlerini izleyerek popup'a bildirim gönderir.
 * Popup bu event'i alınca kullanıcıya "Video değişti, tekrar Klonla'ya bas" uyarısı çıkabilir.
 */

if (window.location.href.includes('youtube.com')) {

  // ── Pasif mesaj dinleyicisi ────────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === 'PING') {
      sendResponse({ alive: true, url: window.location.href });
    }
    return false; // senkron yanıt, kanal açık tutulmaz
  });

  // ── YouTube SPA Navigation Detector ────────────────────────────────────────
  // YouTube kendi için 'yt-navigate-finish' custom event'i fırlatır.
  // Bu event, AJAX ile video değiştiğinde tetiklenir (history.pushState dahil).
  let _lastUrl = window.location.href;

  function _notifyUrlChange(newUrl) {
    if (newUrl !== _lastUrl && newUrl.includes('/watch?')) {
      _lastUrl = newUrl;
      // Popup açıksa bildirim gönder (popup kapalıysa chrome hata loglar, sorun değil)
      chrome.runtime.sendMessage({
        type: 'YT_URL_CHANGED',
        url: newUrl
      }).catch(() => {}); // popup kapalıysa sessizce geç
    }
  }

  // 1. YouTube'un kendi SPA event'i (en güvenilir)
  window.addEventListener('yt-navigate-finish', () => {
    _notifyUrlChange(window.location.href);
  });

  // 2. Fallback: history.pushState / replaceState intercept
  // (yt-navigate-finish güncellemelerden sonra kaybolursa bu devreye girer)
  const _origPush = history.pushState.bind(history);
  const _origReplace = history.replaceState.bind(history);

  history.pushState = function(...args) {
    _origPush(...args);
    _notifyUrlChange(window.location.href);
  };

  history.replaceState = function(...args) {
    _origReplace(...args);
    _notifyUrlChange(window.location.href);
  };

  // 3. popstate (geri/ileri navigasyon)
  window.addEventListener('popstate', () => {
    _notifyUrlChange(window.location.href);
  });
}
