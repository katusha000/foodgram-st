"""Описание вспомогательных функций."""

NUMERAL_BASE = 36


def base36encode(number):
    """Функция переводит число из 10-ой системы счисления в 36-ую."""
    if number < 0:
        raise ValueError("Число не может быть меньше 0")

    if number == 0:
        return "0"

    base36 = ''
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'

    while number:
        number, i = divmod(number, NUMERAL_BASE)
        base36 = alphabet[i] + base36

    return base36
