# agents.py
"""
AgroAskAI v3.0 – Ajan Fabrikası
"""

import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from tools import (
    fetch_nasa_power_history_tool,
    fetch_live_weather_forecast_tool,
    fetch_tmo_pdf_rag_tool,
    tarim_rehberinde_ara,
    get_coordinates_tool,
    fetch_ndvi_health_tool,
    lojistik_maliyet_hesapla_tool,
)

load_dotenv()

DEFAULT_CITY = os.getenv("DEFAULT_LOCATION", "Afyonkarahisar")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
MODEL_ADI    = f"gemini/{os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash')}"

import re

TURKIYE_ILLERI = [
    "adana", "adıyaman", "afyonkarahisar", "ağrı", "amasya", "ankara", "antalya",
    "artvin", "aydın", "balıkesir", "bilecik", "bingöl", "bitlis", "bolu",
    "burdur", "bursa", "çanakkale", "çankırı", "çorum", "denizli", "diyarbakır",
    "edirne", "elazığ", "erzincan", "erzurum", "eskişehir", "gaziantep",
    "giresun", "gümüşhane", "hakkari", "hatay", "ısparta", "mersin", "istanbul",
    "izmir", "kars", "kastamonu", "kayseri", "kırklareli", "kırşehir",
    "kocaeli", "konya", "kütahya", "malatya", "manisa", "kahramanmaraş",
    "mardin", "muğla", "muş", "nevşehir", "niğde", "ordu", "rize",
    "sakarya", "samsun", "siirt", "sinop", "sivas", "tekirdağ", "tokat",
    "trabzon", "tunceli", "şanlıurfa", "uşak", "van", "yozgat", "zonguldak",
    "aksaray", "bayburt", "karaman", "kırıkkale", "batman", "şırnak",
    "bartın", "ardahan", "iğdır", "yalova", "karabük", "kilis", "osmaniye",
    "düzce",
]

def sehir_tespit_et(metin: str) -> str:
    metin_kucuk = metin.lower()
    for il in TURKIYE_ILLERI:
        pattern = rf"\b{re.escape(il)}[a-zçğıöşü'']*\b"
        if re.search(pattern, metin_kucuk):
            return il.title()
    return DEFAULT_CITY

def sehir_profil_mi(sehir: str) -> bool:
    return sehir.strip().lower() == DEFAULT_CITY.strip().lower()

def llm_olustur(temperature: float = 0.3) -> LLM:
    if not GEMINI_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY .env dosyasında bulunamadı! "
            "Lütfen .env dosyasına GEMINI_API_KEY=<anahtar> ekleyin."
        )
    return LLM(model=MODEL_ADI, api_key=GEMINI_KEY, temperature=temperature)

# ----------------------------------------------------------------------
# 1. ORKESTRATÖR – Ziraat Mühendisi (final reçete üretir)
def orkestrator_ajan_olustur() -> Agent:
    return Agent(
        role="Tarım Koordinasyon, Sentez ve Aksiyon Lideri",
        goal=(
            "Tüm uzman ajanların (iklim/toprak, hava, finans/lojistik) "
            "çıktılarını sentezleyerek çiftçiye 5‑7 cümlelik "
            "'Ziraat Mühendisi Reçetesi' sun. PDF üretimi KESİNLİKLE YOK. "
            "Çıktı ŞU FORMATTA olacak (bu formatın dışına çıkma):\n"
            "🌾 [İlçe/Köy] | [Tarih]\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌡️ İKLİM & TOPRAK: [NASA toprak nemi ve kuraklık verisiyle nokta atışı durum]\n"
            "🌦️ HAVA: [Bu hafta tarla operasyon günleri]\n"
            "💰 FİNANS & PİYASA: [Nakliye düşülmüş fiyat, maliyet analizi ve net kâr projeksiyonu]\n"
            "✅ AKSİYON: [Hemen yapılması gereken 2 somut adım]"
        ),
        backstory=(
            "15 yıllık sahada deneyimli bir ziraat mühendisisin. "
            "Çiftçiye kısa, net, mobil‑uyumlu, doğrudan eyleme dönüştürülebilir "
            "tavsiye vermeye odaklanırsın. Asla uzun akademik paragraflar yazmaz, "
            "sadece saha reçetesi sunarsın."
        ),
        tools=[],
        llm=llm_olustur(temperature=0.4),
        verbose=True,
        max_iter=3,
        allow_delegation=False,
    )

