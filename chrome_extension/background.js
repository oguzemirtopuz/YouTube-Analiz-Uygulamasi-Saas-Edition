/**
 * background.js — YT Analiz Pro | Viral Klonlama Motoru
 * Manifest V3 Service Worker
 *
 * Şu an yalnızca kurulum loglaması yapar.
 * İleride bildirim (Notifications API) veya alarm entegrasyonu buraya eklenir.
 */

chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === 'install') {
    console.log('[YT Analiz Pro] Eklenti kuruldu. Viral Klonlama Motoru hazır.');
  }
});
