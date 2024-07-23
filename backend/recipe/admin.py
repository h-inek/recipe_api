from django import forms
from django.contrib import admin

from foodgram.constants import (
    MIN_VALUE_AMOUNT, MIN_VALUE_COOKING_TIME, MIN_VALUE_TEXT
)
from .models import (
    Favorite, Follow, Ingredient, IngredientInRecipe, Recipe, Tag, User,
    ShoppingCart,
)


class IngredientReadUpdateInRecipe(admin.TabularInline):
    """Отображение ингредиентов при создании/редактировании рецепта."""
    model = IngredientInRecipe
    fields = ['ingredient', 'amount']
    extra = 1
    min_num = 1


class RecipeAdminForm(forms.ModelForm):
    """Валидация модели рецепта"""
    class Meta:
        model = Recipe
        exclude = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        text = cleaned_data.get('text')
        cooking_time = cleaned_data.get('cooking_time')

        if not name:
            raise forms.ValidationError(
                'Поле name обязательно для заполнения.'
            )

        if not text or len(text) < MIN_VALUE_TEXT:
            raise forms.ValidationError(
                'Поле text обязательно для заполнения.'
            )

        if cooking_time is None or cooking_time <= MIN_VALUE_COOKING_TIME:
            raise forms.ValidationError(
                'Поле cooking_time должно быть положительным числом.'
            )


class UserAdminForm(forms.ModelForm):
    """Валидация модели юзера"""
    class Meta:
        model = User
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        if not username or not email or not first_name or not last_name:
            raise forms.ValidationError('Заполните все необходимые поля!')


class TagsAdminForm(forms.ModelForm):
    """Валидация модели тэга"""
    class Meta:
        model = Tag
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        color = cleaned_data.get('color')
        slug = cleaned_data.get('slug')

        if not name or not color or not slug:
            raise forms.ValidationError('Заполните все необходимые поля!')

        if Tag.objects.filter(name=name, slug=slug).exists():
            raise forms.ValidationError('Такой тэг уже существует!')


class IngredientAdminForm(forms.ModelForm):
    """Валидация модели ингредиента"""
    class Meta:
        model = Ingredient
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        measurement_unit = cleaned_data.get('measurement_unit')

        if not name or not measurement_unit:
            raise forms.ValidationError('Заполните все необходимые поля!')

        if Ingredient.objects.filter(name=name).exists():
            raise forms.ValidationError('Такой ингредиент уже существует!')


class IngredientInRecipeAdminForm(forms.ModelForm):
    """Валидация модели ингредиента в рецепте"""
    class Meta:
        model = IngredientInRecipe
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        recipe = cleaned_data.get('recipe')
        ingredient = cleaned_data.get('ingredient')
        amount = cleaned_data.get('amount')
        if not recipe or not ingredient or not amount:
            raise forms.ValidationError('Заполните все необходимые поля!')
        if amount < MIN_VALUE_AMOUNT:
            raise forms.ValidationError('Количество слишком маленькое!')
        if IngredientInRecipe.objects.filter(
                recipe=recipe, ingredient=ingredient
        ).exists():
            raise forms.ValidationError(
                'Такой ингредиент уже существует в этом рецепте!'
            )


class FollowAdminForm(forms.ModelForm):
    """Валидация модели подписки"""
    class Meta:
        model = Follow
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        author = cleaned_data.get('author')

        if not user or not author:
            raise forms.ValidationError('Заполните все необходимые поля!')

        if user == author:
            raise forms.ValidationError('Нельзя подписаться на себя самого!')

        if Follow.objects.filter(user=user, author=author).exists():
            raise forms.ValidationError('Пользователь уже подписан!')


class FavoriteAdminForm(forms.ModelForm):
    """Валидация модели избранного"""
    class Meta:
        model = Favorite
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        recipe = cleaned_data.get('recipe')

        if not user or not recipe:
            raise forms.ValidationError('Заполните все необходимые поля!')

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise forms.ValidationError('Рецепт уже добавлен в избранное!')


class ShoppingCartAdminForm(forms.ModelForm):
    """Валидация модели списка покупок"""
    class Meta:
        model = ShoppingCart
        exclude = []

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        recipe = cleaned_data.get('recipe')

        if not user or not recipe:
            raise forms.ValidationError('Заполните все необходимые поля!')

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise forms.ValidationError(
                'Рецепт уже добавлен в список покупок!'
            )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка отображения пользователя в админке."""
    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('username', 'email')
    form = UserAdminForm


@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    """Настройка отображения тэга в админке."""
    list_display = (
        'pk',
        'name',
        'color',
        'slug',
    )
    list_filter = ('name',)
    form = TagsAdminForm


@admin.register(Ingredient)
class IngredientsAdmin(admin.ModelAdmin):
    """Настройка отображения ингредиента в админке."""
    list_display = (
        'pk',
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)
    form = IngredientAdminForm


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка отображения рецепта в админке."""
    list_display = (
        'author',
        'name',
        'text',
        'cooking_time',
        'pub_date',
        'favorite_count',
    )
    inlines = [IngredientReadUpdateInRecipe]
    list_filter = ('author', 'name', 'tags')
    form = RecipeAdminForm


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Настройка отображения ингредиента в рецепте в админке."""
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )
    form = IngredientInRecipeAdminForm


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Настройка отображения подписки в админке."""
    list_display = (
        'user',
        'author',
    )
    form = FollowAdminForm


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка отображения избранного в админке."""
    list_display = (
        'user',
        'recipe',
    )
    form = FavoriteAdminForm


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка отображения списка покупок в админке."""
    list_display = (
        'user',
        'recipe',
    )
    form = ShoppingCartAdminForm
