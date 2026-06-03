import os
import time
import io
import fitz  # PyMuPDF
from PIL import Image
import google.generativeai as genai
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    vision_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logging.warning("GEMINI_API_KEY bulunamadı! Fotoğraf okuma (OCR) devre dışı bırakıldı.")
    vision_model = None

VECTOR_DB_DIR = "./chroma_db"
REHBER_DIR = "./tarim_rehberleri"

def process_pdf_with_vision(pdf_path: str):
    """PDF'i sayfa sayfa açar, normal yazıları ve fotoğrafları/tabloları okur."""
    docs = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logging.error(f"PDF Açılamadı: {pdf_path} - {e}")
        return docs

    logging.info(f"İşleniyor (OCR Destekli): {Path(pdf_path).name} ({len(doc)} sayfa)")
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text("text").strip()
        
        extracted_tables = []
        
        if vision_model:
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Çok küçük resimleri (logo, ikon vs) yoksay (Genişlik/Yükseklik > 150px)
                    if image.width < 150 or image.height < 150:
                        continue
                        
                    # Resmi Gemini API'ye gönder
                    prompt = (
                        "Bu görseldeki tabloyu veya bilgileri anlaşılabilecek şekilde Markdown formatında metne dök. "
                        "Eğer sadece manzara, tünel, traktör vs. gibi dekoratif bir fotoğrafsa ve tablo/bilgi içermiyorsa "
                        "HİÇBİR ŞEY YAZMA, SADECE BOŞ BIRAK."
                    )
                    
                    response = vision_model.generate_content([prompt, image])
                    
                    if response.text and len(response.text.strip()) > 10:
                        extracted_tables.append(f"\n--- GÖRSEL/TABLO İÇERİĞİ (Sayfa {page_num+1}) ---\n{response.text.strip()}\n")
                    
                    # Gemini Free-Tier Limitlerini aşmamak için 3 saniye bekleme
                    time.sleep(3)
                    
                except Exception as e:
                    logging.warning(f"Resim işlenirken hata (Sayfa {page_num+1}): {e}")
        
        # Normal metin ve Görselden alınan metni birleştir
        full_text = page_text
        if extracted_tables:
            full_text += "\n" + "".join(extracted_tables)
            
        if full_text.strip():
            docs.append(Document(
                page_content=full_text,
                metadata={"source": str(pdf_path), "page": page_num + 1}
            ))
            
    return docs

def yukle_ve_guncelle():
    rehber_path = Path(REHBER_DIR)
    if not rehber_path.exists():
        logging.error(f"HATA: {REHBER_DIR} klasörü bulunamadı.")
        return

    logging.info("Tarımsal Rehberler klasörü taranıyor...")
    
    tum_docs = []
    
    # 1. Metin Dosyalarını Yükle (.txt)
    txt_loader = DirectoryLoader(REHBER_DIR, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={'autodetect_encoding': True})
    tum_docs.extend(txt_loader.load())
    
    # 2. PDF Dosyalarını Vision (OCR) Destekli Yükle
    pdf_files = list(rehber_path.glob("**/*.pdf"))
    for pdf in pdf_files:
        pdf_docs = process_pdf_with_vision(str(pdf))
        tum_docs.extend(pdf_docs)

    if not tum_docs:
        logging.warning(f"UYARI: {REHBER_DIR} klasöründe okunabilir .txt veya .pdf bulunamadı.")
        return

    logging.info(f"Toplam {len(tum_docs)} adet sayfa (Metin+Tablo) başarıyla çıkarıldı. Bölme işlemine geçiliyor...")

    # Parçalara ayırma (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=250,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    bolunmus_docs = text_splitter.split_documents(tum_docs)

    logging.info(f"Metinler {len(bolunmus_docs)} adet anlamlı parçaya bölündü. Vektör DB (Chroma) oluşturuluyor...")

    # Embeddings (HuggingFace CPU)
    embedder = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2", 
        model_kwargs={"device": "cpu"}
    )
    
    # Chroma'ya ekle
    db = Chroma.from_documents(
        bolunmus_docs, 
        embedder, 
        persist_directory=VECTOR_DB_DIR
    )

    logging.info("BAŞARILI: Tüm rehberler (Resimler ve Tablolar dahil) sisteme (hafızaya) yüklendi ve kullanıma hazır!")

if __name__ == "__main__":
    print("-" * 60)
    print("AgroAskAI - RAG Yukleyici [VISION / OCR DESTEKLI]")
    print("-" * 60)
    yukle_ve_guncelle()
