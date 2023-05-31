import pymysql
import sqlite3
import telebot
from telebot import types

bot = telebot.TeleBot('6095783736:AAFq6Rk02iz9bu0wAiQZAz2-1ehNTyxDeBw')
host = "127.0.0.1"
user = "root"
password = "qwerty"
db_name = "my_db_cli"

user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Привет, мой друг!\nВашему вниманию представляется уникальный бот в котором ты сможешь насладиться честной игрой и уникальными режимами, которые нигде не найти.\n\n'
    mess1 = f'Баланс: {get_user_balance(message.from_user.id)}\n\n\n'
    mess2 = f'Команды: '
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    id_button = types.KeyboardButton('Профиль')
    game_button = types.KeyboardButton('Игры')
    wallet_button = types.KeyboardButton('Кошелек')
    faq_button = types.KeyboardButton('FAQ?')
    markup.add(game_button, wallet_button, id_button, faq_button)
    bot.send_message(message.chat.id, mess + mess1 + mess2, reply_markup=markup)
    set_user_db(message.from_user.id)
    set_user_last_bet_db(message.from_user.id)

@bot.message_handler(func=lambda message: message.text == 'Профиль')
def ID(message):
    bot.send_message(message.chat.id, f"Твой ID: {message.from_user.id}", parse_mode='html')

