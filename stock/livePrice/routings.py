from django.urls import path
from .consumers import LivePriceConsumer
from django.urls import path

# dont use os path !!!
# map to class in consumer
ws_urlpatterns = [
    path("ws/live-price/", LivePriceConsumer.as_asgi())
]
