from django_filters import FilterSet, ModelMultipleChoiceFilter, NumberFilter

from recipe.models import Recipe, Tag


class RecipeFilterSet(FilterSet):
    """Кастомный фильтр."""
    is_favorited = NumberFilter(
        field_name='is_favorited', method='filter_by_favorite'
    )
    is_in_shopping_cart = NumberFilter(
        field_name='is_in_shopping_cart', method='filter_by_shopping_cart'
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    def filter_by_favorite(self, queryset, name, value):
        if value:
            return queryset.filter(is_favorited=True)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(is_in_shopping_cart=True)
        return queryset

    class Meta:
        model = Recipe
        exclude = ('image', 'cooking_time', 'ingredients')
