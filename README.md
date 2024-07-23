##### Приветствую тебя на моём проекта Foodgram!
Это сервис для создания рецептов и с возможностью поделиться ими с окружающими.

Здесь ты сможешь:
- выставлять свои рецепты на обозрения.
- подписываться на других авторов.
- добавлять любимые рецепты в избранное.
- скачивать список продуктов для выбранных тобою рецептов.

### Для начала работы:

Склонируй репозиторий себе
`git clone https://github.com/h-inek/foodgram-project-react.git`

В директории infra должен быть файл с переменными .env, который тебе потребуется заполнить самостоятельно.
Я добавил в директорию файл .env.example для наглядности.

Шаблон для заполнения:
- DB_ENGINE='django.db.backends.postgresql'
- DB_NAME=db_name
- POSTGRES_USER=user_name
- POSTGRES_PASSWORD=user_password
- DB_HOST=db
- DB_PORT=5432
- SECRET_KEY=XXXX

Так же добавь себе в Secrets/Actions необходимые для работы на удалённом сервере данные.
Помимо указанных выше потребуются так же:

- данные от твоего DockerHub. Назови их DOCKER_USER и DOCKER_PASSWORD
- адрес твоего сервера HOST
- имя, под который ты заходишь на сервер USER
- Секретная часть ключа ssh SSH_KEY
- Если у тебя есть рабочий телеграм-бот, то добавь свой id и token для отправки уведолмений в Telegram. TO_TOKEN, TELEGRAM_TOKEN.

Так же добавь адрес своего сервера в ALLOW_HOST в api_yamdb/api_yamdb/settings.py и в server_name в infra/nginx/default.conf

В workflows уже описаны все необходимые для развертки на сервере работы. Добавь ссылку на свой DockerHub в работы build_and_push_to_docker_hub и deploy.

Это так же потребуется сделать в infra/docker-compose.yaml

Почти всё готово!

Перенеси файлы docker-compose.yaml и nginx.conf на свой боевой сервер:

```
scp [путь к файлу] [имя пользователя]@[имя сервера/ip-адрес]:[путь к файлу]
```
Пример:
```
scp docker-compose.yaml username@123.123.123.123:~/
```

Отлично! Осталось только запушить все изменения и workwlows сделает за тебя всю остальную работу:

```
git add . && git commit -m 'commit' && git push
```

Дождись уведомления в телеграм о выполненной работе и можешь проверять.

Не забудь перед этим создать суперюзера
```
docker-compose exec web python manage.py createsuperuser
```

В проекте уже подготовлен файл с ингредиентами и тэгами, ими надо заполнить БД:

```
docker-compose exec web python manage.py load_data
```

Вот ты и подготовил свой рабочий проект. Удачи!

Автор проекта:

Максим Кавтырев - https://github.com/h-inek

![](https://github.com/h-inek/foodgram-project-react/actions/workflows/main.yml/badge.svg)

### Функционал подготовлен для работы с PostgreSQL и развёрткой в Docker. 

### Используемые технологии
Python 3.7 Django 2.2.16 REST Framework 3.12.4 PyJWT 2.1.0 Django filter 21.1 PostgreSQL 12.2 Docker 20.10.2 подробнее см. прилагаемый файл зависимостей requrements.txt


