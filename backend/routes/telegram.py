import asyncio
import os
from typing import NoReturn

from database import Firestore
from database.models import CustomStates, Responder
from flask import abort, request
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot_calendar import ENGLISH_LANGUAGE, Calendar, CallbackData
from utils.handlers import (
    _retrieve_next_state,
    process_address,
    process_date_of_birth,
    process_gender,
    process_language,
    process_name,
    process_nric,
    process_onboard,
    process_phone_number,
)

from routes import app

API_TOKEN = str(os.getenv("TELEGRAM_API_TOKEN"))
WEBHOOK_URL_BASE = str(os.getenv("WEBHOOK_URL"))
WEBHOOK_URL_PATH = f"/${API_TOKEN}"

bot = AsyncTeleBot(API_TOKEN, state_storage=StateMemoryStorage())
calendar = Calendar(language=ENGLISH_LANGUAGE)
calendar_callback = CallbackData("calendar", "action", "year", "month", "day")


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
async def callback_handler(call: types.CallbackQuery) -> None:
    # callback_data may be in the form of 'language malay'
    callback_data = call.data.split(" ") if " " in call.data else [call.data]
    action = callback_data[0]
    database = Firestore()

    # Handle callback data separately for external calendar module
    if call.data.startswith(calendar_callback.prefix):
        callback_data = call.data
        action = "calendar"

    match action:
        case "onboard":
            await process_onboard(bot, database, call)
        case "language":
            await process_language(bot, database, call, [callback_data[1]])
        case "calendar":
            await process_date_of_birth(
                bot, call, calendar, calendar_callback, str(callback_data)
            )
        case "gender":
            await process_gender(bot, database, call, callback_data[1])


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
        has_error = False
        is_step_completed = False

        match responder.state:
            case CustomStates.NAME:
                await process_name(bot, message, responder)
            case CustomStates.LANGUAGE:
                pass
            case CustomStates.PHONE_NUMBER:
                await process_phone_number(bot, responder, message)
            case CustomStates.NRIC:
                await process_nric(bot, responder, message)
            case CustomStates.ADDRESS:
                await process_address(
                    bot, responder, message, calendar, calendar_callback
                )
            case CustomStates.DATE_OF_BIRTH:
                pass
            case CustomStates.GENDER:
                pass
            case CustomStates.EXISTING_MEDICAL_KNOWLEDGE:
                pass

        if not has_error and is_step_completed:
            responder.state = _retrieve_next_state(responder)
            await database.update_responder(responder)


async def main() -> None:
    # Remove webhook, it fails sometimes if there is a previous webhook
    await bot.remove_webhook()
    # Drop all pending updates to prevent spams
    await bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, drop_pending_updates=True
    )


asyncio.run(main())
