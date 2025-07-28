import os
import re
import json
import base64
import requests
import urllib3
from login import get_credentials

# pycryptodome veya cryptodomex uyumlu import
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import unpad

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sabitler
MODEM_IP   = "192.168.1.1"
URLS_FILE  = "cgi-bin-urls.txt"
OUTPUT_DIR = "decoded_responses"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def sanitize_filename(url: str) -> str:
    """URL'den dosya adı oluşturur."""
    name = url.split("/cgi-bin/")[-1]
    name = re.sub(r'[^\w\-]', '_', name)
    return name or 'root'


def decrypt_response(encrypted_content: str, iv_base64: str, aes_key_b64: str) -> str:
    """Encrypted içeriği AES-CBC ile çözer ve metin olarak döner."""
    # AES anahtarı ve IV decode
    key = base64.b64decode(aes_key_b64)
    iv  = base64.b64decode(iv_base64)[:16]
    # Base64 padding düzeltme
    pad_len = len(encrypted_content) % 4
    if pad_len:
        encrypted_content += '=' * (4 - pad_len)
    data = base64.b64decode(encrypted_content)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(data), AES.block_size)
    return decrypted.decode('utf-8', errors='ignore')


def main():
    # 1) Login bilgilerini al
    print('Giriş bilgileri alınıyor...')
    try:
        session_cookie, zysession_key, aes_key_b64 = get_credentials()
    except Exception as e:
        print(f'❌ Giriş hatası: {e}')
        return

    cookies = {'Session': session_cookie}
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
        'X-Requested-With': 'XMLHttpRequest'
    }

    # 2) URL listesini oku
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    # 3) Her URL için istek yap ve decrypt et
    for url in urls:
        full = f'https://{MODEM_IP}{url}'
        try:
            resp = requests.get(full, headers=headers, cookies=cookies, verify=False)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f'❌ Hata {full}: {e}')
            continue

        if 'content' in data and 'iv' in data:
            decrypted = decrypt_response(data['content'], data['iv'], aes_key_b64)
            fname = sanitize_filename(url) + '.txt'
            path = os.path.join(OUTPUT_DIR, fname)
            with open(path, 'w', encoding='utf-8') as out:
                out.write(decrypted)
            print(f'✅ {url} -> {path}')
        else:
            print(f'⚠️  {url} yanıtında content/iv yok')

if __name__ == '__main__':
    main()
