# ppc-helper-bot
Учебный проект для курса OTUS по Python.  
Целью проекта было создать телеграм бота, который включал бы в себя базовые инструменты для интернет-рекламщиков.  
К сожалению, к моменту защиты, удалось реализовать только концепт приложения. Состояние проекта не релизное, а больше как техническая альфа.

## Запуск
Запустить бота можно через терминал:  
```
python3 run.py --log [log-path] --config [config-path]
```  
log - адрес для логов(по умолчанию None)  
config - адрес файла конфигурации  
### Файл конфигурации
```json
{
  "ppc_helper":
  {
    "workers_count": 1
  },
  "bot":
  {
    "token": "",
    "parse_mode": "MARKDOWN"
  },
  "db_manager":
  {
    "host": "",
    "user": "",
    "password": "",
    "db": "",
    "port": 5432,
    "max_connections": 1,
    "tables_json": "ppc_helper/db_manager/tables.json"
  },
  "function_handlers":
  {
    "vk":
    {
      "app_id": 0,
      "client_secret": "",
      "token": "",
      "scope": 0,
      "api_version": ""
    }
  }
}
```
Параметр | Комметарий
-------- | ----------
workers_count | Количество процессов которое, будет обслуживать бота
token | Токен бота телеграма
parse_mode | Разметка для ответов( MARKDOWN / HTML )
host | хост БД
user | Пользователь БД от которого будет работать приложение
password | Пароль пользователя
db | БД (должна быть создана)
port | Порт
max_connections | Максимальное количество соединений для пула. Должно быть не меньше чем количество воркеров + 1 
tables_json | Пресет таблицы для работы бота
app_id | Идентификатор приложения в ВК
client_secret | Секретный ключ приложения
token | Бессрочный для работы, который должен быть получен перед запуском
scope | Уровень доступа токена
api_version | Версии VK API

## Структура
Приложение состоит из трех модулей:  
* **bot** - отвечает за сбор данных по телеграм апи, обработку данных и отправку результата  
* **db_manager** - по сути набор захордкоженных SQL запросов, которые используются в боте  
* **function_handlers** - содержит в себе обработчики для различного типа запросов   

То как будет обрабатываться запрос, зависит от того, что будет распаршено из callback от телеграмма.  
В ppc_helper/bot/callback_names.py содерживаться список всех возможно callback. В их название заложено:  
1. Будет ли производиться вообще обработка запроса
1. Необходим ли ввод данных
1. Необходим ли ответ
1. Обработчик
1. Название функции обработчика  

Последние два пункта важны потому что функция обработки генерируется через eval()

## Схема работы
При запуске run.py по сути происходит следующее:  
1. Создается экземпляр класса приложения на основе файла конфигурации
1. Создается пул соединений с БД
1. Создается экземпляр бота, при этом ему присваивается соединение для работы с БД из пула
1. Создается процесс на котором будет работать Task Manager
1. Запускается процесс Task Manager, который создает воркеров, которые будут обрабатывать запросы которые они будут брать из очереди, каждому воркеру присваивается соединение из пула БД для работы
1. В треде основного процесса запускается бот, который будет слушать сервера телеграма и все новые запросы ставить в очередь, которую будут слушать воркеры, а их вводные данные писать в БД
![scheme](https://morgoth.ru/images/2020/11/14/937c8797c15b888801a10d20e3a9628e.png)
