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
import gzip
from io import BytesIO

def rastgele_basliklar():
    ua = UserAgent()
    return {
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

def worker(process_item, quantity, worker_id):
    url = "https://sosyaldigital.com/action/"
    max_attempts = 5
    attempt = 0

    while True:
        attempt += 1
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                print(f"Worker {worker_id}: Tor IP adresi yenilendi (Deneme {attempt}).")
                session = requests.Session()
                session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
                headers = rastgele_basliklar()
                params = {
                    "ns_action": "freetool_start",
                    "freetool[id]": "1",
                    "freetool[token]": "",
                    "freetool[process_item]": process_item,
                    "freetool[quantity]": quantity
                }
                try:
                    response = session.post(url, data=params, headers=headers, timeout=15)
                    response.raise_for_status()
                    print(f"Worker {worker_id}: Yanıt Başlıkları (Deneme {attempt}): {response.headers}")
                    print(f"Worker {worker_id}: Yanıt Kodlaması (Deneme {attempt}): {response.encoding}")

                    content_encoding = response.headers.get('Content-Encoding')
                    decompressed_data = None

                    if content_encoding == 'br':
                        try:
                            decompressed_data = brotli.decompress(response.content).decode('utf-8')
                        except brotli.error as e:
                            print(f"Worker {worker_id}: Brotli Decompress Hatası (Deneme {attempt}): {e}")
                            print(f"Worker {worker_id}: Ham Veri (Deneme {attempt}): {response.content}")
                            decompressed_data = response.content.decode('utf-8', errors='ignore')
                    elif content_encoding == 'gzip':
                        try:
                            with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                                decompressed_data = f.read().decode('utf-8')
                        except Exception as e:
                            print(f"Worker {worker_id}: Gzip Decompress Hatası (Deneme {attempt}): {e}")
                            decompressed_data = response.content.decode('utf-8', errors='ignore')
                    else:
                        decompressed_data = response.text

                    if decompressed_data:
                        if "Geçersiz İstek!" in decompressed_data:
                            print(f"Worker {worker_id}: Geçersiz İstek! Tekrar deneniyor... (Deneme {attempt})")
                            time.sleep(random.randint(120, 180))  # Daha uzun bekleme süresi
                            continue
                        match = re.search(r'"freetool_process_token":\s*"([^"]+)"', decompressed_data)
                        if match:
                            token = match.group(1)
                            print(f"Worker {worker_id}: freetool_process_token bulundu: {token} (Deneme {attempt})")
                            params["freetool[token]"] = token
                            response2 = session.post(url, data=params, headers=headers, timeout=15)
                            response2.raise_for_status()
                            print(f"Worker {worker_id}: Tor üzerinden İkinci İstek Yanıtı: {response2.json()} (Deneme {attempt})")
                            time.sleep(random.randint(45,75))
                        else:
                            print(f"Worker {worker_id}: freetool_process_token bulunamadı (Deneme {attempt}).")
                            time.sleep(random.randint(45,75))
                    else:
                        print(f"Worker {worker_id}: Dekompresyon başarısız, ham veri işlenemedi (Deneme {attempt}).")
                        time.sleep(random.randint(45,75))
                except requests.exceptions.RequestException as e:
                    print(f"Worker {worker_id}: İstek Hatası (Deneme {attempt}): {e}")
                    time.sleep(random.randint(45,75))
                except json.JSONDecodeError as e:
                    print(f"Worker {worker_id}: JSON Decode Hatası (Deneme {attempt}): {e}")
                    print(f"Worker {worker_id}: Ham Veri (Deneme {attempt}): {response.text}")
                    time.sleep(random.randint(45,75))
        except Exception as e:
            print(f"Worker {worker_id}: Tor Kontrol Portu Hatası (Deneme {attempt}): {e}")
            time.sleep(random.randint(45,75))

def freetool_islem(process_item, quantity):
    threads = []
    for i in range(10):
        thread = threading.Thread(target=worker, args=(process_item, quantity, f"Worker-{i+1}"))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

process_item = "https://youtu.be/7Ja_w0vQhd8?si=1NL8eGdLuGiDjggo"
quantity = "25"
freetool_islem(process_item, quantity)
