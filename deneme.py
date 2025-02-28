import requests
from stem import Signal
from stem.control import Controller

def freetool_islem(process_item, quantity):
    url = "https://sosyaldigital.com/action/"

    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()  # CookieAuthentication kullanıldığında şifre gerekmez
            controller.signal(Signal.NEWNYM)

        session = requests.session()
        session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        params = {
            "ns_action": "freetool_start",
            "freetool[id]": "1",
            "freetool[token]": "",
            "freetool[process_item]": process_item,
            "freetool[quantity]": quantity
        }

        response = session.post(url, data=params, headers=headers)
        response.raise_for_status()
        veri = response.json()

        print("Tor üzerinden İlk İstek Yanıtı:", veri)

        if veri.get("statu") == True and veri.get("freetool_process_token"):
            if veri.get("alert") and veri["alert"].get("statu") == "success":
                token = veri["freetool_process_token"]
                params["freetool[token]"] = token
                response2 = session.post(url, data=params, headers=headers)
                response2.raise_for_status()
                print("Tor üzerinden İkinci İstek Yanıtı:", response2.json())
            else:
                print("Tor üzerinden İlk istekte işlem başarısız oldu: ", veri.get("alert"))
        else:
            print("Tor üzerinden İlk istekte 'freetool_process_token' bulunamadı veya 'statu' false.")

    except requests.exceptions.RequestException as e:
        print(f"Tor üzerinden hata oluştu: {e}")
    except ValueError:
        print("Tor üzerinden geçersiz JSON yanıtı.")
    except Exception as e:
        print(f"Tor kontrol portu hatası: {e}")

# Kullanım örneği
process_item = "https://youtu.be/DuPrA9dWRb4?si=IzkQynxkssoXuzQH"
quantity = "25"

freetool_islem(process_item, quantity)
