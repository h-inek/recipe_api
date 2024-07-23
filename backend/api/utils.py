from django.conf import settings


def create_file_with_ingredients(shop_cart):
    file_path = f'{settings.BASE_DIR}/shopping-list.txt'
    with open(file_path, 'w+') as file:
        file.write('Список покупок:\n')
        file.write('\n')
        for cart in shop_cart:
            file.write(
                f'Рецепт {cart.recipe.name} от {cart.recipe.author}:\n'
            )
            for ingr_in_recipe in cart.recipe.recipe_ingredients.all():
                ingredient = ingr_in_recipe.ingredient
                file.write(
                    f'{ingredient.name} -'
                    f' {ingr_in_recipe.amount} '
                    f'{ingredient.measurement_unit}\n'
                )
            file.write('\n')
        return file
