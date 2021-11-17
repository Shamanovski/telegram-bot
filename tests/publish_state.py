import asyncio
import os
import base64

from telegram import Bot as BotInitiator
from telethon import TelegramClient
from bot.src.lib.composer import Composer
from bot.src.lib.event_store import EventStore


API_KEY = ""


def test_state_publication(channel):
    """run the script with pytest"""
    composer = Composer()
    bot = BotInitiator(API_KEY)
    composer.bot = bot
    print(channel)
    client = TelegramClient(os.path.abspath(os.path.join("data", os.environ["SESSION_NAME"])),
                            int(os.environ["API_ID"]), os.environ["API_HASH"])
    try:
        client.connect()
        composer.client = client
        store = EventSt     ore()
        loop = asyncio.get_event_loop()
        task = loop.create_task(composer.get_channel_data(channel))
        loop.run_until_complete(task)
    finally:
        client.disconnect()
    data = task.result()
    store.publish("state", "received", **data)
