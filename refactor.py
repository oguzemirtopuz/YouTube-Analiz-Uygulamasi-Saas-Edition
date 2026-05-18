import re
import codecs

with codecs.open('server.pyw', 'r', 'utf-8') as f:
    content = f.read()

# Replace empty file check in analyze_video
old_analyze = '''    try:
        # --- NON-BLOCKING: Dosya kopyalama (aðýr I/O) ---'''
new_analyze = '''    try:
        if video_file.size == 0:
            raise HTTPException(status_code=400, detail="Yüklenen video dosyasý boþ.")

        # --- NON-BLOCKING: Dosya kopyalama (aðýr I/O) ---'''
content = content.replace(old_analyze, new_analyze)

# Replace haarcascade
old_haar = '''            else:
                # Fallback: basit OpenCV yüz tespiti
                try:
                    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    face_cascade = cv2.CascadeClassifier(cascade_path)
                    gray_face = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces_rect = face_cascade.detectMultiScale(
                        gray_face, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                    if len(faces_rect) > 0:
                        result["face_detected"] = True
                        result["face_count"] = len(faces_rect)
                        face_bonus = 1.0
                        summary_parts.append("Thumbnail'de yüz tespit edildi")
                except:
                    pass'''
new_haar = '''            else:
                pass'''
content = content.replace(old_haar, new_haar)

# Replace prints with app_logger
content = content.replace('print(f"translations.xlsx okunamadý', 'app_logger.error(f"translations.xlsx okunamadý')
content = content.replace('print(f"? GPU Codec bulundu', 'app_logger.info(f"? GPU Codec bulundu')
content = content.replace('print("?? GPU codec bulunamadý', 'app_logger.info("?? GPU codec bulunamadý')
content = content.replace('print(f"GEMINI ISTEK GÖNDERILIYOR...")', '')
content = content.replace('print(f"GEMINI YANIT: status={resp.status_code}")', '')
content = content.replace('print(f"GEMINI API HATA: {resp.status_code} - {resp.text}")', 'app_logger.error(f"GEMINI API HATA: {resp.status_code} - {resp.text}")')
content = content.replace('print(f"GEMINI HATA:', 'app_logger.error(f"GEMINI HATA:')
content = content.replace('print(f"Mail gönderilemedi DETAY:', 'app_logger.error(f"Mail gönderilemedi DETAY:')
content = content.replace('print(f"? AKTARMA BAÞARILI:', 'app_logger.info(f"? AKTARMA BAÞARILI:')
content = content.replace('print(f"? AKTARMA HATASI:', 'app_logger.error(f"? AKTARMA HATASI:')
content = content.replace('print(f"DeepFace analiz hatasý:', 'app_logger.warning(f"DeepFace analiz hatasý:')
content = content.replace('print(f"Thumbnail analiz hatasý:', 'app_logger.warning(f"Thumbnail analiz hatasý:')
content = content.replace('print(f"MAIL GÖNDERÝLÝYOR:', 'app_logger.info(f"MAIL GÖNDERÝLÝYOR:')
content = content.replace('print(f"MAIL SONUCU:', 'app_logger.info(f"MAIL SONUCU:')
content = content.replace('print(f"FFmpeg Hatasý Detayý:', 'app_logger.error(f"FFmpeg Hatasý Detayý:')
content = content.replace('print(f"FILE_CONTEXT PREVIEW: {file_context[:500]}")', '')
content = content.replace('#print(f"GEMINI KEY VAR MI', '')

with codecs.open('server.pyw', 'w', 'utf-8') as f:
    f.write(content)
print("Refactoring done.")
