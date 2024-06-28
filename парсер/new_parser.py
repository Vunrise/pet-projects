import time
import random
import config
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import psycopg2 as ps
import re
import telebot


# подключаем бота
TOKEN = config.TOKEN
bot = telebot.TeleBot(TOKEN, parse_mode=None)
CHANNEL_ID = config.CHANNEL_ID


# отправка сообщения в канал
def send_message_to_channel(message, img):
    try:
        bot.send_photo(CHANNEL_ID, photo=img, caption=message)
        print("Сообщение отправлено в канал!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Настройки для запуска Chrome
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--headless")


# Функция для создания новой сессии
def create_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;
        """
    })
    return driver


# подключение к бд
host = config.host
user = config.user
password = config.password
db_name = config.db_name


def conn_to_db():
    conn = ps.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    return conn


# достаем ссылки для парсинга
def get_query_links_db():
    conn = conn_to_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT url, price FROM query""")
    result = cursor.fetchall()
    urls = {}
    for y in result:
        urls[y[0]] = y[1]
    cursor.close()
    conn.close()
    return urls


# достаем id из ссылки товара
def extract_product_id(link):
    match = re.search(r'/product/[^/]+-(\d+)/', link)
    if match:
        return match.group(1)
    return None


# сортируем и сохраняем в бд товары
def save_to_db(link, name, price, img, client_price):
    link_id = int(extract_product_id(link))
    message = " "
    conn = conn_to_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT price FROM goods WHERE link_id=%s""", (link_id, ))
    res = cursor.fetchall()
    if res:
        for x in res:
            old_price = x[0]
        if old_price != price and price < client_price:
            # отправляем сообщение в канал
            message = f'{name}\n\n{price}\n\n{link}'
            send_message_to_channel(message, img)

        cursor.execute("""INSERT INTO goods (link_id, link, name, price, img)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link_id) DO UPDATE SET
                    link = EXCLUDED.link,
                    name = EXCLUDED.name,
                    price = EXCLUDED.price,
                    img = EXCLUDED.img""", (link_id, link, name, price, img, ))
    else:
        cursor.execute("""INSERT INTO goods (link_id, link, name, price, img)
                    VALUES (%s, %s, %s, %s, %s)""", (link_id, link, name, price, img, ))
        if price < client_price:
            # отправляем сообщение в канал
            message = f'{name}\n\n{price}\n\n{link}'
            send_message_to_channel(message, img)
    conn.commit()
    cursor.close()
    conn.close()


# парсим страницы
def parse(driver, stop_event):
    try:
        urls = get_query_links_db()
        for url, client_price in urls.items():
            if stop_event.is_set():
                break
            driver.get(url)
            # Ожидание загрузки страницы
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.tile-root')))

            # Прокрутка страницы для загрузки всех продуктов
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                if stop_event.is_set():
                    break
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            products = driver.find_elements(By.CSS_SELECTOR, ".tile-root")
            try:
                for product in products:
                    if stop_event.is_set():
                        break
                    price = product.find_element(By.CSS_SELECTOR, 'span.tsHeadline500Medium')
                    name = product.find_element(By.CSS_SELECTOR, 'span.tsBody500Medium')
                    link = product.find_element(By.CSS_SELECTOR, 'a.tile-hover-target').get_attribute('href')
                    img = product.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                    price_text = price.text.strip()
                    price = ''.join(price_text.split())
                    price = price.replace('₽', '')
                    price = int(price)
                    save_to_db(link, name.text, price, img, client_price)
            except Exception as e:
                print(e)
        driver.quit()
        # time.sleep(random.uniform(25, 35))
    except KeyboardInterrupt:
        print("Завершение работы парсера")
    finally:
        driver.quit()


stop_event = threading.Event()
parse_thread = None


def start_parsing(stop_event):
    while not stop_event.is_set():
        driver = create_driver()
        parse(driver, stop_event)
        if stop_event.is_set():
            driver.quit()
            break
        time.sleep(random.uniform(295, 310))


users = config.users


@bot.message_handler(commands=['start_bot'])
def start_command(message):
    if message.from_user.id in users:
        global parse_thread
        if parse_thread is None or not parse_thread.is_alive():
            stop_event.clear()
            parse_thread = threading.Thread(target=start_parsing, args=(stop_event, ))
            parse_thread.start()
            bot.reply_to(message, "Парсинг запущен.")
        else:
            bot.reply_to(message, "Парсинг уже запущен.")


@bot.message_handler(commands=['stop_bot'])
def stop_command(message):
    if message.from_user.id in users:
        global parse_thread
        if parse_thread is not None and parse_thread.is_alive():
            stop_event.set()
            parse_thread.join()
            bot.reply_to(message, "Парсинг остановлен.")
        else:
            bot.reply_to(message, "Парсинг не запущен.")


@bot.message_handler(commands=['status'])
def status_command(message):
    if message.from_user.id in users:
        if parse_thread is not None and parse_thread.is_alive():
            bot.reply_to(message, "Парсинг запущен.")
        else:
            bot.reply_to(message, "Парсинг остановлен.")


@bot.message_handler(commands=['add_link'])
def get_query(message):
    if message.from_user.id in users:
        mes = bot.send_message(message.chat.id, "Напишите ссылку")
        try:
            bot.register_next_step_handler(mes, get_price)
        except Exception as e:
            bot.reply_to(message, f'Ошибка: {e}')


def get_price(message):
    if message.from_user.id in users:
        global query_link
        query_link = message.text
        if not query_link.startswith("http://") and not query_link.startswith("https://"):
            bot.reply_to(message, "Ссылка должна начинаться с http:// или https://")
            return

        try:
            driver = create_driver()
            driver.get(query_link)
            driver.quit()
            mes = bot.send_message(message.chat.id, "Напишите цену")
            try:
                bot.register_next_step_handler(mes, add_query)
            except Exception as e:
                bot.reply_to(message, f'Ошибка: {e}')
        except Exception as e:
            bot.reply_to(message, f'Ошибка: {e}')


def add_query(message):
    if message.from_user.id in users:
        query_price = message.text
        conn = conn_to_db()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO query (url, price)
                    VALUES (%s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                    url = EXCLUDED.url,
                    price = EXCLUDED.price""", (query_link, query_price))
        conn.commit()
        cursor.close()
        conn.close()
        bot.send_message(message.chat.id, "Добавлена ссылка")

# Создание базы данных при первом запуске
# create_database()


bot.polling()
