import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_credentials():
    """
    Modeme giriş yaparak:
     - Session cookie (adı "Session"),
     - zySessionKey (localStorage'dan),
     - AES anahtarı (localStorage'dan)
    döndürür.
    """
    # —————— KULLANICI BİLGİLERİ ——————
    USERNAME = "admin"
    PASSWORD = "superonline"

    # —————— Headless Chrome Ayarları ——————
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=options)

    try:
        # 1) Giriş sayfasına git
        driver.get("https://192.168.1.1/login")
        time.sleep(1)

        # 2) Formu doldur ve gönder
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "userpassword").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginBtn").click()
        time.sleep(2)  # Giriş tamamlanana kadar bekle

        # 3) Cookie’den Session değerini al
        session_cookie = None
        for cookie in driver.get_cookies():
            if cookie['name'] == 'Session':
                session_cookie = cookie['value']
                break

        # 4) localStorage’dan zySessionKey’i al
        zysession_key = driver.execute_script(
            "return localStorage.getItem('zySessionKey');"
        )

        # 5) localStorage’dan AES key’i al
        aes_key = driver.execute_script("""
            return localStorage.getItem('AesKey')
                || localStorage.getItem('aeskey')
                || null;
        """)

        return session_cookie, zysession_key, aes_key

    finally:
        driver.quit()


if __name__ == "__main__":
    session_cookie, zysession_key, aes_key = get_credentials()
    print("Session Cookie:", session_cookie)
    print("zySessionKey  :", zysession_key)
    print("AES Key (B64) :", aes_key)
