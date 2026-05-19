# 🎬 YouTube Analiz Pro (SaaS Edition) 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75C2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://deepmind.google/technologies/gemini/)

YouTube Analiz Pro (SaaS Edition), içerik üreticilerinin video performanslarını, SEO altyapılarını ve görsel içeriklerini en üst düzeye çıkarmak için tasarlanmış **üretim kalitesinde (production-grade)**, yapay zeka destekli bir analiz ve optimizasyon platformudur.

Tamamen **asenkron veritabanı mimarisi**, **donanım tabanlı GPU hızlandırması** ve **gelişmiş bilgisayarlı görü (computer vision)** teknolojileri üzerine kurulu olan bu sistem; amatör içerik üreticilerini profesyonel kanallara dönüştürmeyi hedefler.

---

## ✨ Öne Çıkan Gelişmiş Özellikler

### 🤖 1. AI Koç & Akıllı Tavsiye Motoru
*   **Groq (Llama-3.3-70B) Entegrasyonu:** Kanala özel hedef kitle, kanal kategorisi ve performans puanlarını harmanlayarak kişiselleştirilmiş, yapıcı ve doğrudan aksiyon alınabilir geri bildirimler sunar.
*   **Anti-Generic Kural Sistemi:** Yapay zeka asla *"İlk 10 saniyede ilgi çekici ol"* gibi basmakalıp tavsiyeler vermez. **"Nasıl"** sorusunun cevabını somut senaryo ve süre kodlu (timestamp) düzenleme örnekleriyle sunar (*Örn: Uygulama Örneği: 00:02'de ekrana shake efektiyle beraber 'Sırrı Çözüldü!' yazısını ekleyin.*).
*   **Zeka Koruması:** Algoritmik olarak doğru girilmiş etiketleri asla "alakasız" olarak nitelemez, kanalı ve emeği korur.

### 👁️ 2. Bilgisayarlı Görü (Computer Vision) & Thumbnail Zekası
*   **Gemini 2.0 Flash Vision Entegrasyonu:** Thumbnail (küçük resim) tasarımlarınızı yapay zekanın gözünden analiz eder. 
*   **Duygu ve Kontrast Analizi:** Tasarımdaki yüz ifadelerini (`deepface` ile), renk paletini (`colorthief` ile), kontrastı, metin okunabilirliğini ve tıklama oranını (CTR) artıracak görsel çekiciliği puanlar.
*   **Video Akış ve Tempo Analizi:** Video içi sahneleri, kare geçişlerini ve tempo piki noktalarını saptayarak izleyicinin nerede sıkılabileceğini haritalandırır.

### 🎙️ 3. Multimedya Ses & Tempo Analiz Modülü
*   **Librosa & Soundfile Entegrasyonu:** Ses dosyalarındaki ses dalgalarını analiz eder.
*   **Heyecan ve Tempo Katsayısı:** Videodaki konuşma hızını, ses yükselmelerini (peaks) ve heyecan dalgalarını belirleyerek tempo grafiğini çıkarır. Bu sayede izleyicinin videoda kalma süresi (retention) optimize edilir.

### 📈 4. Asenkron & Yüksek Performanslı Altyapı
*   **aiosqlite & WAL Mode:** SQLite veritabanı tamamen asenkron çalışır ve `Write-Ahead Logging (WAL)` modu etkindir. Bu, aynı anda yüzlerce analiz yapılsa bile arayüzde veya sunucuda donma/kilitlenme yaşanmasını engeller.
*   **Performans Otopilotu:** Başlangıçta sistemdeki işlemci çekirdeği sayısını, RAM miktarını ve CUDA çekirdeklerini otomatik tespit ederek iş parçacığı (threading) ve donanım otopilotunu devreye sokar.
*   **GPU Donanım Hızlandırma:** FFmpeg motoru; NVIDIA (`h264_nvenc`), AMD (`h264_amf`) ve Intel (`h264_qsv`) ekran kartlarını tarayarak video işlemlerini ekran kartı gücüyle jet hızında tamamlar.

### 🌐 5. Küresel SaaS Standartları
*   **Çok Dilli Altyapı (TR / EN / ES):** Excel tabanlı dinamik yerelleştirme (`translations.xlsx`) sayesinde tek tıkla tüm arayüz, PDF raporları ve AI analiz dili Türkçe, İngilizce veya İspanyolca olarak değiştirilebilir.
*   **Gelişmiş PDF Rapor Motoru:** `ReportLab` kütüphanesi kullanılarak profesyonel, şık ve endüstri standardı raporlar üretilir. Raporda kullanılan fontlar ve Türkçe karakter desteği (`arial.ttf` güvenli yükleme) kusursuzdur.
*   **SMTP Mail Dağıtıcısı:** Analiz sonuçlarını ve PDF raporlarını tek tıkla şık bir şablon eşliğinde doğrudan kullanıcının e-posta adresine gönderir.
*   **SaaS Güvenlik Katmanı:** PBKDF2 şifreleme ve güvenli oturum token yönetimi ile kullanıcı hesapları ve veriler en üst düzeyde korunur.

---

## 🔒 Sıfır Bilgi & Gizlilik Politikası (Privacy-First)

Bu uygulamanın en büyük avantajı, **verilerinizin ve API anahtarlarınızın tamamen güvende olmasıdır:**
1.  **Yerel Depolama (Local DB):** Tüm analizleriniz, geçmiş kayıtlarınız ve API anahtarlarınız uzak bir SaaS sunucusuna değil, bilgisayarınızda yer alan `channels.db` yerel SQLite veritabanında şifreli olarak saklanır.
2.  **Açık Kaynak Güvenliği:** API anahtarlarınız asla harici bir sunucuyla paylaşılmaz, sadece doğrudan resmi Google Gemini ve Groq API uç noktalarına (secure HTTPS üzerinden) gönderilir.
3.  `.gitignore` koruması sayesinde veritabanınız, API anahtarlarınız veya yerel log dosyalarınız asla GitHub repolarına kazara yüklenmez.

---

## 📋 Gereksinimler

Uygulamayı çalıştırmak için sisteminizde şunların kurulu olması gerekir:

*   **Python 3.10 veya üzeri:** [Python İndir](https://www.python.org/downloads/) (Kurulumda *"Add Python to PATH"* seçeneğini işaretlemeyi unutmayın!)
*   **FFmpeg (Video Analizi İçin):** Bilgisayarınızın PATH ortam değişkenine eklenmiş olmalıdır.
    *   *Windows için Kolay Kurulum:* PowerShell'i yönetici olarak açıp `winget install Gyan.FFmpeg` yazarak saniyeler içinde kurabilirsiniz.

---

## 🚀 A'dan Z'ye Kurulum ve Çalıştırma

### 1. Depoyu Klonlayın veya İndirin
```bash
git clone https://github.com/OguzEmir177/YouTube-Analiz-Uygulamas-Saas-Edition-En-G-ncel-.git
cd YouTube-Analiz-Uygulamas-Saas-Edition-En-G-ncel-
```

### 2. Gerekli Python Kütüphanelerini Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Uygulamayı Başlatın
Masaüstü deneyimi ve kullanım kolaylığı için **3 farklı başlatma seçeneği** sunulmuştur:

*   **Seçenek A (PowerShell - ÖNERİLEN):** `Start-YouTubeAnalyzer.ps1` scripti. En güvenli, kararlı ve terminalde arka planda sessizce çalışan yöntemdir.
*   **Seçenek B (BAT):** Klasördeki `BASLAT.bat` dosyasına çift tıklayarak hızlıca çalıştırabilirsiniz.
*   **Seçenek C (VBScript):** `YouTube Analiz Pro.vbs` dosyası. Hiçbir siyah terminal ekranı açmadan uygulamayı tamamen arka planda görünmez olarak başlatır.

> 💡 **Kısayol Sihirbazı:** Masaüstünüzde bu launcher'ların otomatik kısayollarını oluşturmak için klasördeki `KISAYOL_OLUSTUR.bat` dosyasına çift tıklamanız yeterlidir.

### 4. Arayüzü Kullanma
Uygulama başladığında karşınıza şık, modern ve yerleşik bir **PyWebView masaüstü penceresi** çıkacaktır. Tarayıcıdan erişmek isterseniz:
*   **Adres:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🛠️ İlk Yapılandırma & Kullanım Rehberi

1.  **Kullanıcı Oluşturun:** Arayüze girdikten sonra saniyeler içinde şifreli yerel hesabınızı oluşturun ve giriş yapın.
2.  **API Anahtarlarınızı Girin:** Ayarlar panelinden ücretsiz olarak alabileceğiniz **Groq API Key** ve **Google Gemini API Key** anahtarlarınızı girin. Bu anahtarlar yerel SQLite dosyanıza kaydedilir.
3.  **Kanal Tanımlayın:** *"Kanal Ekle"* kısmından kanalınızın türünü (Örn: Gaming, Eğitim, Vlog) ve hedef kitlesini girin.
4.  **Analizi Başlatın:** Videonuzu sisteme yükleyin (veya YouTube linkini/metadata bilgilerini girin). AI Koç saniyeler içinde size A'dan Z'ye tüm raporu çıkaracak, isterseniz raporu tek tıkla e-postanıza gönderecektir!

---

## 👤 Geliştirici Hakkında

Bu proje, **Oğuz Emir Topuz** tarafından geliştirilmiştir.

*   **Yaş:** 14
*   **İlgi Alanları & Tutkular:** Futbol tutkunu ve aynı zamanda ileri düzey bir yazılım geliştiricisi.
*   **Neler Yapıyor?** SaaS uygulamaları, modern ve şık web siteleri ve 3D oyunlar üzerinde çalışıyor.
*   **İletişim & Portfolyo:** [GitHub Profilim](https://github.com/OguzEmir177)

---

⭐ Bu projeyi beğendiyseniz yıldız (star) vermeyi unutmayın! Geliştirilmeye ve yeni SaaS özellikleri eklenmeye devam edecektir.
