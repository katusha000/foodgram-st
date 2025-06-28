# Foodgram - продуктовый помошник

Foodgram — это удобное веб-приложение для кулинарных энтузиастов, которое помогает публиковать, находить рецепты и составлять списки покупок. Пользователи могут делиться своими рецептами, сохранять любимые блюда, подписываться на интересных авторов и быстро создавать перечень необходимых ингредиентов.

## 🚀 Ключевые функции

- Регистрация и вход пользователей
- Публикация рецептов с подробным описанием, ингредиентами и изображениями
- Добавление рецептов в избранное
- Формирование и загрузка списка покупок
- Фильтрация рецептов по категориям, таким как завтрак, обед и ужин
- Подписка на авторов рецептов
- Документация и примерные запросы к API

## 🛠️ Используемые технологии

- Backend: Python, Django, Django REST Framework, Djoser
- Frontend: React
- База данных: PostgreSQL
- Контейнеризация: Docker и Docker Compose
- Веб-сервер: Nginx

## ⚡ Как запускать
1. Склонируйте репозиторий командой: `git clone https://github.com/katusha000/foodgram-st.git`
2. Создайте в папке backend файл `.env` и заполните его по шаблону:
```plaintext
SECRET_KEY='ваш секретный ключ разработки'
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB='название базы данных'
POSTGRES_USER='имя пользователя'
POSTGRES_PASSWORD='пароль'
DB_HOST=db
DB_PORT=5432
```
2. Создайте в папке infra файл `.env` и заполните его (данные должны совпадать с .env в папке backend!):
```plaintext
POSTGRES_DB='название базы данных'
POSTGRES_USER='имя пользователя'
POSTGRES_PASSWORD='пароль'
DB_HOST=db
DB_PORT=5432
```
3. Переходим в папку infra и запускаем проект командой `docker compose up --build`, в последующие разы хватит `docker compose up`.
4. Переходим внутрь контейнера с бэкэндом командой: `docker exec -it foodgram-backend bash`
5. Выполняем и применияем миграции командами (последовательно): `python manage.py makemigrations`, `python manage.py migrate`
6. Загружаем фикстуры в базу данных командой: `python manage.py loaddata data/data.json`
7. Собираем статические файлы командой: `python manage.py collectstatic`
8. Копируем собранную статику в volume-хранилище: `cp -r collected_static/. /backend_static/static/`
9. Готово! Выходим из контейнера сочетанием клавиш: *ctrl + D*

## 📍 Доступные адреса:

- `localhost/` - главная страница проекта
- `localhost/api/docs` - документация
- `localhost/admin` - админ-панель

## CI/CD:

Автоматизация сборки, тестирования и деплоя реализована через GitHub Actions.

При пуше в ветку main происходит:

- Проверка кода линтером flake8
- Сборка и публикация Docker-образов backend, frontend и nginx на DockerHub
- Автоматический деплой на сервер

**Образы доступны по ссылкам:**
- [foodgram_backend](https://hub.docker.com/r/katusha000/foodgram_backend)
- [foodgram_frontend](https://hub.docker.com/r/katusha000/foodgram_frontend)
- [foodgram_gateway](https://hub.docker.com/r/katusha000/foodgram_gateway)

## 👤 Автор проекта:

- [Бирюкова Светлана](https://github.com/katusha000)