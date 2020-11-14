from collections import namedtuple
from datetime import datetime
import requests
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton as btn
from ppc_helper.db_manager.database_manager import DBM
from ppc_helper.bot import callback_names as cn


class PpcBot(TeleBot):
    def __init__(self, token, parse_mode):
        super().__init__(token, parse_mode)
        self.dbm = None
        self.queue = None

        @self.message_handler(commands=['test'])
        def cmd_test(message):
            self.handle_test(message)

        @self.message_handler(commands=['start'])
        def cmd_test(message):
            self.handle_start(message)

        @self.message_handler(commands=['vk'])
        def cmd_vk(message):
            self.handle_vk(message)

        @self.message_handler(commands=['admin'])
        def cmd_admin(message):
            self.handle_admin(message)

        @self.message_handler(commands=['actions'])
        def cmd_actions(message):
            self.handle_actions(message)

        @self.message_handler(commands=['keywords'])
        def cmd_keywords(message):
            self.handle_keywords(message)

        @self.message_handler(commands=['seo'])
        def cmd_seo(message):
            self.handle_seo(message)

        @self.callback_query_handler(func=lambda call: True)
        def callback(call):
            self.handle_callback(call)

        @self.message_handler(content_types=['text', 'document'], func=lambda message: self.dbm.session_exists(message.chat.id))
        def receive_text_input(message):
            self.handle_text_input(message)

    def assign_queue(self, queue):
        setattr(self, 'queue', queue)

    def assign_connection(self, db_pool):
        conn = db_pool.getconn(key='bot_connection')
        print(f'bot_conn:{conn}')
        dbm = DBM(conn)
        setattr(self, 'dbm', dbm)

    def handle_test(self, message):
        self.send_message(message.chat.id, 'Bot is running')

    def handle_start(self, message):
        self.send_message(message.chat.id, text='Привет! Я нахожусь в разработке. Но я уже что-то умею, и ты можешь попробовать')
        self.dbm.register_new_user(message) # registers only new users

    def handle_vk(self, message):
        text = 'VK command'
        btn1 = btn('Получить id страницы VK по URL', callback_data=cn.vk_get_user_id_by_url)
        btn2 = btn('Собрать все группы участников группы', callback_data=cn.vk_get_common_groups_by_url)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(btn1, btn2)
        self.send_message(message.chat.id, text=text, reply_markup=markup)

    def handle_admin(self, message):
        if message.chat.id != 144581052:
            self.send_message(message.chat.id, text='Ты не мой хозяин!')
            return
        text = 'admin command'
        btn1 = btn('📣 - Дать сообщение всем', callback_data=cn.af_make_announcement)
        btn2 = btn('📊 - Статистика бота', callback_data=cn.af_get_bot_stats)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(btn1, btn2)
        self.send_message(message.chat.id, text=text, reply_markup=markup)

    def handle_actions(self, message):
        text = 'actions command'
        btn1 = btn('Предложить идею', callback_data=cn.act_feedback)
        #btn2 = btn('Проверить статус задач', callback_data=cn.act_get_user_queries)
        btn3 = btn('Связаться с разработчиком', callback_data=cn.act_give_contacts)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(btn1, btn3)
        self.send_message(message.chat.id, text=text, reply_markup=markup)

    def handle_keywords(self, message):
        text = 'keywords command'
        btn1 = btn('Зафиксировать местоимения, предлоги и пр.', callback_data=cn.kf_fixate_keywords)
        btn2 = btn('Сгруппировать неявные дубли', callback_data=cn.kf_group_duplicates)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(btn1, btn2)
        self.send_message(message.chat.id, text=text, reply_markup=markup)

    def handle_seo(self, message):
        text = 'seo command'
        btn1 = btn('Проверить список ссылок на доступность и редиректы', callback_data=cn.seo_check_urls_status_code)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(btn1)
        self.send_message(message.chat.id, text=text, reply_markup=markup)

    def handle_callback(self, call):
        def parse_callback(call):
            Query = namedtuple('Query',
                               'query_id chat_id query_time is_inplace input_required response_required handler func')
            data = call.data.split(':')
            is_inplace, input_required, response_required, handler, func = data
            is_inplace = bool(int(is_inplace))
            input_required = bool(int(input_required))
            response_required = bool(int(response_required))
            return Query(call.id, call.message.chat.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         is_inplace, input_required, response_required, handler, func)

        def send_query_to_db(query):
            data = {
                'query_id': query.query_id,
                'chat_id': query.chat_id,
                'query_time': query.query_time,
                'is_inplace': query.is_inplace,
                'input_required': query.input_required,
                'response_required': query.response_required,
                'handler': query.handler,
                'func': query.func,
                'status': 'pending',
            }
            self.dbm.add_row('queries', data)

        def get_hint(query):
            hints = {
                'vk_get_user_id_by_url': 'URL профилей в вк(до 1000 за раз), разделенных или с новой строки. Если профилей url много - то отправить данные в формате .txt или .csv',
                'vk_get_common_groups_by_url': 'URL страницы, группы или мероприятия в ВК',
                'kf_fixate_keywords': 'Список ключевых слов, разделенных запятой или переносом строки. Если много то в формате .txt',
                'kf_group_duplicates': 'Список ключевых слов, разделенных запятой или переносом строки. Если много то в формате .txt',
                'seo_check_urls_status_code':'Список URL, разделенных запятой или переносом строки. Если много то в формате .txt',
                     }
            func = query.func
            return hints[func] if func in hints else None

        q = parse_callback(call)
        send_query_to_db(q)
        if q.input_required:
            self.dbm.create_session(call)  # Always overwrites old if it exists
            hint = get_hint(q)
            if hint:
                self.send_message(q.chat_id, text=hint)
            self.dbm.update_query(q.query_id, 'status', 'awaiting data')
        else:
            self.queue.put(q.query_id)  # if input required query will be added to queue after data received
            self.dbm.update_query(q.query_id, 'status', 'in queue')
        self.answer_callback_query(q.query_id)  # Close query

    def handle_text_input(self, message):
        chat_id = message.chat.id
        content_type = message.content_type

        if content_type == 'document':
            if message.document.mime_type not in {'text/plain', 'text/csv'}:  # .file_name, .file_size
                self.send_message(chat_id, text=f'Неверный формат ввода. Ожидается .txt, .csv или сообщение')
                return
            file_info = self.get_file(message.document.file_id)  # 20 mb
            data = requests.get(f'https://api.telegram.org/file/bot{self.token}/{file_info.file_path}')
            data.encoding = 'utf-8'
            data = data.text
        elif content_type == 'text':
            data = message.text
        else:
            data = ''
        try:
            query_id, callback_name = self.dbm.get_session(chat_id).split('|')
        finally:
            self.dbm.delete_session(chat_id)

        # Add data to query in db
        try:
            self.dbm.update_query(query_id, 'data', data)
            self.dbm.update_query(query_id, 'status', 'data received')
            self.queue.put(query_id)
            self.send_message(chat_id, text=f'Данные отправлены')
        except Exception as e:
            self.send_message(chat_id, text=f'Не получилось отправить данные')
            self.dbm.update_query(query_id, 'status', 'failed to get data')
            print(e)
        finally:
            self.dbm.delete_session(chat_id)
