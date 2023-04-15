import random
import string


def random_string(length: int = 12):
    return "".join([random.choice(string.ascii_lowercase) for _ in range(length)])
