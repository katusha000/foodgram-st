from users.models import User
from recipes.models import (
    MIN_TIME, MAX_TIME,
    Ingredients, Recipes, IngredientInRecipe,
    MAX_INGREDIENT, MIN_INGREDIENT,
)

import re
import base64

from rest_framework import serializers
from django.contrib.auth import password_validation
from django.core.files.base import ContentFile

MAX_PASSWORD_LENGTH = 128


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)


class BriefRecipesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = (
            "id",
            "name",
            "image",
            "cooking_time"
        )


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = (
            "id",
            "name",
            "measurement_unit"
        )


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source="ingredient"
    )
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT, max_value=MAX_INGREDIENT
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            "amount"
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source="ingredient.id")
    name = serializers.ReadOnlyField(
        source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount"
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "username", "password",
            "first_name", "last_name",
        )

    def validate_username(self, value):
        if not re.match(r"^[\w.@+-]+\Z", value):
            raise serializers.ValidationError(
                "Недопустимые символы в поле username"
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "username", "first_name",
            "last_name", "avatar", "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request and request.user.is_authenticated
            and request.user.following.filter(user=obj).exists()
        )


class FollowSerializer(UserDetailSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserDetailSerializer.Meta):
        fields = (*UserDetailSerializer.Meta.fields,
                  "recipes", "recipes_count")

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        if limit := self.context["request"].query_params.get("recipes_limit"):
            queryset = queryset[:int(limit)] if limit.isdigit() else queryset
        return BriefRecipesSerializer(
            queryset, many=True, context=self.context).data


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class PasswordUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=MAX_PASSWORD_LENGTH, required=True)
    new_password = serializers.CharField(
        max_length=MAX_PASSWORD_LENGTH, required=True)

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data["current_password"]):
            raise serializers.ValidationError({
                "current_password": "Текущий пароль неверный."
            })
        password_validation.validate_password(data["new_password"])
        if user.check_password(data["new_password"]):
            raise serializers.ValidationError({
                "new_password": "Пароль совпадает со старым."
            })

        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class RecipesSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer(
        many=True,
        write_only=True
    )
    author = UserDetailSerializer(
        read_only=True)
    image = Base64ImageField(
        allow_null=False,
        required=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_TIME, max_value=MAX_TIME
    )

    class Meta:
        model = Recipes
        fields = (
            "id", "author", "ingredients",
            "is_in_shopping_cart", "is_favorited",
            "name", "image", "text", "cooking_time"
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Обязательно добавьте фото рецепта."
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Нужен хотя бы один ингредиент."
            )

        ingredient_ids = [item["ingredient"].id for item in value]

        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise serializers.ValidationError(
                "Повторяющихся ингредиентов не должно быть."
            )

        return value

    def validate(self, data):
        if self.context.get("request").method == "PATCH":
            required_fields = {
                "ingredients",
                "name", "image",
                "text", "cooking_time"
            }
            missing_fields = required_fields - data.keys()
            if missing_fields:
                raise serializers.ValidationError({
                    field: "Поле обязательно при обновлении."
                    for field in missing_fields
                })
        return data

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.shopping_cart.filter(recipe=obj).exists()
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and user.favorite_recipes.filter(recipe=obj).exists()
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipes.objects.create(**validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def _save_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
            for ingredient in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update({
            "ingredients": IngredientInRecipeSerializer(
                instance.recipe_ingredients.all(),
                many=True
            ).data,
            "image": representation.get("image") or ""
        })
        return representation

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if ingredients_data is not None:
            instance.ingredients.clear()
            self._save_ingredients(instance, ingredients_data)

        return instance
