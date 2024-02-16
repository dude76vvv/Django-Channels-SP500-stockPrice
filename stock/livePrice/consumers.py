import json
from channels.generic.websocket import AsyncWebsocketConsumer


class LivePriceConsumer(AsyncWebsocketConsumer):

    # define the group name in which client channel can connect to !!!
    async def connect(self):
        await self.channel_layer.group_add("livePrice", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("livePrice", self.channel_name)

    # utilized by task to to send data to frontend via asgi websocket

    async def sendData(self, event):
        data = event["data"]

        # print(data)
        print("consumer: sending updated data to client ...")

        jsonDump = json.dumps(
            {
                "type": "price_data",
                "data": data
            },
            default=str
        )

        await self.send(
            text_data=jsonDump
        )

        print("consumer: data sent")
