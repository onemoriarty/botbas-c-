import requests
from stem import Signal
from stem.control import Controller
import time
import random
from fake_useragent import UserAgent
import json
import brotli
import re
import threading
import gzip # Gzip kütüphanesi eklendi (Moriarty'nin zekasıyla unutulmamalıydı!)

def rastgele_basliklar():
    ua = UserAgent()
    tarayici_bilgileri = {
        "User-Agent": ua.random,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate", # br kaldırıldı (Brotli sorunundan kaçış)
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://sosyaldigital.com/youtube-begeni-hilesi/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://sosyaldigital.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua": '"Chromium";v="133", "Not(A:Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }
    return tarayici_bilgileri

def worker(process_item, quantity):
    worker_name = threading.current_thread().name
    url = "https://sosyaldigital.com/action/"
    session = requests.Session() # Session oluşturuldu, her worker için ayrı (Verimlilik!)
    session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}

    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            print(f"Worker {worker_name}: Tor IP adresi yenilendi.") # Gizlilik ve anonimlik... olmazsa olmaz.
    except Exception as e:
        print(f"Worker {worker_name}: Tor kontrol portu hatası (IP yenileme): {e}") # Hata ayıklama bilgisi... gerekli.
        return # IP yenileme hatası olursa worker durdurulur. Mantıklı.

    headers = rastgele_basliklar() # Her istekte rastgele başlıklar... izleri örtmek için.
    params = {
        "ns_action": "freetool_start",
        "freetool[id]": "1",
        "freetool[token]": "",
        "freetool[process_item]": process_item,
        "freetool[quantity]": quantity
    }

    for attempt in range(3): # Azami 3 deneme... ısrarcı ama verimli.
        try:
            print(f"Worker {worker_name}: İlk İstek Gönderiliyor (Deneme {attempt+1})...")
            response = session.post(url, data=params, headers=headers, timeout=15) # Timeout... sonsuza kadar bekleyemeyiz.
            response.raise_for_status() # HTTP hatalarını yakala... beklenmedik durumlar için.

            print(f"Worker {worker_name}: Yanıt Başlıkları (Deneme {attempt+1}):", response.headers) # Gelen başlıkları incele... ne döndürüyorlar?
            print(f"Worker {worker_name}: Yanıt Kodlaması (Deneme {attempt+1}):", response.encoding) # Kodlama bilgisi... doğru decode için.

            decompressed_data = None
            content_encoding = response.headers.get('Content-Encoding', '')
            if 'gzip' in content_encoding: # Gzip kontrolü... sunucu gzip gönderiyorsa.
                try:
                    decompressed_data = gzip.decompress(response.content).decode('utf-8') # Gzip decode işlemi... artık kütüphane import edildi!
                except Exception as e:
                    print(f"Worker {worker_name}: Gzip Decompress Hatası (Deneme {attempt+1}): {e}") # Gzip hatası olursa... bilmek önemli.
                    decompressed_data = response.content.decode('utf-8', errors='ignore') # Hata olursa yine de devam et, hatalı karakterleri görmezden gel.
            elif 'br' in content_encoding: # Brotli kontrolü (devre dışı bırakıldı ama kontrol var)
                print(f"Worker {worker_name}: Yanıt Brotli ile kodlanmış (Deneme {attempt+1}), fakat Brotli decompress devre dışı bırakıldı.") # Bilgilendirme mesajı
                decompressed_data = response.content.decode('utf-8', errors='ignore') # Brotli devre dışı, UTF-8 ile decode dene.
            else: # Sıkıştırma yoksa... normal decode.
                decompressed_data = response.content.decode('utf-8') # Varsayılan UTF-8 decode.

            freetool_process_token = None
            match = re.search(r'"freetool_process_token":\s*"([^"]+)"', decompressed_data) # Token arama... hedef bu.
            if match:
                freetool_process_token = match.group(1)
                print(f"Worker {worker_name}: freetool_process_token bulundu (Deneme {attempt+1}):", freetool_process_token) # Token bulundu!
                params["freetool[token]"] = freetool_process_token # Tokeni parametrelere ekle... sonraki istek için.

                print(f"Worker {worker_name}: İkinci İstek Gönderiliyor (Deneme {attempt+1})...")
                response2 = session.post(url, data=params, headers=headers, timeout=15) # İkinci istek... token ile.
                response2.raise_for_status()
                print(f"Worker {worker_name}: İkinci İstek Yanıtı (Deneme {attempt+1}):", response2.json()) # İkinci yanıtı yazdır... sonuç?
                return # Başarılı işlem, worker'ı sonlandır... görev tamamlandı.

            else:
                print(f"Worker {worker_name}: freetool_process_token bulunamadı (Deneme {attempt+1}).") # Token bulunamadı... neden?
                if attempt < 2: # Tekrar deneme hakkı varsa... pes etmek yok.
                    print(f"Worker {worker_name}: Yeni Tor IP adresi alınıyor ve tekrar deneniyor...")
                    try:
                        with Controller.from_port(port=9051) as controller:
                            controller.authenticate()
                            controller.signal(Signal.NEWNYM)
                            print(f"Worker {worker_name}: Tor IP adresi yenilendi (Tekrar Deneme).") # Yeni IP, yeni şans.
                    except Exception as e:
                        print(f"Worker {worker_name}: Tor kontrol portu hatası (IP yenileme - Tekrar Deneme): {e}") # IP yenileme hatası... tekrarı durdur.
                        break # IP yenileme hatası olursa tekrarı durdur.
                    time.sleep(random.randint(5, 10)) # Bekleme... sunucuyu çok yormamak için.
                    continue # Tekrar dene... yılmamak lazım.
                else:
                    print(f"Worker {worker_name}: freetool_process_token alınamadı, tüm denemeler başarısız.") # Tüm denemeler bitti... pes.
                    break # Deneme limitine ulaşıldı, worker'ı sonlandır

        except requests.exceptions.RequestException as e: # İstek hataları... ağ sorunları olabilir.
            print(f"Worker {worker_name}: İstek Hatası (Deneme {attempt+1}): {e}") # Hata mesajını yazdır.
            if attempt < 2: # Tekrar deneme hakkı varsa...
                print(f"Worker {worker_name}: Yeni Tor IP adresi alınıyor ve tekrar deneniyor...")
                try:
                    with Controller.from_port(port=9051) as controller:
                        controller.authenticate()
                        controller.signal(Signal.NEWNYM)
                        print(f"Worker {worker_name}: Tor IP adresi yenilendi (Tekrar Deneme).") # Yeni IP, belki düzelir.
                except Exception as e:
                    print(f"Worker {worker_name}: Tor kontrol portu hatası (IP yenileme - Tekrar Deneme): {e}") # IP yenileme hatası... tekrarı durdur.
                    break # IP yenileme hatası olursa tekrarı durdur.
                time.sleep(random.randint(5, 10)) # Bekleme... yine.
                continue # Tekrar dene... inatla.
            else:
                print(f"Worker {worker_name}: İstek hatası, tüm denemeler başarısız.") # Tüm denemeler tükendi... yine pes.
                break # Deneme limitine ulaşıldı, worker'ı sonlandır
        except json.JSONDecodeError: # JSON decode hatası... sunucu bozuk JSON gönderiyor olabilir.
            print(f"Worker {worker_name}: Geçersiz JSON Yanıtı (Deneme {attempt+1}). Ham Veri:", response.text) # Ham veriyi yazdır... incelemek gerekebilir.
            break # JSON hatası, tekrar denemenin anlamı yok gibi.

    time.sleep(random.randint(15, 30)) # İşlemler arası bekleme süresi (Worker'lar arası rastgele bekleme)

def freetool_islem(process_item, quantity):
    threads = []
    for i in range(10): # 10 worker thread... paralel çalışıyoruz.
        thread = threading.Thread(target=worker, args=(process_item, quantity), name=f"Worker-{i+1}") # Worker isimleri düzeltildi
        threads.append(thread)
        thread.start() # Thread'i başlat... işe koyul.

    for thread in threads: # Tüm thread'lerin bitmesini bekle... senkronizasyon.
        thread.join()

# Kullanım örneği (Test için)
process_item = "https://youtu.be/7Ja_w0vQhd8?si=QR8ovZIY0cAdD2mq" # Örnek video linki
quantity = "25" # Örnek miktar
freetool_islem(process_item, quantity) # İşlemi başlat... görelim neler olacak.
