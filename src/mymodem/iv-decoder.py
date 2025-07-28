import base64
import json
from typing import Optional
from login import get_credentials
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad


def decrypt_response(encrypted_content: str, iv_base64: str, aes_key_b64: str) -> Optional[str]:
    """
    Encrypted JSON içeriğini AES-CBC ile çözer, sonucu ekrana basar ve
    eğer varsa yeni sessionkey değerini döndürür.
    """
    try:
        # AES anahtarı ve IV decode
        aes_key = base64.b64decode(aes_key_b64)
        iv = base64.b64decode(iv_base64)[:16]

        # Base64 padding düzeltme
        pad_len = len(encrypted_content) % 4
        if pad_len:
            encrypted_content += '=' * (4 - pad_len)

        # Base64 decode
        encrypted_data = base64.b64decode(encrypted_content)

        # AES-CBC çözme
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # UTF-8 decode
        decrypted_str = decrypted_bytes.decode('utf-8', errors='ignore')
        print('\n✅ **Şifre Çözüldü!**')
        print(decrypted_str)

        # JSON parse ve yeni sessionkey kontrolü
        data = json.loads(decrypted_str)
        if 'sessionkey' in data:
            new_key = data['sessionkey']
            print(f"\n🔑 **Yeni SessionKey:** {new_key}")
            return new_key
        return None

    except (ValueError, base64.binascii.Error) as e:
        print(f"\n❌ **Çözme hatası:** {e}")
        return None
    except json.JSONDecodeError:
        print("\n❌ **Hata: Gönderilen veri JSON değil!**")
        return None


if __name__ == '__main__':
    # Giriş bilgilerini al: session, zysession_key ve aes_key
    try:
        _, _, aes_key_b64 = get_credentials()
    except Exception as e:
        print(f"\n❌ **Giriş hatası:** {e}")
        exit(1)

    # Kullanıcıdan şifreli JSON input al
    raw = input("Şifreli JSON verisini girin (content+iv JSON formatında):\n")
    try:
        payload = json.loads(raw)
        content = payload.get('content')
        iv = payload.get('iv')
        if not content or not iv:
            print("\n❌ **Hata: content veya iv eksik!**")
            exit(1)
        # Çözme
        decrypt_response(content, iv, aes_key_b64)
    except json.JSONDecodeError:
        print("\n❌ **Hata: Geçersiz JSON formatı!**")
        exit(1)