import random
from typing import Any


def random_choice_or_None(choices: list) -> Any:
    choices.append(None)
    return random.choice(choices)


def random_choice_or_blank(choices: list) -> Any:
    choices.append("")
    return random.choice(choices)


def random_bool_or_None():
    return random_choice_or_None([True, False])


def random_bool():
    return random.choice([True, False])
