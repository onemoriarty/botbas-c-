import requests
from stem import Signal
from stem.control import Controller
import time
import random
from fake_useragent import UserAgent
import json
import brotli
import re

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

def freetool_islem(process_item, quantity):
    url = "https://sosyaldigital.com/action/"

    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            while True:
                controller.signal(Signal.NEWNYM)
                print("Tor IP adresi yenilendi.")
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
                    print("Yanıt Başlıkları:", response.headers)
                    print("Yanıt Kodlaması:", response.encoding)
                    if response.headers.get('Content-Encoding') == 'br':
                        try:
                            decompressed_data = brotli.decompress(response.content).decode('utf-8')
                        except brotli.error as e:
                            print(f"Tor kontrol portu hatası: {e}")
                            decompressed_data = response.content.decode('utf-8', errors='ignore') # hatalı veriyi yok say
                        match = re.search(r'"freetool_process_token":\s*"([^"]+)"', decompressed_data)
                        if match:
                            token = match.group(1)
                            print("freetool_process_token bulundu:", token)
                            params["freetool[token]"] = token
                            response2 = session.post(url, data=params, headers=headers, timeout=15)
                            response2.raise_for_status()
                            print("Tor üzerinden İkinci İstek Yanıtı:", response2.json())
                        else:
                            print("freetool_process_token bulunamadı.")
                    else:
                        try:
                            veri = response.json()
                            print("Tor üzerinden İlk İstek Yanıtı:", veri)
                            if veri.get("statu") == True and veri.get("freetool_process_token"):
                                if veri.get("alert") and veri["alert"].get("statu") == "success":
                                    token = veri["freetool_process_token"]
                                    params["freetool[token]"] = token
                                    response2 = session.post(url, data=params, headers=headers, timeout=15)
                                    response2.raise_for_status()
                                    print("Tor üzerinden İkinci İstek Yanıtı:", response2.json())
                                else:
                                    print("Tor üzerinden İlk istekte işlem başarısız oldu: ", veri.get("alert"))
                            else:
                                print("Tor üzerinden İlk istekte 'freetool_process_token' bulunamadı veya 'statu' false.")
                        except json.JSONDecodeError:
                            print("Tor üzerinden geçersiz JSON yanıtı. Ham Veri:", response.text)
                except requests.exceptions.RequestException as e:
                    print(f"Tor üzerinden istek hatası: {e}")
                time.sleep(random.randint(45, 75))  # Rastgele bekleme süresi
    except Exception as e:
        print(f"Tor kontrol portu hatası: {e}")

# Kullanım örneği
process_item = "https://googleusercontent.com/youtube.com/3/DuPrA9dWRb4?si=IzkQynxkssoXuzQH"
quantity = "25"
freetool_islem(process_item, quantity)
