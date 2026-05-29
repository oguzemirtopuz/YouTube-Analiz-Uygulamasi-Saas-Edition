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

// ── DOM References ───────────────────────────── ─────────────────────────────
const $ = id => document.getElementById(id);

const views = {
  login:   $('view-login'),
  idle:    $('view-idle'),
  loading: $('view-loading'),
  result:  $('view-result'),
  debate:  $('view-debate'),
  error:   $('view-error'),
  info:    $('view-info'),
};

const elDot          = $('status-dot');
const elStatusLabel  = $('server-status-label');
const elBtnClone     = $('btn-clone');
const elBtnDebate    = $('btn-debate');
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

// ── View Switch ─────────────────────────────── ────────────────────────────────
function showView(name) {
  Object.values(views).forEach(v => v.classList.remove('active'));
  views[name].classList.add('active');
}

// ── Server Health Check ────────────────────────── ──────────────────────────
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
    elBtnClone.disabled  = false;
    if (elBtnDebate) elBtnDebate.disabled = false;
  } else if (state === 'offline') {
    elStatusLabel.textContent = '● Çevrimdışı';
    elStatusLabel.className   = 'server-status offline';
    elBtnClone.disabled  = true;
    if (elBtnDebate) elBtnDebate.disabled = true;
  } else {
    elStatusLabel.textContent = 'Kontrol ediliyor...';
    elStatusLabel.className   = 'server-status';
  }
}

// ── Error Pointer ────────────────────────────── ──────────────────────────────
function showError(title, msg) {
  elErrorTitle.textContent = title;
  elErrorMsg.textContent   = msg;
  showView('error');
}

// ── Auth & Dashboard ───────────────────────────── ─────────────────────────────
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

// ── Active Tab Detection (For Full Screen Support) ─────────────────────────────
// BUG FIX: tabs[0] fallback has been removed. With passedUrl from URL query
// If there is no matching tab, it returns null — analysis cannot be performed with an empty/wrong URL.
async function getActiveTab() {
  const urlParams = new URLSearchParams(window.location.search);
  const passedUrl = urlParams.get('url');
  
  if (passedUrl) {
    // Full screen mode: Find the tab whose URL matches exactly.
    // If there is no match, return ERROR — don't pick a random YouTube tab!
    let tabs = await chrome.tabs.query({ url: "*://*.youtube.com/*" });
    let matchedTab = tabs.find(t => t.url === passedUrl);
    if (matchedTab) return matchedTab;
    // No match found: return null, the calling function will throw an error.
    return null;
  }
  
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// ── YouTube Tab Verification ───────────────────────── ──────────────────────────
function isYouTubeTab(tab) {
  return tab?.url?.match(/https:\/\/(www\.)?youtube\.com\/watch\?/);
}

function isYouTubeChannelTab(tab) {
    if (!tab || !tab.url) return false;
    const url = tab.url.toLowerCase();
    
    // Open channel formats
    if (url.includes('/@') || url.includes('/channel/') || url.includes('/c/') || url.includes('/user/')) return true;
    
    // Special URLs (ex: youtube.com/mendeburlemur)
    try {
        const u = new URL(url);
        if (u.hostname.includes('youtube.com')) {
            const path = u.pathname;
            const excludePaths = ['/watch', '/results', '/feed', '/shorts', '/playlist', '/account', '/premium', '/gaming', '/trending'];
            if (path.length > 1 && !excludePaths.some(p => path.startsWith(p))) {
                return true;
            }
        }
    } catch(e) {}
    
    return false;
}

// ── Battle Report Mainstream (Channel Analysis) ────────────────────────────────────
async function analyzeChannel() {
  const serverUp = await checkServer();
  if (!serverUp) {
    showError('🔴 Sunucu Çevrimdışı', 'YT Analiz Pro masaüstü uygulaması çalışmıyor.');
    return;
  }
  
  let tab = await getActiveTab();
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
  elLoadingSub.textContent = 'Rakip verileri sömürülüyor... Savaş Raporu hazırlanıyor!';
  
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
    
    if (data.chaos_metrics) {
        const chaosHtml = `
        <div class="chaos-card">
            <h3 class="chaos-title">🌪️ KAOS METRİĞİ</h3>
            <div class="chaos-score">${data.chaos_metrics.score} <span style="font-size:14px; color:#aaa;">/ 10</span></div>
            <div class="chaos-verdict">${data.chaos_metrics.verdict}</div>
        </div>`;
        elResultBox.innerHTML += chaosHtml;
    }
    
    showView('result');
  } catch (err) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${err.message}`);
  }
}

// ── Rabbit Hole (Niche Finder) Mainstream ──────────────────────────────────────
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
  elLoadingSub.textContent = "YouTube'un derinliklerine iniliyor... (Bu işlem 15-30 sn sürebilir)";
  
  const { user_id } = await chrome.storage.local.get(['user_id']);
  
  try {
    const resp = await fetch(`${SERVER}/api/extension/rabbit_hole`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: query, 
        user_id: user_id || localStorage.getItem('user_id') || "default_user" 
      })
    });
    
    const data = await resp.json();
    if (!resp.ok || data.error) {
      showError('⚠️ İşlem Başarısız', data.error || 'Bu nişte aykırı bir trend bulunamadı.');
      return;
    }
    
    let htmlCards = `<h4 style="color:#e0b0ff; margin-bottom:15px;">🐇 '${query}' İçin Aykırı Videolar</h4>`;
    
    data.outliers.forEach(v => {
      let uyumlulukHtml = '';
      if (v.uyumluluk) {
        const isUyumlu = v.uyumluluk.toLowerCase().includes('uyumlu') && !v.uyumluluk.toLowerCase().includes('uyumsuz');
        const color = isUyumlu ? '#22c55e' : '#ef4444'; // Yeşil veya Kırmızı
        const icon = isUyumlu ? '✅' : '⚠️';
        uyumlulukHtml = `
        <div style="margin-top: 10px; padding: 8px; background: rgba(0,0,0,0.4); border-left: 3px solid ${color}; border-radius: 4px; font-size: 0.8rem; color: #e2e8f0; line-height: 1.4;">
            <strong>${icon} Uyumluluk Analizi:</strong> ${v.uyumluluk}
        </div>`;
      }

      htmlCards += `
<div class="rabbit-card" style="background: rgba(10,20,30,0.8); border: 1px solid #06b6d4; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
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
    ${uyumlulukHtml}
</div>`;
    });
    
    elResultBox.innerHTML = htmlCards;
    showView('result');
  } catch (err) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${err.message}`);
  }
}

