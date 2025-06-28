"""URL-конфигурация приложения 'api'."""

from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import UsersViewSet, RecipesViewSet, IngredientsViewSet


app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'users', UsersViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
