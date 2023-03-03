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
from utils.dispatcher import process_false_distress, process_manual_acknowledge_distress
from utils.form import (
    process_address,
    process_date_of_birth,
    process_gender,
    process_language,
    process_name,
    process_nric,
    process_onboard,
    process_phone_number,
    process_welcome_message,
)
from utils.handlers import process_cancel, process_profile, process_welcome_message
from utils.location import process_check_in, process_check_out, process_location
from utils.medical import (
    process_add_medical_condition,
    process_add_medical_condition_description,
    process_list_existing_medical_condition,
    process_list_medical_conditions,
    process_remove_medical_condition,
    process_skip_description,
    process_welcome_message,
)
from utils.responder import process_acknowledge_distress, process_reject_distress

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
    print(callback_data)

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
                bot=bot, database=database, callback=call, gender=callback_data[2]
            )
        case "profile":
            await process_profile(bot=bot, database=database, callback=call)
        case "option":
            option = callback_data[1]

            match option:
                case "add":
                    if len(callback_data) > 2:
                        condition = " ".join(callback_data[2:])
                        await process_add_medical_condition(
                            bot=bot,
                            database=database,
                            callback=call,
                            condition=condition,
                        )
                    else:
                        await process_list_medical_conditions(
                            bot=bot, database=database, callback=call
                        )
                case "remove":
                    if len(callback_data) > 2:
                        condition = " ".join(callback_data[2:])
                        await process_remove_medical_condition(
                            bot=bot,
                            database=database,
                            callback=call,
                            condition=condition,
                        )
                    else:
                        await process_list_existing_medical_condition(
                            bot=bot, database=database, callback=call
                        )
                case "skip":
                    await process_skip_description(
                        bot=bot, database=database, callback=call
                    )
        case "cancel":
            await process_cancel(bot=bot, database=database, callback=call)
        case "check_in":
            await process_check_in(bot=bot, database=database, callback=call)
        case "check_out":
            await process_check_out(
                bot=bot,
                database=database,
                callback=call,
            )
        case "distress":
            option = callback_data[1]
            group_chat_message_id = callback_data[2]

            if option == "accept":
                await process_acknowledge_distress(
                    bot=bot,
                    database=database,
                    callback=call,
                    group_chat_message_id=int(group_chat_message_id),
                )
            else:
                await process_reject_distress(
                    bot=bot,
                    database=database,
                    callback=call,
                    group_chat_message_id=int(group_chat_message_id),
                )
        case "dispatcher":
            option = callback_data[1]

            if option == "accept":
                group_chat_message_id = callback_data[2]
                await process_manual_acknowledge_distress(
                    bot=bot,
                    database=database,
                    callback=call,
                    group_chat_message_id=int(group_chat_message_id),
                )
            else:
                await process_false_distress(
                    bot=bot,
                    database=database,
                    callback=call,
                    group_chat_message_id=call.message.id,
                )


@bot.message_handler(commands=["start"])
async def welcome_message(message: types.Message) -> None:
    database = Firestore()
    await process_welcome_message(bot=bot, database=database, message=message)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.id)


@bot.message_handler(func=lambda message: True, content_types=["location"])
async def location_handler(message: types.Message) -> None:
    database = Firestore()
    await process_location(bot=bot, database=database, message=message)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.id)


@bot.message_handler(func=lambda message: True)
async def message_handler(message: types.Message):
    if not message.text or message.from_user.is_bot:
        return
    if not message.text.startswith("/"):
        database = Firestore()

        # Ignore messages sent by users that have yet to onboard
        try:
            responder = await database.get_responder(message.from_user.id)
        except:
            return await bot.delete_message(
                chat_id=message.chat.id, message_id=message.id
            )

        has_error = False
        is_text_required_completed = False

        match responder.state:
            case CustomStates.NAME:
                is_text_required_completed = await process_name(
                    bot=bot, message=message, responder=responder
                )
            case CustomStates.LANGUAGE:
                pass
            case CustomStates.PHONE_NUMBER:
                is_text_required_completed = await process_phone_number(
                    bot=bot, database=database, responder=responder, message=message
                )
            case CustomStates.NRIC:
                is_text_required_completed = await process_nric(
                    bot=bot, responder=responder, message=message
                )
            case CustomStates.ADDRESS:
                is_text_required_completed = await process_address(
                    bot=bot,
                    responder=responder,
                    message=message,
                    calendar=calendar,
                    factory=calendar_callback,
                )
            case CustomStates.DATE_OF_BIRTH:
                pass
            case CustomStates.GENDER:
                pass
            case CustomStates.EXISTING_MEDICAL_KNOWLEDGE:
                is_text_required_completed = (
                    await process_add_medical_condition_description(
                        bot, responder, message
                    )
                )

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
