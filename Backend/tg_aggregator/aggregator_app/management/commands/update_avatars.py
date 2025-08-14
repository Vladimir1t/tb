# aggregator_app/management/commands/update_avatars.py

import asyncio
from telethon import TelegramClient
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from urllib.parse import urlparse
from aggregator_app.models import Project
from asgiref.sync import sync_to_async  # <-- 1. Импортируем нужный инструмент

# 2. Создаем асинхронную "обертку" для получения списка проектов
@sync_to_async
def get_all_projects():
    # list() заставляет QuerySet выполниться и вернуть конкретный список,
    # что безопасно для передачи между асинхронными и синхронными частями.
    return list(Project.objects.all())

# 3. Создаем асинхронную "обертку" для сохранения экземпляра проекта
@sync_to_async
def save_project(project_instance):
    # update_fields=['icon'] - это оптимизация, чтобы обновлять только одно поле
    project_instance.save(update_fields=['icon'])


class Command(BaseCommand):
    help = 'Updates project avatars using Telethon by downloading them from Telegram.'

    async def handle_async(self):
        client = TelegramClient(
            settings.TELEGRAM_SESSION_NAME,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
        self.stdout.write("Connecting to Telegram...")
        await client.start()
        self.stdout.write(self.style.SUCCESS("Successfully connected to Telegram."))

        # 4. Вызываем нашу новую асинхронную функцию для получения проектов
        projects = await get_all_projects()

        for project in projects:
            try:
                username = urlparse(project.link).path.strip('/')
                if not username:
                    self.stdout.write(self.style.WARNING(f"Skipping project {project.name} due to invalid link."))
                    continue

                self.stdout.write(f"Processing {username}...")
                
                avatar_bytes = await client.download_profile_photo(username, file=bytes)

                if avatar_bytes:
                    file_name = f"{username}.jpg"
                    content_file = ContentFile(avatar_bytes, name=file_name)
                    
                    project.icon = content_file
                    
                    # 5. Вызываем нашу новую асинхронную функцию для сохранения
                    await save_project(project)
                    
                    self.stdout.write(self.style.SUCCESS(f"  Avatar for {username} updated."))
                else:
                    self.stdout.write(f"  No avatar found for {username}.")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Error processing {project.name}: {e}"))

        await client.disconnect()
        self.stdout.write("Disconnected from Telegram.")

    def handle(self, *args, **options):
        asyncio.run(self.handle_async())