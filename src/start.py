# TODO: answers must be validated with regular expressions
# TODO: code might be refactored making it context based data collection
# TODO: add cancel option

from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler

from session import Session
from dialogues import postpone, updater, store

dispatcher = updater.dispatcher

ASK_SECOND_NAME, ASK_THIRD_NAME, ASK_PHONE, ASK_EMAIL, END_SIGNUP = range(5)

sessions = {}


def ask_second_name(update, context):
    message = update.message
    session.name = message.text
    update.message.reply_text(text="Ваша фамилия?")
    return ASK_THIRD_NAME


def ask_third_name(update, context):
    message = update.message
    session.second_name = message.text
    update.message.reply_text(text="Ваше отчество?")
    return ASK_PHONE


def ask_phone(update, context):
    message = update.message
    session.second_name = message.text
    update.message.reply_text(
        "Подтвердите пожалуйста получение вашего номера телефона, привязаннго к Telegram."
        " Телефон послужит улучшению обратной связи с вами,"
        " а также появлению возможности установления двухфакторной авторизации",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отправить мой номер телефона", request_contact=True)]],
                                         resize_keyboard=True, one_time_keyboard=True))
    return ASK_EMAIL


def ask_email(update, context):
    phone_number = update.message.contact.phone_number
    session.phone = phone_number
    update.message.reply_text(text="Ваша почта?")
    return END_SIGNUP


def end_signup(update, context):
    message = update.message
    session.email = message.text
    store.publish('user', 'registered', **{
        "email": session.email, "first_name": session.name, "second_name": session.second_name, "phone": session.phone,
        "third_name": session.third_name, "external_id": update.message.from_user.username})
    update.message.reply_text(text="Регистрация окончена")
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text("Вы отменили процесс регистрации. Чтобы начать заново введите /start")


def start(update, context):
    global session
    session = Session()
    store.publish('registration', 'started', **{})
    update.message.reply_text(text="Ваше имя?")
    return ASK_SECOND_NAME


def unknown(update, context):
    message = update.message
    message.reply_text(text="Введите /signup чтобы начать регистрацию\n"
                            "Введите /postpone чтобы создать отложенный пост")
    print(f'received message {message.text}')
    store.publish('unknown_post', 'received', **{'text': message.text})


def main():
    unknown_handler = MessageHandler(Filters.all, unknown)
    registration_handler = ConversationHandler([CommandHandler("signup", start)],
                                               states={
                                                   ASK_SECOND_NAME: [
                                                       MessageHandler(Filters.text,
                                                                      ask_second_name, pass_chat_data=True,
                                                                      pass_user_data=True)
                                                   ],
                                                   ASK_THIRD_NAME: [
                                                       MessageHandler(Filters.text,
                                                                      ask_third_name, pass_chat_data=True,
                                                                      pass_user_data=True)
                                                   ],
                                                   ASK_PHONE: [
                                                       MessageHandler(Filters.text, ask_phone, pass_user_data=True,
                                                                      pass_chat_data=True)
                                                   ],
                                                   ASK_EMAIL: [
                                                       MessageHandler(Filters.contact,
                                                                      ask_email, pass_chat_data=True,
                                                                      pass_user_data=True)
                                                   ],
                                                   END_SIGNUP: [
                                                       MessageHandler(Filters.text,
                                                                      end_signup, pass_chat_data=True,
                                                                      pass_user_data=True)
                                                   ]
                                               },
                                               fallbacks=[CommandHandler("cancel", cancel)]
                                               )

    dispatcher.add_handler(registration_handler)
    dispatcher.add_handler(postpone.handler)
    dispatcher.add_handler(unknown_handler)


main()

updater.start_polling()
updater.idle()