# ----------------------------------------------------------------------
# 2. İKLİM & TOPRAK AJANI – NASA POWER + toprak nemi
def iklim_toprak_ajani_olustur() -> Agent:
    return Agent(
        role="Hassas İklim, Toprak Nem ve Bitki Sağlığı Analisti",
        goal=(
            "1. OpenCage ile il/ilçe/köy seviyesinde nokta atışı koordinat al.\n"
            "2. NASA POWER'dan T2M, PRECTOTCORR, GWETPROF (kök toprak nemi) ve "
            "GWETTOP (yüzey toprak nemi) verilerini çek.\n"
            "3. Toprak nemi <30% ise 'Toprak nemi %X'e düşmüş, acil sulama yapın' "
            "gibi nokta atışı uyarı üret.\n"
            "4. NDVI bitki sağlığı indeksini kontrol et ve stres varsa raporla.\n"
            "5. Kuraklık riski, toprak durumu ve bitki sağlığı özetini çıkar."
        ),
        backstory=(
            "NASA uydu verileri ve OpenCage entegrasyonlarıyla çiftçinin "
            "tarlasının mikro‑iklimini, toprak su durumunu ve bitki sağlığını "
            "hassas koordinatlarla izleyen bir uzaktan algılama bilim insanısın."
        ),
        tools=[fetch_nasa_power_history_tool, get_coordinates_tool, fetch_ndvi_health_tool, tarim_rehberinde_ara],
        llm=llm_olustur(temperature=0.1),
        verbose=True,
        max_iter=3,
        allow_delegation=False,
    )

# ----------------------------------------------------------------------
# 3. HAVA AJANI – Canlı tahmin ve saha takvimi
def hava_ajani_olustur() -> Agent:
    return Agent(
        role="Meteorolojik Aksiyon ve Saha Planlayıcısı",
        goal=(
            "OpenWeatherMap’ten 5 günlük 3‑saatlik tahmin al, "
            "don riski, yağış, nem ve tarımsal eylem pencerelerini "
            "hesapla. Ürün dalga, gübreleme ve sulama öner."
        ),
        backstory=(
            "Meteoroloji mühendisisin, çiftçinin haftalık saha takvimini "
            "gerçek zamanlı hava verisiyle belirliyorsun."
        ),
        tools=[fetch_live_weather_forecast_tool],
        llm=llm_olustur(temperature=0.1),
        verbose=True,
        max_iter=3,
        allow_delegation=False,
    )

# ----------------------------------------------------------------------
# 4. FINANS & PİYASA AJANI – Dinamik ürün, kâr hesaplama + lojistik akıl yürütme
def finans_ajani_olustur() -> Agent:
    return Agent(
        role="Tarım Finans, Piyasa ve Lojistik Analisti",
        goal=(
            "Kullanıcıdan gelen {ürün} ve {maliyetler} sözlüğüne göre "
            "TMO fiyatları ve tahmini rekolte üzerinden Net Kâr hesapla. "
            "KESİN KURAL‑1 (VARSAYILAN REKOLTE): Eğer çiftçi sorusunda tahmini bir verim "
            "(rekolte) belirtmemişse, ASLA hesaplama yapmaktan vazgeçme. "
            "RAG veritabanından veya genel tarımsal verilerden "
            "(Örn: İç Anadolu buğdayı için ortalama 350‑400 kg/dekar) hedef ürün ve bölge için "
            "ORTALAMA BİR REKOLTEYİ otomatik olarak VARSAYILAN (default) değer kabul et.\n"
            "KESİN KURAL‑2 (LOJİSTİK FIRE): Ulusal TMO baz fiyatını aldıktan sonra, "
            "lojistik_maliyet_hesapla_tool ile çiftçinin konumunun ana borsa merkezlerine "
            "(Polatlı, Konya vb.) olan uzaklığını hesapla. Dönen nakliye/fire kesinti "
            "oranını (%2‑%5) ulusal baz fiyattan düş ve 'Revize Yerel Fiyat' olarak kullan.\n"
            "FORMÜL: Tahmini Gelir = Varsayılan Rekolte × Revize Yerel Fiyat | "
            "Net Kâr = Tahmini Gelir - Çiftçinin Toplam Maliyeti.\n"
            "Çıktında mutlaka şu cümle formatını kullan: 'Girdiğiniz maliyetler ve bölgenin "
            "ortalama rekoltesi (örn: 400kg/dekar) baz alındığında, merkez borsalara "
            "uzaklığınızdan kaynaklı tahmini nakliye fireleri düşüldüğünde "
            "X TL kâr/zarar etme riskiniz bulunmaktadır.'\n"
            "Net kâr > 0 ise 'SAT', =0 ise 'BEKLE', <0 ise 'EKME' tavsiyesini ver."
        ),
        backstory=(
            "Tarım ekonomisti ve lojistik analistisin. Dinamik ürün ve maliyet "
            "girdileriyle çiftçinin kârlılığını anlık değerlendirir, borsa merkezlerine "
            "uzaklık bazlı nakliye/tüccar komisyon firelerini hesaba katarsın."
        ),
        tools=[fetch_tmo_pdf_rag_tool, tarim_rehberinde_ara, lojistik_maliyet_hesapla_tool],
        llm=llm_olustur(temperature=0.5),
        verbose=True,
        max_iter=4,
        allow_delegation=False,
    )

# ----------------------------------------------------------------------
# Ajan Fabrikası – hepsini bir seferde üret
def tum_ajanlari_olustur() -> dict:
    return {
        "orkestrator": orkestrator_ajan_olustur(),
        "iklim_toprak": iklim_toprak_ajani_olustur(),
        "hava": hava_ajani_olustur(),
        "finans": finans_ajani_olustur(),
    }
