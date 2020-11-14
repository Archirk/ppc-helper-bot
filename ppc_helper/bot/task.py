from datetime import datetime
from ppc_helper.function_handlers import admin_functions as af
from ppc_helper.function_handlers import actions as act
from ppc_helper.function_handlers import keyword_functions as kf
from ppc_helper.function_handlers import seo_functions as sf

class Task(object):
    def __init__(self, query_id, dbm, bot):
        self.query_id = query_id
        self.dbm = dbm
        self.bot = bot
        self.handlers = {'vk', 'af', 'sf', 'kf', 'act'}

        self.chat_id = None
        self.response_required = False
        self.handler = None
        self.func = None
        self.data = ''
        self.result = ''

    def __str__(self):
        return f'Task:{self.query_id} - {self.func}'

    def get_query_from_db(self):
        self.chat_id, self.response_required, self.handler, self.func, self.data = self.dbm.get_task(self.query_id)
        self.dbm.update_query(self.query_id, 'status', 'taken by worker')

    def validate(self):
        if self.handler not in self.handlers:
            raise Exception(f'Неизвестный обработчик: {self.handler}')
        self.dbm.update_query(self.query_id, 'status', 'validated')

    def process(self):
        self.dbm.update_query(self.query_id, 'status', 'in process')
        from ppc_helper.function_handlers import vk

        # Fast but not reliable to use eval in such manner
        data = {'data': self.data,
                'dbm': self.dbm,
                'bot': self.bot,
                'chat_id': self.chat_id}
        eval_str = f'{self.handler}.{self.func}(data)'
        print(f'Function to be evaled: {eval_str}')

        self.result = eval(eval_str)
        self.dbm.update_query(self.query_id, 'status', 'job done')
        finish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.dbm.update_query(self.query_id, 'query_finish_time', finish_time)

