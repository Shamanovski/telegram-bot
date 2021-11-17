import base64

from telegram import ChatPhoto
from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.sync import functions


class Composer:
    """Composition of telegram bot and telegram client interfaces"""

    def __init__(self):
        self._client = None
        self._bot = None

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def bot(self):
        return self._bot

    @bot.setter
    def bot(self, value):
        self._bot = value

    async def get_participants(self, channel):
        participants = await self.client.get_participants(channel)
        result = [user.id for user in participants]
        return result

    async def get_channel_data(self, channel_id: int, from_message=[]):
        """The method iterates through the messages of the channel specified.
        The order starts with the message which id goes as an argument into the GetMessagesRequest function
        For example: from_message equals to [30], the method will start fetching messages from the 30rd message and
        up to the end in order, oldest to newest
        """
        subscribers_num = self.bot.get_chat_members_count(channel_id)
        # from_message parameter takes a list with one value (which is a message id) as an argument. Example: [30]
        # Specifications on other 3 values in the list of the id parameter are unclear.
        channel = self.client.get_entity(channel_id)
        messages_response = await self.client(functions.channels.GetMessagesRequest(channel=channel, id=from_message))
        messages_response = messages_response.to_dict()
        messages = messages_response["messages"]
        total_coverage = 0

        # fetch messages from array according to the period of time given
        for message in messages:
            try:
                total_coverage += message["views"]
            except KeyError:
                continue
        post_coverage = total_coverage / len(messages)
        err = post_coverage / subscribers_num * 100
        image_binary = self.get_channel_image(channel)
        if image_binary:
            image_encoded = base64.b64encode(image_binary)
            image_ascii = image_encoded.decode("ascii")
        else:
            image_ascii = None
        return {
            "external_id": channel,
            "subscribers_num": subscribers_num,
            "total_coverage": total_coverage,
            "post_coverage": round(post_coverage),
            "err": round(err, 2),
            "ic": 0,  # not implemented
            "image": image_ascii
        }

    async def get_messages(self, channel_id, messages_limit=100):

        return await self.client.get_messages(channel_id, messages_limit)

    async def get_last_message(self, channel_id):

        messages = await self.client.get_messages(channel_id)
        return messages[0]

    async def get_channel_permissions(self, channel_id):
        try:
            permissions = await self.client.get_permissions(channel_id, self.bot.get_me()['username'])
            return {
                "is_admin": permissions.is_admin,
                "is_subscriber": True,
                "is_banned": permissions.is_banned,
            }
        except UserNotParticipantError:
            return {
                "is_admin": False,
                "is_subscriber": False,
                "is_banned": False
            }

    def get_pinned_message(self, channel_id):
        return self.bot.get_chat(channel_id).pinned_message

    def get_channel_image(self, channel):
        data = self.bot.get_chat(channel).to_dict()
        if "photo" not in data:
            return None

        sizes = data["photo"]
        chat_image = ChatPhoto(sizes["small_file_id"], sizes["small_file_unique_id"], sizes["big_file_id"],
                               sizes["big_file_unique_id"], bot=self.bot)
        image_binary = chat_image.get_big_file(timeout=30).download_as_bytearray()
        return image_binary
