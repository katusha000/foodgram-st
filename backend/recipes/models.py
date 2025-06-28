from users.models import User

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

MIN_INGREDIENT = 1
MAX_INGREDIENT = 32000
MIN_TIME = 1
MAX_TIME = 32000


class Ingredients(models.Model):
    name = models.CharField(
        max_length=128,
        unique=True,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name="Единица",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipes(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
    )
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Фото",
    )
    text = models.TextField(
        verbose_name="Описание",
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through="IngredientInRecipe",
        related_name="recipes",
        verbose_name="Список ингредиентов",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (минуты)",
        validators=[
            MinValueValidator(
                MIN_TIME, message="Минимум 1 минута"
            ),
            MaxValueValidator(
                MAX_TIME, message="Слишком много минут"
            ),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата добавления", auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f"{self.name}"


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipes, verbose_name="Рецепт",
        on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredients, verbose_name="Ингредиент",
        on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиента",
        validators=[
            MinValueValidator(
                MIN_INGREDIENT, message="Добавьте хотя бы 1 ингредиент"
            ),
            MaxValueValidator(
                MAX_INGREDIENT, message="Слишком много ингредиентов"
            ),
        ],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_in_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.amount} {self.ingredient} в {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, verbose_name="Владелец корзины",
        on_delete=models.CASCADE,
        related_name="shopping_cart",
    )
    recipe = models.ForeignKey(
        Recipes, verbose_name="Рецепт в корзине",
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
    )

    class Meta:
        verbose_name = "Рецепт из корзины"
        verbose_name_plural = "Рецепты из корзины"
        ordering = ["user", "recipe"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.recipe}"


class Favorites(models.Model):
    user = models.ForeignKey(
        User, verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="favorite_recipes",
    )
    recipe = models.ForeignKey(
        Recipes, verbose_name="Блюдо",
        on_delete=models.CASCADE,
        related_name="favorited_by_user",
    )

    class Meta:
        ordering = ["user", "recipe"]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorites",
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.recipe}"
