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
import os
import subprocess

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

def restart_tor():
    try:
        subprocess.run(['sudo', 'service', 'tor', 'restart'], check=True, capture_output=True)
        print("Tor servisi yeniden başlatıldı.")
    except subprocess.CalledProcessError as e:
        print(f"Tor servisi yeniden başlatılamadı: {e.stderr.decode()}")
        return False
    return True

def stop_tor():
    try:
        subprocess.run(['sudo', 'service', 'tor', 'stop'], check=True, capture_output=True)
        print("Tor servisi durduruldu.")
    except subprocess.CalledProcessError as e:
        print(f"Tor servisi durdurulamadı: {e.stderr.decode()}")
        return False
    return True

def clear_cookies_and_cache():
    cookie_file = 'session.cookies'
    cache_file = 'session.cache'
    try:
        if os.path.exists(cookie_file):
            os.remove(cookie_file)
        if os.path.exists(cache_file):
            os.remove(cache_file)
        print("Çerezler ve önbellek temizlendi.")
    except FileNotFoundError:
        print("Çerez veya önbellek dosyası bulunamadı.")
    except Exception as e:
        print(f"Çerez ve önbellek temizlenirken hata oluştu: {e}")

def renew_tor_circuit():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
        print("Yeni Tor devresi oluşturuldu.")
        return True
    except Exception as e:
        print(f"Yeni Tor devresi oluşturulamadı: {e}")
        return False

def process_item_function(process_item_url, quantity, session):
    url = "https://sosyaldigital.com/action/"

    if not renew_tor_circuit():
        print("Tor devresi yenileme başarısız. İşlem durduruluyor.")
        return False

    headers = rastgele_basliklar()
    params = {
        "ns_action": "freetool_start",
        "freetool[id]": "1",
        "freetool[token]": "",
        "freetool[process_item]": process_item_url,
        "freetool[quantity]": quantity
    }
    try:
        print("Birinci İstek Gönderiliyor...")
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

        print(f"Birinci Yanıt: {decompressed_data}")

        if decompressed_data:
            try:
                json_response = json.loads(decompressed_data)
                if json_response.get("statu") == True and json_response.get("alert", {}).get("statu") == "success" and "freetool_process_token" in json_response:
                    token = json_response.get("freetool_process_token")
                    params["freetool[token]"] = token
                    print("Token bulundu, ikinci istek gönderiliyor...")
                    response2 = session.post(url, data=params, headers=headers, timeout=15)
                    response2.raise_for_status()
                    decompressed_data_response2 = response2.text # İkinci yanıt dekompresyonuna gerek yok, text yeterli
                    print(f"İkinci Yanıt: {decompressed_data_response2}")
                    if "İşlem Başarılı!" in decompressed_data_response2:
                        print("İşlem Başarılı!")
                        return True
                    else:
                        print("İkinci istek başarısız oldu: İşlem Başarılı! yanıtı alınamadı.")
                        return False
                else:
                    print("Birinci istek başarısız oldu: statu veya alert.statu veya token eksik.")
                    return False
            except json.JSONDecodeError as e:
                print(f"JSON hatası (Birinci Yanıt): {e}")
                return False

        else:
            print("Birinci Yanıt dekompresyon başarısız.")
            return False

    except requests.exceptions.RequestException as e:
        print(f"İstek hatası: {e}")
        print(f"Hata Yanıtı: {response.text if 'response' in locals() and 'response' in vars() else 'Yanıt alınamadı'}")
        return False
    except Exception as e:
        print(f"Bilinmeyen Hata: {e}")
        return False

def freetool_islem(process_item_url, quantity, repeat_count):
    session = requests.Session()
    session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
    for _ in range(repeat_count):
        while not process_item_function(process_item_url, quantity, session):
            print("İşlem başarısız, tekrar deneniyor...")
            time.sleep(5) # Kısa bir bekleme süresi eklendi
        print("Tekrar sayısı tamamlandı, döngü devam ediyor...")

    print("Tüm tekrarlar tamamlandı.")

process_item_url = "https://youtu.be/7Ja_w0vQhd8?si=o4afyY2k98CCy4m8" # Gerçek bir YouTube URL'si ile değiştirin
quantity = "25"
repeat_count = 10
freetool_islem(process_item_url, quantity, repeat_count)
