import json
from datetime import datetime
from psycopg2 import sql


class DBM(object):
    def __init__(self, conn):
        self.connected = False
        self.conn = conn
        self.cur = conn.cursor()

    def disconnect(self):
        if self.connected:
            self.conn.close()
            self.conn = None
            self.cur = None

    def create_column(self, table, c_name, c_type):
        q = f'ALTER TABLE {table} ADD COLUMN {c_name} {c_type}'
        self.cur.execute(q)
        self.conn.commit()

    def create_table(self, table_name, columns_dic):
        columns = '('
        for name, c_type in columns_dic.items():
            columns += f'{name} {c_type},'
        columns = columns[:-1]
        columns += ')'
        q = f'CREATE TABLE {table_name} {columns}'
        print(q)
        self.cur.execute(q)
        self.conn.commit()

    def table_exists(self, table_name):
        q = f'SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_schema=\'public\' AND table_name=\'{table_name}\')'
        self.cur.execute(q)
        return self.cur.fetchone()[0]

    def get_table_columns(self, table_name):
        q = f'SELECT column_name, data_type FROM information_schema.columns WHERE table_name=\'{table_name}\''
        self.cur.execute(q)
        return {i[0]: i[1] for i in self.cur.fetchall()}

    def add_row(self, table, data_dic):
        columns, values = [], []
        for c_name, value in data_dic.items():
            columns.append(c_name)
            values.append(str(value))
        q = 'INSERT INTO {} ({}) VALUES ({})'
        q = sql.SQL(q).format(sql.Identifier(table),
                              sql.SQL(', ').join(map(sql.Identifier, columns)),
                              sql.SQL(', ').join(map(sql.Literal, values)))
        self.cur.execute(q)
        self.conn.commit()

    def migrate(self, tables_file):
        with open(tables_file, 'r') as t:
            tables = json.load(t)

        for table, columns in tables.items():
            if not self.table_exists(table):
                self.create_table(table, columns)
            else:
                current_columns = self.get_table_columns(table)
                for c_name, c_type in columns.items():
                    if c_name not in current_columns:
                        self.create_column(table, c_name, c_type)

    def get_task(self, query_id):
        # orders matters for task class for get_query_from_db() method
        q = 'SELECT chat_id, response_required, handler, func, data FROM queries WHERE query_id={}'
        q = sql.SQL(q).format(sql.Literal(query_id))
        self.cur.execute(q)
        return self.cur.fetchall()[0]

    def update_query(self, query_id, column, value):
        q = 'UPDATE queries SET {}={} WHERE query_id={}'
        q = sql.SQL(q).format(sql.Identifier(column), sql.Literal(value), sql.Literal(query_id))
        self.cur.execute(q)
        self.conn.commit()

    def create_session(self, call):
        chat_id = call.message.chat.id
        info = f'{call.id}|{call.data}'
        if self.session_exists(chat_id):
            self.delete_session(chat_id)
        q = 'INSERT INTO active_sessions (chat_id, info) VALUES ({})'
        q = sql.SQL(q).format(sql.SQL(', ').join(map(sql.Literal, (chat_id, info))))
        self.cur.execute(q)
        self.conn.commit()

    def session_exists(self, chat_id):
        q = f'SELECT EXISTS(SELECT chat_id FROM active_sessions WHERE chat_id = {chat_id})'
        self.cur.execute(q)
        return self.cur.fetchone()[0]

    def get_session(self, chat_id):
        q = f'SELECT info FROM active_sessions WHERE chat_id = {chat_id}'
        self.cur.execute(q)
        return self.cur.fetchone()[0]

    def delete_session(self, chat_id):
        q = f'DELETE FROM active_sessions WHERE chat_id = {chat_id}'
        self.cur.execute(q)
        self.conn.commit()

    def register_new_user(self, message):
        q = f'SELECT EXISTS(SELECT chat_id FROM users WHERE chat_id = {message.chat.id})'
        self.cur.execute(q)
        exists = self.cur.fetchone()[0]
        if not exists:
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            q = 'INSERT INTO users(chat_id,username,launch_datetime) VALUES ({})'
            q = sql.SQL(q).format(sql.SQL(', ').join(map(sql.Literal, (message.chat.id,
                                                                       message.chat.username,
                                                                       time))))
            self.cur.execute(q)
            self.conn.commit()

    def get_all_chat_ids(self):
        q = 'SELECT chat_id from users'
        self.cur.execute(q)
        return [i[0] for i in self.cur.fetchall()]

    def get_bot_stats(self):
        stats = {
            'users': 0,
            'new_users_week': 0,
            'queries_today': 0,
            'queries_today_complete': 0,
            'queries_today_process': 0,
        }
        q = 'SELECT COUNT(chat_id) from users'
        self.cur.execute(q)
        stats['users'] = self.cur.fetchone()[0]

        q = 'SELECT COUNT(query_id) FROM queries WHERE query_time>={}'
        today = datetime.strftime(datetime.today(),'%Y-%m-%d')
        q = sql.SQL(q).format(sql.Literal(today))
        self.cur.execute(q)
        stats['queries_today'] = self.cur.fetchone()[0]
        return stats

    def get_user_queries(self, chat_id):
        q = f'SELECT query_id, status FROM queries WHERE chat_id={chat_id} AND status=\'in process\''
        self.cur.execute(q)
        return self.cur.fetchall()

if __name__ == '__main__':
    print('Running sql_handler')
