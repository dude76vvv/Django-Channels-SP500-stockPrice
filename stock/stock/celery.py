import os
from celery import Celery

# refer to project folder name not appName !!!
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock.settings")

app = Celery("stock")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# setup beat schedule to run the task every x interval in sec
app.conf.beat_schedule = {

    'get_live_price': {
        'task': 'livePrice.tasks.get_yf_data_task',
        'schedule': 120.0
    }

}
