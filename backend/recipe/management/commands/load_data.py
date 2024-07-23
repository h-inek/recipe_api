import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Ingredient, Tag


class Command(BaseCommand):
    help = 'Load data from static'

    def handle(self, *args, **kwargs):
        """Добавляем ингредиенты и теги в базы из готового CSV."""
        with open(
                f'{settings.BASE_DIR}/static/data/ingredients.csv',
                'r',
                encoding='utf-8'
        ) as csv_file:
            data = csv.reader(csv_file, delimiter=",")
            for row in data:
                Ingredient.objects.get_or_create(
                    name=row[0].capitalize(),
                    measurement_unit=row[1].capitalize(),
                )

        with open(
                f'{settings.BASE_DIR}/static/data/tags.csv',
                'r',
                encoding='utf-8'
        ) as csv_file:
            data = csv.reader(csv_file, delimiter=",")
            for row in data:
                Tag.objects.get_or_create(
                    name=row[0],
                    color=row[1],
                    slug=row[2],
                )
