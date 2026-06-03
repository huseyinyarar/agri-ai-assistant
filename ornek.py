import requests

def iklim_ajani_calistir(api_key, sehir="Afyonkarahisar"):
    # OpenWeather API bağlantı noktası
    url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={api_key}&units=metric&lang=tr"
    
    try:
        response = requests.get(url)
        veri = response.json()
        
        if response.status_code == 200:
            sicaklik = veri['main']['temp']
            durum = veri['weather'][0]['description']
            
            print(f"--- İKLİM VE ÇEVRE AJANI AKTİF ---")
            print(f"📍 Konum: {sehir}")
            print(f"🌡️ Anlık Sıcaklık: {sicaklik}°C")
            print(f"☁️ Hava Durumu: {durum.capitalize()}")
            
            # Proaktif Risk Algılama (Sistemin en önemli özelliği)
            print("\n🚨 RİSK ANALİZİ:")
            if sicaklik < 5:
                print("⚠️ DİKKAT: Don riski tespit edildi! Orkestratör Ajan'a ve Çiftçiye uyarı gönderiliyor...")
            elif sicaklik > 35:
                print("⚠️ DİKKAT: Aşırı sıcaklık/Kuraklık riski! Sulama takvimi güncellenmeli.")
            else:
                print("✅ Şu an için kritik bir iklim riski bulunmuyor. Tarımsal faaliyetler normal seyrinde devam edebilir.")
                
        else:
            print("API'den veri çekilemedi. Lütfen API anahtarını kontrol et.")
            
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

# KULLANIM:
# OpenWeather sitesinden aldığın ücretsiz API anahtarını buraya yapıştır
benim_api_anahtarim = "203b470a035f5d20097e0dd2beaee515" 

iklim_ajani_calistir(benim_api_anahtarim)