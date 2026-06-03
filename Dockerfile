# Temel Python imajını kullanıyoruz (3.11 RAG kütüphaneleri için stabil)
FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# ChromaDB ve HuggingFace için gereken C/C++ build araçlarını yükle
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılık listesini kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını konteynere kopyala
COPY . .

# Logların anında terminale yansıması için buffer'ı kapat
ENV PYTHONUNBUFFERED=1

# Uygulamayı başlat
CMD ["python", "main.py"]
