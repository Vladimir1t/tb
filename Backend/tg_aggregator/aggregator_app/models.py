# aggregator_app/models.py

from django.db import models

class User(models.Model):
    """
    Модель пользователя, идентифицируемого по Telegram ID.
    """
    id = models.BigIntegerField(primary_key=True, help_text="Telegram User ID")
    username = models.CharField(max_length=255, null=True, blank=True)
    stars = models.IntegerField(default=0)
    balance = models.FloatField(default=0)

    @property
    def projects_count(self):
        """
        Вычисляемое свойство для получения количества проектов пользователя.
        Это поле не хранится в БД, а рассчитывается на лету.
        """
        # Для этого свойства требуется определить related_name='projects' в модели Project,
        # если вы решите связать проекты с пользователями.
        return self.projects.count()

    def __str__(self):
        return f"User {self.id} ({self.username or 'N/A'})"

class Project(models.Model):
    """
    Модель проекта (канал, бот или mini-app).
    """
    class ProjectType(models.TextChoices):
        CHANNEL = 'channel', 'Channel'
        BOT = 'bot', 'Bot'
        MINI_APP = 'mini_app', 'Mini App'

    # Основная информация
    type = models.CharField(max_length=20, choices=ProjectType.choices)
    name = models.CharField(max_length=255)
    link = models.URLField(max_length=500, unique=True, help_text="Уникальная ссылка на проект, например, https://t.me/username")
    theme = models.CharField(max_length=100)
    
    # Иконка проекта. Хранится как файл, а не URL.
    # upload_to='avatars/' указывает, что файлы будут сохраняться в папку MEDIA_ROOT/avatars/
    icon = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Метаданные и статистика
    is_premium = models.BooleanField(default=False)
    likes = models.IntegerField(default=0)
    subscribers = models.IntegerField(default=0)
    
    # Раскомментируйте, если хотите связать проект с конкретным пользователем-владельцем
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)

    def __str__(self):
        return f"[{self.get_type_display()}] {self.name}"

    class Meta:
        # Сортировка по умолчанию: сначала премиум, затем по количеству лайков
        ordering = ['-is_premium', '-likes']

class Task(models.Model):
    """
    Модель для отслеживания выполненных пользователем заданий.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=50)
    completed = models.BooleanField(default=True)

    def __str__(self):
        return f"Task '{self.task_type}' for User {self.user.id}"

    class Meta:
        # Гарантирует, что пара (user, task_type) уникальна.
        # Это аналог PRIMARY KEY (user_id, task_type) из вашего SQLite.
        unique_together = ('user', 'task_type')