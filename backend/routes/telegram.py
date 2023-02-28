import asyncio
import os
from typing import NoReturn

from database import Firestore
from database.models import CustomStates, Responder
from flask import abort, request
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from utils.calendar import Calendar, CallbackFactory
from utils.handlers import (
    _retrieve_next_state,
    process_address,
    process_cancel,
    process_date_of_birth,
    process_gender,
    process_language,
    process_list_medical_conditions,
    process_name,
    process_nric,
    process_onboard,
    process_phone_number,
    process_profile,
    process_welcome_message,
)

from routes import app

API_TOKEN = str(os.getenv("TELEGRAM_API_TOKEN"))
WEBHOOK_URL_BASE = str(os.getenv("WEBHOOK_URL"))
WEBHOOK_URL_PATH = f"/${API_TOKEN}"

bot = AsyncTeleBot(API_TOKEN, state_storage=StateMemoryStorage())
calendar = Calendar()
calendar_callback = CallbackFactory("calendar", "action", "day", "month", "day")


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
    # callback_data are separated by <action> <payload>
    callback_data = call.data.split(" ") if " " in call.data else [call.data]
    action = callback_data[0]
    database = Firestore()

    match action:
        case "onboard":
            await process_onboard(bot=bot, database=database, callback=call)
        case "language":
            await process_language(
                bot=bot, database=database, callback=call, languages=[callback_data[1]]
            )
        case "calendar":
            await process_date_of_birth(
                bot=bot,
                database=database,
                callback=call,
                calendar=calendar,
                callback_data=callback_data,
            )
        case "gender":
            await process_gender(
                bot=bot, database=database, callback=call, gender=callback_data[1]
            )
        case "profile":
            await process_profile(bot=bot, database=database, callback=call)
        case "option":
            option = callback_data[1]
            print(callback_data)

            match option:
                case "add":
                    if len(callback_data) > 2:
                        pass
                    else:
                        await process_list_medical_conditions(bot=bot, callback=call)
                case "remove":
                    pass
        case "cancel":
            await process_cancel(bot=bot, callback=call)


@bot.message_handler(commands=["start"])
async def welcome_message(message: types.Message) -> None:
    await process_welcome_message(bot, message)


@bot.message_handler(func=lambda message: True)
async def message_handler(message: types.Message):
    if not message.text:
        return

    if not message.text.startswith("/"):
        database = Firestore()
        responder = await database.get_responder(message.from_user.id)
        has_error = False
        is_text_required_completed = False

        match responder.state:
            case CustomStates.NAME:
                is_text_required_completed = await process_name(bot, message, responder)
            case CustomStates.LANGUAGE:
                pass
            case CustomStates.PHONE_NUMBER:
                is_text_required_completed = await process_phone_number(
                    bot, database, responder, message
                )
            case CustomStates.NRIC:
                is_text_required_completed = await process_nric(bot, responder, message)
            case CustomStates.ADDRESS:
                is_text_required_completed = await process_address(
                    bot, responder, message, calendar, calendar_callback
                )
            case CustomStates.DATE_OF_BIRTH:
                pass
            case CustomStates.GENDER:
                pass
            case CustomStates.EXISTING_MEDICAL_KNOWLEDGE:
                pass

        if not has_error and is_text_required_completed:
            await database.update_responder(responder)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.id)


async def main() -> None:
    # Remove webhook, it fails sometimes if there is a previous webhook
    await bot.remove_webhook()
    # Drop all pending updates to prevent spams
    await bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, drop_pending_updates=True
    )


asyncio.run(main())
