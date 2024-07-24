# Сервис пользовательских данных

Серверная часть сервиса хранения и управления информации о пользователе

[<img src="https://cdn.profcomff.com/easycode/easycode.svg" width="200"></img>](https://easycode.profcomff.com/templates/docker-fastapi/workspace?mode=manual&param.Repository+URL=https://github.com/profcomff/userdata-api.git&param.Working+directory=userdata-api)

![Auth Schema](https://github.com/profcomff/auth-api/assets/5656720/ab2730be-054a-454c-ab76-5475e615bb64)

## Функционал
1. Управление категориями, параметрами, источниками данных.
2. Управление правами доступа к информации
3. Получение/изменение пользовательской информации через HTTP
4. Потоковое изменение пользовательской информации на основе данных передаваемых OAuth методами входа

- Про понятия использоованные в этом пункте можно почитать ниже(см. Основные абстракции)

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
    foo@bar:~$ pip install -r requirements.dev.txt
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

## ENV-variables description

:star2: Все параметры для Kafka являются необязательными

- `DB_DSN=postgresql://postgres@localhost:5432/postgres` – Данные для подключения к БД
- `KAFKA_DSN` - URL для подключение к Kafka
- `KAFKA_LOGIN` - логин для подключения к Kafka
- `KAFKA_PASSWORD` - пароль для подключения к Kafka
- `KAFKA_TOPICS` - Kafka топики, из которых читается информация
- `KAFKA_GROUP_ID` - Группа, от имени которой происходит чтение топиков
- Остальные общие для всех АПИ параметры описаны [тут](https://docs.profcomff.com/tvoy-ff/backend/settings.html)

## Основные абстракции

- Параметр - поле для пользовательской информации(например: Email, Телефон, Адрес, Курс обучения, Номер студенческого билета)

- Категория - объединение нескольких параметров по общему признаку. Например: Email, Телефон - _личная информация_; Курс обучения, Номер студенческого билета - _учеба_. Категория имеет `read_scope` - право на её чтение другими пользователями и `update_scope` - право на её изменение дургими пользователями

- Источник - откуда пришла информация о пользователе. Наприимер: VK, GitHub, LKMSU, User(он сам её добавил), Admin(админ её добавил). Источник имеет `trust_level`: то есть информации из одних источников мы можем доверять больше, чем другим

- Информация - само значение поля. Имеет ссылку на параметр и источник. Соответственно, значение одного параметра у пользователя может быть списком, так как информация для этого параметра пришла из различных источников

### Пример

Пользователь с `id=1`

| Категория  |  Параметр | Источник  |  Значение |
|---|---|---|---|
| Учёба  | Курс обучения  |  User | 4  |
| Учёба  | Курс обучения  | LKMSU  | 4  |
| Учёба  |  Номер студенческого билета | LKMSU  |  42424242 |
| Личная информация  | Email  |  User | email1@real.email  |
| Личная информация  | Email  | Admin  | email2@real.email  |
| Личная информация  |  Email | VK  |  email3@vk.real.email |
| Личная информация  | Email  |  Yandex | email4@ya.real.email  |
| Личная информация  | Email  | GitHub  | email5@github.email  |
| Личная информация  |  Телефон | User  |  +79094242 |


## Сценарий использования

### Создать категорию

1. Дёрнуть ручку `POST /category`. Вы передаете
```json
{
  "name": "", // Имя категории
  "read_scope": "", // Скоуп на чтение
  "update_scope": "" // Скоуп на запись
}
```
2. Сооздать в Auth API нужные scopes(если передали не `null`)

### Создать параметр

1. Дернуть ручку `POST /category/{category_id}/param`. Передать
```json
{
  "name": "", // Имя параметра
  "is_required": bool, // Обязателен ли он
  "changeable": bool, // Изменяем ли он после установки
  "type": "all || last || most_trusted" // Какой значение параметра из множества, задаваемого источником, будет возвращаться
}
```

### Получить список категорий

1. Дернуть ручку `GET /category`. Если нужна иинформация о параметрах, которые есть в каждой из категорий, то дернуть ручку `GET /category?query=param`

### Обновить информацию о пользователе

1. Дернуть ручку `POST /user/{user_id}`, передать туда
```json
{
  "items": [ // Список новых значений
    {
      "category": "", // Имя категории в которой находится параметр
      "param": "", // Имя изменяемого параметра
      "value": "" // Новое значение. Если раньше значения не существовало, то оно будет создано. Если передать null, то значение будет удалено.
    }
  ],
  "source": "string" // Источник информации. По http доступно только user и admin
}
```
- Информацию меняется только в пределах источника. То есть админ не может поменять инфоормацию, переданную пользователем. Он может только создать новую или поменять информацию из источника admin

- Пользователь может создать любую информацию о себе

- Пользователь может обновить/удалить только _изменяемую_ информацию

- Неизменяемая информация изменяема при наличии scope `userdata.info.update`

- Обновить информацию о другом пользователе из конкретноой категории можно только при наличии права на изменение в этой категории (см. `category.update_scope`)

### Получить информацию о пользователе

Дернуть ручку `GET /user/{user_id}`. Информация вернутся в соотвествии с переданными scopes.

- Пользователь может получить всю информацию о себе

- Любой другой человек может получить только информацию из тех категорий на которые у него есть права (см `category.read_scope`)

- Информация будет возвращаться в соответствии с поставленными `param.type`.
  - Если поставлен `all` то вернется информация соотв. данному параметру из всех источников
  - `last` - вернется последняя обновленная информация
  - `most_trusted` - вернется информация из самого доверенного источника

## Contributing

- Основная [информация](https://docs.profcomff.com/tvoy-ff/backend/index.html) по разработке наших приложений

- [Ссылка](https://github.com/profcomff/userdata-api/blob/main/CONTRIBUTING.md) на страницу с информацией по разработке userdata-api
