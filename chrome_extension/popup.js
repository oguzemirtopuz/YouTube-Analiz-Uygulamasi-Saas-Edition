/**
 * popup.js — YT Analiz Pro | Viral Klonlama Motoru
 * Manifest V3 — popup script
 *
 * Akış:
 *   1. Popup açıldığında sunucu sağlık kontrolü yap.
 *   2. Kullanıcı "Klonla" butonuna basınca:
 *      a. Aktif sekmenin YouTube olduğunu doğrula.
 *      b. content.js'i enjekte ederek video metadata'yı çek.
 *      c. POST /api/extension/clone_video → yanıtı göster.
 *   3. Hata durumlarını şık error-view ile göster.
 */

const SERVER = 'http://127.0.0.1:8000';

// ── DOM Referansları ──────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const views = {
  idle:    $('view-idle'),
  loading: $('view-loading'),
  result:  $('view-result'),
  error:   $('view-error'),
};

const elDot          = $('status-dot');
const elStatusLabel  = $('server-status-label');
const elBtnClone     = $('btn-clone');
const elBtnReset     = $('btn-reset');
const elBtnRetry     = $('btn-retry');
const elResultBox    = $('result-content');
const elThumbWrap    = $('video-thumb-wrap');
const elThumbImg     = $('video-thumb');
const elThumbMeta    = $('video-meta');
const elLoadingSub   = $('loading-sub-text');
const elErrorTitle   = $('error-title');
const elErrorMsg     = $('error-msg');

// ── View Geçişi ───────────────────────────────────────────────────────────────
function showView(name) {
  Object.values(views).forEach(v => v.classList.remove('active'));
  views[name].classList.add('active');
}

// ── Sunucu Sağlık Kontrolü ────────────────────────────────────────────────────
async function checkServer() {
  setServerStatus('checking');
  try {
    const resp = await fetch(`${SERVER}/health`, { method: 'GET', cache: 'no-store' });
    if (resp.ok) { setServerStatus('online'); return true; }
    setServerStatus('offline'); return false;
  } catch {
    setServerStatus('offline'); return false;
  }
}

function setServerStatus(state) {
  elDot.className = `dot dot--${state}`;
  if (state === 'online') {
    elStatusLabel.textContent = '● Çevrimiçi';
    elStatusLabel.className   = 'server-status online';
    elBtnClone.disabled = false;
  } else if (state === 'offline') {
    elStatusLabel.textContent = '● Çevrimdışı';
    elStatusLabel.className   = 'server-status offline';
    elBtnClone.disabled = true;
  } else {
    elStatusLabel.textContent = 'Kontrol ediliyor...';
    elStatusLabel.className   = 'server-status';
  }
}

// ── Hata Gösterici ────────────────────────────────────────────────────────────
function showError(title, msg) {
  elErrorTitle.textContent = title;
  elErrorMsg.textContent   = msg;
  showView('error');
}

// ── YouTube Sekme Doğrulama ───────────────────────────────────────────────────
function isYouTubeTab(tab) {
  return tab?.url?.match(/https:\/\/(www\.)?youtube\.com\/watch\?/);
}

