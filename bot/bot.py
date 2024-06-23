import os
from dotenv import load_dotenv
import psycopg2 as ps
import telebot

load_dotenv()

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode=None)

host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
db_name = os.getenv("db")


def conn_to_db():
    conn = ps.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    return conn


commands = '''Используйте комманды: /add-добавить рецепт, /list-список всех
рецептов, /get-рецепт по названию, /edit-изменить рецепт,
/delete-удалить рецепт'''


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global user_id
    user_id = message.from_user.id
    bot.reply_to(message, commands)


@bot.message_handler(commands=['add'])
def add_recipe_name(message):
    global user_id
    user_id = message.from_user.id
    mes = bot.send_message(message.chat.id, "Напишите название рецепта")
    try:
        bot.register_next_step_handler(mes, add_recipe_ingredients)
    except Exception as e:
        bot.reply_to(message, f'Ошибка: {e}')


def add_recipe_ingredients(message):
    global name
    name = message.text
    mes = bot.send_message(message.chat.id, "Напишите ингредиенты")
    try:
        bot.register_next_step_handler(mes, add_recipe_steps)
    except Exception as e:
        bot.reply_to(message, f'Ошибка: {e}')


def add_recipe_steps(message):
    global ingredients
    ingredients = message.text
    mes = bot.send_message(message.chat.id, "Напишите шаги приготовления")
    try:
        bot.register_next_step_handler(mes, add_recipe)
    except Exception as e:
        bot.reply_to(message, f'Ошибка: {e}')


def add_recipe(message):
    global steps
    steps = message.text
    conn = conn_to_db()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO recipes (name, ingredients, steps, user_id)
                    VALUES (%s, %s, %s, %s)""", (name, ingredients, steps, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, f'Рецепт "{name}" добавлен')


@bot.message_handler(commands=['list'])
def list_all_recipes(message):
    global user_id
    user_id = message.from_user.id
    conn = conn_to_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT name FROM recipes WHERE user_id=%s""", (user_id,))
    recipes_lst = cursor.fetchall()
    cursor.close()
    conn.close()
    if recipes_lst:
        recipe_names = []
        for recipe in recipes_lst:
            recipe_names.append(recipe[0])
        recipe_names = '\n'.join(map(str, recipe_names))
        bot.reply_to(message, f'*Рецепты*:\n{recipe_names}', parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Список рецептов пуст')


@bot.message_handler(commands=['get'])
def get_recipe_name(message):
    global user_id
    user_id = message.from_user.id
    mes = bot.send_message(message.chat.id, "Напишите название рецепта")
    bot.register_next_step_handler(mes, get_recipe)


def get_recipe(message):
    name = message.text
    conn = conn_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE name = %s and user_id=%s', (name, user_id,))
    recipe = cursor.fetchone()
    cursor.close()
    conn.close()
    if recipe:
        bot.reply_to(message, f'*Название:* {recipe[1]}\n\n*Ингредиенты:*\n{recipe[2]}\n\n*Шаги:* {recipe[3]}', parse_mode='Markdown')
    else:
        bot.reply_to(message, f'Рецепт "{name}" не найден.')


@bot.message_handler(commands=['delete'])
def get_name(message):
    global user_id
    user_id = message.from_user.id
    mes = bot.send_message(message.chat.id, "Напишите название рецепта для удаления")
    bot.register_next_step_handler(mes, delete_recipe)


def delete_recipe(message):
    name = message.text
    conn = conn_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE name=%s and user_id=%s', (name, user_id,))
    recipe = cursor.fetchone()
    if recipe:
        cursor.execute('DELETE FROM recipes WHERE name=%s and user_id=%s', (name, user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        bot.reply_to(message, f'Рецепт "{recipe[1]}" удален')
    else:
        bot.reply_to(message, f'Рецепт "{name}" не найден.')


@bot.message_handler(func=lambda m: True)
def welcome(message):
    bot.reply_to(message, commands)


bot.infinity_polling()
