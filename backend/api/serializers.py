import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from foodgram.constants import (
    MAX_VALUE_NAME, MIN_VALUE_COOKING_TIME, MIN_VALUE_PASSWORD, MIN_VALUE_NAME,
    MIN_VALUE_TEXT, MIN_VALUE_AMOUNT
)
from recipe.models import (Favorite, Follow, Ingredient, IngredientInRecipe,
                           Recipe, ShoppingCart, Tag, User)


class Base64ImageField(serializers.ImageField):
    """Обработка изображений."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэга."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class CustomUserRegister(UserCreateSerializer):
    """
    Сериализатор регистрации юзера.
    Используется кастомный сериализатор, так как изменяется модель User.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=MIN_VALUE_PASSWORD
    )

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError(
                'Email обязателен для заполнения.'
            )
        return value

    def validate_password(self, value):
        if (not any(part.isalpha() for part in value)
                or not any(part.isdigit() for part in value)):
            raise serializers.ValidationError(
                'Пароль должен содержать как минимум одну букву и одну цифру'
            )
        return value

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'first_name', 'last_name', 'role',
            'username'
        )


class CustomUserSerializer(UserSerializer):
    """Кастомный сериализатор юзера."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        exclude = (
            'password', 'role', 'is_staff', 'is_superuser', 'is_active',
            'date_joined', 'groups', 'last_login', 'user_permissions'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.is_anonymous
            or user.follower.filter(author=obj.id).exists()
        )


class CustomUserForRecipeSerializer(UserSerializer):
    """Мини сериализатор юзера."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Отобразить ингредиент внутри рецепта. Для создания рецепта.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient.id'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        extra_kwargs = {
            'amount': {
                'min_value': None
            }
        }


class FollowSerializer(CustomUserSerializer):
    """
    Сериализатор подписки.
    recipes - отображение рецептов у автора, на которого подписаны.
    recipes_count - количество рецептов у автора, на которого подписаны.
    Выдаем количество рецептов, определённое в переменной limit_recipes.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        limit_recipes = self.context['request'].query_params.get(
            'recipes_limit'
        )

        if limit_recipes is None:
            return ListRecipeSerializer(obj.recipe, many=True).data

        if limit_recipes.isdigit():

            return ListRecipeSerializer(
                obj.recipe, many=True
            ).data[:(int(limit_recipes))]

        raise ValueError(
            'recipes_limit должен быть числом!'
        )

    def get_recipes_count(self, obj):

        return obj.recipe.count()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Короткий сериализатор для отображения при добавлении в избранное и корзину
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        """Вывод при добавлении в избранное согласно документации."""
        return ShortRecipeSerializer(self.instance.recipe).data

    def validate(self, validated_data):
        user = validated_data['user']
        recipe = validated_data['recipe']
        if user.favorite_recipes.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное!'
            )

        return validated_data

    @staticmethod
    def destroy(user, recipe):
        try:
            user.favorite_recipes.get(recipe=recipe).delete()
        except Favorite.DoesNotExist:
            raise serializers.ValidationError('Рецепт не был в избранном.')


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        """Вывод при добавлении в список покупок согласно документации."""
        return ShortRecipeSerializer(self.instance.recipe).data

    def validate(self, validated_data):
        user = validated_data['user']
        recipe = validated_data['recipe']
        if user.shop_recipes.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в списке покупок!'
            )

        return validated_data

    @staticmethod
    def destroy(user, recipe):
        try:
            user.shop_recipes.get(recipe=recipe).delete()
        except ShoppingCart.DoesNotExist:
            raise serializers.ValidationError('Рецепта здесь и не было :)')


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def to_representation(self, instance):
        return CustomUserForRecipeSerializer(self.instance.author).data

    def validate(self, validated_data):
        user = validated_data['user']
        author = validated_data['author']
        if user == author:
            raise serializers.ValidationError(
                'Невозможно подписаться на себя!'
            )
        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )

        return validated_data

    @staticmethod
    def destroy(user, author):
        try:
            user.follower.get(author=author).delete()
        except Follow.DoesNotExist:
            raise serializers.ValidationError('Подписки не существует.')


class ListRecipeSerializer(serializers.ModelSerializer):
    """
    Отображение списка рецептов.
    Дополнительные параметры is_favorited, is_in_shopping_cart для отображения
    избранных рецептов и рецептов, находящихся в списке покупок.
    """
    author = CustomUserForRecipeSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'cooking_time', 'tags',
            'ingredients', 'is_favorited', 'is_in_shopping_cart'
        )


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    """
    Создание и изменение рецепта.
    """
    author = CustomUserForRecipeSerializer(
        required=False,
        default=serializers.CurrentUserDefault()
    )
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(required=False)
    cooking_time = serializers.IntegerField()
    text = serializers.CharField()
    name = serializers.CharField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'cooking_time', 'tags',
            'ingredients'
        )

    def to_representation(self, instance):
        return ListRecipeSerializer(instance).data

    def validate_tags(self, value):
        tags = [tag.id for tag in value]
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тэг!'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Нельзя добавить два одинаковых тэга в рецепт!'
            )

        return value

    def validate_cooking_time(self, value):
        if value < MIN_VALUE_COOKING_TIME:
            raise serializers.ValidationError(
                'Время готовки не может быть меньше 1 минуты!'
            )

        return value

    def validate_ingredients(self, value):
        ingredients = [
            ingredient['ingredient']['id'] for ingredient in value
        ]
        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        for ingredient in value:
            if ingredient['ingredient']['id'] not in Ingredient.objects.all():
                raise serializers.ValidationError(
                    'Такого ингредиента не существует'
                )
            if ingredient['amount'] < MIN_VALUE_AMOUNT:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше 1!'
                )
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Нельзя добавить два одинаковых ингредиента в рецепт.'
            )

        return value

    def validate_name(self, value):
        if len(value) < MIN_VALUE_NAME:
            raise serializers.ValidationError(
                'Название рецепта должно быть не менее 2 символов!'
            )
        if len(value) > MAX_VALUE_NAME:
            raise serializers.ValidationError(
                'Название рецепта не может быть больше 40 символов!'
            )

        return value

    def validate_text(self, value):
        if len(value) < MIN_VALUE_TEXT:
            raise serializers.ValidationError(
                'Добавьте описание своего рецепта!'
            )

        return value

    @staticmethod
    def create_ingredients(recipe, ingredients):
        """Функция создания ингредиентов. Для создания и изменения рецепта."""
        ingredients_data = []
        for ingredient in ingredients:
            ingredients_data.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient['ingredient']['id'],
                    amount=ingredient['amount']
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredients_data)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        new_recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe=new_recipe, ingredients=ingredients)

        new_recipe.tags.add(*tags)

        return new_recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.add(*tags)
        list_ingr = IngredientInRecipe.objects.filter(recipe=instance)
        list_ingr.delete()
        self.create_ingredients(recipe=instance, ingredients=ingredients)

        instance = super().update(instance, validated_data)
        instance.save()

        return instance
