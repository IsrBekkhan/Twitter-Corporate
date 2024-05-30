import aiofiles
import aiohttp
from random import randint
import asyncio
from typing import Coroutine
import json

fox_url = "https://fish-text.ru/get"

#
# async def test():
#     query_params = {
#         "number": 1
#     }
#     async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
#         async with client.get(fox_url, params=query_params) as response:
#             print(response.status)
#             if response.status == 200:
#                 text = await response.json(encoding="utf-8", content_type="text/html")
#                 print(text["text"])
#
#
# if __name__ == "__main__":
#     asyncio.run(test())

# list_d = [{'имя': 'Анна', 'возраст': 25}, {'имя': 'Вас', 'возраст': 30}, {'имя': 'Маша', 'возраст': 18}]
#
# sorted_list = sorted(list_d, key=lambda x: len(x["имя"]), reverse=True)
# print(sorted_list)

try:
    a = 1 / 0
except ZeroDivisionError as exc:
    typ = type(exc)
    t = str(typ).split("'")
    print(t[1])
