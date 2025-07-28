import requests
import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import urllib3
import os
import sys

# Add the 'src' directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from mymodem.login import get_credentials

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔹 Modem IP Adresi
MODEM_IP = "192.168.1.1"

# --- Login ---
session_cookie, zysession_key, AES_KEY_B64 = get_credentials()
cookies = {"Session": session_cookie}

# 🔹 HTTP Başlıkları
headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/133.0"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"https://{MODEM_IP}/",
    "Origin": f"https://{MODEM_IP}",
    "Host": MODEM_IP,
    "CsrfToken": zysession_key,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}



# 🔹 Attack: False olacak JSON

json_data = {

  "EnableCWMP":True,

  "URL":"http://cwmp-devreha-dm-uce4713.acs.tr069.pro",

  "Username":"superadmin",

  "Password":"jDKHoThc3d4YTO3Vr2ya",

  "ConnectionRequestUsername":"superadmin",

  "ConnectionRequestPassword":"jDKHoThc3d4YTO3Vr2ya",

  "PeriodicInformEnable":True,

  "PeriodicInformInterval":86400,

  "PeriodicInformTime":"0001-01-01T00:00:00Z",

  "X_ZYXEL_ActiveNotifyUpdateInterval":30,

  "DebugLevelEnable":13,

  "FetureOptionEnable":2,

  "X_ZYXEL_ConnectionRequestPort":7547,

  "IPv6_Enable":False,

  "IPv4_Enable":True,

  "DisplaySOAP":False,

  "EnableAuthentication":None,

  "BoundInterfaceMode":"Multi_WAN",

  "BoundInterfaceList":"IP.Interface.2,IP.Interface.3",

  "ConnectionRequestURL":"",

  "CheckCert":False,

  "DataModelSpec":"TR-098",

  "Certificate":0,



}







# 🔹 Yeni IV Al

def get_iv():

  response = requests.get(

        f"https://{MODEM_IP}/cgi-bin/",

    headers=headers,

    cookies=cookies,

    verify=False

  )

  if response.status_code == 200:

    data = response.json()

    if "iv" in data:

      iv = data["iv"]

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

  decrypted_bytes = unpad(cipher.decrypt(base64.b64decode(encrypted_content)), AES.block_size)

   

  decrypted_json = decrypted_bytes.decode("utf-8")

  print("\n✅ **Şifre Çözüldü!**")

  print(decrypted_json)



  # **Yeni Session Key'i çek**

  try:

    response_dict = json.loads(decrypted_json)

    if "sessionkey" in response_dict:

      new_session_key = response_dict["sessionkey"]

      print(f"\n🔑 **Yeni SessionKey:** {new_session_key}")

      return new_session_key

  except json.JSONDecodeError:

    print("\n❌ **Hata: Yanıt JSON formatında değil!**")

  return None



# 🔹 IV Al

iv_base64 = get_iv()

if not iv_base64:

  exit()



# 🔹 JSON'u Şifrele

encrypted_content = encrypt_data(json_data, iv_base64)



# 🔹 Modeme Güncellenmiş Attack: False isteği gönder

payload = {

  "content": encrypted_content,

  "iv": iv_base64

}

print(payload)



print("\n📡 **Modeme Güncellenmiş İstek Gönderiliyor...**")

response = requests.put(

    f"https://{MODEM_IP}/cgi-bin/DAL?oid=tr69",

  headers=headers,

  cookies=cookies,

  json=payload,

  verify=False

)



if response.status_code == 200:

  try:

    # Yanıt JSON formatında ve şifrelenmiş geliyor

    response_data = response.json()

    encrypted_content = response_data["content"]

    iv_base64 = response_data["iv"]



    # Şifre çözüp yeni sessionKey alalım

    new_session_key = decrypt_response(encrypted_content, iv_base64)
    
    # Yeni session key başarıyla alındıysa kullanıcıya bildir
    if new_session_key:
        print("\n✅ **İşlem Başarılı:** TR069 ayarları güncellendi ve yeni bir session key alındı.")
        print("🔔 **Bilgi:** Yeni session key'i gelecek istekler için kullanabilirsiniz.")
    else:
        print("\n❌ **Uyarı:** TR069 ayarları güncellenmiş olabilir ancak yeni session key alınamadı.")

  except json.JSONDecodeError:

    print("\n❌ **Hata: Yanıt JSON formatında değil!**")

else:

  print(f"\n❌ **Hata! HTTP Kodu:** {response.status_code}")

  print(response.text)