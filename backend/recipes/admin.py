from django.contrib import admin

from .models import (Favorites, Ingredients, Recipes,
                     IngredientInRecipe, ShoppingCart)


admin.site.register(Favorites)
admin.site.register(ShoppingCart)
admin.site.register(IngredientInRecipe)


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientInRecipe
    autocomplete_fields = ("ingredient",)
    min_num = 1
    extra = 1


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "pub_date",
        "get_favorite_count",
    )
    autocomplete_fields = ("author",)
    search_fields = ("name", "author__username")
    list_filter = ("name", "pub_date")
    inlines = (RecipeIngredientInline,)
    readonly_fields = ("pub_date", "get_favorite_count")
    empty_value_display = "Ничего нет"

    @admin.display(description="В избранном.")
    def get_favorite_count(self, obj):
        return obj.favorited_by_user.count()


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    list_filter = ("measurement_unit",)
    search_fields = ("name",)
    empty_value_display = "Ничего нет"
