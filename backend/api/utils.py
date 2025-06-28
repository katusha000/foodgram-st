import string
from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipes

ALPHABET = string.digits + string.ascii_lowercase
NUMERAL_BASE = 36


def encode36(number):
    if number < 0:
        raise ValueError("Число должно быть положительным.")
    if number == 0:
        return "0"
    number36 = ''

    while number:
        number, i = divmod(number, NUMERAL_BASE)
        number36 = ALPHABET[i] + number36

    return number36


def s_redirect(request, id):
    id = int(id, NUMERAL_BASE)
    recipe = get_object_or_404(Recipes, id=id)
    return redirect(f"/recipes/{recipe.id}/")
