# Сервис пользовательских данных

Серверная часть сервиса хранения и управления информации о пользователе

![Auth Schema](https://github.com/profcomff/auth-api/assets/5656720/ab2730be-054a-454c-ab76-5475e615bb64)

## Запуск

1. Перейдите в папку проекта

2. Создайте виртуальное окружение командой и активируйте его:
    ```console
    foo@bar:~$ python3 -m venv venv
    foo@bar:~$ source ./venv/bin/activate  # На MacOS и Linux
    foo@bar:~$ venv\Scripts\activate  # На Windows
    ```

3. Установите библиотеки
    ```console
    foo@bar:~$ pip install -r requirements.txt
    ```
4. Запускайте приложение!
    ```console
    foo@bar:~$ python -m userdata_api start --instance api -- запустит АПИ
    foo@bar:~$ python -m userdata_api start --instance worker -- запустит Kafka worker
    ```
   
Приложение состоит из двух частей - АПИ и Kafka worker'а. 

АПИ нужно для управления структурой пользовательских данных - 
контроль над категориями данных, параметрами, источниками данных.
Также, в АПИ пользовательские данные может слать
сам пользователь(владелец этих данных), а также админ

Kafka worker нужен для того, чтобы разгребать поступающие от OAuth 
методов авторизации AuthAPI пользовательские данные

## ENV-file description
- `DB_DSN=postgresql://postgres@localhost:5432/postgres` – Данные для подключения к БД
