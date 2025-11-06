import requests
import asyncio
import time
from environs import Env
from telegram import Bot


def send_self_message(bot, chat_id, text: str):
    asyncio.run(bot.send_message(chat_id=chat_id, text=text))


def check_update_lesson(bot, chat_id, devman_token):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {devman_token}'
    }
    timestamp = None

    while True:
        params = {}
        if timestamp is not None:
            params['timestamp'] = timestamp

        try:
            response = requests.get(url, headers=headers, params=params, timeout=90)
            response.raise_for_status()
            devman_response = response.json()

            if devman_response.get('status') == 'timeout':
                timestamp = devman_response.get('timestamp_to_request')
            elif devman_response.get('status') == 'found':
                timestamp = devman_response.get('last_attempt_timestamp', timestamp)

                if devman_response['new_attempts'][0].get('is_negative'):
                    send_self_message(
                        bot,
                        chat_id,
                        'У вас проверили работу "Отправляем уведомления о проверке работ"\n'
                        'К сожалению, в работе нашлись ошибки.\n'
                        f'Ссылка на урок: {devman_response["new_attempts"][0].get("lesson_url")}'
                    )
                else:
                    send_self_message(
                        bot,
                        chat_id,
                        'У вас проверили работу "Отправляем уведомления о проверке работ"\n'
                        'Преподавателю всё понравилось, можно приступать к следующему уроку!'
                    )

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            print('Проблемы с интернетом, пробуем переподключиться...')
            time.sleep(5)
            continue


def main():
    env = Env()
    env.read_env()

    telegram_bot_token = env('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = env('TELEGRAM_CHAT_ID')
    devman_token = env('DEVMAN_TOKEN')

    bot = Bot(token=telegram_bot_token)
    check_update_lesson(bot, telegram_chat_id, devman_token)


if __name__ == "__main__":
    main()
