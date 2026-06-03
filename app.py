# app.py
"""
AgroAskAI v3.0 – Flask Web Sunucusu (Multi-Tenant Hafıza + APScheduler)
"""

import os, time, datetime, logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from crewai import Crew, Process
from tasks import gorevleri_olustur
from agents import sehir_tespit_et, DEFAULT_CITY
from tools import otomatik_tmo_kaziyici_ve_rag_guncelle
from profil_yonetimi import profil_oku, profil_guncelle, profil_klasoru_hazirla

load_dotenv(override=True)

app = Flask(__name__)

# Profil klasörünü başlangıçta otomatik oluştur
profil_klasoru_hazirla()

# ----------------------------------------------------------------------
# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ----------------------------------------------------------------------
# APScheduler – her sabah 10:00'da TMO scraping + RAG güncelle (Borsa/TMO verilerinin güncel olması için saat yükseltildi)
def _planli_guncelle():
    logging.info("[Scheduler] Tam Otonom TMO Scraper tetiklendi.")
    sonuc = otomatik_tmo_kaziyici_ve_rag_guncelle()
    logging.info(f"[Scheduler] Sonuç: {sonuc}")

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(_planli_guncelle, "cron", hour=10, minute=0, id="tmo_update")
    scheduler.start()
    logging.info("[Scheduler] 10:00 günlük TMO scraping job'ı başlatıldı.")
except Exception as e:
    logging.warning(f"[Scheduler] APScheduler başlatılamadı: {e}")

# ----------------------------------------------------------------------
# Startup – chroma_db yoksa ilk çalıştırmada otomatik RAG güncelle
import threading
from pathlib import Path

def _startup_rag_kontrol():
    db_dir = Path("./chroma_db")
    if not db_dir.exists() or not any(db_dir.iterdir()):
        logging.info("[Startup] chroma_db bulunamadı – ilk kez otonom RAG güncelleniyor...")
        sonuc = otomatik_tmo_kaziyici_ve_rag_guncelle()
        logging.info(f"[Startup] İlk RAG güncelleme sonucu: {sonuc}")
    else:
        logging.info("[Startup] chroma_db mevcut – RAG veritabanı hazır.")

# Ana thread'i bloklamadan arka planda çalıştır
threading.Thread(target=_startup_rag_kontrol, daemon=True).start()

# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------------------------------------------------
@app.route("/api/profile/<kullanici_id>", methods=["GET"])
def get_profile(kullanici_id):
    try:
        profil = profil_oku(kullanici_id)
        return jsonify(profil)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data   = request.json or {}
    soru   = data.get("soru", "").strip()
    konum  = data.get("konum", "").strip()
    ekili_urunler = data.get("ekili_urunler", [])
    if not ekili_urunler and data.get("urun"):
        ekili_urunler = [{"urun_adi": data.get("urun", "buğday").strip().lower(), "dekar": 0}]
    maliyet = data.get("maliyetler") or {}
    kullanici_id = data.get("kullanici_id", "anonim").strip()

    if not soru:
        return jsonify({"error": "Lütfen tarımsal sorununuzu girin."}), 400

    # Şehir tespiti (tam adres)
    hedef_sehir = konum if konum else sehir_tespit_et(soru)

    # ── Long-Term Memory: Çiftçi profilini oku ──
    kullanici_profili = profil_oku(kullanici_id)

    logging.info("\n" + "="*60)
    logging.info("[AgroAskAI] Yeni analiz isteği")
    logging.info(f"  Kullanıcı: {kullanici_id}")
    logging.info(f"  Soru   : {soru}")
    logging.info(f"  Konum  : {hedef_sehir}")
    logging.info(f"  Ürünler: {ekili_urunler}")
    logging.info(f"  Maliyet: {maliyet}")
    logging.info(f"  Profil : {'Mevcut ✅' if kullanici_profili.get('son_soru') else 'Yeni kullanıcı 🆕'}")
    logging.info(f"  Zaman  : {datetime.datetime.now().strftime('%H:%M:%S')}")
    logging.info("="*60 + "\n")

    try:
        # Görev zinciri oluştur (profil bağlamıyla)
        gorevler = gorevleri_olustur(
            soru, hedef_sehir, ekili_urunler=ekili_urunler,
            maliyetler=maliyet,
            kullanici_profili=kullanici_profili,
        )

        crew = Crew(
            agents=[g.agent for g in gorevler],
            tasks=gorevler,
            process=Process.sequential,
            verbose=True,
            # memory=True,   # DEVRE DIŞI: OpenAI Embeddings gerektirir ve Gemini serbest katman kotasını çok hızlı doldurur
        )

        # ---- Retry mekanizması (503/429) ----
        MAX_DENEME   = 4
        bekleme_sure = 3
        baslangic    = time.time()
        sonuc        = None

        for deneme in range(1, MAX_DENEME + 1):
            try:
                logging.info(f"[AgroAskAI] 🚀 Deneme {deneme}/{MAX_DENEME} başlıyor...")
                sonuc = crew.kickoff()
                break
            except Exception as hata:
                txt = str(hata)
                kod_503 = "503" in txt or "UNAVAILABLE" in txt
                kod_429 = "429" in txt or "RESOURCE_EXHAUSTED" in txt or "RateLimitError" in txt
                if (kod_503 or kod_429) and deneme < MAX_DENEME:
                    tur = "503 Sunucu Meşgul" if kod_503 else "429 Kota Aşımı"
                    logging.warning(f"[AgroAskAI] {tur} – {bekleme_sure}s bekleniyor…")
                    time.sleep(bekleme_sure)
                    bekleme_sure = min(bekleme_sure * 2, 15)
                else:
                    raise

        sure = round(time.time() - baslangic, 1)
        logging.info(f"\n[AgroAskAI] ✅ Analiz tamamlandı! Süre: {sure}s\n")

        # Çıktıyı temizle (Thought / markdown kalıntıları)
        recete = str(sonuc)
        if "🌾" in recete:
            recete = "🌾" + recete.split("🌾", 1)[1]
        recete = recete.replace("```markdown", "").replace("```", "").strip()

        # ── Long-Term Memory: Profili güncelle ──
        try:
            toplam_maliyet_val = 0.0
            if isinstance(maliyet, dict):
                for val in maliyet.values():
                    try:
                        toplam_maliyet_val += float(val)
                    except (ValueError, TypeError):
                        pass

            profil_guncelle(kullanici_id, {
                "son_soru": soru,
                "son_tavsiye_ozeti": recete[:200],
                "konum": hedef_sehir,
                "ekili_urunler": ekili_urunler,
                "toplam_maliyet": toplam_maliyet_val
            })
        except Exception as profil_hata:
            logging.warning(f"[Profil] Profil güncellenemedi: {profil_hata}")

        return jsonify({
            "result": recete,
            "sehir": hedef_sehir,
            "kullanici_id": kullanici_id,
            "sure_saniye": sure,
        })
    except Exception as e:
        err = str(e)
        logging.error(f"[AgroAskAI] ❌ Kalıcı hata: {err}")
        if "503" in err or "UNAVAILABLE" in err:
            mesaj = "Google AI sunucuları yoğun, lütfen 1‑2 dk sonra tekrar deneyin."
        elif "429" in err or "quota" in err.lower():
            mesaj = "API kotası doldu. Yarın ya da farklı bir anahtarla deneyin."
        else:
            mesaj = err
        return jsonify({"error": mesaj}), 500

# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Production önerisi: gunicorn app:app
    app.run(host="0.0.0.0", port=5000, debug=False)
