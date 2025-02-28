import requests

def freetool_islem(process_item, quantity):
    url = "https://sosyaldigital.com/action/"

    # Çerezleri engelleme ve oturum oluşturma
    session = requests.Session()
    session.cookies.clear()

    # Başlıkları ayarlama (Brave'in kalkanlarına benzer)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        # Gerekli diğer başlıkları buraya ekleyin
    }

    params = {
        "ns_action": "freetool_start",
        "freetool[id]": "1",
        "freetool[token]": "",
        "freetool[process_item]": process_item,
        "freetool[quantity]": quantity
    }

    try:
        response = session.post(url, data=params, headers=headers)
        response.raise_for_status()
        veri = response.json()

        print("İlk İstek Yanıtı:", veri)

        if veri.get("statu") == True and veri.get("freetool_process_token"):
            if veri.get("alert") and veri["alert"].get("statu") == "success":
                token = veri["freetool_process_token"]
                params["freetool[token]"] = token
                response2 = session.post(url, data=params, headers=headers)
                response2.raise_for_status()
                print("İkinci İstek Yanıtı:", response2.json())
            else:
                print("İlk istekte işlem başarısız oldu: ", veri.get("alert"))
        else:
            print("İlk istekte 'freetool_process_token' bulunamadı veya 'statu' false.")

    except requests.exceptions.RequestException as e:
        print(f"Hata oluştu: {e}")
    except ValueError:
        print("Geçersiz JSON yanıtı.")

# Kullanım örneği
process_item = "https://youtu.be/DuPrA9dWRb4?si=IzkQynxkssoXuzQH"
quantity = "25"

freetool_islem(process_item, quantity)
