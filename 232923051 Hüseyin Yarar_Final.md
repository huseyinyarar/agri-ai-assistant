# agri-ai-assistant: Çoklu Ajan (Multi-Agent) ve RAG Tabanlı Otonom Tarımsal Karar Destek Sistemi

## 1-) Problem Tanımı
Tarım sektörü, küresel iklim değişikliğine bağlı olarak artan kuraklık, düzensiz yağış rejimleri ve öngörülemeyen patojenik (hastalık) risklerle karşı karşıyadır. Çiftçiler ve tarım paydaşları; karmaşık meteorolojik uydu verilerini, bölgesel patojen risklerini ve anlık piyasa fiyatlarını eşzamanlı olarak analiz edip kârlı ve güvenli kararlar almakta zorlanmaktadır. Literatürde mevcut olan CROPWAT gibi kural tabanlı sistemler kullanım zorluğu çekerken, standart Büyük Dil Modelleri (LLM) ise spesifik tarım matematiğinde ve bağlamsal doğrulukta "halüsinasyon" (yanılsama) riski taşımaktadır. Bu projenin temel problemi; dağınık ve heterojen verilerin (API, uydu, PDF dokümanları, fiyat bültenleri) küçük ölçekli çiftçilere otonom, güvenilir ve %100 bağlama sadık bir şekilde ulaştırılamamasıdır.

*(Bu alana sorunun büyüklüğünü veya klasik sistemlerin karmaşıklığını gösteren bir grafik veya arayüzün boş/başlangıç ekranını koyabilirsiniz)*
> **[EKRAN GÖRÜNTÜSÜ 1: agri-ai-assistant Web Arayüzü Başlangıç Ekranı]**

---

## 2-) Makale/Tez ve Literatür Taraması
Bu projenin temel mimarisi, literatürdeki **"agri-ai-assistant: A Multi-Agentic AI Framework for Supporting Smallholder Farmers’ Enquiries Globally" (Cantonjos ve Biswas, 2025 - arXiv:2512.14910)** başlıklı çalışmaya dayanmaktadır. 

İlgili makale, tekil bir yapay zeka modelinin (örn. salt ChatGPT) tarım gibi kritik alanlarda yetersiz kalacağını savunarak "Çoklu Ajan (Multi-Agent)" mimarisini önermektedir. Bu projede, referans alınan mimariye uygun olarak sistem bağımsız, uzmanlaşmış ajanlara bölünmüştür:
1. **İklim ve Toprak Ajanı (Climate & Soil Agent):** Uzaktan algılama (Remote Sensing) araçlarıyla geçmiş iklim ve toprak nemi verilerini analiz eder.
2. **Hava Ajanı (Weather Agent):** Canlı meteorolojik tahminleri analiz ederek don, yağış ve saha operasyon pencerelerini belirler.
3. **Finans Ajanı (Finance & Logistics Agent):** TMO fiyat bültenlerinden, güncel piyasa fiyatlarından ve lojistik/nakliye mesafelerinden yola çıkarak net kâr-zarar projeksiyonları üretir.
4. **Orkestratör Ajan (Orchestrator & Reviewer):** Tüm uzman ajanlardan gelen verileri sentezleyerek kısa, net ve doğrudan eyleme dönüştürülebilir "Ziraat Mühendisi Reçetesi" sunar; halüsinasyonu filtreler.

*(Bu alana agri-ai-assistant ajan mimarisini (Agent Manager, İklim, Finans ajanlarının şeması) veya ajanların terminalde sırayla çalıştığını gösteren bir log görüntüsü koyabilirsiniz)*
> **[EKRAN GÖRÜNTÜSÜ 2: Terminalde Ajanların Birbirleriyle İletişim Kurduğu (Thought/Action) Çalışma Logları]**

---

## 3-) Dataset ve Metodoloji
Projenin karar destek motoru, dinamik ve statik olmak üzere iki ana veri hattından beslenmektedir:

