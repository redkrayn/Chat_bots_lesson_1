import requests
from aiogram import Bot, Dispatcher
import asyncio

from environs import Env


env = Env()
env.read_env()

TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = env('TELEGRAM_CHAT_ID')

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def send_self_message(text: str):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)


async def check_update_lesson():
    url = 'https://dvmn.org/api/long_polling/'
    devman_token = env('DEVMAN_TOKEN')
    headers = {
        'Authorization': f'Token {devman_token}'
    }
    timestamp = None
    while True:
        params = {}
        if timestamp is not None:
            params['timestamp'] = timestamp
        try:
            response = requests.get(url, headers=headers, params=params, timeout=86400)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'timeout':
                timestamp = data.get('timestamp_to_request')
            elif data.get('status') == 'found':
                timestamp = data.get('last_attempt_timestamp', timestamp)
                if data['new_attempts'][0].get('is_negative'):
                    await send_self_message(
                        'У вас проверили работу "Отправляем уведомления о проверке работ"\n'
                        'К сожалению, в работе нашлись ошибки.\n'
                        f'Ссылка на урок: {data['new_attempts'][0].get('lesson_url')}'
                    )
                elif not data['new_attempts'][0].get('is_negative'):
                    await send_self_message(
                        'У вас проверили работу "Отправляем уведомления о проверке работ"\n'
                        'Преподавателю всё понравилось, можно приступать к следующему уроку!'
                    )

        except requests.exceptions.ReadTimeout:
            print('timeout')
            continue
        except requests.exceptions.ConnectionError:
            print('no internet')
            continue


async def main():
    await asyncio.gather(
        check_update_lesson()
    )


if __name__ == "__main__":
    asyncio.run(main())
