import requests
from stem import Signal
from stem.control import Controller
import time
import random
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def rastgele_basliklar():
    ua = UserAgent()
    tarayici_bilgileri = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "tr-TR,tr;q=0.9"]),
        "Referer": random.choice(["https://www.google.com/", "https://www.example.com/"])
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
                except requests.exceptions.RequestException as e:
                    print(f"Tor üzerinden istek hatası: {e}")
                except ValueError:
                    print("Tor üzerinden geçersiz JSON yanıtı.")
                time.sleep(random.randint(45, 75))  # Rastgele bekleme süresi
    except Exception as e:
        print(f"Tor kontrol portu hatası: {e}")

# Kullanım örneği
process_item = "https://youtu.be/DuPrA9dWRb4?si=IzkQynxkssoXuzQH"
quantity = "25"
freetool_islem(process_item, quantity)
