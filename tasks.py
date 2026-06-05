# tasks.py
"""
agri-ai-assistant v3.0 – Görev Tanımları (Multi-Tenant Hafıza Desteği)
"""

from crewai import Task
from agents import (
    tum_ajanlari_olustur,
    sehir_tespit_et,
    sehir_profil_mi,
    DEFAULT_CITY,
)
from profil_yonetimi import profil_baglam_metni_olustur

def gorevleri_olustur(soru: str, konum: str = "", ekili_urunler: list | None = None,
                     maliyetler: dict | None = None,
                     kullanici_profili: dict | None = None) -> list[Task]:
    # Şehir belirleme
    if konum and konum.strip():
        hedef_sehir = konum.strip()
    else:
        hedef_sehir = sehir_tespit_et(soru)

    profil_mi = sehir_profil_mi(hedef_sehir)
    cache_notu = (
        f"⚡ Profil şehri ({hedef_sehir}) → Önbellekten (cache) okundu."
        if profil_mi else f"🌐 Farklı şehir ({hedef_sehir}) → API on‑demand."
    )

    # ── Çiftçi profili bağlam metni (Long-Term Memory enjeksiyonu) ──
    baglam_metni = ""
    if kullanici_profili:
        baglam_metni = profil_baglam_metni_olustur(kullanici_profili)
    baglam_bloku = f"\n\n{baglam_metni}\n" if baglam_metni else ""

    # Ajanları oluştur
    ajanlar = tum_ajanlari_olustur()

    # ------------------------------------------------------------------
    # GÖREV 1 – İKLİM & TOPRAK
    iklim_gorevi = Task(
        description=(
            f"Hedef Lokasyon: **{hedef_sehir}** (il/ilçe/köy detayında)\n"
            f"{cache_notu}\n"
            f"{baglam_bloku}"
            f"Soru: '{soru}'\n\n"
            "=== GÖREV TALİMATI ===\n"
            "1. `get_coordinates_tool` ile tam adresin (il/ilçe/köy) nokta atışı enlem‑boylamını al.\n"
            "2. KESİN KURAL: `fetch_nasa_power_history_tool` aracını kullanarak sıcaklık (T2M), yağış (PRECTOTCORR), "
            "kök‑toprak‑nem (GWETPROF) ve yüzey‑toprak‑nem (GWETTOP) verilerini ÇEKMEK ZORUNDASIN. Bu aracı kullanmadan ASLA devam etme!\n"
            "3. Eğer NASA aracı başarıyla çalışırsa KESİNLİKLE 'NASA verilerine göre kök nemi %X, yüzey nemi %Y' yaz. Eğer araç HATA döndürürse, uydurma veri üretme ve sadece 'NASA HATA' aldığını raporda açıkça belirt.\n"
            "4. `fetch_ndvi_health_tool` ile bitki sağlığı indeksini (NDVI) kontrol et ve stres varsa raporla.\n"
            "5. Kullanıcı sorusunda 'Sarı Pas', 'Rastık' vb. spesifik bir hastalık/zararlı geçiyorsa MUHAKKAK `tarim_rehberinde_ara` aracını kullanarak riskleri rehberden oku.\n"
            "6. Sonuç: NASA kök/yüzey nem oranları (veya hata durumu), hastalık/kuraklık riski, NDVI bitki sağlığı ve hava özetini üret."
        ),
        expected_output=(
            "NASA verilerine göre kök nemi %X, yüzey nemi %Y değerlerini (veya erişilemediyse NASA HATA mesajını), "
            "NDVI bitki sağlığı durumunu, ortalama sıcaklık (°C) ve yağış (mm) değerlerini içeren kısa özet."
        ),
        agent=ajanlar["iklim_toprak"],
    )

    # ------------------------------------------------------------------
    # GÖREV 2 – HAVA
    hava_gorevi = Task(
        description=(
            f"Hedef Şehir: **{hedef_sehir}**\n"
            f"{cache_notu}\n"
            f"{baglam_bloku}"
            f"Soru: '{soru}'\n\n"
            "=== GÖREV TALİMATI ===\n"
            "1. `fetch_live_weather_forecast_tool` ile 5 günlük tahmin al.\n"
            "2. Tarımsal eylem (ilaçlama, gübreleme, sulama) için uygun günleri "
            "belirle; don riski, yüksek yağış ve nem şartlarını vurgula.\n"
            "3. Çıktı: Bu hafta için en uygun saha operasyon günleri."
        ),
        expected_output=(
            "Haftalık hava‑özet, don riski günleri, yağış <5 mm olan "
            "gübreleme/ilaçlama pencereleri."
        ),
        agent=ajanlar["hava"],
    )

    # ------------------------------------------------------------------
    # GÖV​ER 3 – FINANS & PİYASA (dinamik ürün + maliyet)
    maliyet_str = ""
    if maliyetler:
        parts = [f"{k}:{v}₺" for k, v in maliyetler.items()]
        maliyet_str = " | ".join(parts)

    urun_str = "Belirtilmedi"
    if ekili_urunler:
        urun_str = ", ".join([f"{u.get('urun_adi', '')} ({u.get('dekar', 0)} dekar)" for u in ekili_urunler])

    finans_gorevi = Task(
        description=(
            f"Hedef Lokasyon: **{hedef_sehir}**\n"
            f"{cache_notu}\n"
            f"{baglam_bloku}"
            f"Soru: '{soru}'\n"
            f"Ekili Ürünler ve Tarlalar: **{urun_str}**\n"
            f"Maliyetler: {maliyet_str or 'verilmedi'}\n\n"
            "=== GÖREV TALİMATI ===\n"
            "1. `fetch_tmo_pdf_rag_tool` ile güncel TMO/ulusal baz fiyatını al.\n"
            "2. `lojistik_maliyet_hesapla_tool` ile çiftçinin konumunun ana borsa merkezlerine "
            "(Polatlı, Konya vb.) uzaklığını hesapla. Dönen nakliye/fire kesinti oranını (%2‑%5) "
            "ulusal baz fiyattan düşerek 'Revize Yerel Fiyat' hesapla. Çıktıda bu mantığı "
            "'Merkez borsalara uzaklığınızdan kaynaklı tahmini nakliye fireleri düşüldüğünde "
            "revize fiyatınız...' şeklinde açıkla.\n"
            "3. Tarım rehberinden (`tarim_rehberinde_ara`) olası rekolte bilgisi çıkar. "
            "Eğer çiftçi sorusunda rekolte belirtmemişse, ASLA hesaplamadan vazgeçme. "
            "Hedef ürün ve bölge için ORTALAMA BİR REKOLTEYİ (örn: İç Anadolu buğdayı için "
            "350‑400 kg/dekar) otomatik olarak VARSAYILAN (default) kabul et.\n"
            "4. DİKKAT: Çiftçinin tarlaları ve ürünleri 'Ekili Ürünler ve Tarlalar' kısmında veya profil bağlamında verilmiştir. "
            "Eğer soruda belirli bir üründen bahsediliyorsa hesaplamayı onun dekar büyüklüğü üzerinden yap. "
            "Eğer hiçbir yerde bulamazsan varsayılan olarak 1 dekar kabul et. "
            "Tahmini Gelir = (Varsayılan Rekolte × Tarla Büyüklüğü (Dekar) × Revize Yerel Fiyat) olarak hesapla.\n"
            "5. Net Kâr Hesaplaması: KESİN KURAL-3 (MATEMATİK YAP) Asla kullanıcıya 'kendiniz hesaplayın' deme! "
            "Profil bağlamında verilen 'Toplam Maliyet' değeri ile sana verilen yeni 'Maliyetler' girdisindeki rakamları KENDİN TOPLA "
            "ve bunu Genel Toplam Maliyet olarak kullan. Net Kâr = Tahmini Gelir - Genel Toplam Maliyet formülünü bizzat hesapla. "
            "KESİN KURAL-4: Sadece `fetch_tmo_pdf_rag_tool` aracından dönen fiyatı baz al, asla kafandan farklı bir fiyat uydurma!\n"
            "6. Çıktında KESİNLİKLE şu formatta bir cümle kur: 'Girdiğiniz maliyetler ve "
            "X dekarlık tarlanız için bölgenin ortalama rekoltesi (örn: 400kg/dekar) baz alındığında, merkez borsalara "
            "uzaklığınızdan kaynaklı tahmini nakliye fireleri düşüldüğünde X TL kâr/zarar etme "
            "riskiniz bulunmaktadır.'\n"
            "7. FENOLOJİK EVRE KURALI (ZORUNLU): Kullanıcının mesajından bitkinin tarladaki durumunu "
            "(yeni ekilmiş, büyüme evresinde veya hasat edilmiş) mutlaka analiz et. "
            "Kullanıcı 'yeni ektim', 'gübre atıyorum' veya 'suluyorum' gibi işlemlerden bahsediyorsa, "
            "ASLA 'SAT' veya 'BEKLE' gibi hasat sonrası ticari komutlar VERME. "
            "Sadece 'Hasat dönemi için öngörülen tahmini kâr projeksiyonunuz X TL'dir' diyerek vizyon çiz.\n"
            "8. Çıktı: Ulusal baz fiyat, revize yerel fiyat, tahmini/varsayılan rekolte, "
            "tarla büyüklüğü, toplam maliyet, net kâr ve tavsiye."
        ),
        expected_output=(
            "Ulusal baz fiyat, nakliye firesi düşülmüş revize yerel fiyat, tahmini rekolte, "
            "toplam maliyet, net kâr projeksiyonu ve fenolojik evreye uygun tavsiye."
        ),
        agent=ajanlar["finans"],
    )

    # ------------------------------------------------------------------
    # GÖREV 4 – ORKESTRASYON (final reçete)
    # Orkestrasyon görevine profil-kişiselleştirme kuralı
    profil_kural = ""
    if baglam_metni:
        profil_kural = (
            "\n🔁 KİŞİSELLEŞTİRME KURALI: Bu çiftçinin geçmiş profili mevcut. "
            "Reçetede 'Geçmiş bakiyenizi/durumunuzu dikkate alarak...' şeklinde "
            "kişiselleştirilmiş tavsiyelerde bulun. Negatif bakiye varsa "
            "risk koruma odaklı konuş.\n"
        )

    orkestrasyon_gorevi = Task(
        description=(
            f"Hedef Lokasyon: **{hedef_sehir}**\n"
            f"Soru: '{soru}'\n"
            f"{baglam_bloku}"
            f"{profil_kural}\n"
            "Önceki 3 ajanın (İklim/Toprak, Hava, Finans/Lojistik) analiz sonuçlarını sentezle.\n"
            "ÇIKTI FORMATI (KATI KURAL: SADECE VE SADECE aşağıdaki şablonu doldurarak çıktı ver. "
            "Şablonun dışına KESİNLİKLE çıkma! İngilizce meta-yorumlar, giriş veya kapanış ASLA ekleme!):\n\n"
            "🌾 [İlçe/Köy] | [Tarih]\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌡️ İKLİM & TOPRAK: [Önceki ajanlardan gelen kök ve yüzey nemi oranlarını NASA verisi olarak yaz. Eğer ajan 'NASA HATA' uyarısı vermişse uydurma veri yerine 'NASA API kapalı, manuel kontrol edin' yaz, ardından NDVI bilgisini ekle]\n"
            "🌦️ HAVA: [Bu hafta tarla operasyonları için en güvenli günler, don/yağış riski]\n"
            "💰 FİNANS & PİYASA: [Nakliye firesi düşülmüş revize yerel fiyat, kümülatif maliyet analizi, net kâr/zarar projeksiyonu]\n"
            "✅ AKSİYON: [Hemen yapılması gereken 2 somut adım]\n\n"
            "UYARI: SADECE yukarıdaki emojili metni üret, başına veya sonuna HİÇBİR ŞEY ekleme."
        ),
        expected_output=(
            "KATI FORMAT: Kesinlikle ve sadece yukarıdaki 5 satırlık emojili şablon. "
            "Hiçbir ek açıklama, İngilizce not, numaralandırma veya meta-yorum içermemeli."
        ),
        agent=ajanlar["orkestrator"],
        context=[iklim_gorevi, hava_gorevi, finans_gorevi],
    )

    return [iklim_gorevi, hava_gorevi, finans_gorevi, orkestrasyon_gorevi]
