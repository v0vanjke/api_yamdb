import csv

from django.conf import settings
from django.core.management import BaseCommand
from reviews.models import (
    Category, Genre, Review, ReviewComment, Title, User, GenreTitle
)

TABLES = {
    User: 'users.csv',
    Category: 'category.csv',
    Genre: 'genre.csv',
    Title: 'titles.csv',
    Review: 'review.csv',
    ReviewComment: 'comments.csv',
    GenreTitle: 'genre_title.csv',
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for model, csv_f in TABLES.items():
            with open(f'{settings.BASE_DIR}/static/data/{csv_f}', newline='',
                      encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file, delimiter=',')
                if csv_f == 'titles.csv':
                    for data in reader:
                        category = Category.objects.get(
                            pk=data.pop('category'))
                        obj = model(category=category, **data)
                        obj.save()
                elif csv_f in ['review.csv', 'comments.csv']:
                    for data in reader:
                        user = User.objects.get(pk=data.pop('author'))
                        obj = model(author=user, **data)
                        obj.save()
                else:
                    model.objects.bulk_create(
                        [model(**data) for data in reader])
        self.stdout.write(('Данные csv-файлов импортированы'))
