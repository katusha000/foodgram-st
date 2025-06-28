from django_filters import rest_framework as filters
from recipes.models import Recipes


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')
    is_favorited = filters.BooleanFilter(method='filter_favorites')
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipes
        fields = ['author', 'is_in_shopping_cart', 'is_favorited']

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        if str(value).lower() in ('true', '1'):
            return queryset.filter(in_shopping_cart__user=user)
        return queryset.exclude(in_shopping_cart__user=user)

    def filter_favorites(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        if str(value).lower() in ('true', '1'):
            return queryset.filter(favorited_by_user__user=user)
        return queryset.exclude(favorited_by_user__user=user)