// ── Klonlama Ana Akışı ────────────────────────────────────────────────────────
async function cloneVideo() {
  // 1. Sunucu online mı?
  const serverUp = await checkServer();
  if (!serverUp) {
    showError(
      '🔴 Sunucu Çevrimdışı',
      'YT Analiz Pro masaüstü uygulaması çalışmıyor.\n127.0.0.1:8000 adresinde FastAPI sunucusunu başlatın.'
    );
    return;
  }

  // 2. Aktif sekme YouTube'da mı?
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!isYouTubeTab(tab)) {
    showError(
      '📺 YouTube Sayfası Gerekli',
      'Bu eklenti yalnızca YouTube video sayfalarında (/watch?v=...) çalışır.\nBir video açıp tekrar deneyin.'
    );
    return;
  }

  // 3. Loading göster
  showView('loading');
  elLoadingSub.textContent = 'Sayfa verisi okunuyor...';

  // 4. content.js inject et ve metadata çek
  let videoData;
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractYouTubeData,
    });

    // executeScript dönüşü: { result: <fonksiyonun döndürdüğü değer> }
    const extracted = result?.result;

    // Fonksiyon içinden { error: "..." } geldiyse yakala
    if (!extracted || extracted.error) {
      showError('❌ Veri Çekme Hatası', extracted?.error || 'Sayfa verisi okunamadı.');
      return;
    }

    videoData = extracted;

    if (!videoData.videoId) {
      showError('❌ Video Verisi Bulunamadı', 'Sayfa henüz yüklenmiş olmayabilir. Video sayfasını yenileyin.');
      return;
    }
  } catch (err) {
    showError('❌ Script Hatası', `İçerik scripti çalışmadı: ${err.message}`);
    return;
  }

  // 5. Thumbnail göster
  if (videoData.thumbnail) {
    elThumbImg.src     = videoData.thumbnail;
    elThumbMeta.textContent = `${videoData.title || 'Video'} · ${videoData.channel || ''}`;
    elThumbWrap.style.display = 'block';
  }

  elLoadingSub.textContent = 'AI konsept üretiyor...';

  // 6. Backend'e POST — yalnızca bilinen alanları gönder (422 önlemi)
  const requestBody = {
    url:       videoData.url       || '',
    videoId:   videoData.videoId   || '',
    title:     videoData.title     || 'Başlık Yok',
    channel:   videoData.channel   || 'Bilinmeyen Kanal',
    thumbnail: videoData.thumbnail || '',
  };

  try {
    const resp = await fetch(`${SERVER}/api/extension/clone_video`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body:    JSON.stringify(requestBody),
    });

    const data = await resp.json();

    if (!resp.ok || data.error) {
      // Backend'den error mesajı geldiyse doğrudan onu göster. Yoksa genel HTTP statüsünü yazdır.
      const msg = data.error || `Bilinmeyen Hata (HTTP ${resp.status})`;
      showError('⚠️ İşlem Başarısız', msg);
      return;
    }

    // 7. Sonucu göster
    elResultBox.textContent = data.result || '(Boş yanıt)';
    showView('result');

  } catch (fetchErr) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${fetchErr.message}`);
  }
}

// ── YouTube Veri Çekici (Sayfa içinde çalışır) ────────────────────────────────
function extractYouTubeData() {
  try {
    const url     = window.location.href;
    const videoId = new URLSearchParams(window.location.search).get('v');

    if (!videoId) {
      return { error: 'Geçerli bir YouTube video ID\'si bulunamadı. /watch?v= parametresi eksik.' };
    }

    const title = (
      document.querySelector('h1.ytd-watch-metadata yt-formatted-string') ||
      document.querySelector('#title h1') ||
      document.querySelector('h1.title')
    )?.textContent?.trim() || 'Başlık bulunamadı';

    const channel = (
      document.querySelector('#channel-name a') ||
      document.querySelector('ytd-channel-name a') ||
      document.querySelector('#owner-name a')
    )?.textContent?.trim() || 'Kanal adı bulunamadı';

    const thumbnail = `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`;

    return { url, videoId, title, channel, thumbnail };
  } catch (err) {
    return { error: `Veri çekme hatası: ${err.message}` };
  }
}

// ── Event Listeners ───────────────────────────────────────────────────────────
elBtnClone.addEventListener('click', cloneVideo);

elBtnReset.addEventListener('click', () => {
  elThumbWrap.style.display = 'none';
  elThumbImg.src = '';
  elResultBox.textContent = '';
  showView('idle');
});

elBtnRetry.addEventListener('click', () => showView('idle'));

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  elBtnClone.disabled = true; // sunucu kontrolü bitene kadar devre dışı
  await checkServer();
  showView('idle');
})();
