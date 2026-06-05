# 🌾 Agri-AI: Çoklu Ajan Destekli Akıllı Tarım Asistanı

> **Geliştirici:** Hüseyin Yarar
> **Proje Türü:** Yapay Zeka (AI) & Multi-Agent Sistemler

Agri-AI, çiftçilere günlük operasyonlarında (sulama, gübreleme, ilaçlama) nokta atışı kararlar aldırabilmek için **CrewAI** ve **LangChain** teknolojilerini kullanarak geliştirilmiş, yapay zeka destekli otonom bir ziraat mühendisi asistanıdır.

---

## 🚀 Proje Hakkında

Sistem arka planda 4 farklı uzman ajan (Agent) çalıştırarak çiftçinin sorusunu analiz eder, dış veri kaynaklarından (API ve PDF) anlık veriler çeker ve finansal kar-zarar projeksiyonu ile birlikte tavsiye reçetesi oluşturur.

### 🧠 Ajan (Agent) Mimarisi
1. **İklim ve Toprak Ajanı:** NASA POWER API kullanarak tarlanın anlık kök ve yüzey nemi oranlarını çeker. Copernicus Sentinel-2 NDVI simülasyonlarıyla bitki stresi ve kuraklık riski ölçümü yapar.
2. **Hava Ajanı:** OpenWeather API kullanarak 5 günlük hava tahminlerini analiz eder; don riskini ve tarımsal operasyon (ilaçlama vb.) pencerelerini belirler.
3. **Finans ve Lojistik Ajanı:** TMO'nun güncel PDF raporlarını RAG (Retrieval-Augmented Generation) ile okuyarak güncel ürün baz fiyatını bulur. Çiftçinin borsaya olan uzaklığını hesaplayarak nakliye firesini düşer ve tahmini bir kar/zarar projeksiyonu sunar.
4. **Yönetici Orkestratör:** Önceki 3 ajanın getirdiği karmaşık verileri sentezleyerek "Ziraat Mühendisi Reçetesi" formatında şeffaf, anında eyleme dönük ve 5 satırlık nihai bir çıktı üretir.

---

## 📸 Sistem Çıktıları ve Ekran Görüntüleri

Projenin çıktılarını ve ajanların arka plandaki çalışma (düşünce) süreçlerini aşağıda görebilirsiniz:

### Sistem Arayüzü ve Nihai Reçete Çıktısı
Aşağıdaki görselde, Agri-AI sisteminin kullanıcı dostu web arayüzünü ve arka planda ajanların ürettiği otonom Ziraat Mühendisi Reçetesini görebilirsiniz:

<img width="1919" height="904" alt="Ekran görüntüsü 2026-06-06 000949" src="https://github.com/user-attachments/assets/b319f375-5379-4394-ab2e-956891853b52" />

---

## ⚙️ Kurulum ve Çalıştırma (Hocalar ve Geliştiriciler İçin)

Projenin tüm özellikleri API destekli olduğu için kendi lokal bilgisayarınızda kolayca çalıştırabilirsiniz.

### 1. Depoyu İndirin ve Gereksinimleri Yükleyin
Proje dizininde bir terminal açarak gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

### 2. API Anahtarlarını Ayarlayın
Projenin çalışması için `.env` dosyasındaki ortam değişkenlerini doldurmalısınız. Güvenlik nedeniyle `.env` dosyası repoda bulunmamaktadır (veya private repoda paylaşılmıştır).

Bir `.env` dosyası oluşturun ve aşağıdaki formatta kendi API anahtarlarınızı girin:
```env
GEMINI_API_KEY=AIzaSy...
OPENWEATHER_API_KEY=xxxx...
OPENCAGE_KEY=xxxx...
```

### 3. Uygulamayı Başlatın
Flask tabanlı web arayüzünü başlatmak için aşağıdaki komutu çalıştırın:
```bash
python app.py
```
Terminalde çıkacak olan `http://127.0.0.1:5000` adresine tarayıcınızdan giderek Agri-AI'yi kullanmaya başlayabilirsiniz.
