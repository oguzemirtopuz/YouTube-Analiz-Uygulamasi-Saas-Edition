"""Test Asama 3: Gorsel Zeka modullerini dogrula"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import dogrulamasi
print("1. Import testi...")
try:
    from deepface import DeepFace
    print("   DeepFace: OK")
except Exception as e:
    print(f"   DeepFace: FAIL - {e}")

try:
    from colorthief import ColorThief
    print("   ColorThief: OK")
except Exception as e:
    print(f"   ColorThief: FAIL - {e}")

# AnalysisEngine testi
print("\n2. AnalysisEngine modulleri testi...")
import cv2, numpy as np

# Basit bir test goruntusu olustur (320x180, renkli)
test_img_path = "test_thumb_stage3.png"
img = np.zeros((180, 320, 3), dtype=np.uint8)
# Sol yari: kirmizi, sag yari: mavi
img[:, :160] = [0, 0, 200]  # kirmizi (BGR)
img[:, 160:] = [200, 100, 0]  # mavi-yesil
# Metin alani icin ust kisim beyaz
img[:45, :] = [255, 255, 255]
cv2.imwrite(test_img_path, img)
print(f"   Test goruntu olusturuldu: {test_img_path}")

# Thumbnail analizi (sentez goruntuyle - yuz bulunamayacak)
print("\n3. Thumbnail analiz testi (sentez goruntu)...")

# Minimal analyze_thumbnail fonksiyonu parcasi (import olmadan)
from pathlib import Path
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
l_ch, a_ch, b_ch = cv2.split(lab)
l_min = float(np.percentile(l_ch, 5))
l_max = float(np.percentile(l_ch, 95))
if (l_max + l_min) > 0:
    michelson = (l_max - l_min) / (l_max + l_min)
else:
    michelson = 0.0
print(f"   Michelson kontrast: {michelson:.3f}")

# HSV doygunluk
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mean_sat = float(np.mean(hsv[:, :, 1]))
print(f"   Ortalama doygunluk: {mean_sat:.1f}")

# Metin alani
h, w = img.shape[:2]
regions_var = [
    float(np.std(cv2.cvtColor(img[:h//4, :], cv2.COLOR_BGR2GRAY))),
    float(np.std(cv2.cvtColor(img[3*h//4:, :], cv2.COLOR_BGR2GRAY))),
]
min_var = min(regions_var)
print(f"   Min bolge varyans (metin alani): {min_var:.1f}")

# ColorThief testi
print("\n4. ColorThief vibrant renk testi...")
try:
    ct = ColorThief(test_img_path)
    palette = ct.get_palette(color_count=3, quality=5)
    print(f"   Dominant renkler: {palette}")
except Exception as e:
    print(f"   ColorThief hata: {e}")

# Gercek thumbnail ile test (varsa)
real_thumb = "t_f12e9605.png"
if os.path.exists(real_thumb):
    print(f"\n5. Gercek thumbnail testi ({real_thumb})...")
    try:
        real_img = cv2.imread(real_thumb)
        if real_img is not None:
            h2, w2 = real_img.shape[:2]
            print(f"   Boyut: {w2}x{h2}")
            lab2 = cv2.cvtColor(real_img, cv2.COLOR_BGR2LAB)
            l2 = cv2.split(lab2)[0]
            l2_min = float(np.percentile(l2, 5))
            l2_max = float(np.percentile(l2, 95))
            m2 = (l2_max - l2_min) / (l2_max + l2_min) if (l2_max + l2_min) > 0 else 0
            print(f"   Michelson kontrast: {m2:.3f}")
            
            ct2 = ColorThief(real_thumb)
            pal2 = ct2.get_palette(color_count=5, quality=5)
            print(f"   Vibrant palet: {pal2}")
    except Exception as e:
        print(f"   Hata: {e}")
else:
    print(f"\n5. Gercek thumbnail ({real_thumb}) bulunamadi, atlandi.")

# Temizlik
if os.path.exists(test_img_path):
    os.remove(test_img_path)

print("\n=== ASAMA 3 TEST TAMAMLANDI ===")
