import requests
import base64
import json
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
import logging
from typing import Optional, Dict, Any
import urllib3
import os
import sys

# Add the 'src' directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from mymodem.login import get_credentials

# Kendinden imzalı sertifikalar için uyarıları bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModemLogger:
    def __init__(self, modem_ip: str, session_cookie: str, zysession_key: str, aes_key_b64: str):
        self.MODEM_IP = modem_ip
        self.cookies = {"Session": session_cookie}
        self.zysession_key = zysession_key
        self.AES_KEY_B64 = aes_key_b64
        
        # Validate inputs
        if not all([modem_ip, session_cookie, zysession_key, aes_key_b64]):
            raise ValueError("All authentication parameters must be provided")

        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://{self.MODEM_IP}/LogSetting",
            "Origin": f"https://{self.MODEM_IP}",
            "Host": self.MODEM_IP,
            "CsrfToken": self.zysession_key,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }

        self.json_data = {
            "Enable": True,
            "LogMode": "Local",
            "LogServer": "",
            "UDPPort": 514,
            "Interval": 60,
            "MailEnable": False,
            "MailTo": "",
            "MailSubject": "",
            "MailRef": "",
            "AlarmTo": "",
            "AlarmSubject": "",
            "WAN-DHCP": True,
            "DHCP Server": True,
            "PPPoE": True,
            "TR-069": True,
            "HTTP": True,
            "UPNP": True,
            "System": True,
            "ACL": True,
            "Wireless": True,
            "Voice": True,
            "MESH": True,
            "IGMP": True,
            "Account": True,
            "Attack": True,
            "Firewall": True,
            "MAC Filter": True,
            "systemLog": [
                "WAN-DHCP", "DHCP Server", "PPPoE", "TR-069", "HTTP", "UPNP",
                "System", "ACL", "Wireless", "Voice", "MESH", "IGMP"
            ],
            "securityLog": [
                "Account", "Attack", "Firewall", "MAC Filter"
            ]
        }

    def get_iv(self) -> Optional[str]:
        try:
            response = requests.get(
                f"https://{self.MODEM_IP}/cgi-bin/DAL?oid=logset",
                headers=self.headers,
                cookies=self.cookies,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            data = response.json()
            iv = data.get("iv")
            if iv:
                logger.info(f"New IV received: {iv[:8]}...")
                return iv
            logger.error("IV not found in response")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get IV: {e}")
            return None

    def encrypt_data(self, data: Dict[str, Any], iv: str) -> Optional[str]:
        try:
            aes_key = base64.b64decode(self.AES_KEY_B64)
            iv_decoded = base64.b64decode(iv)[:16]
            json_string = json.dumps(data, separators=(",", ":"))
            cipher = AES.new(aes_key, AES.MODE_CBC, iv_decoded)
            encrypted_data = cipher.encrypt(pad(json_string.encode(), AES.block_size))
            return base64.b64encode(encrypted_data).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def decrypt_response(self, encrypted_content: str, iv_base64: str) -> Optional[str]:
        try:
            aes_key = base64.b64decode(self.AES_KEY_B64)
            iv = base64.b64decode(iv_base64)[:16]
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted_bytes = unpad(cipher.decrypt(base64.b64decode(encrypted_content)), AES.block_size)
            decrypted_json = decrypted_bytes.decode("utf-8")
            logger.info("Successfully decrypted response")
            response_dict = json.loads(decrypted_json)
            new_session_key = response_dict.get("sessionkey")
            if new_session_key:
                logger.info(f"New session key received: {new_session_key[:8]}...")
                return new_session_key
            logger.error("Session key not found in response")
            return None
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def update_logs(self) -> bool:
        iv_base64 = self.get_iv()
        if not iv_base64:
            return False
        encrypted_content = self.encrypt_data(self.json_data, iv_base64)
        if not encrypted_content:
            return False
        payload = {"content": encrypted_content, "iv": iv_base64}
        try:
            logger.info("Sending updated request to modem...")
            response = requests.put(
                f"https://{self.MODEM_IP}/cgi-bin/DAL?oid=logset",
                headers=self.headers,
                cookies=self.cookies,
                json=payload,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            response_data = response.json()
            new_session_key = self.decrypt_response(response_data.get("content"), response_data.get("iv"))
            if new_session_key:
                self.zysession_key = new_session_key
                self.headers["CsrfToken"] = new_session_key
                return True
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return False
        except json.JSONDecodeError:
            logger.error("Invalid JSON response")
            return False


def main():
    # get_credentials ile modem bilgilerini al
    try:
        session_cookie, zysession_key, aes_key_b64 = get_credentials()
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return

    logger.info("Initializing ModemLogger...")
    modem_logger = ModemLogger("192.168.1.1", session_cookie, zysession_key, aes_key_b64)
    if modem_logger.update_logs():
        logger.info("Log settings updated successfully")
    else:
        logger.error("Failed to update log settings")

if __name__ == "__main__":
    main()