// ── A/B Test Debate Main Flow ────────────────────── ───────────────────────
async function debateVideo(eventOrData = null) {
  let isAuto = eventOrData && !(eventOrData instanceof Event);
  let autoData = isAuto ? eventOrData : null;

  // 1. Is the server online?
  const serverUp = await checkServer();
  if (!serverUp) {
    showError('🔴 Sunucu Çevrimdışı', 'YT Analiz Pro masaüstü uygulaması çalışmıyor.');
    return;
  }

  let tab = null;
  if (!autoData) {
      // 2. Is the active tab a YouTube video?
      tab = await getActiveTab();
      if (!tab) {
        showError('🔗 Sekme Bulunamadı', 'Analiz edilecek YouTube video sekmesi bulunamadı.');
        return;
      }
      if (!isYouTubeTab(tab)) {
        showError('📺 YouTube Sayfası Gerekli', 'Bu özellik yalnızca YouTube video sayfalarında çalışır.');
        return;
      }
  }

  // 3. Show Battle loading screen (with 3s progress bar animation)
  showView('loading');
  elLoadingSub.textContent = 'Persona A vs B savaşıyor...';

  // Inject progress bar (only in debate mode)
  const existingBar = document.getElementById('battle-bar-wrap');
  if (!existingBar) {
    const barWrap = document.createElement('div');
    barWrap.id = 'battle-bar-wrap';
    barWrap.className = 'battle-progress-wrap';
    barWrap.innerHTML = `
      <div class="battle-progress-label">⚔️ Ajanlar Kapışıyor... Hakem Karar Veriyor...</div>
      <div class="battle-progress-bar"><div class="battle-progress-fill"></div></div>
    `;
    // add at the end of loading view
    views.loading.appendChild(barWrap);
  } else {
    // Restart animation if applicable
    const fill = existingBar.querySelector('.battle-progress-fill');
    if (fill) { fill.style.animation = 'none'; fill.offsetHeight; fill.style.animation = ''; }
  }

  // 4. Get metadata
  let videoData;
  if (autoData) {
      videoData = autoData;
  } else {
      try {
        const [result] = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: extractYouTubeData,
        });
        const extracted = result?.result;
        if (!extracted || extracted.error) {
          showError('❌ Veri Çekme Hatası', extracted?.error || 'Sayfa verisi okunamadı.');
          return;
        }
        videoData = extracted;
        if (!videoData.videoId) {
          showError('❌ Video Verisi Bulunamadı', 'Video sayfasını yenileyin.');
          return;
        }
      } catch (err) {
        showError('❌ Script Hatası', `İçerik scripti çalışmadı: ${err.message}`);
        return;
      }
  }

  const { user_id } = await chrome.storage.local.get(['user_id']);

  // Request enriched with Predictive Intelligence fields
  const requestBody = enrichVideoData(videoData, user_id);

  // 5. POST /api/extension/clone_debate
  try {
    const resp = await fetch(`${SERVER}/api/extension/clone_debate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body:    JSON.stringify(requestBody),
    });

    const data = await resp.json();

    // Fail-Fast: HTTP error or backend error field → press screen honestly
    if (!resp.ok || !data.success) {
      const msg = data.detail || data.error || `Bilinmeyen Hata (HTTP ${resp.status})`;
      showError('⚠️ Tartışma Başarısız', msg);
      return;
    }

    const d = data.debate;
    const debateViews    = requestBody.views || 0;
    const debateTier     = requestBody.tier  || (debateViews >= 5000 ? 'viral' : debateViews >= 500 ? 'potential' : 'dead');
    const debateVelocity = requestBody.velocity_per_day;
    const debateWindow   = requestBody.time_window;
    const debatePenetr   = requestBody.penetration_ratio;

    // 6. Fill in the Debate result view
    document.getElementById('debate-critic-summary').textContent  = d.eleştirmen_fikri  || '—';
    document.getElementById('debate-wizard-summary').textContent  = d.buyucu_fikri      || '—';
    document.getElementById('debate-winner-title').textContent    = d.kazanan_baslik    || '—';
    document.getElementById('debate-winner-hook').textContent     = d.kazanan_kanca     || '—';
    document.getElementById('debate-winner-thumb').textContent    = d.kazanan_thumbnail || '—';

    // Dynamic fields
    const winnerCard = document.querySelector('.debate-winner-card');
    if (winnerCard) {
        const oldExtra = winnerCard.querySelector('.dynamic-debate-extras');
        if (oldExtra) oldExtra.remove();
        
        let extraHtml = '';

        // ── 5 Tier Tier Banner (Debate) ──────────────────────────────────
        const TIER_CONFIG = {
          dead:       { emoji: '🔴', label: 'ÖLÇÜM',         color: '#ef4444', bg: 'rgba(239,68,68,0.12)',    sub: 'Acil müdahale önerileri aşağıda.' },
          potential:  { emoji: '🟡', label: 'POTANSİYEL VAR', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', sub: 'Bir hamle eksik — öneriler aşağıda.' },
          rising:     { emoji: '🚀', label: 'YÜKSELIYOR!',   color: '#f97316', bg: 'rgba(249,115,22,0.15)',   sub: 'Momentum yakalandı — şimdi harekete geç.' },
          viral:      { emoji: '🟢', label: 'VİRAL',         color: '#22c55e', bg: 'rgba(34,197,94,0.12)',    sub: 'Başarının anatomisi aşağıda.' },
          mega_viral: { emoji: '🔵', label: 'MEGA VİRAL',    color: '#38bdf8', bg: 'rgba(56,189,248,0.12)',   sub: 'Algoritma kırıcı — sistemi çıkart, kazayı kopyalama.' },
        };
        const dtc = TIER_CONFIG[debateTier] || TIER_CONFIG['potential'];
        const dViewsStr = debateViews > 0 ? debateViews.toLocaleString('tr-TR') + ' izlenme' : 'İzlenme verisi alınamadı';

        let dChips = '';
        if (debateVelocity !== null && debateVelocity !== undefined) {
          dChips += `<span class="pi-chip">📈 ~${debateVelocity.toLocaleString('tr-TR')} izlenme/gün</span>`;
        }
        if (debateWindow) {
          const wLabels = { fresh: '⏱ Yeni yayınlandı', burst: '⚡ Patlama penceresi', established: '📅 Algoritma yayılımı', evergreen: '🌿 Evergreen içerik' };
          dChips += `<span class="pi-chip">${wLabels[debateWindow] || debateWindow}</span>`;
        }
        if (debatePenetr !== null && debatePenetr !== undefined) {
          const pLabel = debatePenetr >= 1 ? 'Yüksek' : debatePenetr >= 0.1 ? 'Orta' : 'Düşük';
          dChips += `<span class="pi-chip">👥 Abone oranı: ${debatePenetr.toFixed(1)}x (${pLabel})</span>`;
        }

        extraHtml += `<div class="tier-banner" style="border-color:${dtc.color}; background:${dtc.bg}; margin-bottom:12px;">
          <div class="tier-banner__header">
            <span class="tier-banner__emoji">${dtc.emoji}</span>
            <strong class="tier-banner__label" style="color:${dtc.color};">${dtc.label}</strong>
            <span class="tier-banner__views">${dViewsStr}</span>
          </div>
          <div class="tier-banner__sub">${dtc.sub}</div>
          ${dChips ? `<div class="pi-chips">${dChips}</div>` : ''}
        </div>`;

        if (d.viral_anatomi) {
          const isViralTier = debateTier === 'viral' || debateTier === 'mega_viral';
          const anatomyLabel = isViralTier ? '[VİRAL ANATOMİ: Bu Video Neden Patladı?]'
            : debateTier === 'rising' ? '[MOMENTUM ANALİZİ: Bu Video Neden Yükseliyor?]'
            : '[VİDEO ANALİZİ: Bu Video Neden Kitle Bulamıyor?]';
          const anatomyColor = isViralTier ? '#fbbf24' : debateTier === 'rising' ? '#f97316' : '#f87171';
          extraHtml += `<div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1);"><strong style="color:${anatomyColor};">${anatomyLabel}</strong><br><span style="font-size:11px; color:#e2e8f0;">${d.viral_anatomi}</span></div>`;
        }
        if (d.nis_uyarisi) extraHtml += `<div style="margin-top:10px; padding-top:10px; border-top:1px solid rgba(239,68,68,0.3); color:#fca5a5; font-size:11px;"><strong>${d.nis_uyarisi}</strong></div>`;
        
        if (extraHtml) {
            const extraDiv = document.createElement('div');
            extraDiv.className = 'dynamic-debate-extras';
            extraDiv.innerHTML = extraHtml;
            winnerCard.insertBefore(extraDiv, winnerCard.firstChild);
        }
    }

    showView('debate');

  } catch (fetchErr) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${fetchErr.message}`);
  }
}

// ── Cloning Main Flow ──────────────────────────── ────────────────────────────
async function cloneVideo(eventOrData = null) {
  let isAuto = eventOrData && !(eventOrData instanceof Event);
  let autoData = isAuto ? eventOrData : null;

  // 1. Is the server online?
  const serverUp = await checkServer();
  if (!serverUp) {
    showError(
      '🔴 Sunucu Çevrimdışı',
      'YT Analiz Pro masaüstü uygulaması çalışmıyor.\n127.0.0.1:8000 adresinde FastAPI sunucusunu başlatın.'
    );
    return;
  }

  let tab = null;
  if (!autoData) {
      // 2. Is the active tab on YouTube?
      // BUG FIX: getActiveTab() can now return null (if there is no match in fullscreen mode).
      // Added null check — If the URL is missing, the analysis is STRICTLY rejected.
      tab = await getActiveTab();
      if (!tab) {
        showError(
          '🔗 Sekme Bulunamadı',
          'Analiz edilecek YouTube video sekmesi bulunamadı. Bir YouTube video sekmesini aktif yapıp tekrar deneyin.'
        );
        return;
      }
      if (!isYouTubeTab(tab)) {
        showError(
          '📺 YouTube Sayfası Gerekli',
          'Bu eklenti yalnızca YouTube video sayfalarında (/watch?v=...) çalışır.\nBir video açıp tekrar deneyin.'
        );
        return;
      }
  }

  // 3. Show loading
  showView('loading');
  elLoadingSub.textContent = 'Sayfa verisi okunuyor...';

  // 4. Inject content.js and pull metadata
  let videoData;
  if (autoData) {
      videoData = autoData;
  } else {
      try {
        const [result] = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: extractYouTubeData,
        });

        // executeScript return: { result: <function returned value> }
        const extracted = result?.result;

        // Catch if { error: "..." } comes from within the function
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
  }

  // 5. Show thumbnail
  if (videoData.thumbnail) {
    elThumbImg.src     = videoData.thumbnail;
    elThumbMeta.textContent = `${videoData.title || 'Video'} · ${videoData.channel || ''}`;
    elThumbWrap.style.display = 'block';
  }

  elLoadingSub.textContent = 'AI konsept üretiyor...';

  const { user_id } = await chrome.storage.local.get(['user_id']);

  // 6. POST to Backend — enriched with Predictive Intelligence fields
  const requestBody = enrichVideoData(videoData, user_id);

  try {
    const resp = await fetch(`${SERVER}/api/extension/clone_video`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body:    JSON.stringify(requestBody),
    });

    const data = await resp.json();

    if (!resp.ok || data.error) {
      // If an error message comes from the backend, show it directly. Otherwise print public HTTP status.
      const msg = data.error || `Bilinmeyen Hata (HTTP ${resp.status})`;
      showError('⚠️ İşlem Başarısız', msg);
      return;
    }

    // 7. Show result — 5-Level Tier System
    const videoViews    = requestBody.views || 0;
    const videoTier     = requestBody.tier  || (videoViews >= 5000 ? 'viral' : videoViews >= 500 ? 'potential' : 'dead');
    const videoVelocity = requestBody.velocity_per_day;
    const videoWindow   = requestBody.time_window;
    const videoPenetr   = requestBody.penetration_ratio;

    try {
      let rawText = data.result.trim();
      if (rawText.startsWith('```json')) rawText = rawText.replace(/^```json/, '').replace(/```$/, '').trim();
      else if (rawText.startsWith('```')) rawText = rawText.replace(/^```/, '').replace(/```$/, '').trim();

      const parsed = JSON.parse(rawText);
      let htmlCards = '';

      // ── 5 Tier Tier Banner ─────────────────────── ────────────────────────
      const TIER_CONFIG = {
        dead:       { emoji: '🔴', label: 'ÖLÇÜM',        color: '#ef4444', bg: 'rgba(239,68,68,0.12)',       sub: 'Acil müdahale önerileri aşağıda.' },
        potential:  { emoji: '🟡', label: 'POTANSİYEL VAR', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)',    sub: 'Bir hamle eksik — öneriler aşağıda.' },
        rising:     { emoji: '🚀', label: 'YÜKSELIYOR!',  color: '#f97316', bg: 'rgba(249,115,22,0.15)',      sub: 'Momentum yakalandı — şimdi harekete geç.' },
        viral:      { emoji: '🟢', label: 'VİRAL',        color: '#22c55e', bg: 'rgba(34,197,94,0.12)',       sub: 'Başarının anatomisi aşağıda.' },
        mega_viral: { emoji: '🔵', label: 'MEGA VİRAL',   color: '#38bdf8', bg: 'rgba(56,189,248,0.12)',      sub: 'Algoritma kırıcı — sistemi çıkart, kazayı kopyalama.' },
      };
      const tc = TIER_CONFIG[videoTier] || TIER_CONFIG['potential'];
      const viewsStr = videoViews > 0 ? videoViews.toLocaleString('tr-TR') + ' izlenme' : 'İzlenme verisi alınamadı';

      // Chips (show if available)
      let chips = '';
      if (videoVelocity !== null && videoVelocity !== undefined) {
        chips += `<span class="pi-chip">📈 ~${videoVelocity.toLocaleString('tr-TR')} izlenme/gün</span>`;
      }
      if (videoWindow) {
        const windowLabels = { fresh: '⏱ Yeni yayınlandı', burst: '⚡ Patlama penceresi', established: '📅 Algoritma yayılımı', evergreen: '🌿 Evergreen içerik' };
        chips += `<span class="pi-chip">${windowLabels[videoWindow] || videoWindow}</span>`;
      }
      if (videoPenetr !== null && videoPenetr !== undefined) {
        const penetLabel = videoPenetr >= 1 ? 'Yüksek' : videoPenetr >= 0.1 ? 'Orta' : 'Düşük';
        chips += `<span class="pi-chip">👥 Abone oranı: ${videoPenetr.toFixed(1)}x (${penetLabel})</span>`;
      }

      htmlCards += `<div class="tier-banner" style="border-color:${tc.color}; background:${tc.bg};">
        <div class="tier-banner__header">
          <span class="tier-banner__emoji">${tc.emoji}</span>
          <strong class="tier-banner__label" style="color:${tc.color};">${tc.label}</strong>
          <span class="tier-banner__views">${viewsStr}</span>
        </div>
        <div class="tier-banner__sub">${tc.sub}</div>
        ${chips ? `<div class="pi-chips">${chips}</div>` : ''}
      </div>`;

      let fikirler = Array.isArray(parsed) ? parsed : (parsed.fikirler || []);

      if (!Array.isArray(parsed) && parsed.viral_anatomi) {
        const isViral = videoTier === 'viral' || videoTier === 'mega_viral';
        const anatomyLabel = isViral ? '[VİRAL ANATOMİ: Bu Video Neden Patladı?]'
          : videoTier === 'rising' ? '[MOMENTUM ANALİZİ: Bu Video Neden Yükseliyor?]'
          : '[VİDEO ANALİZİ: Bu Video Neden Kitle Bulamıyor?]';
        const anatomyColor = isViral ? '#fbbf24' : videoTier === 'rising' ? '#f97316' : '#f87171';
        htmlCards += `<div style="margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1);"><strong style="color:${anatomyColor};">${anatomyLabel}</strong><br><span style="font-size:13px; color:#e2e8f0; line-height:1.6;">${parsed.viral_anatomi}</span></div>`;
      }

      if (fikirler.length > 0) {
        fikirler.forEach(idea => {
          htmlCards += `<div style="background: rgba(30,20,50,0.8); border: 1px solid #a855f7; border-radius: 12px; padding: 15px; margin-bottom: 15px;"><h4 style="color: white; margin-bottom: 8px; font-size: 1.1rem;">💡 ${idea.title || 'Başlık Yok'}</h4><div style="margin-bottom: 8px;"><span style="color: #f59e0b; font-size: 0.8rem; font-weight: bold;">KANCA (HOOK)</span><br><span style="color: #d8b4fe; font-size: 0.9rem;">"${idea.hook || 'Kanca Yok'}"</span></div><div><span style="color: #10b981; font-size: 0.8rem; font-weight: bold;">THUMBNAIL</span><br><span style="color: #94a3b8; font-size: 0.85rem;">${idea.thumbnail || 'Thumbnail önerisi yok'}</span></div></div>`;
        });
      }

      if (!Array.isArray(parsed) && parsed.nis_uyarisi && parsed.nis_uyarisi.trim() !== "") {
        htmlCards += `<div style="margin-top:15px; padding:10px; border-left:4px solid #ef4444; background:rgba(239,68,68,0.1); color:#fca5a5; font-size:13px;"><strong>${parsed.nis_uyarisi}</strong></div>`;
      }
      
      elResultBox.innerHTML = htmlCards || '<div style="color:white;">Fikir bulunamadı.</div>';
    } catch (e) {
      elResultBox.innerHTML = `<div style="color: #e2e8f0; font-size: 14px; white-space: pre-wrap;">${data.result}</div>`;
    }
    showView('result');

  } catch (fetchErr) {
    showError('🔌 Bağlantı Hatası', `Sunucuya ulaşılamadı: ${fetchErr.message}`);
  }
}

