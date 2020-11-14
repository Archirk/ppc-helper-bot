import multiprocessing as mp
from threading import Thread
from ppc_helper.db_manager.database_manager import DBM
from ppc_helper.bot.task import Task
from ppc_helper.bot.response import Response


class TaskManager(object):
    def __init__(self, workers_count, db_pool, queue, token, bot):
        self.workers_count = workers_count
        self.db_pool = db_pool
        self.queue = queue
        self.token = token
        self.bot = bot

        self.running_workers = []

    def create_workers(self):
        print('Creating workers')
        for i in range(self.workers_count):
            conn = self.db_pool.getconn()
            dbm = DBM(conn)
            name = f'TaskManagerWorker-{i + 1}'
            print(conn)
            p = mp.Process(target=self.listen, args=(dbm,), name=name)
            p.start()
            self.running_workers.append(p)
        for w in self.running_workers:
            w.join()

    def terminate_workers(self):
        for w in self.running_workers:
            w.terminate()
            print(f'{w.name} is terminated')

    def listen(self, dbm):
        try:
            while True:
                query_id = self.queue.get()
                task_handler = Thread(target=self.handle, args=(query_id, dbm, self.bot,), name='test')
                task_handler.start()

                print(f'Processed query: {query_id} by PID: - {mp.current_process()}')
        finally:
            print('dissconnected')
            dbm.disconnect()

    def handle(self, query_id, dbm, bot):
        task = Task(query_id, dbm, bot)
        task.get_query_from_db()
        try:
            task.validate()
            task.process()
            response = Response(self.token, task)
        except Exception as e:
            msg = 'Не удалось выполнить запрос. Возможно ошибка в данных?'
            print(e)
            response = Response(self.token, task, msg)
        response.send()


