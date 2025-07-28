import base64
import json
import requests
import sys
import urllib3
import os

# Add the 'src' directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from mymodem.login import get_credentials

# pycryptodome veya pycryptodomex ile uyumlu import
try:
    # Eğer pip install pycryptodome kullandıysanız:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    # Eğer pip install pycryptodomex kullandıysanız:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import unpad

# InsecureRequestWarning'ı bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Konfigürasyon
MODEM_URL = "https://192.168.1.1/cgi-bin/DAL?oid=wan"

headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

def decrypt_response(encrypted_content: str, iv_base64: str, aes_key_b64: str):
    """
    Modem'den gelen base64 şifreli içeriği çözer.
    """
    # Base64'ten byte dizilerine dönüştür
    aes_key = base64.b64decode(aes_key_b64)
    iv = base64.b64decode(iv_base64)[:16]

    # Base64 padding düzeltmesi
    pad_len = 4 - len(encrypted_content) % 4
    if pad_len < 4:
        encrypted_content += "=" * pad_len

    # AES CBC ile çözme
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    raw = cipher.decrypt(base64.b64decode(encrypted_content))
    data = unpad(raw, AES.block_size)

    # JSON parse + yazdırma
    try:
        obj = json.loads(data)
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        text = data.decode("utf-8", errors="ignore")
        print(text.replace(",", ",\n").replace('"', ""))


def main():
    print("Giriş bilgileri alınıyor...")
    try:
        # get_credentials artık 3 değer döndürüyor
        session_cookie, zysession_key, aes_key_b64 = get_credentials()
        if not session_cookie or not aes_key_b64:
            print("HATA: Session veya AES anahtarı alınamadı!")
            sys.exit(1)
    except Exception as e:
        print(f"Giriş hatası: {e}")
        sys.exit(1)

    cookies = {"Session": session_cookie}

    print("Modem bilgileri alınıyor...")
    try:
        resp = requests.get(
            MODEM_URL,
            headers=headers,
            cookies=cookies,
            verify=False,
            timeout=15
        )
        resp.raise_for_status()
        j = resp.json()
        print("Veri alındı, çözülüyor...")
        decrypt_response(j["content"], j["iv"], aes_key_b64)
    except requests.exceptions.RequestException as e:
        print(f"Bağlantı hatası: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Veri format hatası: Eksik alan - {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Geçersiz JSON yanıtı alındı")
        sys.exit(1)

if __name__ == "__main__":
    main()