// ── YouTube Data Extractor (Works within the page) ────────────────────────────────
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

    // ── Views Pull ───────────────────────── ─────────────────────────
    // Try from meta tag first (most reliable)
    let views = 0;
    const metaViewCount = document.querySelector('meta[itemprop="interactionCount"]');
    if (metaViewCount && metaViewCount.content) {
      views = parseInt(metaViewCount.content.replace(/[^\d]/g, ''), 10) || 0;
    }
    // Fallback: parse view count from text
    // SECURE PARSER: Turkish (1,234,567), English (1,234,567) and
    // Correctly handles abbreviated (1.2M, 500B, 3K) formats.
    if (views === 0) {
      const viewEl = (
        document.querySelector('.view-count') ||
        document.querySelector('ytd-video-view-count-renderer .view-count') ||
        document.querySelector('#count .view-count-renderer span')
      );
      if (viewEl) {
        const raw = viewEl.textContent.trim().toLowerCase();
        // Decide the abbreviation formats first (1.2m, 1.2b, 3k, 500b etc.)
        const shortMatch = raw.match(/([\d][\d.,]*)\s*([mbk]|mn|bn|milyon|milyar|bin)/);
        if (shortMatch) {
          const num = parseFloat(shortMatch[1].replace(',', '.'));
          const suffix = shortMatch[2];
          if (suffix === 'k' || suffix === 'bin') views = Math.round(num * 1_000);
          else if (suffix === 'm' || suffix === 'mn' || suffix === 'milyon') views = Math.round(num * 1_000_000);
          else if (suffix === 'b' || suffix === 'bn' || suffix === 'milyar') views = Math.round(num * 1_000_000_000);
        } else {
          // Standard issue: delete all dot/comma/space thousands separator, then parse
          const digitsOnly = raw.replace(/[^\d]/g, '');
          views = parseInt(digitsOnly, 10) || 0;
        }
      }
    }

    // ── Release Date (for Velocity) ──────────────────── ─────────────────────
    let uploadDate = null;
    const uploadMeta = document.querySelector('meta[itemprop="uploadDate"]') ||
                       document.querySelector('meta[itemprop="datePublished"]');
    if (uploadMeta && uploadMeta.content) {
      uploadDate = uploadMeta.content; // In ISO 8601 format: "2025-05-20T14:00:00+00:00"
    }

    // ── Number of Subscribers (for Penetration Rate) ────────────────────────────────
    let subscriberCount = null;
    const subEl = (
      document.querySelector('yt-formatted-string#subscriber-count') ||
      document.querySelector('#owner-sub-count') ||
      document.querySelector('ytd-channel-name + div span')
    );
    if (subEl && subEl.textContent) {
      const subRaw = subEl.textContent.trim().toLowerCase();
      // Decode abbreviation formats: 1.2M, 500B, 3K, etc.
      const subMatch = subRaw.match(/([\d][.\d,]*)\s*([mbk]|mn|bn|milyon|milyar|bin)?/);
      if (subMatch) {
        const num = parseFloat(subMatch[1].replace(',', '.'));
        const suffix = subMatch[2] || '';
        const isEnglish = subRaw.includes('sub');

        if (suffix === 'k' || suffix === 'bin') subscriberCount = Math.round(num * 1_000);
        else if (suffix === 'm' || suffix === 'mn' || suffix === 'milyon') subscriberCount = Math.round(num * 1_000_000);
        else if (suffix === 'bn' || suffix === 'milyar') subscriberCount = Math.round(num * 1_000_000_000);
        else if (suffix === 'b') {
            // No channel on YouTube has 1 billion views, but 'B' means billion in English.
            // In Turkish, 'B' means thousand.
            subscriberCount = isEnglish ? Math.round(num * 1_000_000_000) : Math.round(num * 1_000);
        }
        else subscriberCount = Math.round(num) || null;
      }
    }

    // ── Comment Signals (for Quality Analysis) ───────────────────────────────
    // Collect raw text of first 5 comments — will be reported to AI for spiking protection
    let commentSignals = '';
    const commentEls = document.querySelectorAll('ytd-comment-thread-renderer #content-text');
    if (commentEls.length > 0) {
      const firstFive = Array.from(commentEls).slice(0, 5);
      commentSignals = firstFive.map(el => el.textContent.trim()).filter(Boolean).join(' ||| ');
    }

    return { url, videoId, title, channel, thumbnail, views, uploadDate, subscriberCount, commentSignals };
  } catch (err) {
    return { error: `Veri çekme hatası: ${err.message}` };
  }
}

