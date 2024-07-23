from django.conf import settings
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipe.models import Ingredient, Recipe, Tag, User
from .filters import RecipeFilterSet
from .paginators import CustomPagination
from .permissions import IsAdminOrAuthorOrReadOnly
from .utils import create_file_with_ingredients
from .serializers import (CreateUpdateRecipeSerializer, CustomUserSerializer,
                          FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, ListRecipeSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          TagSerializer)


class CustomUserViewSet(UserViewSet):
    """Вью для работы с юзером, подпиской  отображением подписки."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)

    @action(
        detail=False, methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Отображение подписок."""
        authors = User.objects.filter(
            following__user=self.request.user
        )
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = FollowSerializer(
                page, many=True, context={'request': request}
            )

            return self.get_paginated_response(serializer.data)

        serializer = FollowSerializer(
            authors, many=True, context={'request': request}
        )

        return Response(serializer.data)

    @action(
        detail=True, methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        """Переопределяем метод создания подписки."""
        user = request.user
        author = self.get_object()
        serializer = SubscribeSerializer(
            data={'user': user.id, 'author': author.id}
        )
        serializer.is_valid()

        if request.method == 'POST':
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        serializer.destroy(user=user, author=author)

        return Response(
            {'detail': f'{user} отписался от {author}.'},
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вью для работы с тегами."""
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вью для работы с ингредиентами."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вью для работы с рецептами. Сериализатор в зависимости от метода."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAdminOrAuthorOrReadOnly, ]
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    search_fields = ('^name',)
    filterset_class = RecipeFilterSet

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            queryset = Recipe.objects.with_is_favorite_and_shopping_cart(
                user=user
            )
        else:
            queryset = Recipe.objects.all()

        return queryset

    def get_serializer_class(self):
        """выбор сериализатора."""
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:

            return CreateUpdateRecipeSerializer

        return ListRecipeSerializer

    @action(
        detail=True, methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавление в избранное, удаление из избранного. +валидация"""
        user = request.user
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )

        if request.method == 'POST':
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        serializer.destroy(user=user, recipe=recipe)

        return Response(
            {'detail': f'Рецепт {recipe.name} удалён из избранного!'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True, methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добаление в список покупок, удаление из него. +валидация"""
        user = request.user
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid()

        if request.method == 'POST':

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        serializer.destroy(user=user, recipe=recipe)

        return Response(
            {'detail': f'Рецепт {recipe.name} удалён из списка покупок!'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False, methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, *args, **kwargs):
        """Скачивание файла в txt-формате."""
        create_file_with_ingredients(
            shop_cart=self.request.user.shop_recipes.all().prefetch_related(
                'recipe__recipe_ingredients__ingredient'
            )
        )
        with open(f'{settings.BASE_DIR}/shopping-list.txt', 'r+') as file:
            response = FileResponse(file.read(), content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response
