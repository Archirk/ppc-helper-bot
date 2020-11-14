def act_feedback(data):
    bot, msg = data['bot'], data['data']
    header = '🎈 <b>Пришел отзыв на бота</b>\n'
    msg = f'{header}\"{msg}\"'
    bot.send_message(144581052, text=msg, parse_mode="html")

def act_give_contacts(data):
    contacts = 'Если есть какие-то предложения, требующие отправки файлов или обратной связи, напишите мне на ppc_helper_bot@gmail.com'
    return contacts

def act_get_user_queries(data):
    dbm = data['dbm']
    r = dbm.get_user_queries(data['chat_id'])
    return str(r)

def act_about(data):
    about = 'Бот находится в разработке. Цель бота - сделать базовые инструменты для интернет продвижения доступными в одном месте'
    return about
