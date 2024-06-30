import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Настройки для запуска Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-popup-blocking")

# Инициализация веб-драйвера
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            const newProto = navigator.__proto__
            delete newProto.webdriver
            navigator.__proto__ = newProto
            """
        })


# URL сайта Ozon
url = config.url
# Переход на сайт
driver.get(url)


try:
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.tsBody400Small')))
    button.click()
    time.sleep(2)

    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.b214-b2')))
    button.click()
    time.sleep(2)

    time.sleep(2)
    button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Курьером']]")))
    button.click()
    time.sleep(2)

    textarea = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea.f005-a0')))
    textarea.click()
    time.sleep(2)

    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.a205-b1.a205-d6.a205-f0')))
    button.click()
    time.sleep(2)

    textarea.send_keys("Татарстан Республика, Казань, Большая Красная улица, 51")
    textarea.send_keys(Keys.RETURN)
    time.sleep(2)

    textarea = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea.f005-a0.f005-a4.f005-a1')))
    textarea.send_keys(Keys.RETURN)
    time.sleep(2)

    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.vb_7.b214-a0.b214-b2.b214-a4')))
    button.click()
    time.sleep(2)
    print("Адрес изменен")
except Exception as e:
    print(f"Произошла ошибка при нажатии на кнопку: {e}")

time.sleep(5)
driver.quit()
