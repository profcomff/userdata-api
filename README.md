# Сервис пользовательских данных

Серверная часть сервиса хранения и управления информации о пользователе

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
    foo@bar:~$ python -m userdata_api
    ```

## ENV-file description
- `DB_DSN=postgresql://postgres@localhost:5432/postgres` – Данные для подключения к БД
