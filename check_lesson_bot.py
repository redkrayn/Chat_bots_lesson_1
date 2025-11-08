import time
import logging
import requests

from environs import Env
from telegram import Bot


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def setup_logging(tg_bot=None, chat_id=None):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(message)s'
    )

    tg_handler = TelegramLogsHandler(tg_bot, chat_id)
    tg_handler.setLevel(logging.INFO)
    tg_handler.setFormatter(formatter)
    logger.addHandler(tg_handler)

    return logger


def check_update_lesson(bot, chat_id, devman_token, logger):
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
                    bot.send_message(
                        bot,
                        chat_id,
                        'У вас проверили работу "Отправляем уведомления о проверке работ"\n'
                        'К сожалению, в работе нашлись ошибки.\n'
                        f'Ссылка на урок: {devman_response["new_attempts"][0].get("lesson_url")}'
                    )
                else:
                    bot.send_message(
                        bot,
                        chat_id,
                        'У вас проверили работу "Отправляем уведомления о проверке работ"\n'
                        'Преподавателю всё понравилось, можно приступать к следующему уроку!'
                    )

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            logger.warning('Проблемы с интернетом, переподключение...')
            time.sleep(5)
            continue
        except Exception as e:
            logger.error(f"Бот упал с ошибкой: {e}", exc_info=True)
            time.sleep(30)
            continue


def main():
    env = Env()
    env.read_env()

    telegram_bot_token = env('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = env('TELEGRAM_CHAT_ID')
    devman_token = env('DEVMAN_TOKEN')

    bot = Bot(token=telegram_bot_token)
    logger = setup_logging(bot, telegram_chat_id)

    logger.info('Бот запущен')
    check_update_lesson(bot, telegram_chat_id, devman_token, logger)


if __name__ == "__main__":
    main()
