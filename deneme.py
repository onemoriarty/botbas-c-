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

def rastgele_basliklar():
    ua = UserAgent()
    tarayici_bilgileri = {
        "User-Agent": ua.random,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
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
    session = requests.Session() # Session oluşturuldu, her worker için ayrı
    session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}

    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            print(f"Worker {worker_name}: Tor IP adresi yenilendi.")
    except Exception as e:
        print(f"Worker {worker_name}: Tor kontrol portu hatası (IP yenileme): {e}")
        return # IP yenileme hatası olursa worker durdurulur.

    headers = rastgele_basliklar()
    params = {
        "ns_action": "freetool_start",
        "freetool[id]": "1",
        "freetool[token]": "",
        "freetool[process_item]": process_item,
        "freetool[quantity]": quantity
    }

    for attempt in range(3): # İstekler için tekrar deneme mekanizması
        try:
            print(f"Worker {worker_name}: İlk İstek Gönderiliyor (Deneme {attempt+1})...")
            response = session.post(url, data=params, headers=headers, timeout=15)
            response.raise_for_status() # Hatalı HTTP durum kodları için hata yükselt

            print(f"Worker {worker_name}: Yanıt Başlıkları (Deneme {attempt+1}):", response.headers)
            print(f"Worker {worker_name}: Yanıt Kodlaması (Deneme {attempt+1}):", response.encoding)

            decompressed_data = None
            try:
                if response.headers.get('Content-Encoding') == 'br':
                    decompressed_data = brotli.decompress(response.content).decode('utf-8')
                else:
                    decompressed_data = response.content.decode('utf-8')
            except brotli.error as e:
                print(f"Worker {worker_name}: Brotli Decompress Hatası (Deneme {attempt+1}): {e}")
                decompressed_data = response.content.decode('utf-8', errors='ignore') # Brotli hatasında bile devam et

            freetool_process_token = None
            match = re.search(r'"freetool_process_token":\s*"([^"]+)"', decompressed_data)
            if match:
                freetool_process_token = match.group(1)
                print(f"Worker {worker_name}: freetool_process_token bulundu (Deneme {attempt+1}):", freetool_process_token)
                params["freetool[token]"] = freetool_process_token

                print(f"Worker {worker_name}: İkinci İstek Gönderiliyor (Deneme {attempt+1})...")
                response2 = session.post(url, data=params, headers=headers, timeout=15)
                response2.raise_for_status()
                print(f"Worker {worker_name}: İkinci İstek Yanıtı (Deneme {attempt+1}):", response2.json())
                return # Başarılı işlem, worker'ı sonlandır

            else:
                print(f"Worker {worker_name}: freetool_process_token bulunamadı (Deneme {attempt+1}).")
                if attempt < 2: # 3 deneme hakkı
                    print(f"Worker {worker_name}: Yeni Tor IP adresi alınıyor ve tekrar deneniyor...")
                    try:
                        with Controller.from_port(port=9051) as controller:
                            controller.authenticate()
                            controller.signal(Signal.NEWNYM)
                            print(f"Worker {worker_name}: Tor IP adresi yenilendi (Tekrar Deneme).")
                    except Exception as e:
                        print(f"Worker {worker_name}: Tor kontrol portu hatası (IP yenileme - Tekrar Deneme): {e}")
                        break # IP yenileme hatası olursa tekrarı durdur.
                    time.sleep(random.randint(5, 10)) # Tekrar denemeden önce bekle
                    continue # Tekrar dene
                else:
                    print(f"Worker {worker_name}: freetool_process_token alınamadı, tüm denemeler başarısız.")
                    break # Deneme limitine ulaşıldı, worker'ı sonlandır

        except requests.exceptions.RequestException as e:
            print(f"Worker {worker_name}: İstek Hatası (Deneme {attempt+1}): {e}")
            if attempt < 2:
                print(f"Worker {worker_name}: Yeni Tor IP adresi alınıyor ve tekrar deneniyor...")
                try:
                    with Controller.from_port(port=9051) as controller:
                        controller.authenticate()
                        controller.signal(Signal.NEWNYM)
                        print(f"Worker {worker_name}: Tor IP adresi yenilendi (Tekrar Deneme).")
                except Exception as e:
                    print(f"Worker {worker_name}: Tor kontrol portu hatası (IP yenileme - Tekrar Deneme): {e}")
                    break # IP yenileme hatası olursa tekrarı durdur.
                time.sleep(random.randint(5, 10))
                continue # Tekrar dene
            else:
                print(f"Worker {worker_name}: İstek hatası, tüm denemeler başarısız.")
                break # Deneme limitine ulaşıldı, worker'ı sonlandır
        except json.JSONDecodeError:
            print(f"Worker {worker_name}: Geçersiz JSON Yanıtı (Deneme {attempt+1}). Ham Veri:", response.text)
            break # JSON hatası, tekrar denemenin anlamı yok gibi.

    time.sleep(random.randint(15, 30)) # İşlemler arası bekleme süresi azaltıldı, zaten worker içinde uyuyor.

def freetool_islem(process_item, quantity):
    threads = []
    for i in range(10):
        thread = threading.Thread(target=worker, args=(process_item, quantity), name=f"Worker-{i+1}") # Worker isimleri düzeltildi
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

# Kullanım örneği
process_item = "https://youtu.be/7Ja_w0vQhd8?si=QR8ovZIY0cAdD2mq"
quantity = "25"
freetool_islem(process_item, quantity)
