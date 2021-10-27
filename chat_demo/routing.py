from channels.routing import ProtocolTypeRouter, URLRouter
from  django.urls import path
from channels.auth import AuthMiddlewareStack

from  chat.consumers import EchoConsumer, ChatConsumer, ChatAsyncConsumer
from chat.notify_consumers import NotifyConsumer


application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
            URLRouter([
            path('ws/chat/<str:username>/', ChatAsyncConsumer.as_asgi()),
            path('ws/chat/', EchoConsumer.as_asgi()),

            # path('ws/notify/<str:user_id>/', NotifyConsumer.as_asgi()),
            path('ws/notify/', NotifyConsumer.as_asgi())
        ])
    )
})