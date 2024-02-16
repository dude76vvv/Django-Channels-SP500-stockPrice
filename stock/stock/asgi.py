"""
ASGI config for stock project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application
from livePrice.routings import ws_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock.settings')

# application = get_asgi_application()

# register socket to a websocket url
# websocket will be map to a class in the consumer
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(ws_urlpatterns)
        )

        # "websocket": URLRouter(urls.websocket_urlpatterns)
    }
)