// ── Predictive Intelligence: Velocity + Tier + Penetration Calculation ────────────
/**
 * Ham videoData objesini alır, analitik alanlarla zenginleştirir ve
 * backend'e gönderilmeye hazır requestBody döner.
 *
 * Hesaplanan alanlar:
 *   velocity_per_day  — günlük tahmini izlenme artışı
 *   time_window       — fresh / burst / established / evergreen
 *   tier              — dead / potential / rising / viral / mega_viral
 *   penetration_ratio — izlenme / abone (abone yoksa null)
 */
function enrichVideoData(videoData, userId) {
  const views          = videoData.views          || 0;
  const uploadDate     = videoData.uploadDate     || null;
  const subscriberCount = videoData.subscriberCount || null;
  const commentSignals = videoData.commentSignals || '';

  // ── Video Age + Velocity ──────────────────────── ─────────────────────────
  let videoAgeHours  = null;
  let velocityPerDay = null;
  let timeWindow     = null;

  if (uploadDate) {
    try {
      const publishedAt  = new Date(uploadDate).getTime();
      const nowMs        = Date.now();
      videoAgeHours      = Math.max((nowMs - publishedAt) / 3_600_000, 0.01); // division by zero protection
      velocityPerDay     = Math.round((views / videoAgeHours) * 24);

      if (videoAgeHours < 6)         timeWindow = 'fresh';
      else if (videoAgeHours < 48)   timeWindow = 'burst';
      else if (videoAgeHours < 168)  timeWindow = 'established'; // 7 gün
      else                           timeWindow = 'evergreen';
    } catch (e) {
      // Invalid date format — all velocity fields remain null
    }
  }

  // ── Spectrum Tier ─────────────────────── ───────────────────────
  let tier;
  if      (views >= 100_000) tier = 'mega_viral';
  else if (views >=   5_000) tier = 'viral';
  else if (views >=     500) tier = 'potential';
  else                       tier = 'dead';

  // Special Rule: Rising — potential + burst + speed > 1,000/day
  if (tier === 'potential' && timeWindow === 'burst' && velocityPerDay > 1_000) {
    tier = 'rising';
  }

  // ── Subscriber Penetration Rate ─────────────────────── ────────────────────────
  let penetrationRatio = null;
  if (subscriberCount && subscriberCount > 0 && views > 0) {
    penetrationRatio = parseFloat((views / subscriberCount).toFixed(3));
  }

  return {
    url:               videoData.url       || '',
    videoId:           videoData.videoId   || '',
    title:             videoData.title     || 'Başlık Yok',
    channel:           videoData.channel   || 'Bilinmeyen Kanal',
    thumbnail:         videoData.thumbnail || '',
    views,
    user_id:           userId || 0,
    // ── New Predictive Fields ──
    upload_date:       uploadDate,
    subscriber_count:  subscriberCount,
    velocity_per_day:  velocityPerDay,
    time_window:       timeWindow,
    tier,
    penetration_ratio: penetrationRatio,
    comment_signals:   commentSignals || null,
  };
}

