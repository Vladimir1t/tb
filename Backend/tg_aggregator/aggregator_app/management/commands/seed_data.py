# aggregator_app/management/commands/seed_data.py

from django.core.management.base import BaseCommand
from aggregator_app.models import Project
from aggregator_app.utils import get_telegram_avatar_url
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fills the database with initial project data if it is empty.'

    def handle(self, *args, **options):
        if Project.objects.exists():
            self.stdout.write(self.style.WARNING('Database is not empty. Skipping seeding.'))
            return

        self.stdout.write('Database is empty, starting to seed data...')

        test_data = [
            ('channel', 'Хабр', 'https://t.me/habr_com', 'программирование', True, 100, 122000),
            ('channel', 'Новости Москвы', 'https://t.me/moscowmap', 'новости', False, 50, 2730000),
            ('channel', 'Книга животных', 'https://t.me/knigajivotnih1', 'природа', False, 50, 15000),
            ('channel', 'МФТИ', 'https://t.me/miptru', 'вузы', False, 50, 15000),
            ('channel', 'ТРУСЫ РАЙЗА', 'https://t.me/raiznews', 'cs2', False, 50, 335000),
            ('channel', 'Банки, деньги, два офшора', 'https://t.me/bankrollo', 'экономика', False, 50, 15000),
            ('channel', 'МЯЧ Production', 'https://t.me/myachPRO', 'футбол', False, 50, 260000),
            ('channel', 'Фонтанка SPB Online', 'https://t.me/fontankaspb', 'новости', False, 50, 350000),
            ('channel', 'Real Madrid CF | Реал Мадрид', 'https://t.me/realmadridcdf', 'футбол', False, 50, 280000),
            ('channel', 'Бестиарий', 'https://t.me/bestiariy_mif', 'искусство', False, 50, 65000),
            ('channel', 'OverDrive | 20 ЛЕТ В АРКАДЕ', 'https://t.me/ihuntnoobs', 'киберспорт', False, 50, 205000),
            ('channel', 'Белый Лебедь • Про Бизнес и Финансы', 'https://t.me/SwamCapital', 'экономика', False, 50, 40000),
            ('channel', 'catharsis', 'https://t.me/truecatharsis', 'art', False, 50, 15000),
            ('channel', 'Формула-1 | Прямые трансляции', 'https://t.me/f1_sports', 'гонки', False, 50, 55000),
            ('channel', 'Семнадцатый номер', 'https://t.me/deginc17', 'футбол', False, 50, 30000),
            ('bot', 'Погодный Бот', 'https://t.me/weather_bot', 'utility', False, 30, 5000),
            ('bot', 'Финансовый помощник', 'https://t.me/finance_bot', 'finance', True, 80, 18000),
            ('mini_app', 'Головоломки', 'https://t.me/puzzle_app', 'games', False, 20, 8000),
        ]

        for item in test_data:
            icon_url = get_telegram_avatar_url(item[2])
            Project.objects.create(
                type=item[0],
                name=item[1],
                link=item[2],
                theme=item[3],
                is_premium=item[4],
                likes=item[5],
                subscribers=item[6],
                icon=icon_url
            )
            self.stdout.write(f"  Added project: {item[1]}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database.'))