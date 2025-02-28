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
import queue

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

def process_item(process_item, quantity):
    url = "https://sosyaldigital.com/action/"

    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            print("Yeni Tor devresi oluşturuldu.")
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
                content_encoding = response.headers.get('Content-Encoding')
                decompressed_data = None

                if content_encoding == 'br':
                    try:
                        decompressed_data = brotli.decompress(response.content).decode('utf-8')
                    except brotli.error as e:
                        decompressed_data = response.content.decode('utf-8', errors='ignore')
                elif content_encoding == 'gzip':
                    try:
                        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                            decompressed_data = f.read().decode('utf-8')
                    except Exception as e:
                        decompressed_data = response.content.decode('utf-8', errors='ignore')
                else:
                    decompressed_data = response.text

                if decompressed_data:
                    if "Geçersiz İstek!" in decompressed_data:
                        print("Geçersiz İstek! Yeni IP ve oturumla tekrar deneniyor...")
                        return False
                    match = re.search(r'"freetool_process_token":\s*"([^"]+)"', decompressed_data)
                    if match:
                        token = match.group(1)
                        params["freetool[token]"] = token
                        response2 = session.post(url, data=params, headers=headers, timeout=15)
                        response2.raise_for_status()
                        print("İşlem Başarılı!")
                        return True
                    else:
                        print("Token bulunamadı. Yeni IP ve oturumla tekrar deneniyor...")
                        return False
                else:
                    print("Dekompresyon başarısız. Yeni IP ve oturumla tekrar deneniyor...")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"İstek hatası: {e}. Yeni IP ve oturumla tekrar deneniyor...")
                return False
            except json.JSONDecodeError as e:
                print(f"JSON hatası: {e}. Yeni IP ve oturumla tekrar deneniyor...")
                return False
    except Exception as e:
        print(f"Tor hatası: {e}. Yeni IP ve oturumla tekrar deneniyor...")
        return False

def freetool_islem(process_item, quantity):
    while True:
        if process_item(process_item, quantity):
            time.sleep(random.randint(60, 120))
        else:
            time.sleep(random.randint(180, 240))

process_item = "https://www.youtube.com/live/qrIrwWpMUWI?si=3gcrluOIcYVEW3A0"
quantity = "25"
freetool_islem(process_item, quantity)
