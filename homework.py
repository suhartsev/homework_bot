import logging
import time

import requests
import telegram
from http import HTTPStatus

import error_msg_info
from exceptions import (
    CheckApiKey, CheckHomeworkStatus,
    ResponseError, TokenError,
    GetEndpointError, SendMessageError
)
from settings import (
    ENDPOINT, FIRST_CUTOOF_ZERO,
    HEADERS, HOMEWORK_VERDICTS,
    PRACTICUM_TOKEN, RETRY_PERIOD,
    TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)


def check_tokens():
    """Проверка наличия токенов и чат-id."""
    tokens_list = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    ]
    for tokens in tokens_list:
        if tokens is None:
            return False
        return True


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(error_msg_info.SEND_MSG_TG)
    except Exception:
        logger.error(error_msg_info.ERROR_SEND_MSG)
        raise SendMessageError(error_msg_info.ERROR_SEND_MSG)
    else:
        logger.debug(error_msg_info.SEND_MSG_OK)


def get_api_answer(current_timestamp):
    """Проверка ответа сервера."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        raise GetEndpointError(error_msg_info.ERROR_GET_ENDPOINT)
    if response.status_code != HTTPStatus.OK:
        raise ResponseError(f'{error_msg_info.ERROR_NOT_200}'
                            f'{response.status_code}')
    return response.json()


def check_response(response):
    """Проверка API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(error_msg_info.ERROR_HOMEWORKS_NOT_DICT)
    if 'homeworks' not in response:
        raise CheckApiKey(error_msg_info.ERROR_GET_NOT_KEY_HOMEWORKS)
    if not isinstance(response['homeworks'], list):
        raise TypeError(error_msg_info.ERROR_HOMEWORKS_NOT_LIST)
    return response['homeworks']


def parse_status(homework):
    """Проверяем статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError(error_msg_info.ERROR_GET_NOT_KEY_HOMEWORK_NAME)
    if 'status' not in homework:
        raise CheckHomeworkStatus(error_msg_info.ERROR_GET_NOT_KEY_STATUS)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(error_msg_info.ERROR_NOT_VERDICTS_FOR_STATUS)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return (f'{error_msg_info.STATUS_WOMEWORK_CHANGE}'
            f'"{homework_name}". {verdict}')


def main():
    """Основная функция программы."""
    logger.info(error_msg_info.CHEK_TOKEN)
    if not check_tokens():
        logger.critical(error_msg_info.ERROR_NOT_FOUND_TOKEN)
        raise TokenError(error_msg_info.ERROR_NOT_FOUND_TOKEN)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, error_msg_info.STSRT_BOT_MSG)
    logger.info(error_msg_info.STSRT_BOT_MSG)
    current_timestamp = FIRST_CUTOOF_ZERO
    previous_message = ''
    error_message = ''
    while True:
        try:
            response = get_api_answer(FIRST_CUTOOF_ZERO)
            homeworks = check_response(response)
            if homeworks:
                status_update = parse_status(homeworks[0])
                if previous_message != status_update:
                    send_message(bot, status_update)
                    previous_message = status_update
            logger.debug(error_msg_info.STATUS_WOMEWORK_NOT_CHANGE)
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            message = (
                f'{error_msg_info.ERROR_PROGRAM_FAILURE}{error}'
            )
            logger.error(message)
            if error_message != message:
                send_message(bot, message)
                error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s,'
            '%(levelname)s,'
            '%(message)s,'
            '%(name)s,'
            '%(funcName)s,'
            '%(lineno)d,'
        ),
        filename='main.log',
        filemode="w",
    )
    logger = logging.getLogger(__name__)
    main()
