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
  login:   $('view-login'),
  idle:    $('view-idle'),
  loading: $('view-loading'),
  result:  $('view-result'),
  error:   $('view-error'),
};

const elDot          = $('status-dot');
const elStatusLabel  = $('server-status-label');
const elBtnClone     = $('btn-clone');
const elBtnAnalyze   = $('btn-analyze');
const elRabbitQuery  = $('rabbit-query');
const elBtnRabbit    = $('btn-rabbit');
const elBtnReset     = $('btn-reset');
const elBtnRetry     = $('btn-retry');
const elResultBox    = $('result-content');
const elThumbWrap    = $('video-thumb-wrap');
const elThumbImg     = $('video-thumb');
const elThumbMeta    = $('video-meta');
const elLoadingSub   = $('loading-sub-text');
const elErrorTitle   = $('error-title');
const elErrorMsg     = $('error-msg');

const elLoginUser    = $('login-username');
const elLoginPass    = $('login-password');
const elLoginError   = $('login-error');
const elBtnLogin     = $('btn-login');
const elDashUser     = $('dash-username');
const elBtnLogout    = $('btn-logout');
const elRecentList   = $('recent-list');

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

// ── Auth & Dashboard ──────────────────────────────────────────────────────────
async function loadRecentAnalyses(userId) {
  try {
    const resp = await fetch(`${SERVER}/api/extension/recent_analyses?user_id=${userId}`);
    const data = await resp.json();
    elRecentList.innerHTML = '';
    
    if (data.success && data.analyses.length > 0) {
      data.analyses.forEach(a => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="recent-name" title="${a.video_name}">${a.video_name}</span><span class="recent-score">${a.score}</span>`;
        elRecentList.appendChild(li);
      });
    } else {
      elRecentList.innerHTML = '<li style="color:#666; font-style:italic;">Henüz analiz yok.</li>';
    }
  } catch (err) {
    elRecentList.innerHTML = '<li style="color:var(--error);">Veriler çekilemedi.</li>';
  }
}

async function handleLogin() {
  const username = elLoginUser.value.trim();
  const password = elLoginPass.value.trim();
  
  if (!username || !password) {
    elLoginError.textContent = 'Kullanıcı adı ve şifre zorunludur.';
    elLoginError.style.display = 'block';
    return;
  }
  
  const serverUp = await checkServer();
  if (!serverUp) {
    elLoginError.textContent = 'Sunucuya bağlanılamadı.';
    elLoginError.style.display = 'block';
    return;
  }

  elBtnLogin.textContent = 'Giriş yapılıyor...';
  elBtnLogin.disabled = true;
  elLoginError.style.display = 'none';
  
  try {
    const resp = await fetch(`${SERVER}/api/extension/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || 'Giriş başarısız.');
    }
    
    await chrome.storage.local.set({ user_id: data.user_id, username: data.username });
    showDashboard(data.username, data.user_id);
    
  } catch (err) {
    elLoginError.textContent = err.message;
    elLoginError.style.display = 'block';
  } finally {
    elBtnLogin.textContent = 'Giriş Yap';
    elBtnLogin.disabled = false;
  }
}

function showDashboard(username, userId) {
  elDashUser.textContent = username;
  showView('idle');
  loadRecentAnalyses(userId);
}

function handleLogout() {
  chrome.storage.local.remove(['user_id', 'username'], () => {
    elLoginUser.value = '';
    elLoginPass.value = '';
    elLoginError.style.display = 'none';
    showView('login');
  });
}

// ── YouTube Sekme Doğrulama ───────────────────────────────────────────────────
function isYouTubeTab(tab) {
  return tab?.url?.match(/https:\/\/(www\.)?youtube\.com\/watch\?/);
}

function isYouTubeChannelTab(tab) {
  return tab?.url?.match(/https:\/\/(www\.)?youtube\.com\/(@|channel\/|c\/)/);
}

// ── Savaş Raporu Ana Akışı (Kanal Analizi) ────────────────────────────────────
async function analyzeChannel() {
  const serverUp = await checkServer();
  if (!serverUp) {
    showError('🔴 Sunucu Çevrimdışı', 'YT Analiz Pro masaüstü uygulaması çalışmıyor.');
    return;
  }
  
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!isYouTubeChannelTab(tab)) {
    showError('📺 Kanal Sayfası Gerekli', 'Bu işlem yalnızca YouTube kanal sayfalarında çalışır.');
    return;
  }
  
  const { user_id } = await chrome.storage.local.get(['user_id']);
  if (!user_id) {
    showError('🔐 Giriş Gerekli', 'Kanal analizi için giriş yapmalısınız.');
    return;
  }
  
  showView('loading');
  elLoadingSub.textContent = 'Kanal verileri çekiliyor ve Savaş Raporu oluşturuluyor... (Bu işlem biraz sürebilir)';
  
  try {
    const resp = await fetch(`${SERVER}/api/extension/analyze_channel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel_url: tab.url, user_id })
    });
    
    const data = await resp.json();
    if (!resp.ok || data.error) {
      showError('⚠️ İşlem Başarısız', data.error || 'Bilinmeyen Hata');
      return;
    }
    
    elResultBox.innerHTML = `<strong>⚔️ VS ${data.rival_name || 'Rakip'}</strong><br><br>${data.result}`;
    showView('result');
  } catch (err) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${err.message}`);
  }
}

