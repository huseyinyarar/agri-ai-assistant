import sys
import logging
from tools import otomatik_tmo_kaziyici_ve_rag_guncelle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    print("Test: TMO Scraping ve RAG Güncelleme Fonksiyonu Çalıştırılıyor...")
    try:
        sonuc = otomatik_tmo_kaziyici_ve_rag_guncelle()
        print("Sonuç:")
        print(sonuc)
    except Exception as e:
        print(f"Hata oluştu: {e}")
