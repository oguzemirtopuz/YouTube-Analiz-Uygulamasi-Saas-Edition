# -*- coding: utf-8 -*-
import os
import re

with open('chrome_extension/popup.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = {
    '<html lang="tr">': '<html lang="en">',
    'YT Analiz Pro': 'YT Analyzer Pro',
    'Viral Klonlama Motoru': 'Viral Cloning Engine',
    'Nasıl Çalışır?': 'How It Works?',
    'Tam Ekran Aç': 'Open Fullscreen',
    'Sunucu durumu kontrol ediliyor...': 'Checking server status...',
    'Sunucu Bekleniyor...': 'Waiting for Server...',
    'Sunucu Bağlantısı Kurulamadı': 'Could Not Connect to Server',
    'Uygulamanın açık olduğundan emin olun': 'Make sure the application is open',
    'Video Analizini Başlat': 'Start Video Analysis',
    'Bağlantı Bekleniyor': 'Waiting for Connection',
    'Lütfen uygulamayı başlatın': 'Please start the application',
    'Giriş Yap': 'Login',
    'Kayıt Ol': 'Register',
    'E-posta': 'Email',
    'Şifre': 'Password',
    'Hesabınız yok mu?': "Don't have an account?",
    'Hesabınız var mı?': 'Already have an account?',
    'Tekrar Dene': 'Try Again',
    'Çıkış': 'Logout'
}

for k, v in replacements.items():
    text = text.replace(k, v)

with open('chrome_extension/popup.html', 'w', encoding='utf-8') as f:
    f.write(text)
