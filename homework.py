import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import error_msg_info

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
logger.addHandler(log_handler)


def check_tokens():
    """Проверка наличия токенов и чат-id."""
    logger.info(error_msg_info.CHEK_TOKEN)
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return all(tokens)


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        logger.info(error_msg_info.SEND_MSG_TG)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        logger.error(error_msg_info.ERROR_SEND_MSG)
    else:
        logger.debug(error_msg_info.SEND_MSG_OK)


def get_api_answer(current_timestamp):
    """Проверка ответа сервера."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException:
        logger.error(error_msg_info.ERROR_GET_ENDPOINT)
    if response.status_code == HTTPStatus.OK:
        return response.json()
    if response.status_code != HTTPStatus.OK:
        logger.error(f'{error_msg_info.ERROR_CONNECT_SERVER}'
                     f'{response.status_code}')
        raise (f'{error_msg_info.ERROR_NOT_200}{response.status_code}')
    else:
        logger.error(f'{error_msg_info.ERROR_GET_API}{response.status_code}')


def check_response(response):
    """Проверка API на корректность."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logger.error(error_msg_info.ERROR_GET_NOT_KEY_HOMEWORKS)
        raise KeyError(error_msg_info.ERROR_GET_NOT_KEY_HOMEWORKS)
    else:
        if not isinstance(homeworks, list):
            logger.error(error_msg_info.ERROR_HOMEWORKS_NOT_LIST)
            raise TypeError(error_msg_info.ERROR_HOMEWORKS_NOT_LIST)
        if not isinstance(response, dict):
            logger.error(error_msg_info.ERROR_HOMEWORKS_NOT_DICT)
            raise TypeError(error_msg_info.ERROR_HOMEWORKS_NOT_DICT)
        if not homeworks:
            logger.debug(error_msg_info.STATUS_WOMEWORK_NOT_CHANGE)
        return homeworks


def parse_status(homework):
    """Проверяем статус домашней работы."""
    if 'homework_name' not in homework:
        logger.error(error_msg_info.ERROR_GET_NOT_KEY_HOMEWORK_NAME)
        raise KeyError(error_msg_info.ERROR_GET_NOT_KEY_HOMEWORK_NAME)
    elif 'status' not in homework:
        logger.error(error_msg_info.ERROR_GET_NOT_KEY_STATUS)
        raise KeyError(error_msg_info.ERROR_GET_NOT_KEY_STATUS)
    else:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(error_msg_info.ERROR_NOT_VERDICTS_FOR_STATUS)
    else:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return (f'{error_msg_info.STATUS_WOMEWORK_CHANGE}'
                f'"{homework_name}". {verdict}')


def main():
    """Основная функция программы."""
    if not check_tokens():
        logger.critical(error_msg_info.ERROR_NOT_REQUIRED_VARIABLES)
        raise (error_msg_info.ERROR_NOT_REQUIRED_VARIABLES)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    send_message(bot, error_msg_info.STSRT_BOT_MSG)
    logging.info(error_msg_info.STSRT_BOT_MSG)
    while True:
        try:
            check_tokens()
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                status_update = parse_status(homeworks[0])
                send_message(bot, status_update)
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            error_msg = (f'{error_msg_info.ERROR_PROGRAM_FAILURE}{error}')
            logging.info(error_msg)
            send_message(bot, error_msg)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        filemode='w',
    )
    main()
