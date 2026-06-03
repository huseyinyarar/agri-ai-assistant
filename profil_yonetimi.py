# profil_yonetimi.py
"""
AgroAskAI v3.0 – Çok Kiracılı (Multi-Tenant) Profil Yönetimi
=============================================================
Her çiftçi için ./profiller/{kullanici_id}.json dosyası oluşturur,
okur ve günceller. Long-Term Memory katmanını oluşturur.
"""

import os
import json
import re
import logging
from datetime import datetime, date
from pathlib import Path

# ── Sabitler ──────────────────────────────────────────────────────────
PROFIL_DIZINI = Path("./profiller")

# Boş profil iskeleti
_BOS_PROFIL = {
    "kullanici_id": "",
    "kayit_tarihi": "",
    "konum": "",
    "ekili_urunler": [],
    "son_soru": "",
    "son_tavsiye_ozeti": "",
    "son_islem_tarihi": None,
    "finansal_bakiye": 0.0,
    "toplam_maliyet": 0.0,
    "toplam_gelir": 0.0,
    "gecmis_sorular": [],       # Son 5 soru kaydı
}

MAX_GECMIS = 5   # Geçmiş sorular listesinde en fazla kaç kayıt tutulsun


# ── Yardımcı: ID Slug ────────────────────────────────────────────────
def _slugify(metin: str) -> str:
    """
    Kullanıcı girdisini dosya-adı-güvenli hale getirir.
    Örn: 'Ahmet Çiftçi +90 555' → 'ahmet_ciftci_90_555'
    """
    metin = metin.strip().lower()
    # Türkçe karakter dönüşümü (dosya adı güvenliği)
    tr_map = str.maketrans("çğıöşü", "cgiosu")
    metin = metin.translate(tr_map)
    # Alfanümerik olmayan her şeyi _ yap, ardından tekrarları temizle
    metin = re.sub(r"[^a-z0-9]+", "_", metin)
    metin = metin.strip("_")
    return metin or "anonim"


# ── Klasör Hazırlık ──────────────────────────────────────────────────
def profil_klasoru_hazirla() -> Path:
    """./profiller klasörünü oluşturur (zaten varsa sessizce geçer)."""
    PROFIL_DIZINI.mkdir(exist_ok=True)
    return PROFIL_DIZINI


# ── Profil Okuma ─────────────────────────────────────────────────────
def profil_oku(kullanici_id: str) -> dict:
    """
    Kullanıcı profilini okur.
    - Varsa JSON'dan yükler
    - Yoksa boş iskelet oluşturup diske yazar ve döner
    """
    profil_klasoru_hazirla()
    safe_id = _slugify(kullanici_id)
    dosya = PROFIL_DIZINI / f"{safe_id}.json"

    if dosya.exists():
        try:
            with open(dosya, "r", encoding="utf-8") as f:
                profil = json.load(f)
            logging.info(f"[Profil] ✅ Mevcut profil yüklendi: {safe_id}")
            return profil
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"[Profil] ⚠️ Profil okunamadı ({safe_id}), sıfırdan oluşturuluyor: {e}")

    # Yeni profil oluştur
    profil = _BOS_PROFIL.copy()
    profil["kullanici_id"] = safe_id
    profil["kayit_tarihi"] = date.today().isoformat()
    profil["gecmis_sorular"] = []

    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)

    logging.info(f"[Profil] 🆕 Yeni profil oluşturuldu: {safe_id}")
    return profil