- **Dinamik API ve Kazıma (Scraping):**
  - **TMO Günlük Piyasa Bülteni:** Toprak Mahsulleri Ofisi sunucularından anlık olarak kazınan güncel hububat baz fiyatları (`piyasabulteni_tr.pdf`).
  - **NASA POWER & OpenWeather API:** OpenCage kütüphanesi ile geocoding yapılarak elde edilen koordinatlar üzerinden kök nemi (GWETPROF), yüzey nemi ve don riski verileri.
- **RAG (Retrieval-Augmented Generation) Vektör Veriseti:**
  - Tarım Bakanlığı ve akademi kaynaklı, hastalık (Sarı Pas vb.) ve verim yönetimi üzerine toplam **13 adet PDF'ten oluşan 705 sayfalık** doküman seti. 
  - Metinler ve tablolar **Gemini Vision (Multimodal AI)** ve PyMuPDF ile temizlenip, LangChain kullanılarak 1000 karakterlik parçalara (chunk) ayrılmıştır. HuggingFace kullanılarak vektörizasyon yapılmış ve **ChromaDB** içerisinde saklanmıştır.

*(Bu alana VS Code veya projenin bulunduğu klasördeki `tarim_rehberleri` PDF'lerini veya `chroma_db` klasörünü gösteren bir görüntü ekleyebilirsiniz)*
> **[EKRAN GÖRÜNTÜSÜ 3: Projedeki 13 PDF'in Bulunduğu Klasör veya ChromaDB Veritabanı Dizini]**

---

## 4-) Problem Hangi Sorunu Çözüyor?
agri-ai-assistant, tarımdaki **Bilgi Asimetrisi** ve çiftçi üzerindeki **Bilişsel Yük** sorununu çözmektedir. Bir çiftçinin tarlasındaki hastalığı 700 sayfalık teknik dokümanlarda araması, o esnada NASA'dan lokal nem verisini kontrol edip TMO'dan nakliye firesini düşerek kâr hesaplaması manuel olarak yapılamaz. Sistem, bu heterojen verileri otonom şekilde saniyeler içinde işler, sentezler ve çiftçiye doğrudan eyleme dönüştürülebilir ("2 gün sonra don riski yok, sarı pas için ilaçlama yap ve bekle") net direktifler sunar.

*(Bu alana, sistemden aldığınız çok başarılı, hem hastalığı bilen hem de kar-zarar hesaplayan o güzel çıktılardan birinin ekran görüntüsünü koymalısınız)*
> **[EKRAN GÖRÜNTÜSÜ 4: agri-ai-assistant Arayüzünden Alınmış Başarılı Bir Karar/Analiz Çıktısı (Örn: Karapınar Mısır Analizi)]**

---

## 5-) Doğruluk Metrikleri ve Halüsinasyon Önleme (Accuracy Metrics)
Projede geleneksel makine öğrenmesi sınıflandırması yerine ajan tabanlı RAG mimarisi kullanıldığından, doğruluk (accuracy) metrikleri sistemin bağlama sadakati üzerinden raporlanmıştır:

- **Retrieval (Geri Getirme) Doğruluğu:** Kullanıcının tarımsal soruları vektörlere dönüştürülüp, ChromaDB veritabanında **Cosine Similarity (Kosinüs Benzerliği)** matematiği ile taranır. Ajanların yalnızca en yüksek benzerliğe sahip (Top-K) dökümanları okuması zorunlu kılınarak konu dışı veri üretimi engellenmiştir.
- **Sıfır Halüsinasyon Kontrolü:** Kapsam dışı cevapları engellemek adına "Değerlendirici (Reviewer)" ajanlar ve katı sistem komutları (Prompt Engineering kısıtlamaları) uygulanmıştır.
- **Matematiksel Determinizm (%100 Doğruluk):** LLM'lerin matematiksel zafiyetleri göz önüne alınarak; kümülatif maliyet hesabı, TMO baz fiyatları ve nakliye fireleri serbest dil üretimine bırakılmamış, deterministik Python fonksiyonları ile %100 doğruluğa sabitlenmiştir.

---

## 6-) Kodların Bulunduğu GitHub Linki
**GitHub Repository:** https://github.com/huseyinyarar/agri-ai-assistant

---
**Öğrenci:** 232923051 – Hüseyin Yarar
