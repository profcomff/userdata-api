import random
import string


def random_string(length: int = 12):
    """
    Сгенерировать рандомную строку
    :param length: длина строки(по умолчанию 12)
    :return: Сгенериированную строку
    """
    return "".join([random.choice(string.ascii_lowercase) for _ in range(length)])
