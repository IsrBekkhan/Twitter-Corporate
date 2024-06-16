<h1 align="center">Twitter Corporate</h1>
<h2 align="center">

[![Mentioned in Awesome Vue.js](https://awesome.re/mentioned-badge.svg)](https://github.com/vuejs/awesome-vue)

</h2>

<p align="center">
  
<img src="https://img.shields.io/npm/dy/silentlad">

<img src="https://img.shields.io/badge/made%20by-silentlad-blue.svg" >

<img src="https://img.shields.io/badge/vue-2.2.4-green.svg">

<img src="https://img.shields.io/github/stars/silent-lad/VueSolitaire.svg?style=flat">

<img src="https://img.shields.io/github/languages/top/silent-lad/VueSolitaire.svg">

<img src="https://img.shields.io/github/issues/silent-lad/VueSolitaire.svg">

<img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat">
</p>

<img src="./readme_assets/main_page.png" width="100%">

## Описание сервиса

Twitter Corporate - урезанная версия твиттера, предназначенного для использования в корпоративной сети, в качестве серивиса микроблогов. Имеет следующие функциональные возможности:
1. Пользователь может добавить новый твит.
2. Пользователь может удалить свой твит.
3. Пользователь может подписаться на другого пользователя.
4. Пользователь может отписаться от другого пользователя.
5. Пользователь может отмечать твит как понравившийся.
6. Пользователь может убрать отметку «Нравится».
7. Пользователь может получить ленту из своих твитов и твитов от пользователей, на которых он подписан. Сортировка списка твитов ленты будет отображен отсортированным в
порядке убывания по популярности 
8. Твит может содержать картинку.

## Установка и запуск

Для запуска сервиса вам понадобится система с установленным Docker.
Если он уже установлен - скопируйте репозиторий и из директории с файлом docker-compose.yml ведите следующую команду в терминале:

```
docker compose up
```
*Примечание: перед запуском убедитесь, что в директории запуска имеется файл .env c определёнными переменными окружения*

Теперь откройте интернет-браузер и введите в строке URL сервиса: по умолчанию http://localhost/8000 

## Настройки запуска

При желании можно запустить сервис с предпочтительными для вас настройками. Они находятся в файле .env корневой директории сервиса. Список включает следующие настройки:

* POSTGRES_USER=admin - логин пользователя в СУБД Postgres
* POSTGRES_PASSWORD=admin - пароль пользователя в СУБД Postgres
* POSTGRES_DB=twitter_db - название базы данных в СУБД Postgres
 
* POSTGRES_PORT=5432 - порт, который будет слушать запросы в СУБД Postgres
* FASTAPI_PORT=8000 - порт сервиса, который будет слушать http-запросы клиента

* TEST_MODE=false - если установить значение true, то сервис после запуска заполнит базу данных случайными записями. Это полезная функция, использование которой представит вам работу сервиса с заполненными страницами с различными твитами с различными картинками.

Для безопасности можно удалить этот файл .env и передать эти переменные в команде запуска __docker compose run__ в параметре __--env__.
Пример:
```
docker compose run --env POSTGRES_USER=admin <service name>
```

## Project setup

```
npm install
npm run serve
```

## Support on Beerpay

Обратная связь