# ── Profil Güncelleme ────────────────────────────────────────────────
def profil_guncelle(kullanici_id: str, yeni_veri: dict) -> dict:
    """
    Mevcut profili okur, gelen sözlükle günceller ve diske yazar.

    Parametre olarak gelen yeni_veri örneği:
    {
        "son_soru": "Konya'da buğday ilaçlama",
        "son_tavsiye_ozeti": "Toprak nemi %28...",
        "konum": "Konya, Karatay",
        "ekili_urunler": [{"urun_adi": "buğday", "dekar": 40}, {"urun_adi": "mısır", "dekar": 20}],
        "toplam_maliyet": 15000.0,    # eklenecek yeni maliyet (overwrite edilmez)
    }
    """
    profil_klasoru_hazirla()
    safe_id = _slugify(kullanici_id)
    profil = profil_oku(kullanici_id)

    # Basit alanları güncelle
    for alan in ["konum", "son_soru", "son_tavsiye_ozeti", "ekili_urunler"]:
        if alan in yeni_veri and yeni_veri[alan]:
            profil[alan] = yeni_veri[alan]
            
    # Finansal alanları BİRİKİMLİ (Akümülatif) güncelle
    for finans_alani in ["finansal_bakiye", "toplam_maliyet", "toplam_gelir"]:
        if finans_alani in yeni_veri and yeni_veri[finans_alani]:
            mevcut_deger = float(profil.get(finans_alani, 0.0))
            eklenen_deger = float(yeni_veri[finans_alani])
            profil[finans_alani] = mevcut_deger + eklenen_deger

    # Son işlem tarihini otomatik güncelle
    profil["son_islem_tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Geçmiş sorular listesine ekle (FIFO – son 5)
    if yeni_veri.get("son_soru"):
        gecmis_kayit = {
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "soru": yeni_veri["son_soru"],
            "ozet": yeni_veri.get("son_tavsiye_ozeti", "")[:150],
        }
        if not isinstance(profil.get("gecmis_sorular"), list):
            profil["gecmis_sorular"] = []
        profil["gecmis_sorular"].append(gecmis_kayit)
        profil["gecmis_sorular"] = profil["gecmis_sorular"][-MAX_GECMIS:]

    # Diske yaz
    dosya = PROFIL_DIZINI / f"{safe_id}.json"
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)

    logging.info(f"[Profil] 💾 Profil güncellendi: {safe_id}")
    return profil


# ── Profil Bağlam Metni (Enjeksiyon İçin) ────────────────────────────
def profil_baglam_metni_olustur(profil: dict) -> str:
    """
    Profil verisinden, ajan promptlarına enjekte edilecek
    düz metin bağlam bloğu üretir.
    Eğer profil boşsa (yeni kullanıcı) boş string döner.
    """
    # Yeni kullanıcı kontrolü – hiç soru sorulmamışsa bağlam gereksiz
    if not profil.get("son_soru"):
        return ""

    satirlar = [
        "━━━ GEÇMİŞ BAĞLAM (Çiftçi Profili) ━━━",
        f"• Kullanıcı ID : {profil.get('kullanici_id', 'anonim')}",
    ]

    if profil.get("konum"):
        satirlar.append(f"• Konum        : {profil['konum']}")
        
    ekili_urunler = profil.get("ekili_urunler", [])
    if ekili_urunler and isinstance(ekili_urunler, list):
        urun_str = ", ".join([f"{u.get('urun_adi', '')} ({u.get('dekar', 0)} dekar)" for u in ekili_urunler])
        satirlar.append(f"• Ekili Ürünler: {urun_str}")
        
    if profil.get("son_soru"):
        satirlar.append(f"• Son Soru     : \"{profil['son_soru']}\"")
    if profil.get("son_tavsiye_ozeti"):
        satirlar.append(f"• Son Tavsiye  : {profil['son_tavsiye_ozeti'][:120]}...")

    bakiye = profil.get("finansal_bakiye", 0)
    if bakiye != 0:
        satirlar.append(f"• Finansal Bakiye: {bakiye:,.0f} TL")

    maliyet = profil.get("toplam_maliyet", 0)
    if maliyet > 0:
        satirlar.append(f"• Toplam Maliyet : {maliyet:,.0f} TL")

    if profil.get("son_islem_tarihi"):
        satirlar.append(f"• Son İşlem    : {profil['son_islem_tarihi']}")

    satirlar.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    satirlar.append(
        "KESİN KURAL: Kullanıcının geçmiş durumunu (bakiye, ekili ürün, son aksiyon) "
        "mutlaka hesaba kat. Negatif bakiye varsa riski korumaya yönelik konuş."
    )

    return "\n".join(satirlar)
