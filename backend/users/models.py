from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(
        verbose_name="Имя", max_length=150)

    last_name = models.CharField(
        verbose_name="Фамилия", max_length=150)

    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=150, unique=True)

    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        max_length=254, unique=True)

    avatar = models.ImageField(
        verbose_name="Аватар пользователя",
        upload_to="users/avatars/", null=True,
        blank=True)

    REQUIRED_FIELDS = (
        "username", "first_name", "last_name"
    )
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Follow(models.Model):
    user = models.ForeignKey(
        User, verbose_name="Пользователь",
        related_name="following",
        on_delete=models.CASCADE,
    )
    following = models.ForeignKey(
        User, verbose_name="Подписан на",
        related_name="followers",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["user", "following"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"],
                name="unique_follow"
            )
        ]

    def __str__(self):
        return f"{self.user} подписан на {self.following}"
