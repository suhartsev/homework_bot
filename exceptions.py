class TokenError(Exception):
    """Отсутствует один или несколько токенов."""

    pass


class CheckApiKey(Exception):
    """Произошёл сбой получения ключей API response."""

    pass


class CheckHomeworkStatus(Exception):
    """Произошёл сбой получения статуса домашней работы."""

    pass


class ResponseError(Exception):
    """Произошёл сбой в ответе сервера."""

    pass


class GetEndpointError(Exception):
    """'Произошёл сбой при запросе к эндпоинту."""

    pass


class SendMessageError(Exception):
    """Произошёл сбой в отправке сообщения."""

    pass
