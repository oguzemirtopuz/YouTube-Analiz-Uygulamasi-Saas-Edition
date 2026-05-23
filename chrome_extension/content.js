/**
 * content.js — YT Analiz Pro | Viral Klonlama Motoru
 *
 * Manifest V3 content script — YouTube sayfasına enjekte edilir.
 * popup.js, chrome.scripting.executeScript ile extractYouTubeData
 * fonksiyonunu doğrudan inject ettiğinden bu dosya pasif bir guard
 * görevi görür ve bağımsız mesaj dinleyicisi olarak da kullanılabilir.
 */

// Güvenlik kontrolü: script yalnızca YouTube watch sayfasında anlam taşır.
if (!window.location.href.includes('youtube.com/watch')) {
  // Sessizce çık — popup.js zaten URL doğrulaması yapar.
  // Bu satır yalnızca content_scripts tetiklemesi için korumadır.
} else {
  // İleride genişletilebilir: sayfa içi mesaj kanalı vs.
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === 'PING') {
      sendResponse({ alive: true, url: window.location.href });
    }
    return false; // senkron yanıt, kanal açık tutulmaz
  });
}