// ── Prophet's Pick — Automatic Viral Recommendation System
/**
 * BabaClutch nişine (Oyun/Kaos) uygun, YouTube'da şu an patlamakta olan
 * 3 "Aykırı" videoyu çekip Matrix Vision Glow efektli kart grid'i olarak gösterir.
 * Tetikleyici: initSuggestion() içinde, video sayfasında DEĞİLSEK çağrılır.
 * 
 * Akış:
 *   1. POST /api/extension/prophet_picks → {success, picks:[...]}
 *   2. Dashboard'un üstüne 3'lü yatay kart grid'i enjekte et
 *   3. Her kartta: Başlık (2 satır), 🔥 Hız chip, ⚡ Klonla + ⚔️ Tartış butonları
 */
async function fetchProphetPicks(userId) {
  // Add again if already shown
  if (document.getElementById('prophet-picks-section')) return;

  try {
    const resp = await fetch(`${SERVER}/api/extension/prophet_picks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId || 0 })
    });

    if (!resp.ok) return;
    const data = await resp.json();
    if (!data.success || !data.picks || data.picks.length === 0) return;

    // ── Generate card HTML ─────────────────────────── ───────────────────────────
    let cardsHtml = '';
    data.picks.forEach((v, idx) => {
      // Remove videoId from URL (Required for Clone/Discuss)
      let videoId = '';
      if (v.url && v.url.includes('v=')) {
        videoId = v.url.split('v=')[1].split('&')[0];
      } else if (v.url) {
        videoId = v.url.split('/').pop().split('?')[0];
      }
      const thumbnail = videoId ? `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg` : '';
      const velocityStr = (v.velocity || 0).toLocaleString('tr-TR');

      cardsHtml += `
<div class="prophet-card matrix-glow" data-url="${v.url || ''}" data-videoid="${videoId}" data-title="${encodeURIComponent(v.title || '')}" data-channel="${encodeURIComponent(v.channel || '')}" data-thumbnail="${thumbnail}">
  <div class="prophet-card__rank">#${idx + 1}</div>
  <div class="prophet-card__title">${v.title || 'Başlık Yok'}</div>
  <div class="prophet-card__speed">
    <span class="prophet-speed-chip">🔥 ${velocityStr} izl/gün</span>
  </div>
  <div class="prophet-card__actions">
    <button class="prophet-btn prophet-btn--clone" data-idx="${idx}" title="Klonla">⚡ Klonla</button>
    <button class="prophet-btn prophet-btn--debate" data-idx="${idx}" title="Tartış">⚔️</button>
  </div>
</div>`;
    });

    // ── Section container ──────────────────────── ─────────────────────────
    const section = document.createElement('div');
    section.id = 'prophet-picks-section';
    section.innerHTML = `
      <div class="prophet-picks-header">
        <span class="prophet-picks-badge">🔮 PROPHET'S PICK</span>
        <span class="prophet-picks-sub">Şu an patlıyor</span>
        <button id="btn-prophet-close" class="prophet-close-btn" title="Kapat">✖</button>
      </div>
      <div class="prophet-picks-grid">${cardsHtml}</div>
    `;

    // Add just below the dashboard header (top position)
    const idleView = document.getElementById('view-idle');
    if (!idleView) return;
    const dashHeader = idleView.querySelector('.dashboard-header');
    if (dashHeader) {
      dashHeader.insertAdjacentElement('afterend', section);
    } else {
      idleView.insertBefore(section, idleView.firstChild);
    }

    // ── Close button ─────────────────────────── ───────────────────────────
    document.getElementById('btn-prophet-close').addEventListener('click', () => {
      section.remove();
    });

    // ── Card actions: set up videoData object and clone/start discussion ─
    const storedPicks = data.picks; // save for closure
    section.querySelectorAll('.prophet-btn--clone').forEach(btn => {
      btn.addEventListener('click', () => {
        const card = btn.closest('.prophet-card');
        const vd = _prophetCardToVideoData(card, storedPicks[parseInt(btn.dataset.idx)]);
        cloneVideo(vd);
      });
    });
    section.querySelectorAll('.prophet-btn--debate').forEach(btn => {
      btn.addEventListener('click', () => {
        const card = btn.closest('.prophet-card');
        const vd = _prophetCardToVideoData(card, storedPicks[parseInt(btn.dataset.idx)]);
        debateVideo(vd);
      });
    });

    // ── Opening the video in a new tab when you click on the cards ─────────────────────
    section.querySelectorAll('.prophet-card').forEach(card => {
      card.style.cursor = 'pointer'; // Tıklanabilir hissi ver
      card.addEventListener('click', (e) => {
        // If the Clone, Discuss or Close buttons are not clicked, open in a new tab
        if (e.target.closest('.prophet-btn') || e.target.closest('.prophet-close-btn')) return;
        
        const url = card.dataset.url;
        if (url) {
          chrome.tabs.create({ url: url, active: false }); // open in background
        }
      });
    });

  } catch (err) {
    console.error("[fetchProphetPicks] Hata:", err);
  }
}

/** Prophet kart elemanından cloneVideo/debateVideo için uyumlu videoData objesi üretir. */
function _prophetCardToVideoData(card, pick) {
  const videoId = card.dataset.videoid || '';
  return {
    url:       pick.url || card.dataset.url || '',
    videoId:   videoId,
    title:     decodeURIComponent(card.dataset.title || pick.title || 'Başlık Yok'),
    channel:   decodeURIComponent(card.dataset.channel || pick.channel || 'Bilinmeyen Kanal'),
    thumbnail: card.dataset.thumbnail || (videoId ? `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg` : ''),
    views:     pick.view_count || 0,
    velocity_per_day: pick.velocity || null,
  };
}

// ── Opening Intelligence (Contextual Auto-Suggestion) ────────────────────────────────
async function initSuggestion() {
  const tab = await getActiveTab();
  if (!tab || !tab.url) return;

  if (isYouTubeTab(tab)) {
    // --- CRITICAL ADD: Clear the screen and give focus to the video ---
    const recentTitle = document.querySelector('.recent-analyses-title') || document.querySelector('.recent-analyses .recent-title');
    const recentList = document.querySelector('.recent-list');
    if (recentTitle) recentTitle.style.display = 'none'; // "Son Analizlerim" yazısını gizle
    if (recentList) recentList.style.maxHeight = '100px'; // Listeyi daralt veya tamamen gizle
    // -------------------------------------------------------

    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractYouTubeData,
      });
      const videoData = result?.result;
      if (videoData && !videoData.error && videoData.videoId) {
        const { dismissed_video_id } = await chrome.storage.local.get(['dismissed_video_id']);
        if (dismissed_video_id !== videoData.videoId) {
          showSuggestionCard(videoData, "Bu videoyu analiz etmeye hazır mısın?");
        }
      }
    } catch (e) {}
    return;
  }

  if (isYouTubeChannelTab(tab)) {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const titleEl = document.querySelector('meta[property="og:title"]');
          return titleEl ? titleEl.content : null;
        }
      });
      const channelName = result?.result;
      if (channelName) {
        const { user_id } = await chrome.storage.local.get(['user_id']);
        const resp = await fetch(`${SERVER}/api/extension/rabbit_hole`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: channelName, user_id: user_id || 0 })
        });
        const data = await resp.json();
        if (resp.ok && data.success && data.outliers && data.outliers.length > 0) {
           const best = data.outliers[0];
           // Extract videoId from url
           let videoId = "";
           if (best.url.includes("v=")) {
               videoId = best.url.split("v=")[1].split("&")[0];
           } else {
               videoId = best.url.split("/").pop().split("?")[0];
           }
           if (videoId) {
               const videoData = {
                   url: best.url,
                   videoId: videoId,
                   title: best.title,
                   channel: best.channel,
                   thumbnail: `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`
               };
               const { dismissed_video_id } = await chrome.storage.local.get(['dismissed_video_id']);
               if (dismissed_video_id !== videoId) {
                   showSuggestionCard(videoData, "Kanalın en hızlı yükselen videosunu klonla!");
               }
           }
        }
      }
    } catch(e) {}
    return;
  }

  // ── Prophet's Pick: We are not on the video page or the channel page ──────
  // (Show Prophet Picks on home page, search results, trending, etc.)
  const { user_id: prophetUserId } = await chrome.storage.local.get(['user_id']);
  // Run asynchronously in background — does not block UI, loads in 2 seconds
  fetchProphetPicks(prophetUserId).catch(() => {});
}

function showSuggestionCard(videoData, subtitle) {
  const idleView = document.getElementById('view-idle');
  if (!idleView || document.getElementById('smart-suggestion-card')) return;

  // --- CRITICAL ADD: Hide duplicate buttons at the bottom ---
  const cloneBtnGroup = document.getElementById('clone-btn-group');
  const btnAnalyze = document.getElementById('btn-analyze');
  if (cloneBtnGroup) cloneBtnGroup.style.display = 'none';
  if (btnAnalyze) btnAnalyze.style.display = 'none';
  // --------------------------------------------------------

  const card = document.createElement('div');
  card.id = 'smart-suggestion-card';
  card.className = 'smart-suggestion-card';
  card.innerHTML = `
    <div class="suggestion-header">
      <span class="suggestion-badge">🔥 AKILLI SEÇİM</span>
      <button id="btn-dismiss-suggestion" class="suggestion-dismiss" title="Kapat">✖</button>
    </div>
    <h4 class="suggestion-title">${videoData.title}</h4>
    <p class="suggestion-subtitle">${subtitle}</p>
    <div class="suggestion-actions" style="display:flex; gap:8px;">
      <button id="btn-suggest-clone" class="btn btn--primary suggestion-btn-clone" style="flex:1;">
        ⚡ Klonla
      </button>
      <button id="btn-suggest-debate" class="btn btn--debate suggestion-btn-debate" style="flex:1;">
        ⚔️ Tartış
      </button>
    </div>
  `;

  const dashboardHeader = idleView.querySelector('.dashboard-header');
  if (dashboardHeader) {
    dashboardHeader.insertAdjacentElement('afterend', card);
  } else {
    idleView.insertBefore(card, idleView.firstChild);
  }

  document.getElementById('btn-dismiss-suggestion').addEventListener('click', async () => {
    card.remove();
    chrome.storage.local.set({ dismissed_video_id: videoData.videoId });

    // --- CRITICAL IMPROVEMENT: Bring back buttons at the bottom according to page type ---
    const tab = await getActiveTab();
    const cloneBtnGroup = document.getElementById('clone-btn-group');
    const btnAnalyze = document.getElementById('btn-analyze');
    if (isYouTubeChannelTab(tab)) {
      if (cloneBtnGroup) cloneBtnGroup.style.display = 'none';
      if (btnAnalyze) btnAnalyze.style.display = 'block';
    } else {
      if (cloneBtnGroup) cloneBtnGroup.style.display = 'flex';
      if (btnAnalyze) btnAnalyze.style.display = 'none';
    }
  });

  document.getElementById('btn-suggest-clone').addEventListener('click', () => {
    cloneVideo(videoData);
  });
  const btnSuggestDebate = document.getElementById('btn-suggest-debate');
  if (btnSuggestDebate) {
      btnSuggestDebate.addEventListener('click', () => {
        debateVideo(videoData);
      });
  }
}

// ── Event Listeners ───────────────────────────── ──────────────────────────────
elBtnLogin.addEventListener('click', handleLogin);
elBtnLogout.addEventListener('click', handleLogout);
elBtnClone.addEventListener('click', cloneVideo);
if (elBtnDebate) elBtnDebate.addEventListener('click', debateVideo);
elBtnAnalyze.addEventListener('click', analyzeChannel);
elBtnRabbit.addEventListener('click', findRabbitHole);

const elBtnInfo = $('btn-info');
const elBtnInfoClose = $('btn-info-close');
if (elBtnInfo) elBtnInfo.addEventListener('click', async () => {
  let tab = await getActiveTab();
  let infoHtml = '';

  if (isYouTubeTab(tab)) {
    infoHtml = `
      <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 10px; margin-bottom: 15px; border-radius: 4px;">
        <strong style="color: #34d399; font-size: 14px;">Şu an Strateji Modundasın.</strong>
        <p style="margin-top: 5px; color: #cbd5e1; font-size: 12px;">Video sayfasındasın. <strong>Akıllı Seçim</strong> devrededir. (Odaklanman için Prophet's Pick gizlendi).</p>
        <ul style="margin-top: 5px; padding-left: 15px; color: #94a3b8; font-size: 12px; list-style-type: disc;">
          <li><strong>Akıllı Seçim:</strong> Bu videoyu anında klonla veya tartıştır.</li>
          <li><strong>Viral Anatomi:</strong> Videonun neden patladığını (veya neden çöktüğünü) anla.</li>
        </ul>
      </div>
    `;
  } else if (isYouTubeChannelTab(tab)) {
    infoHtml = `
      <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 10px; margin-bottom: 15px; border-radius: 4px;">
        <strong style="color: #fbbf24; font-size: 14px;">Şu an İstihbarat Modundasın.</strong>
        <p style="margin-top: 5px; color: #cbd5e1; font-size: 12px;">Kanal sayfasındasın.</p>
        <ul style="margin-top: 5px; padding-left: 15px; color: #94a3b8; font-size: 12px; list-style-type: disc;">
          <li><strong>Kanal Savaşları:</strong> Rakibini tarat, zayıf noktalarını bul.</li>
          <li><strong>Kaos Metriği:</strong> Rakibin öfke ve tempo analizini gör.</li>
        </ul>
      </div>
    `;
  } else {
    infoHtml = `
      <div style="background: rgba(168, 85, 247, 0.1); border-left: 4px solid #a855f7; padding: 10px; margin-bottom: 15px; border-radius: 4px;">
        <strong style="color: #d8b4fe; font-size: 14px;">Şu an Keşif Modundasın.</strong>
        <p style="margin-top: 5px; color: #cbd5e1; font-size: 12px;">YouTube Ana Sayfası veya Arama sonuçlarındasın.</p>
        <ul style="margin-top: 5px; padding-left: 15px; color: #94a3b8; font-size: 12px; list-style-type: disc;">
          <li><strong>Matrix Vision:</strong> Trend videolar neon yeşil parlar.</li>
          <li><strong>Kahinin Seçimi:</strong> Senin için seçtiğim 3 viral fırsatı gör.</li>
        </ul>
      </div>
    `;
  }

  const dynamicContent = document.getElementById('dynamic-info-content');
  if (dynamicContent) {
    dynamicContent.innerHTML = infoHtml;
  }
  showView('info');
});
if (elBtnInfoClose) elBtnInfoClose.addEventListener('click', () => showView('idle'));

// Debate reset button
const elBtnDebateReset = $('btn-debate-reset');
if (elBtnDebateReset) {
  elBtnDebateReset.addEventListener('click', () => {
    showView('idle');
  });
}

const elBtnFullscreen = $('btn-fullscreen');
if (elBtnFullscreen) {
  elBtnFullscreen.addEventListener('click', async () => {
    let tab = await getActiveTab();
    let ytUrl = tab ? tab.url : '';
    chrome.tabs.create({ url: chrome.runtime.getURL('popup.html') + '?url=' + encodeURIComponent(ytUrl) });
  });
}

elBtnReset.addEventListener('click', () => {
  elThumbWrap.style.display = 'none';
  elThumbImg.src = '';
  elResultBox.textContent = '';
  showView('idle');
});

elBtnRetry.addEventListener('click', () => showView('idle'));

// ── Init ─────────────────────────────────── ───────────────────────────────────
(async () => {
  elBtnClone.disabled = true; // disabled until server control is finished
  if (elBtnDebate) elBtnDebate.disabled = true;
  await checkServer();
  
  let tab = await getActiveTab();
  const btnClone   = document.getElementById('btn-clone');
  const btnDebate  = document.getElementById('btn-debate');
  const btnGroup   = document.getElementById('clone-btn-group');
  const btnAnalyze = document.getElementById('btn-analyze');
  
  if (isYouTubeChannelTab(tab)) {
      if (btnGroup)   btnGroup.style.display   = 'none';
      if (btnAnalyze) btnAnalyze.style.display = 'block';
  } else {
      if (btnGroup)   btnGroup.style.display   = 'flex';
      if (btnAnalyze) btnAnalyze.style.display = 'none';
  }
  
  chrome.storage.local.get(['user_id', 'username'], (res) => {
    if (res.user_id && res.username) {
      showDashboard(res.username, res.user_id);
    } else {
      showView('login');
    }
  });

  // Start smart suggestion in the background
  initSuggestion();
})();

// ── YouTube SPA Navigation Listener ──────────────────── ────────────────────
// SPA FIX: Listen for YT_URL_CHANGED message from content.js.
// Reset popup when YouTube changes video via AJAX.
// Without this, if the user presses "Clone", it may pull the data of the old video.
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'YT_URL_CHANGED') {
    const prophetPicks = document.getElementById('prophet-picks-section');
    if (prophetPicks) prophetPicks.remove();

    const activeView = Object.entries(views).find(([, el]) => el.classList.contains('active'));
    const currentView = activeView ? activeView[0] : 'idle';

    // If we are on the results or loading screen, reset
    if (currentView === 'result' || currentView === 'loading') {
      elThumbWrap.style.display = 'none';
      elThumbImg.src = '';
      elResultBox.textContent = '';
      showView('idle');
    }

    // BUG FIX: Debate control has been moved into the block where currentView is valid.
    // Previously used outside block → strict-mode ReferenceError
    if (currentView === 'debate') {
      showView('idle');
    }

    // Show Clone + Discuss group for new video
    const btnGroup   = document.getElementById('clone-btn-group');
    const btnAnalyze = document.getElementById('btn-analyze');
    if (btnGroup)   btnGroup.style.display   = 'flex';
    if (btnAnalyze) btnAnalyze.style.display = 'none';
  }
});
