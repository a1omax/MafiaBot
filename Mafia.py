from datetime import datetime
from sqlite3.dbapi2 import connect
import telebot
from telebot import types
import sqlite3
from cfg import *


bot=telebot.TeleBot(TOKEN)



def db_connect():
    global conn 
    conn = sqlite3.connect('members.db')


def to_db(msg, phone=0):
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS members(
            userid INT,
            first_name TEXT,  
            username TEXT,
            register_date TEXT,
            answer TEXT,
            phone TEXT
            )""")
    user = msg.from_user
    date = datetime.strftime(datetime.now(), "%d.%m.%Y")
    user_id = user.id
    if phone:
        answer = 'да'
    else:
        answer = 'нет'

    insert_data = (user_id, user.first_name, user.username, date, answer, phone)

    id_list = cur.execute("""SELECT userid FROM members""").fetchall()

    flag = True
    for i in id_list:
        if user_id in i:
            cur.execute("""UPDATE members SET answer = (?) WHERE userid = (?)""", (answer, user_id))
            if phone:
                cur.execute("""UPDATE members SET phone = (?) WHERE userid = (?)""",(phone, user_id))
            flag = False
            break
    if flag:
        cur.execute("""INSERT INTO members VALUES (?,?,?,?,?,?)""", insert_data)
    conn.commit()
    number = cur.execute("""SELECT COUNT(*) as count FROM members WHERE answer = 'да' """).fetchone()
    return number

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Да', 'Нет')  # Имена кнопок
    msg = bot.reply_to(message, 'Привет! Хочешь записаться на игру?', reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)

def process_step(message):

    def phone(msg):

        if msg.contact == None:
            to_db(message)
            bot.reply_to(msg, "Нажмите на кнопку Отправить номер телефона")
            agreed()
        else:
            number = to_db(message, msg.contact.phone_number)
            if number[0] <= 25:
                reply = "Отлично! Вы записаны в качестве участника."
            else:
                reply = "Участников уже достаточное количество. Если освободится место, то Вам сообщат"
            bot.reply_to(message, reply)

    def agreed():
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)  # Подключаем клавиатуру
        button_phone = types.KeyboardButton(text="Отправить телефон", request_contact=True)
        keyboard.add(button_phone)
        msg = bot.reply_to(message, 'Отправьте ваш номер телефона', reply_markup=keyboard)
        bot.register_next_step_handler(msg, phone)

    def denied():
        to_db(message)
        reply = "Очень жаль! Если передумаете, напишите команду /start и ответьте Да"
        bot.reply_to(message, reply)

    if message.text.lower() == 'да':
        agreed()

    elif message.text.lower() == 'нет':
        denied()

    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Да', 'Нет')
        msg = bot.reply_to(message, 'Не совсем понял, пожалуйста, отвечайте: Да или Нет', reply_markup=markup)
        bot.register_next_step_handler(msg, process_step)



@bot.message_handler(commands=['get_data'])
def get_data(message):
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS members(
        userid INT,
        first_name TEXT,  
        username TEXT,
        register_date TEXT,
        answer TEXT,
        phone TEXT
    )""")
    conn.commit()
    data = cur.execute("""SELECT * FROM members ORDER BY answer""").fetchall()
    number = cur.execute("""SELECT COUNT(*) as count FROM members""").fetchone()[0]
    reply = "\nВсего участников = {}\n\nИмя--Ник--Дата--Телефон--Ответ\n\n".format(number)
    counter = 1
    for member in data:
        reply += "{count}. {name}--{nick}--{date}--{phone}--{answer}\n".format(count=counter, name=member[1], nick=member[2],
                                                                     date=member[3], answer=member[4], phone=member[5])
        counter += 1

    bot.reply_to(message, reply)

@bot.message_handler(commands=['set_all_no'])
def set_to_no(message):
    cur = conn.cursor()
    cur.execute("""UPDATE members SET answer='нет'""")
    conn.commit()
    bot.reply_to(message, "Всем установлен ответ 'нет'")

@bot.message_handler(commands=['send_all'])
def send_all(message):

    def send_message_all(mail):
        cur = conn.cursor()
        to_send = mail.text
        if to_send.lower() != "отмена":
            id_users = cur.execute("""SELECT userid FROM members""").fetchall()

            for i in id_users:
                bot.send_message(i[0], to_send)
            bot.reply_to(mail, "Сообщение отправлено (наверное)")
        else:
            bot.reply_to(mail, "Сообщение не отправлено")


    msg = bot.reply_to(message, 'Какое сообщение вы хотите отправить?')
    bot.register_next_step_handler(msg, send_message_all)

@bot.message_handler(commands=['send_agreed'])
def send_agreed(message):

    def send_message_all(mail):
        cur = conn.cursor()
        to_send = mail.text
        if to_send.lower() != "отмена":
            id_users = cur.execute("""SELECT userid FROM members WHERE answer = 'да'""").fetchall()

            for i in id_users:
                bot.send_message(i[0], to_send)
            bot.reply_to(mail, "Сообщение отправлено (наверное)")
        else:
            bot.reply_to(mail, "Сообщение не отправлено")


    msg = bot.reply_to(message, 'Какое сообщение вы хотите отправить?')
    bot.register_next_step_handler(msg, send_message_all)

@bot.message_handler(content_types=['text'])
def text(message):
    bot.reply_to(message, "Введите команду /start чтобы записаться или отменить запись.")


if __name__ == '__main__':
    try:
        db_connect()
    except:
        print("error with db coonect")
    else:
        bot.polling(none_stop=True)
    
