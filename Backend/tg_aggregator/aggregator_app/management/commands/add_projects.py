# aggregator_app/management/commands/add_projects.py

from django.core.management.base import BaseCommand
from aggregator_app.models import Project

class Command(BaseCommand):
    help = 'Adds a predefined list of channels to the Project table if they do not exist.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to add new channels to the project list...")

        # Список никнеймов каналов для добавления
        channels_to_add = [
            'miptru',
            'raiznews',
            'bankrollo',
            'myachPRO',
            'fontankaspb',
            'realmadridcdf',
            'bestiariy_mif',
            'ihuntnoobs',
            'SwamCapital',
            'truecatharsis',
            'f1_sports',
            'deginc17'
        ]

        added_count = 0
        skipped_count = 0

        for username in channels_to_add:
            # Формируем ссылку, которая является уникальным идентификатором
            channel_link = f"https://t.me/{username}"

            # Используем get_or_create для имитации "INSERT OR IGNORE"
            # Он пытается найти объект по link. Если находит - ничего не делает.
            # Если не находит - создает новый.
            project, created = Project.objects.get_or_create(
                link=channel_link,
                defaults={
                    'name': username.capitalize(), # В качестве имени по умолчанию ставим никнейм
                    'type': 'channel',             # Тип проекта - канал
                    'theme': 'default',            # Тема по умолчанию
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  Successfully added project: {username}"))
                added_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"  Project {username} already exists. Skipping."))
                skipped_count += 1
        
        self.stdout.write("\n" + self.style.SUCCESS(f"Operation complete. Added: {added_count}, Skipped: {skipped_count}."))
        self.stdout.write("You can now run 'python manage.py update_avatars' to fetch their icons.")