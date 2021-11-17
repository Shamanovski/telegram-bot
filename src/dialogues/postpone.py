import base64
import datetime
from datetime import timedelta

import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler, CallbackQueryHandler
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from . import store

reply_keyboard = ReplyKeyboardMarkup([["Текст поста", "Добавить дату и время"],
                                      ["Прикрепить картинку", "Указать канал", "Создать пост"]],
                                     one_time_keyboard=True,
                                     resize_keyboard=True)
PARAMS, TYPING_CHOICE = range(2)


class MyStyleCalendar(DetailedTelegramCalendar):
    # previous and next buttons style. they are emoji now!
    prev_button = "⬅️"
    next_button = "➡️"
    # you do not want empty cells when month and year are being selected
    empty_month_button = ""
    empty_year_button = ""


def text(update, context):
    update.message.reply_text("Напишите текст")
    context.user_data["choice"] = "contents"
    return TYPING_CHOICE


def date(update, context):
    calendar, step = MyStyleCalendar(min_date=datetime.date.today()).build()
    update.message.reply_text(f"Выберите {LSTEP[step]}", reply_markup=calendar)
    MyStyleCalendar.func()
    return TYPING_CHOICE


def image(update, context):
    update.message.reply_text("Загрузите картинку или пришлите ссылку на нее")
    context.user_data["choice"] = "image"
    return TYPING_CHOICE


def channel(update, context):
    update.message.reply_text("Укажите название канала (начинается с @)")
    context.user_data["choice"] = "channel"
    return TYPING_CHOICE


def create_post(update, context):
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    user_data["status"] = 1  # pending
    user_data["post_id"] = update.message.message_id
    store.publish("post", "created", **user_data)
    update.message.reply_text("Отложенный пост создан.")
    return ConversationHandler.END


def start(update, context):
    user_exists = requests.get("http://web:4000/request-user",
                               params={"external_id": update.effective_user.username}).json()
    if not user_exists:
        update.message.reply_text("Пожалуйста, пройдите для начала регистрацию (/signup)")
        return
    context.user_data["username"] = update.effective_user.username
    update.message.reply_text("Для того, чтобы создать отложенный пост,"
                              " укажите текст, дату и время. Картинка по усмотрению",
                              reply_markup=reply_keyboard)
    return PARAMS


def save(update, context):
    user_data = context.user_data
    choice = user_data["choice"]
    if choice in ("contents", "channel"):
        user_data[choice] = update.message.text
    elif choice == "image":
        # a while loop is needed since the IndexError might be raised
        # if a pic is uploaded even with a small delay
        sizes = update.message.photo
        # the last size is the biggest one
        image_binary = sizes[-1].get_file(timeout=30).download_as_bytearray()
        image_encoded = base64.b64encode(image_binary)
        user_data["image"] = image_encoded.decode("ascii")
    update.message.reply_text(f"Данные post {choice} сохранены", reply_markup=reply_keyboard)
    return PARAMS


def save_date(update, context):
    user_data = context.user_data
    result, key, step = MyStyleCalendar(
        min_date=datetime.date.today() - timedelta(weeks=4)).process(update.callback_query.data)
    if not result and key:
        update.effective_chat.send_message(f"Выберите {LSTEP[step]}", reply_markup=key)
        return
    elif result:
        update.effective_chat.send_message(f"Вы назначили дату на {result}", reply_markup=reply_keyboard)
    # result = datetime.date(2022, 8, 18)
    user_data["date"] = str(result)
    return PARAMS


handler = ConversationHandler([CommandHandler("postpone", start)],
                              states={
                                  PARAMS: [
                                      MessageHandler(Filters.regex("^Текст поста$"), text),
                                      MessageHandler(Filters.regex("^Указать канал$"), channel),
                                      MessageHandler(Filters.regex("^Добавить дату и время$"), date),
                                      MessageHandler(Filters.regex("^Прикрепить картинку$"), image)
                                  ],
                                  TYPING_CHOICE: [
                                      MessageHandler(
                                          Filters.all & (~Filters.command | ~Filters.regex("^Создать пост$")), save),
                                      CallbackQueryHandler(save_date)
                                  ]
                              },
                              fallbacks=[MessageHandler(Filters.regex("^Создать пост$"), create_post,
                                                        pass_user_data=True)]
                              )
