import os
import sys

# Proje dizinindeki modülleri görebilmek için yola ekliyoruz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import otomatik_tmo_kaziyici_ve_rag_guncelle

print("TMO Fiyatları güncelleniyor, lütfen bekleyin...")
sonuc = otomatik_tmo_kaziyici_ve_rag_guncelle()
print("\nGüncelleme Sonucu:")
print(sonuc)
