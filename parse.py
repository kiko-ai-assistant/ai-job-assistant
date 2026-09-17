import requests
import time

headers = {
    'User-Agent': "AIKikoAssistant/1.0 (vovvovin5124@yandex.ru)",
    'HH-User-Agent': "AIKikoAssistant/1.0 (vovvovin5124@yandex.ru)"  # дополнительный заголовок
}
response = requests.get('https://api.hh.ru/vacancies', headers=headers)
print(f"Status: {response.status_code}")
print(f"Body: {response.text}")
