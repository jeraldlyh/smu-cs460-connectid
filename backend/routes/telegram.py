import asyncio
import os
import uuid
from typing import NoReturn

from database import Firestore
from database.models import CustomStates, Responder
from flask import abort, request
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from routes import app

API_TOKEN = str(os.getenv("TELEGRAM_API_TOKEN"))
WEBHOOK_URL_BASE = str(os.getenv("WEBHOOK_URL"))
WEBHOOK_URL_PATH = f"/${API_TOKEN}"

bot = AsyncTeleBot(API_TOKEN, state_storage=StateMemoryStorage())


@app.route(WEBHOOK_URL_PATH, methods=["POST"])
async def webhook() -> str | NoReturn:
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = types.Update.de_json(json_string)

        if update:
            await bot.process_new_updates([update])
        return ""
    else:
        abort(403)


@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call: types.CallbackQuery) -> None:
    match call.data:
        case "onboard":
            database = Firestore()

            # User might not have granted location permissions
            latitude, longitude = 0, 0
            if call.message.location:
                latitude = call.message.location.latitude
                longitude = call.message.location.longitude

            responder = Responder(
                id=str(uuid.uuid4()),
                name=call.from_user.full_name,
                telegram_id=call.from_user.id,
                state=CustomStates.NAME,
                location={
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )
            await database.create_responder(responder)
            await bot.send_message(call.message.chat.id, f"Kindly enter your full name")


@bot.message_handler(commands=["start"])
async def onboard_responder(message: types.Message) -> None:
    onboard_button = types.InlineKeyboardButton("📝 Onboard", callback_data="onboard")
    check_in_button = types.InlineKeyboardButton(
        "🕹️ Check-In", callback_data="check_in"
    )
    check_out_button = types.InlineKeyboardButton(
        "❌ Check-Out", callback_data="check_out"
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(onboard_button)
    keyboard.add(check_in_button, check_out_button, row_width=2)

    await bot.reply_to(
        message,
        ("Welcome to ConnectID, below are a list of actions available."),
        reply_markup=keyboard,
    )


@bot.message_handler(func=lambda message: True)
async def message_handler(message: types.Message):
    if message.text and not message.text.startswith("/"):
        database = Firestore()
        responder = await database.get_responder(message.from_user.id)
        match responder.state:
            case CustomStates.NAME:
                responder.name = message.text
            case CustomStates.LANGUAGE:
                pass
            case CustomStates.PHONE_NUMBER:
                pass
            case CustomStates.NRIC:
                pass
            case CustomStates.ADDRESS:
                pass
            case CustomStates.DATE_OF_BIRTH:
                pass
            case CustomStates.GENDER:
                pass
            case CustomStates.EXISTING_MEDICAL_KNOWLEDGE:
                pass

        responder.state = _retrieve_next_state(responder)
        await database.update_responder(responder)


async def _process_name(message: types.Message, responder: Responder):
    await bot.send_message(message.chat.id, "Kindly enter your fullname")
    return


def _retrieve_next_state(responder: Responder) -> CustomStates:
    return CustomStates(responder.to_dict()["state"] + 1)


async def main() -> None:
    # Remove webhook, it fails sometimes if there is a previous webhook
    await bot.remove_webhook()
    # Drop all pending updates to prevent spams
    await bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, drop_pending_updates=True
    )


asyncio.run(main())