@bot.message_handler(func=lambda message: message.text == 'Игры')
def game(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    crazytime_button = types.KeyboardButton('Crazy Time')
    coin_button = types.KeyboardButton('Coin Flip')
    back_button = types.KeyboardButton('Назад')
    markup.add(crazytime_button, coin_button, back_button)
    bot.send_message(message.chat.id,f'Выбор игр' , reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Crazy Time')
def crazy_time(message):
    bot.send_message(message.chat.id, "Вы выбрали Crazy Time!")


@bot.message_handler(func=lambda message: message.text == 'Coin Flip')
def coin_flip(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    start_button = types.KeyboardButton('Начать игру')
    back_button = types.KeyboardButton('Назад')
    markup.add(start_button, back_button)
    mess = 'Coin flip - быстрый режим в котором шансы равны для всех 50% на 50% выбери Орёл или Решку и выигрывай!\n\nДля того чтобы играть нажми кнопку "Начать игру"'
    bot.send_message(message.chat.id,mess, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Начать игру')
def coin_flip_start(message):
    user_id = message.from_user.id
    last_bet = get_user_last_bet(user_id)
    balance = get_user_balance(user_id)
    mess = f'Баланс: {balance}'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bet_buttons = [types.KeyboardButton(str(amount)) for amount in ALLOWED_BETS]
    back_button = types.KeyboardButton('Назад')
    markup.add(*bet_buttons, back_button)

    if last_bet > 0:
        bot.send_message(message.chat.id,
                         mess + f"\nТекущая ставка: {last_bet}\nВы хотите изменить ставку или продолжить с текущей?",
                         parse_mode='html', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, mess + f"\nСделайте ставку:", parse_mode='html', reply_markup=markup)
    user_states[user_id] = "coin"


ALLOWED_BETS = ['10', '20', '50', '100', '500', '1000', '5000', '10000']


@bot.message_handler(
    func=lambda message: message.text in ALLOWED_BETS and user_states.get(message.from_user.id) == "coin",
    content_types=['text'])
def make_bet(message):
    user_id = message.from_user.id
    bet_amount = int(message.text)
    user_balance = get_user_balance(user_id)
    if bet_amount <= user_balance:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        eagle_button = types.KeyboardButton('Орёл')
        tails_button = types.KeyboardButton('Решка')
        back_button = types.KeyboardButton('Назад')
        markup.add(eagle_button, tails_button, back_button)

        # Обновляем последнюю ставку в БД
        update_last_bet_db(user_id, bet_amount)

        bot.send_message(message.chat.id, f"Баланс: {get_user_balance(user_id)}\nВаша ставка: {bet_amount}",
                         parse_mode='html', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"Баланс: {get_user_balance(user_id)}\nНедостаточно средств на балансе",
                         parse_mode='html')


import random

@bot.message_handler(func=lambda message: message.text == 'Орёл')
def eagle(message):
    user_id = message.from_user.id
    bet_amount = get_user_last_bet(user_id)
    if bet_amount > get_user_balance(user_id):
        bot.send_message(message.chat.id, f'Баланс: {get_user_balance(user_id)}\nНедостаточно средств на балансе', parse_mode='html')
        return
    coin_result = random.randint(0, 1)
    if coin_result == 0:  # орёл
        update_balance_db(user_id, bet_amount * 2)  # Обновляем баланс на выигрышную ставку
        mess = f'Вы выиграли! Ваша ставка удвоилась.\n\n'
    else:
        update_balance_db(user_id, -bet_amount)  # Обновляем баланс на проигрышную ставку
        mess = f'Вы проиграли. Попробуйте снова.\n\n'
    mess += f'Баланс: {get_user_balance(user_id)}'
    bot.send_message(message.chat.id, mess)
    user_states[user_id] = "coin_side"


@bot.message_handler(func=lambda message: message.text == 'Решка')
def tails(message):
    user_id = message.from_user.id
    bet_amount = get_user_last_bet(user_id)
    if bet_amount > get_user_balance(user_id):
        bot.send_message(message.chat.id, f'Баланс: {get_user_balance(user_id)}\nНедостаточно средств на балансе', parse_mode='html')
        return
    coin_result = random.randint(0, 1)
    if coin_result == 1:  # решка
        update_balance_db(user_id, bet_amount * 2)  # Обновляем баланс на выигрышную ставку
        mess = f'Вы выиграли! Ваша ставка удвоилась.\n\n'
    else:
        update_balance_db(user_id, -bet_amount)  # Обновляем баланс на проигрышную ставку
        mess = f'Вы проиграли. Попробуйте снова.\n\n'
    mess += f'Баланс: {get_user_balance(user_id)}'
    bot.send_message(message.chat.id, mess)
    user_states[user_id] = "coin_side"





@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    if user_state == "withdrawing" or user_state == "earning":
        user_states[user_id] = None
        wallet(message)
    elif user_state == "coin":
        user_states[user_id] = None
        coin_flip(message)
    elif user_state == "coin_side":
        user_states[user_id] = None
        update_last_bet_db(user_id, 0)  # Сбрасываем ставку пользователя
        coin_flip_start(message)  # Возвращаем пользователя к выбору ставки
    else:
        start(message)



@bot.message_handler(func=lambda message: message.text == 'Кошелек')
def wallet(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    earn_money = types.KeyboardButton('Пополнить')
    get_money = types.KeyboardButton('Вывести')
    back_button = types.KeyboardButton('Назад')
    markup.add(earn_money, get_money, back_button)
    bot.send_message(message.chat.id, f'Ваш баланс: {get_user_balance(message.from_user.id)}', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Вывести')
def withdraw_money(message):
    user_id = message.from_user.id
    user_states[user_id] = "withdrawing"  # установим состояние в "withdrawing"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_button = types.KeyboardButton('Назад')
    markup.add(back_button)
    bot.send_message(message.chat.id, "Введите сумму для вывода:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Пополнить')
def earn_money(message):
    user_id = message.from_user.id
    user_states[user_id] = "earning"  # установим состояние в "earning"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_button = types.KeyboardButton('Назад')
    markup.add(back_button)
    bot.send_message(message.chat.id, "Введите сумму пополнения:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.isdigit() and user_states.get(message.from_user.id) == "earning", content_types=['text'])
def add_money(message):
    user_id = message.from_user.id
    add_balance = int(message.text)
    update_balance_db(user_id, add_balance)
    bot.send_message(message.chat.id, f"Средства успешно пополнены: {add_balance}")
    user_states[user_id] = None  # сбросим состояние после пополнения баланса
    start(message)

@bot.message_handler(func=lambda message: message.text.isdigit() and user_states.get(message.from_user.id) == "withdrawing", content_types=['text'])
def withdraw_money_amount(message):
    user_id = message.from_user.id
    withdraw_amount = int(message.text)
    user_balance = get_user_balance(user_id)
    if withdraw_amount <= user_balance:  # проверяем, достаточно ли средств на балансе для вывода
        update_balance_db(user_id, -withdraw_amount)  # уменьшаем баланс на сумму вывода
        bot.send_message(message.chat.id, f"Средства успешно выведены: {withdraw_amount}")
    else:
        bot.send_message(message.chat.id, "Недостаточно средств на балансе")
    user_states[user_id] = None  # сбросим состояние после вывода средств
    start(message)


@bot.message_handler(content_types=['text'])
def incorrect_input(message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    if user_state == "coin":
        bot.send_message(message.chat.id, "Введите корректную ставку (10, 20, 50, 100, 500, 1000, 5000, 10000)")
    elif user_state == "withdrawing" or user_state == "earning":
        bot.send_message(message.chat.id, "Введите корректную сумму")
    else:
        bot.send_message(message.chat.id, "Введите корректную команду")


@bot.message_handler(func=lambda message: message.text == 'FAQ?')
def faq(message):
    bot.send_message(message.chat.id, f"Вообще похуй!", parse_mode='html')

def set_user_db(user_id):
    try:
        with pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        ) as connection:
            print("successfully connected...")
            print("#" * 20)

            with connection.cursor() as cursor:
                select_query = "SELECT * FROM users WHERE id = %s;"
                cursor.execute(select_query, (user_id,))
                result = cursor.fetchone()

                if result is None:
                    insert_query = "INSERT INTO users (id, balance) VALUES (%s, 0);"
                    cursor.execute(insert_query, (user_id,))
                    connection.commit()
                    print("Query executed successfully")

    except Exception as ex:
        print("Connection refused...")
        print(ex)

def set_user_last_bet_db(user_id):
    try:
        with pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        ) as connection:
            print("successfully connected...")
            print("#" * 20)

            with connection.cursor() as cursor:
                select_query = "SELECT * FROM user_last_bet WHERE user_id = %s;"
                cursor.execute(select_query, (user_id,))
                result = cursor.fetchone()

                if result is None:
                    insert_query = "INSERT INTO user_last_bet (user_id, last_bet) VALUES (%s, 0);"
                    cursor.execute(insert_query, (user_id,))
                    connection.commit()
                    print("Query executed successfully")

    except Exception as ex:
        print("Connection refused...")
        print(ex)

def get_user_balance(user_id):
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("successfully connected...")

        cursor = connection.cursor()
        cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            return result['balance']
        else:
            return 0
    except Exception as ex:
        print("Connection refused...")
        print(ex)


def update_balance_db(user_id, add_balance):
    current_balance = get_user_balance(user_id)
    if add_balance < 0 and abs(add_balance) > current_balance:
        return

    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("successfully connected...")

        try:
            cursor = connection.cursor()
            # Обновляем баланс пользователя
            update_query = "UPDATE `users` SET balance = balance + %s WHERE id = %s;"
            cursor.execute(update_query, (add_balance, user_id))
            connection.commit()  # Не забудьте подтвердить транзакцию

        finally:
            connection.close()

    except Exception as ex:
        print("Connection refused...")
        print(ex)


def get_user_last_bet(user_id):
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("successfully connected...")

        cursor = connection.cursor()
        cursor.execute('SELECT last_bet FROM user_last_bet WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            return result['last_bet']
        else:
            return 0
    except Exception as ex:
        print("Connection refused...")
        print(ex)
def update_last_bet_db(user_id, bet_amount):
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("successfully connected...")
        try:
            cursor = connection.cursor()
            # Обновляем ставку пользователя
            update_query = "UPDATE `user_last_bet` SET last_bet = %s WHERE user_id = %s;"
            cursor.execute(update_query, (bet_amount, user_id))
            connection.commit()  # Не забудьте подтвердить транзакцию

        finally:
            connection.close()

    except Exception as ex:
        print("Connection refused...")
        print(ex)


bot.polling(none_stop=True)


