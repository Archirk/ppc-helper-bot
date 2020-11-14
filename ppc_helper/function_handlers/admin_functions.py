def af_make_announcement(data):
    dbm, bot = data['dbm'], data['bot']
    chat_ids = dbm.get_all_chat_ids()
    for i in chat_ids:
        bot.send_message(i, text=data['data'])


def af_get_bot_stats(data):
    dbm = data['dbm']
    stats = dbm.get_bot_stats()
    users = stats['users']
    queries_today = stats['queries_today']
    return f'В БД существует {users} пользовователей.\nСегодня было {queries_today} запросов'
