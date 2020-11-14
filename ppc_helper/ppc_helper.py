import json
import time
import os
import multiprocessing as mp
from ppc_helper.bot.ppcbot import PpcBot
from ppc_helper.bot.task_manager import TaskManager
from psycopg2 import pool


class PPCHelper(object):
    def __init__(self, config_file):
        self.config_file = config_file
        self.queue = mp.Queue()

        self.config = None

        self.workers_count = None

        self.token = None
        self.parse_mode = None

        self.db_host = None
        self.db_user = None
        self.db_password = None
        self.db = None
        self.db_port = None
        self.db_max_connections = None
        self.db_tables_json = None
        self.vk_config = None

        self.db_pool = None
        self.bot = None

        self.tm = None
        self.tm_process = None

    def read_config(self):
        with open(self.config_file, 'r') as f:
            setattr(self, 'config', json.load(f))

    def apply_config(self):
        self.workers_count = self.config['ppc_helper']['workers_count']
        self.token = self.config['bot']['token']
        self.parse_mode = self.config['bot']['parse_mode']
        self.db_host = self.config['db_manager']['host']
        self.db_user = self.config['db_manager']['user']
        self.db_password = self.config['db_manager']['password']
        self.db = self.config['db_manager']['db']
        self.db_port = self.config['db_manager']['port']
        self.db_max_connections = self.config['db_manager']['max_connections']
        self.db_tables_json = self.config['db_manager']['tables_json']
        self.vk_config = self.config['function_handlers']['vk']

    def set_handlers_variables(self):
        if self.vk_config:
            os.environ['VK_APP_ID'] = str(self.vk_config['app_id'])
            os.environ['VK_CLIENT_SECRET'] = str(self.vk_config['client_secret'])
            os.environ['VK_TOKEN'] = str(self.vk_config['token'])
            os.environ['VK_SCOPE'] = str(self.vk_config['scope'])
            os.environ['VK_API_VERSION'] = str(self.vk_config['api_version'])

    def create_db_pool(self):
        self.db_pool = pool.ThreadedConnectionPool(minconn=1, maxconn=self.db_max_connections,
                                                   host=self.db_host, port=self.db_port, database=self.db,
                                                   user=self.db_user, password=self.db_password)

    def close_db_pool(self):
        if self.db_pool:
            self.db_pool.closeall()

    def create_bot(self):
        self.bot = PpcBot(token=self.token, parse_mode=self.parse_mode)
        self.bot.assign_queue(self.queue)
        if self.db_pool:
            self.bot.assign_connection(self.db_pool)
            self.bot.dbm.migrate(self.db_tables_json)
        else:
            raise Exception

    def run_bot(self):
        self.bot.polling(none_stop=True, interval=0, timeout=60)

    def stop_bot(self):
        self.bot.stop_bot()
        print('stopping bot')

    def run_task_manager(self):
        print('Starting Task Manager')
        self.tm = TaskManager(workers_count=self.workers_count, db_pool=self.db_pool, queue=self.queue,
                              token=self.token, bot=self.bot)
        self.tm.create_workers()

    def stop_task_manager(self):
        self.tm.terminate_workers()
        self.tm_process.terminate()
        print('stopped Task manager')


