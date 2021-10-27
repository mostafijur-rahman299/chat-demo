from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class NotifyConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def receive_json(self, content):
        command = content.get('command', None)
        token = content.get("token", None)
        
        if command == 'join' and token == "234233sdfgwert345":
    
            self.user = self.scope['user']
            self.room_name = f'notify_room_for_user_{self.user.id}' # self.user.id should be secret_key
            
            await self.channel_layer.group_add(self.room_name, self.channel_name)

            # message = text_json_data['message']
            # sender = text_json_data['sender']

            # await self.channel_layer.group_send(self.room_name, {
            #     'type': 'notification',
            #     'message': message,
            #     'sender': sender
            # })

    # async def disconnect(self, close_code):
    #     print(type(close_code))
    #     await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def notification(self, event):
        print("event=========",type(event))

        print('notify consumer')
        await self.send_json(event)