// ── Tavşan Deliği (Niş Bulucu) Ana Akışı ──────────────────────────────────────
async function findRabbitHole() {
  const query = elRabbitQuery.value.trim();
  if (!query) {
    showError('⚠️ Eksik Bilgi', 'Lütfen aramak için bir kelime (niş) girin.');
    return;
  }
  
  const serverUp = await checkServer();
  if (!serverUp) {
    showError('🔴 Sunucu Çevrimdışı', 'YT Analiz Pro masaüstü uygulaması çalışmıyor.');
    return;
  }
  
  showView('loading');
  elLoadingSub.textContent = 'Derinlere iniliyor... (Bu işlem biraz sürebilir)';
  
  try {
    const resp = await fetch(`${SERVER}/api/extension/rabbit_hole`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    const data = await resp.json();
    if (!resp.ok || data.error) {
      showError('⚠️ İşlem Başarısız', data.error || 'Bu nişte aykırı bir trend bulunamadı.');
      return;
    }
    
    let htmlCards = `<h4 style="color:#e0b0ff; margin-bottom:15px;">🐇 '${query}' İçin Aykırı Videolar</h4>`;
    
    data.outliers.forEach(v => {
      htmlCards += `
<div style="background: rgba(10,20,30,0.8); border: 1px solid #06b6d4; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
    <h4 style="color: white; margin-bottom: 8px; font-size: 1.05rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${v.title}</h4>
    <div style="margin-bottom: 8px; font-size: 0.85rem; color: #94a3b8;">
        Kanal: <span style="color: #cbd5e1;">${v.channel}</span>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="background: linear-gradient(90deg, #f43f5e, #f97316); color: white; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; box-shadow: 0 0 10px rgba(244,63,94,0.5);">
            🔥 Hız: ${v.velocity} izlenme/gün
        </span>
        <a href="${v.url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.8rem; font-weight: bold;">İzle ↗</a>
    </div>
</div>`;
    });
    
    elResultBox.innerHTML = htmlCards;
    showView('result');
  } catch (err) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${err.message}`);
  }
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

  const { user_id } = await chrome.storage.local.get(['user_id']);

  // 6. Backend'e POST — yalnızca bilinen alanları gönder (422 önlemi)
  const requestBody = {
    url:       videoData.url       || '',
    videoId:   videoData.videoId   || '',
    title:     videoData.title     || 'Başlık Yok',
    channel:   videoData.channel   || 'Bilinmeyen Kanal',
    thumbnail: videoData.thumbnail || '',
    user_id:   user_id || 0
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
    try {
      const ideas = JSON.parse(data.result);
      if (Array.isArray(ideas)) {
        let htmlCards = '';
        ideas.forEach(idea => {
          htmlCards += `
<div style="background: rgba(30,20,50,0.8); border: 1px solid #a855f7; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
    <h4 style="color: white; margin-bottom: 8px; font-size: 1.1rem;">💡 ${idea.title || 'Başlık Yok'}</h4>
    <div style="margin-bottom: 8px;">
        <span style="color: #f59e0b; font-size: 0.8rem; font-weight: bold;">KANCA (HOOK)</span><br>
        <span style="color: #d8b4fe; font-size: 0.9rem;">"${idea.hook || 'Kanca Yok'}"</span>
    </div>
    <div>
        <span style="color: #10b981; font-size: 0.8rem; font-weight: bold;">THUMBNAIL</span><br>
        <span style="color: #94a3b8; font-size: 0.85rem;">${idea.thumbnail || 'Thumbnail önerisi yok'}</span>
    </div>
</div>`;
        });
        elResultBox.innerHTML = htmlCards;
      } else {
        throw new Error("Dizi değil");
      }
    } catch (e) {
      // JSON.parse hata verirse ham metni göster
      elResultBox.textContent = data.result || '(Boş yanıt)';
    }
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
elBtnLogin.addEventListener('click', handleLogin);
elBtnLogout.addEventListener('click', handleLogout);
elBtnClone.addEventListener('click', cloneVideo);
elBtnAnalyze.addEventListener('click', analyzeChannel);
elBtnRabbit.addEventListener('click', findRabbitHole);

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
  
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (isYouTubeChannelTab(tab)) {
    elBtnClone.style.display = 'none';
    elBtnAnalyze.style.display = 'inline-flex';
  } else {
    elBtnClone.style.display = 'inline-flex';
    elBtnAnalyze.style.display = 'none';
  }
  
  chrome.storage.local.get(['user_id', 'username'], (res) => {
    if (res.user_id && res.username) {
      showDashboard(res.username, res.user_id);
    } else {
      showView('login');
    }
  });
})();
