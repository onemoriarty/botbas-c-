import time
import random
import requests
from fake_useragent import UserAgent
import json
import subprocess
import signal
import os

# Rotating user agent for better anonymity
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

# Restart Tor service with careful handling
def restart_tor():
    try:
        subprocess.run(['sudo', 'service', 'tor', 'restart'], check=True, capture_output=True)
        print("Tor servisi yeniden başlatıldı.")
        time.sleep(random.randint(10, 15))  # Randomized delay
    except subprocess.CalledProcessError as e:
        print(f"Tor servisi yeniden başlatılamadı: {e.stderr.decode()}")
        return False
    return True

# Stop Tor service with error handling
def stop_tor():
    try:
        subprocess.run(['sudo', 'service', 'tor', 'stop'], check=True, capture_output=True)
        print("Tor servisi durduruldu.")
    except subprocess.CalledProcessError as e:
        print(f"Tor servisi durdurulamadı: {e.stderr.decode()}")
        return False
    return True

# Kill the Tor process if necessary to renew the circuit
def kill_tor():
    try:
        pid_process = subprocess.run(['pidof', 'tor'], capture_output=True, text=True, check=True)
        pid = pid_process.stdout.strip()
        if pid:
            os.kill(int(pid), signal.SIGKILL)
            print(f"Tor process (PID {pid}) killed.")
            time.sleep(random.randint(5, 10))  # Random sleep after killing
            return True
        else:
            print("Tor process PID not found.")
            return False
    except Exception as e:
        print(f"Error killing Tor process: {e}")
        return False

# Renew Tor circuit and add randomized delays
def renew_tor_circuit(session):
    max_retries = 3
    for retry in range(max_retries):
        initial_ip = get_current_ip(session)
        print(f"Devre yenileme denemesi {retry + 1}/{max_retries}: Başlangıç IP: {initial_ip}")
        
        try:
            stop_tor()
            kill_tor()
            restart_tor()
            clear_cookies_and_cache()  # Ensure old session data is cleaned
            time.sleep(random.randint(15, 20))  # Random delay for more natural behavior

            new_ip = get_current_ip(session)
            print(f"Yeni IP: {new_ip}")
            if new_ip != initial_ip:
                print(f"Yeni Tor devresi oluşturuldu: {initial_ip} -> {new_ip}")
                return True
            else:
                print(f"IP değişmedi, devre yenileme başarısız.")
        except Exception as e:
            print(f"Tor devresi yenileme başarısız: {e}")
    
    return False

# Get the current IP address using a reliable service
def get_current_ip(session):
    try:
        response = session.get("http://httpbin.org/ip", timeout=10)
        response.raise_for_status()
        ip_json = json.loads(response.text)
        return ip_json.get("origin", "IP alınamadı")
    except requests.exceptions.RequestException as e:
        print(f"IP adresi kontrol hatası: {e}")
        return "IP alınamadı"

# Clear cookies and cache to ensure fresh requests
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

# Main function to handle the process with intelligent retries and handling
def process_item_function(process_item_url, quantity):
    url = "https://sosyaldigital.com/action/"
    session = requests.Session()
    session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
    
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

        if content_encoding == 'gzip':
            decompressed_data = response.content.decode('utf-8', errors='ignore')
        else:
            decompressed_data = response.text

        print(f"Birinci Yanıt: {decompressed_data}")

        if decompressed_data:
            try:
                json_response = json.loads(decompressed_data)
                if json_response.get("statu") == True and json_response.get("alert", {}).get("statu") == "danger":
                    print("Hata: Çok sık istek yapıldı. Tor devresi yenileniyor...")
                    if not renew_tor_circuit(session):
                        print("Tor devresi yenileme başarısız.")
                        return False
                    else:
                        return False
                else:
                    print("Birinci istek başarılı.")
                    return True
            except json.JSONDecodeError:
                print("JSON hatası.")
                return False

    except requests.exceptions.RequestException as e:
        print(f"İstek hatası: {e}")
        return False

# Retry the process with intelligent delays
def freetool_islem(process_item_url, quantity, repeat_count):
    for attempt in range(repeat_count):
        print(f"İşlem {attempt + 1}/{repeat_count} başlatılıyor...")
        success = process_item_function(process_item_url, quantity)
        if not success:
            print("İşlem başarısız, yeniden deneniyor...")
            time.sleep(random.randint(5, 10))  # Randomized retry delay
        else:
            print("İşlem başarıyla tamamlandı.")

process_item_url = "https://youtu.be/7Ja_w0vQhd8?si=o4afyY2k98CCy4m8"  # Gerçek bir YouTube URL'si ile değiştirin
quantity = "25"
repeat_count = 5
freetool_islem(process_item_url, quantity, repeat_count)
