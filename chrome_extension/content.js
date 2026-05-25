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

  // ==========================================
  // 🔥 MATRIX VISION: PASİF OUTLIER RADARI 🔥
  // ==========================================
  
  // Matrix Vision CSS Enjeksiyonu
  const matrixStyle = document.createElement('style');
  matrixStyle.innerHTML = `
    /* Neon Yeşil ve Altın Sarısı Glow Efekti */
    .matrix-vision-glow {
        position: relative;
        border-radius: 12px !important;
        box-shadow: 0 0 15px 2px rgba(57, 255, 20, 0.7), 0 0 25px 5px rgba(255, 215, 0, 0.3) !important;
        transition: box-shadow 0.3s ease-in-out, transform 0.3s ease-in-out !important;
        z-index: 10;
    }
    
    .matrix-vision-glow:hover {
        box-shadow: 0 0 20px 4px rgba(57, 255, 20, 0.9), 0 0 35px 8px rgba(255, 215, 0, 0.5) !important;
        transform: scale(1.02);
        z-index: 99;
    }
    
    /* Thumbnail köşesindeki 🔥 TREND Rozeti */
    .matrix-trend-badge {
        position: absolute;
        top: 6px;
        right: 6px;
        background: linear-gradient(135deg, #FF3D00, #FFEA00);
        color: #000;
        font-weight: 800;
        font-size: 11px;
        font-family: 'Roboto', 'Arial', sans-serif;
        padding: 4px 8px;
        border-radius: 6px;
        z-index: 999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.7);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        pointer-events: auto;
        animation: matrix-pulse-badge 1.5s infinite alternate;
    }
    
    @keyframes matrix-pulse-badge {
        0% { transform: scale(1); box-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        100% { transform: scale(1.1); box-shadow: 0 4px 12px rgba(255, 61, 0, 0.6); }
    }
  `;
  document.head.appendChild(matrixStyle);

  const MATRIX_VISION = {
      config: {
          velocityThreshold: 5000, 
          maxAgeDays: 7,           
      },
      
      regex: {
          views: /([\d,.]+)\s*(B|M|K)?\s*(görüntüleme|views)/i,
          time: /(\d+)\s*(saniye|dakika|saat|gün|hafta|ay|yıl|second|minute|hour|day|week|month|year)s?\s*(önce|ago)/i
      },
  
      parseViews: function(text) {
          const match = text.match(this.regex.views);
          if (!match) return 0;
          
          let numStr = match[1];
          const multiplier = match[2] ? match[2].toUpperCase() : '';
          let num = 0;
  
          if (multiplier) {
              numStr = numStr.replace(',', '.');
              num = parseFloat(numStr);
              if (multiplier === 'B' || multiplier === 'K') num *= 1000;
              if (multiplier === 'M') num *= 1000000;
          } else {
              numStr = numStr.replace(/[,.]/g, '');
              num = parseInt(numStr, 10);
          }
          return num;
      },
  
      parseHours: function(text) {
          const match = text.match(this.regex.time);
          if (!match) return -1;
          
          const value = parseInt(match[1]);
          const unit = match[2].toLowerCase();
          
          if (unit.includes('saniye') || unit.includes('second')) return value / 3600;
          if (unit.includes('dakika') || unit.includes('minute')) return value / 60;
          if (unit.includes('saat') || unit.includes('hour')) return value;
          if (unit.includes('gün') || unit.includes('day')) return value * 24;
          if (unit.includes('hafta') || unit.includes('week')) return value * 24 * 7;
          if (unit.includes('ay') || unit.includes('month')) return value * 24 * 30; 
          if (unit.includes('yıl') || unit.includes('year')) return value * 24 * 365;
          
          return -1;
      },
  
      analyzeVideo: function(videoEl) {
          try {
              if (videoEl.dataset.matrixVisionDone) return;
              videoEl.dataset.matrixVisionDone = "true";
  
              const allSpans = videoEl.querySelectorAll('#metadata-line span');
              let viewText = "", timeText = "";
              
              allSpans.forEach(span => {
                  const text = span.textContent.trim();
                  if (this.regex.views.test(text)) viewText = text;
                  if (this.regex.time.test(text)) timeText = text;
              });
  
              if (!viewText || !timeText) return;
  
              const views = this.parseViews(viewText);
              const hours = this.parseHours(timeText);
  
              if (views <= 0 || hours <= 0) return;
  
              if (hours > (this.config.maxAgeDays * 24)) return;
  
              const velocity = views / hours;
  
              if (velocity >= this.config.velocityThreshold) {
                  this.injectUI(videoEl, velocity);
              }
          } catch (e) {}
      },
  
      injectUI: function(videoEl, velocity) {
          const thumbnail = videoEl.querySelector('ytd-thumbnail');
          if (!thumbnail) return;
  
          thumbnail.classList.add('matrix-vision-glow');
  
          if (!thumbnail.querySelector('.matrix-trend-badge')) {
              const badge = document.createElement('div');
              badge.className = 'matrix-trend-badge';
              badge.innerHTML = '🔥 TREND';
              badge.title = `Tahmini Hız: ${Math.round(velocity).toLocaleString()} izlenme/saat`;
              
              const overlays = thumbnail.querySelector('#overlays');
              if (overlays) {
                  overlays.appendChild(badge);
              } else {
                  thumbnail.appendChild(badge);
              }
          }
      },
  
      init: function() {
          const observer = new IntersectionObserver((entries) => {
              entries.forEach(entry => {
                  if (entry.isIntersecting) {
                      this.analyzeVideo(entry.target);
                  }
              });
          }, { root: null, rootMargin: '200px', threshold: 0.1 });
  
          setInterval(() => {
              const newVideos = document.querySelectorAll(`
                  ytd-rich-item-renderer:not([data-matrix-vision-observed]), 
                  ytd-video-renderer:not([data-matrix-vision-observed]),
                  ytd-compact-video-renderer:not([data-matrix-vision-observed])
              `);
              
              newVideos.forEach(video => {
                  video.dataset.matrixVisionObserved = "true";
                  observer.observe(video);
              });
          }, 2000);
      }
  };
  
  if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => MATRIX_VISION.init());
  } else {
      MATRIX_VISION.init();
  }
}
