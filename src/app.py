import asyncio
import base64
import os
import tempfile
import time

from quart import Quart, make_response, jsonify, request, redirect, url_for
from telegram import Bot as BotInitiator
from telegram import ParseMode
from telegram.error import TelegramError
from telethon import TelegramClient

from .lib.composer import Composer
from .lib.event_store import EventStore

app = Quart(__name__)

store = EventStore()
store.publish("connection", "established", **{})

composer = Composer()


@app.before_serving
async def startup():
    global client
    loop = asyncio.get_event_loop()
    client = TelegramClient(os.path.abspath(os.path.join("data", os.environ["SESSION_NAME"])),
                            int(os.environ["API_ID"]), os.environ["API_HASH"], loop=loop)

    composer.bot = BotInitiator(os.environ["API_KEY"])

    try:
        await client.connect()
        composer.client = client

    except OSError:
        print('Failed to connect')


@app.after_serving
async def cleanup():
    await client.disconnect()


@app.route("/api/bot/getcode", methods=["GET"])
async def get_code():
    await client.send_code_request(os.environ["PHONE"])
    return "OK", 200


@app.route("/api/bot/initialize", methods=["POST"])
async def initialize():
    code = None
    result = await request.get_json()
    if result:
        code = result["code"]
    try:
        await client.sign_in(code=code)
    except Exception as err:
        if not await client.is_user_authorized():
            return redirect(url_for("get_code"))
        return f"Failed to start the client ( {err} )", 500

    composer.client = client
    return "OK", 200


@app.route("/api/channel/<channel_id>", methods=["GET"])
async def get_channel_data(channel_id):
    data = await composer.get_channel_data(channel_id)
    response = await make_response(jsonify(data), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/channel/<channel_id>/check_access')
async def check_channel_access(channel_id):
    permissions = await composer.get_channel_permissions(channel_id)
    response = await make_response(jsonify(permissions), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/channel/<channel_id>/users')
async def get_participants(channel_id):
    data = await composer.get_participants(channel_id)
    response = await make_response(jsonify(data), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/channel/<channel_id>/posts/pinned/<message_content>')
async def content_pinned_post(channel_id, message_content):
    pinned_message = composer.get_pinned_message(channel_id)
    data = pinned_message["text"]

    success = False
    if message_content == data:
        success = True
    response = await make_response(jsonify(success=success), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/channel/<channel_id>/is_first/<message_content>')
async def get_is_first(channel_id, message_content):
    success = False
    message = await composer.get_last_message(channel_id)

    if message.text == message_content:
        success = True

    response = await make_response(jsonify(success=success), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/channel/<channel_id>/get_order/<message_content>')
async def get_message_order(channel_id, message_content):

    messages = await composer.client.get_messages(channel_id)

    success = False

    for idx, message in enumerate(messages):
        if message.text == message_content:
            success = True
            order = idx
            break

    response = await make_response(jsonify(order=order, success=success), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/api/channel/sendmessage', methods=["POST"])
async def send_message():
    # make_response
    fp = tempfile.TemporaryFile()
    response = await request.get_json()
    advertisement = response["advertisement"]
    img_binary = base64.decodebytes(advertisement["image"].encode())
    fp.write(img_binary)
    fp.seek(0)
    error = None
    try:
        composer.bot.send_photo(response["channel_id"], fp, caption=advertisement["contents"],
                                parse_mode=ParseMode.HTML)
        success = True
    except TelegramError as err:
        success = False
        error = err.message
    fp.close()
    response = await make_response(jsonify(success=success, error=error), 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.route("/api/channel/collectstates", methods=["POST"])
async def collect_channel_states():
    channels = await request.get_json()
    ctr = 0
    try:
        for ctr, channel in enumerate(channels):
            data = await composer.get_channel_data(channel)
            if data is None:
                # This should be handled. It occurs when a channel couldn't be found with the channel name given.
                print(f"channel couldn't be found: {channel}")
                continue
            store.publish("state", "received", **data)
            time.sleep(1)
    finally:
        print("Number of channels data received: ", ctr)
    return "OK", 200
