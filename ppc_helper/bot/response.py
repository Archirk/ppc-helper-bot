import requests
import io
import csv


class Response(object):
    def __init__(self, token, task, msg=None):
        self.token = token
        self.task = task
        self.msg = msg

        self.query_id = task.query_id
        self.chat_id = task.chat_id
        self.data = task.result
        self.dbm = task.dbm
        self.rows_to_file = 3

        if self.msg is None:
            self.response = self.prepare_response()

    @property
    def response_type(self):
        if isinstance(self.data, str):
            if len(self.data) > 4096:  # max length of text message in Telegram
                return 'file'
            else:
                return 'string'
        if isinstance(self.data, list):
            if len(self.data) < self.rows_to_file:
                return 'short_file'
            else:
                return 'file'

    @property
    def csv_response(self):
        """
        Write self.result to csv-file to in-memory
        :param name: Output file name
        :return: in-memory buffer with csv
        """
        s = io.StringIO()
        csv.writer(s).writerows(self.data)
        s.seek(0)
        buf = io.BytesIO()
        buf.write(s.getvalue().encode())
        buf.seek(0)
        buf.name = f'{self.query_id}.csv'
        return buf

    def prepare_response(self):
        if self.response_type == 'string':
            return self.data
        if self.response_type == 'short_file':
            result = self.data[1:]  # 0 - header
            result = [','.join(map(str, row)) for row in result]
            return '\n'.join(result)
        if self.response_type == 'file':
            return self.csv_response

    def send(self):
        if self.msg:
            params = {'chat_id': self.chat_id, 'text': self.msg}
            requests.get(f'https://api.telegram.org/bot{self.token}/sendMessage', params=params)
            return

        self.dbm.update_query(self.query_id, 'status', 'sending to bot')
        if self.response_type != 'file':
            params = {'chat_id': self.chat_id, 'text': self.response}
            r = requests.get(f'https://api.telegram.org/bot{self.token}/sendMessage', params=params)
        else:
            # 50 MB limit
            r = requests.post(f'https://api.telegram.org/bot{self.token}/sendDocument',
                              data={"chat_id": self.chat_id, "caption": 'Ваш запрос выполнен!'},
                              files={'document': self.response})
        if r.status_code == 200:
            self.dbm.update_query(self.query_id, 'status', 'done')
        else:
            self.dbm.update_query(self.query_id, 'status', f'Failed to send: {r.status_code}')