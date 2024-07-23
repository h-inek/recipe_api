from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from foodgram.constants import (
    HEX_FORMAT_VALIDATE, LENGTH_EMAIL, MAX_LENGTH_CHARFIELD,
    MAX_VALUE_COOKING_TIME, MAX_VALUE_NAME, MAX_VALUE_SLUG,
    MIN_VALUE_COOKING_TIME, MAX_VALUE_COLOR, MIN_VALUE_AMOUNT
)


class Users:
    """Роли пользователя."""
    USER = 'user'
    ADMIN = 'admin'


class User(AbstractUser):
    """Модель пользователя."""
    ROLE_CHOICES = [
        (Users.USER, 'Пользователь'),
        (Users.ADMIN, 'Администратор'),
    ]
    email = models.EmailField(max_length=LENGTH_EMAIL, unique=True, null=False)
    password = models.CharField(max_length=MAX_LENGTH_CHARFIELD, null=False)
    first_name = models.CharField(max_length=MAX_LENGTH_CHARFIELD, null=False)
    last_name = models.CharField(max_length=MAX_LENGTH_CHARFIELD, null=False)
    role = models.CharField(
        max_length=MAX_LENGTH_CHARFIELD,
        choices=ROLE_CHOICES,
        default=Users.USER,
        verbose_name='Роль',
    )

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == Users.ADMIN

    @property
    def is_user(self):
        return self.role == Users.USER


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(max_length=MAX_VALUE_NAME, unique=True)
    color = models.CharField(
        max_length=MAX_VALUE_COLOR,
        validators=[RegexValidator(
            regex=HEX_FORMAT_VALIDATE,
            message='Цвет должен быть в формате HEX',
            code='invalid_color'
        )],
        unique=True
    )
    slug = models.SlugField(max_length=MAX_VALUE_SLUG, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингидиента."""
    name = models.CharField(
        max_length=MAX_LENGTH_CHARFIELD,
        verbose_name='Название',
        db_index=True,
        null=False
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_CHARFIELD,
        verbose_name='Единица измерения',
        null=False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class RecipeManager(models.Manager):
    def with_is_favorite_and_shopping_cart(self, user):
        """
        Возвращаем queryset рецептов с дополнительными полями
        is_favorite и is_in_shopping_cart.
        """
        return super().get_queryset().annotate(
            is_favorited=models.Exists(
                Favorite.objects.filter(
                    recipe=models.OuterRef('pk'), user=user
                )
            ),
            is_in_shopping_cart=models.Exists(
                ShoppingCart.objects.filter(
                    recipe=models.OuterRef('pk'), user=user
                )
            )
        )


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipe',
    )
    name = models.CharField(max_length=MAX_VALUE_NAME, null=False, blank=False)
    image = models.ImageField(
        upload_to='recipe/image/', null=True, blank=True, default=None)
    text = models.TextField(null=False, blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        null=False,
        help_text='В минутах.',
        validators=[
            MinValueValidator(MIN_VALUE_COOKING_TIME),
            MaxValueValidator(MAX_VALUE_COOKING_TIME)
        ]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='recipe',
    )
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты',
        related_name='recipe',
    )
    objects = RecipeManager()

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт',
        verbose_name_plural = 'Рецепты',
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_name_recipe'
            )
        ]

    @property
    def current_user(self):
        return self.author

    @current_user.setter
    def current_user(self, value):
        self.user = value

    def favorite_count(self):
        """Количество добавлений в избранное."""
        return self.favorite_users.count()

    def __str__(self):
        return f'{self.name}'


class IngredientInRecipe(models.Model):
    """Ингредиент в рецепте."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(MIN_VALUE_AMOUNT)]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        unique_together = ('ingredient', 'recipe')

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class Follow(models.Model):
    """
    Модель подписки.
    follower - можно получить всех авторов, на которых подписан юзер.
    following - можно получить всех юзеров, подписанных на автора.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Кто подписан',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='На кого подписан',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='cant_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}.'


class Favorite(models.Model):
    """
    Модель избранного.
    favorite_recipes - можно получить рецепты, добавленные юзером в избранное.
    favorite_users - можно получить юзеров, добавивших рецепт в избранное.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_users',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe')
        ]


class ShoppingCart(models.Model):
    """
    Модель списка покупок.
    shop_users - можно получить юзеров, которые добавили рецепт в покупки.
    shop_recipes - можно получить рецепты, добавленные юзером в покупки.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shop_users',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_recipes',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_recipe_in_shop_cart'
            )
        ]
