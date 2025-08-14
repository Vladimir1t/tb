INSTALLED_APPS = [
    ...
    'api.apps.ApiConfig',  
]

TELEGRAM_BOT_TOKEN = "ваш_токен_бота" 

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'aggregator.db',  
    }
}
