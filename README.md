<h1 align="center">Twitter Corporate</h1>
  

<p align="center">

<img alt="Static Badge" src="https://img.shields.io/badge/Docker-26.1.4-white?logo=docker&logoColor=white&labelColor=%232496ED">

<img alt="Static Badge" src="https://img.shields.io/badge/Python-3.10-%23EAD248?logo=python&logoColor=white&labelColor=%233776AB">

<img alt="Static Badge" src="https://img.shields.io/badge/FastAPI-0.110.2-green?logo=fastapi&logoColor=white&labelColor=%23009688">

<img alt="Static Badge" src="https://img.shields.io/badge/SQLAlchemy-2.0.29-%23D71F00?logo=sqlalchemy&logoColor=white&labelColor=%2385924F">

<img alt="Static Badge" src="https://img.shields.io/badge/PostgreSQL-16.3-gray?logo=postgresql&logoColor=white&labelColor=%234169E1">

<img alt="Static Badge" src="https://img.shields.io/badge/pytest-8.1.2-%23c7d302?logo=pytest&logoColor=white&labelColor=%230A9EDC">

</p>

<p align="center">
<img src="./readme_assets/main_page.png" width="100%"></p>

## Описание сервиса

Twitter Corporate - урезанная версия твиттера, предназначенного для использования в корпоративной сети,
в качестве серивиса микроблогов. Имеет следующие функциональные возможности:
1. Пользователь может добавить новый твит.
2. Пользователь может удалить свой твит.
3. Пользователь может подписаться на другого пользователя.
4. Пользователь может отписаться от другого пользователя.
5. Пользователь может отмечать твит как понравившийся.
6. Пользователь может убрать отметку «Нравится».
7. Пользователь может получить ленту из своих твитов и твитов от пользователей, на которых он подписан. 
Сортировка списка твитов ленты будет отображен отсортированным в порядке убывания по популярности 
8. Твит может содержать картинку.

## Установка и запуск

1. Для запуска сервиса вам понадобится система с установленным Docker.
2. Если он уже установлен - скопируйте репозиторий на свою систему.
3. В директории с файлом docker-compose.yml создайте файл __.env__ и определите в нём 
переменные окружения. Пример содержимого файла __.env__ описан в файле __.env.template__, а также далее на данной 
странице
4. И наконец - из директории с файлом docker-compose.yml ведите следующую команду в терминале:

```
docker compose up
```

5. Теперь откройте интернет-браузер и введите в строке URL сервиса: по умолчанию http://localhost/8000 

## Режим демонстрации

Режим демонстрации позволит вам увидеть работу сервиса, как она выглядела бы после некоторого времени 
использования в крупной корпоративной сети, т.е. с заполненными страницами с твитами и картинками. 
Включить этот режим можно с передачей переменного окружения __DEMO_MODE__ со значением __true__.
После запуска сервиса, таблицы базы данных будут заполненны с множеством случайных записей.
<p align="center">
<img src="./readme_assets/demo_mode.gif" width="100%"></p>

## Настройки запуска

При желании можно запустить сервис с предпочтительными для вас настройками. Они находятся в файле .env корневой 
директории сервиса. Список включает следующие настройки:

* __POSTGRES_USER=admin__ - логин пользователя в СУБД Postgres
* __POSTGRES_PASSWORD=admin__ - пароль пользователя в СУБД Postgres
* __POSTGRES_DB=twitter_db__ - название базы данных в СУБД Postgres
 
* __POSTGRES_PORT=5432__ - порт, который будет слушать запросы в СУБД Postgres
* __FASTAPI_PORT=8000__ - порт сервиса, который будет слушать http-запросы клиента

* __DEMO_MODE=false__ - если установить значение __true__, сервис после запуска заполнит базу данных случайными 
записями. Это полезная функция, использование которой представит вам работу сервиса с заполненными страницами с 
различными твитами с различными картинками.

Для безопасности можно удалить этот файл .env и передать эти переменные в команде запуска __docker compose run__ 
в параметре __--env__.
Пример:
```
docker compose run --env POSTGRES_USER=admin <service name>
```

## Документация API

Всю документация OpenAPI маршрутов приложения вы можете получить по ссылке http://localhost/8000/docs
<p align="center">
<img src="./readme_assets/docs.png" width="100%"></p>

или по ссылке http://localhost/8000/redoc с другим стилем визуализации
<p align="center">
<img src="./readme_assets/redoc.png" width="100%"></p>

## Тестирование

Для тестирования функций приложения, необходимо сначала установить все зависимости из файла 
_.twitter_clone/tests/requirements_for_tests.txt__ командой:
```
pip install -r <requiremets file>
```
Далее из директории twitter_clone c файлом конфигурации pytest.ini необходимо запустить команду:
```
pytest -v
```

## Обратная связь

По всем вопросам пишите мне на почту: 
<a href="mailto:israpal@bk.ru" rel="noopener noreferrer" class="link">Бекхан Исрапилов</a>
