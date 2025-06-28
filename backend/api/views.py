from .utils import encode36
from users.models import Follow, User
from recipes.models import (
    Ingredients,
    Recipes,
    ShoppingCart,
    IngredientInRecipe,
    Favorites,
)
from .serializers import (
    FollowSerializer,
    UserRegistrationSerializer,
    UserDetailSerializer,
    AvatarUpdateSerializer,
    PasswordUpdateSerializer,
    IngredientsSerializer,
    RecipesSerializer,
    BriefRecipesSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter

from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Sum, F

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    AllowAny, IsAuthenticated,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        if self.action == "set_avatar":
            return AvatarUpdateSerializer
        if self.action == "update_password":
            return PasswordUpdateSerializer
        return UserDetailSerializer

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def set_avatar(self, request):
        user = request.user

        if request.method == "DELETE":
            if not user.avatar:
                return Response(
                    {"detail": "Аватар не установлен"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "PUT":
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["post"],
        detail=False,
        url_path="set_password",
        permission_classes=[IsAuthenticated],
    )
    def update_password(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Пароль изменён."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="subscribe",
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        following = self.get_object()
        user = request.user

        if user == following:
            return Response(
                {"detail": "Невозможно подписаться/отписаться на/от себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == "POST":
            return self._handle_subscribe(user, following)

        elif request.method == "DELETE":
            return self._handle_unsubscribe(user, following)

    def _handle_subscribe(self, user, following):
        if user.following.filter(following=following).exists():
            return Response(
                {"detail": "Вы уже подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=user, following=following)
        serializer = FollowSerializer(
            following,
            context={"request": self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_unsubscribe(self, user, following):
        subscription = user.following.filter(following=following).first()
        if not subscription:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        url_path="subscriptions",
        permission_classes=[IsAuthenticated],
    )
    def follows(self, request):
        user = request.user

        following = User.objects.filter(followers__user=user)
        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(
            following, request)
        serializer = FollowSerializer(
            page, context={"request": request}, many=True
        )

        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=["get"],
        detail=False,
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientsSerializer
    queryset = Ingredients.objects.all()
    filter_backends = (
        DjangoFilterBackend,)
    filterset_fields = ("name",)
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):

    serializer_class = RecipesSerializer
    filterset_class = RecipeFilter
    filter_backends = (
        DjangoFilterBackend, filters.SearchFilter
    )
    permission_classes = [
        IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly
    ]
    queryset = Recipes.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=["get"],
        detail=True,
        url_path="get-link",
        permission_classes=[AllowAny],
    )
    def get_s_link(self, request, pk=None):
        recipe = self.get_object()

        id = encode36(recipe.id)
        short_path = reverse(
            "s_link", args=[id]
        )
        short_url = request.build_absolute_uri(short_path)
        return Response({"short-link": short_url})

    @action(
        methods=["get"],
        detail=False,
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_list(self, request):
        cart_items = request.user.shopping_cart.select_related("recipe")
        recipe_ids = [item.recipe_id for item in cart_items]

        needed_ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__in=recipe_ids)
            .values(
                title=F("ingredient__name"),
                measure=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
            .order_by("title")
        )

        text_lines = ["Список необходимых продуктов:\n"]
        for ing in needed_ingredients:
            text_lines.append(
                f"* {ing['title']} — {ing['total']} {ing['measure']}"
            )

        file_response = HttpResponse(
            "\n".join(text_lines),
            content_type="text/plain; charset=utf-8"
        )
        file_response[
            "Content-Disposition"
        ] = 'attachment; filename="my_shopping_list.txt"'
        return file_response

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = self.get_object()

        if request.method == "DELETE":
            deleted_count, _ = user.shopping_cart.filter(
                recipe=recipe).delete()
            if not deleted_count:
                return Response(
                    {"errors": "Рецепт отсутствует в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "POST":
            if user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен в список покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(
                user=user,
                recipe=recipe
            )

            serializer = BriefRecipesSerializer(
                recipe,
                context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["post", "delete"],
        detail=True,
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "DELETE":
            deleted_count, _ = user.favorite_recipes.filter(
                recipe=recipe).delete()
            if not deleted_count:
                return Response(
                    {"errors": "Рецепт отсутствует в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "POST":
            if user.favorite_recipes.filter(recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже есть в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorites.objects.create(
                user=user, recipe=recipe
            )
            serializer = BriefRecipesSerializer(
                recipe,
                context={"request": request}
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
