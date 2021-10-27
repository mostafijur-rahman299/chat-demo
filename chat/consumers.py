from channels.consumer import SyncConsumer, AsyncConsumer
from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.layers import ChannelLayerManager, get_channel_layer

from django.db.models import F
from chat.models import Thread, Message, Notification
import json
import base64
from django.core.files.base import ContentFile
from django.conf import settings


User = get_user_model()


def base64_file(data, name=None):
    _format, _img_str = data.split(';base64,')
    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]
    return ContentFile(base64.b64decode(_img_str), name='{}.{}'.format(name, ext))


class ChatAsyncConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        self.user = self.scope['user']
        other_username = self.scope['url_route']['kwargs']['username']
        self.other_user = await sync_to_async(User.objects.get)(username=other_username)

        if self.user and self.other_user:
            self.thread_obj = await sync_to_async(Thread.objects.get_or_create_personal_thread)(self.user, self.other_user)

            self.room_name = f'personal_thread_{self.thread_obj.id}'
            await self.channel_layer.group_add(self.room_name, self.channel_name)
            await self.send({
                "type": 'websocket.accept'
            })

            await self.update_user_incr(self.user)

    async def websocket_receive(self, event):
        json_text_data = json.loads(event['text'])
        message = json_text_data['message']

        image = json_text_data.get('image')
        audio = json_text_data.get('audio')

        if image:
            image = base64_file(image)
        if audio: 
            audio = base64_file(audio)

        if message:
            # obj = await self.store_message(message, image)
            msg_obj = await sync_to_async(Message.objects.create)(thread=self.thread_obj, sender=self.scope['user'], text=message,  image=image, audio_file=audio)

            msg = json.dumps({
                'message': message,
                'is_typing': json_text_data['is_typing'],
                'username': self.user.username,
                'image': f"{settings.SITE_HOST}{msg_obj.image.url}" if msg_obj.image else ""
            })

            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'websocket.message',
                    'text': msg,
                }
            )

        if json_text_data['notification_read']:
            sender = await self.read_notification(json_text_data['sender'])

            await self.channel_layer.group_send(
                f"notify_room_for_user_{self.user.id}",
                {
                    'type': 'notification',
                    'read_notification': True,
                    'sender': json_text_data['sender']
                }
            )

    async def websocket_message(self, event):
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        }
        )

    async def websocket_disconnect(self, event):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        await self.update_user_decr(self.user)

    @database_sync_to_async
    def store_message(self, text, image):
        Message.objects.create(
            thread=self.thread_obj,
            sender=self.scope['user'],
            text=text,
            image=image
        )

    @database_sync_to_async
    def update_user_incr(self, user):
        User.objects.filter(pk=user.pk).update(online=F('online') + 1)

    @database_sync_to_async
    def update_user_decr(self, user):
        User.objects.filter(pk=user.pk).update(online=F('online') - 1)

    @database_sync_to_async
    def read_notification(self, username):
        sender = User.objects.filter(username=username).first()
        Notification.objects.filter(
            notification_user=sender).update(notification_read=True)


class ChatConsumer(SyncConsumer):
    def websocket_connect(self, event):
        me = self.scope['user']
        other_username = self.scope['url_route']['kwargs']['username']
        other_user = User.objects.filter(username=other_username).first()
        self.thread_obj = Thread.objects.get_or_create_personal_thread(
            me, other_user)

        self.room_name = f'personal_thread_{self.thread_obj.id}'
        async_to_sync(self.channel_layer.group_add)(
            self.room_name, self.channel_name)
        self.send({
            "type": 'websocket.accept'
        })

        print(f'[{self.channel_name}] - You are connected')

    def websocket_receive(self, event):
        msg = json.dumps({
            'text': event['text'],
            'username': self.scope['user'].username
        })

        self.store_message(event.get('text'))

        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                'type': 'websocket.message',
                'text': msg
            }
        )

        print(f'[{self.channel_name}] - Received message {event["text"]}')

    def websocket_message(self, event):
        self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

        print(f'[{self.channel_name}] - Message sent {event["text"]}')

    def websocket_disconnect(self, event):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name)
        print('disconnedted')

    def store_message(self, text):
        Message.objects.create(
            thread=self.thread_obj,
            sender=self.scope['user'],
            text=text
        )


# echo consomers
class EchoConsumer(SyncConsumer):
    def websocket_connect(self, event):
        self.room_name = 'broadcast'
        self.send({
            "type": 'websocket.accept'
        })

        async_to_sync(self.channel_layer.group_add)(
            self.room_name, self.channel_name)

        print(f'[{self.channel_name}] - You are connected')

    def websocket_receive(self, event):
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                'type': 'websocket.message',
                'text': event.get('text')
            }
        )

        print(f'[{self.channel_name}] - Received message {event["text"]}')

    def websocket_message(self, event):
        self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

        print(f'[{self.channel_name}] - Message sent {event["text"]}')

    def websocket_disconnect(self, event):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name)
        print('disconnedted')
