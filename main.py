"""
============================================================
agri-ai-assistant v3.0 - Komut Satırı Çalıştırma Modülü (main.py)
============================================================
Kullanıcıdan şehir ve soru alır, 4 ajanı sırayla çalıştırır
ve kısa "Ziraat Mühendisi Reçetesi" çıktısını ekrana basar.

v3.0: PDF üretimi YOK — çıktı doğrudan ekranda görünür.
============================================================
"""

import os
import time
import datetime
from dotenv import load_dotenv
from crewai import Crew, Process
from tasks import gorevleri_olustur
from tools import rag_veritabanini_hazirla, sabah_cache_guncelle
from agents import sehir_tespit_et, DEFAULT_CITY


def ana_dongu():
    load_dotenv()

    print()
    print("=" * 62)
    print("  🌾 agri-ai-assistant v3.0 — Otonom Tarım Asistanı")
    print("=" * 62)
    print(f"  Profil Şehri : {DEFAULT_CITY}")
    print(f"  Başlangıç    : {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 62)

    # ── RAG Veritabanı Kontrolü ───────────────────────────────
    pdf_yolu = "yerel_rehber.pdf"
    db_yolu  = "./chroma_db"

    print("\n[SİSTEM] RAG Vektör Veritabanı kontrol ediliyor...")
    if os.path.exists(pdf_yolu) and not os.path.exists(db_yolu):
        print("[SİSTEM] Yeni doküman bulundu, RAG veritabanı indeksleniyor...")
        rag_veritabanini_hazirla(pdf_yolu)
    elif os.path.exists(db_yolu):
        print("[SİSTEM] RAG veritabanı hazır. ✅")
    else:
        print("[UYARI]  'yerel_rehber.pdf' bulunamadı → RAG kapalı, genel bilgi kullanılacak.")

    # ── Profil Şehri Önbellek Kontrolü ───────────────────────
    cache_dir = "./cache"
    bugun = datetime.date.today().isoformat()
    cache_files = []
    if os.path.exists(cache_dir):
        import glob
        cache_files = glob.glob(f"{cache_dir}/{DEFAULT_CITY.lower()}*_{bugun}.json")

    if cache_files:
        print(f"[CACHE]   {DEFAULT_CITY} için bugünün verileri önbellekte mevcut. ⚡")
    else:
        guncelle = input(
            f"\n[CACHE]  {DEFAULT_CITY} için bugünün verisi yok.\n"
            "         Şimdi arka planda çekilsin mi? (e/h): "
        ).strip().lower()
        if guncelle == "e":
            print(f"[CACHE]  {DEFAULT_CITY} verileri güncelleniyor...")
            sabah_cache_guncelle(DEFAULT_CITY)

    # ── Kullanıcı Girdisi ─────────────────────────────────────
    print("\n" + "─" * 62)
    print("  Lütfen tarımsal durumunuzu tanımlayın:")
    print("─" * 62)
    konum = input("📍 Şehriniz  (boş bırakırsanız varsayılan kullanılır): ").strip()
    soru  = input(
        "❓ Sorunuz:\n"
        "   (Örn: Konya'da buğday için ilaçlama zamanı ne zaman?)\n"
        "   > "
    ).strip()

    if not soru:
        print("[UYARI] Soru girilmedi, örnek soru kullanılıyor.")
        soru = "Bu hafta ilaçlama ve gübreleme için en uygun günler hangileri?"

    # Şehir belirleme
    hedef_sehir = konum.strip().title() if konum else sehir_tespit_et(soru)

    print()
    print("─" * 62)
    print(f"  🌆 Hedef Şehir : {hedef_sehir}")
    print(f"  ❓ Soru        : {soru}")
    print("─" * 62)
    print("  🚀 4 ajan göreve başlıyor...")
    print("  ⏳ Bu işlem 1-3 dakika sürebilir, lütfen bekleyin.\n")

    # ── CrewAI Pipeline ──────────────────────────────────────
    gorevler = gorevleri_olustur(soru, konum)

    crew = Crew(
        agents=[g.agent for g in gorevler],
        tasks=gorevler,
        process=Process.sequential,
        verbose=True,
    )

    # Retry mekanizması (503 / 429 otomatik yeniden deneme)
    MAX_DENEME   = 4
    bekleme_sure = 15
    baslangic    = time.time()
    sonuc        = None

    for deneme in range(1, MAX_DENEME + 1):
        try:
            print(f"[agri-ai-assistant] Deneme {deneme}/{MAX_DENEME} başlıyor...")
            sonuc = crew.kickoff()
            break

        except Exception as hata_obj:
            hata_str = str(hata_obj)
            kod_503  = "503" in hata_str or "UNAVAILABLE" in hata_str
            kod_429  = "429" in hata_str or "RESOURCE_EXHAUSTED" in hata_str or "RateLimitError" in hata_str

            if (kod_503 or kod_429) and deneme < MAX_DENEME:
                import re as _re
                m = _re.search(r'retryDelay.*?(\d+)', hata_str)
                if m:
                    bekleme_sure = int(m.group(1)) + 5

                tur = "503 Sunucu Meşgul" if kod_503 else "429 Kota Aşımı"
                print(f"[agri-ai-assistant] {tur} — {bekleme_sure}sn bekleniyor... (Deneme {deneme}/{MAX_DENEME})")
                time.sleep(bekleme_sure)
                bekleme_sure = min(bekleme_sure * 2, 120)
            else:
                print(f"\n[HATA] Tüm denemeler başarısız: {hata_str[:200]}")
                raise

    sure = round(time.time() - baslangic, 1)

    # ── Sonuç Ekranı ─────────────────────────────────────────
    print()
    print("=" * 62)
    print("  🌾 ZİRAAT MÜHENDİSİ REÇETESİ")
    print("=" * 62)
    print(str(sonuc))
    print("=" * 62)
    print(f"  Tamamlandı: {sure} saniye")
    print("=" * 62)


if __name__ == "__main__":
    ana_dongu()
