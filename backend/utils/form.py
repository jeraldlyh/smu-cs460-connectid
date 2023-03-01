import asyncio
import uuid
from datetime import datetime
from typing import List

from database import Firestore
from database.models import CustomStates, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils.calendar import Calendar, CallbackFactory
from utils.handlers import process_welcome_message
from utils.text import format_form_text


def _retrieve_next_state(responder: Responder) -> CustomStates:
    return CustomStates(responder.to_dict()["state"] + 1)


async def process_onboard(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    # User might not have granted location permissions
    latitude, longitude = 0, 0
    if callback.message.location:
        latitude = callback.message.location.latitude
        longitude = callback.message.location.longitude

    responder = Responder(
        id=str(uuid.uuid4()),
        name=callback.from_user.full_name,
        telegram_id=callback.from_user.id,
        state=CustomStates.NAME,
        location={
            "latitude": latitude,
            "longitude": longitude,
        },
    )
    await database.create_responder(responder)

    text = format_form_text(responder, "Kindly enter your full name")
    message = await bot.send_message(
        chat_id=callback.message.chat.id, text=text, parse_mode="HTML"
    )
    await database.update_latest_bot_message(responder, message.id)


async def process_name(
    bot: AsyncTeleBot, message: types.Message, responder: Responder
) -> bool:
    if not message.text:
        return False

    responder.name = message.text
    responder.state = _retrieve_next_state(responder)
    languages = ["Chinese", "English", "Malay"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            language, callback_data=f"language {language.lower()}"
        )
        for language in languages
    ]
    keyboard.add(*buttons, row_width=3)
    text = format_form_text(responder, "Kindly pick your language")

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=responder.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return True


async def process_language(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    languages: list[str],
) -> None:
    # Handle language selection
    responder = await database.get_responder(callback.from_user.id)
    # TODO - allow multiple languages
    responder.languages = languages
    responder.state = _retrieve_next_state(responder)
    await database.update_responder(responder)

    # Proceed to next step
    text = format_form_text(responder, "Kindly provide your phone number")
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        parse_mode="HTML",
    )


async def process_phone_number(
    bot: AsyncTeleBot, database: Firestore, responder: Responder, message: types.Message
) -> bool:
    # Handle phone number input
    if not message.text:
        return False

    responder.phone_number = message.text
    responder.state = _retrieve_next_state(responder)

    # Proceed to next step
    text = format_form_text(responder, "Kindly provide your NRIC")
    response = await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=responder.message_id,
        text=text,
        parse_mode="HTML",
    )

    if isinstance(response, types.Message):
        await database.update_latest_bot_message(responder, message.id)
    return True


async def process_nric(
    bot: AsyncTeleBot, responder: Responder, message: types.Message
) -> bool:
    # Handle NRIC input
    if not message.text:
        return False

    responder.nric = message.text
    responder.state = _retrieve_next_state(responder)

    # Proceed to next step
    text = format_form_text(responder, "Kindly provide your address")
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=responder.message_id,
        text=text,
        parse_mode="HTML",
    )
    return True


async def process_address(
    bot: AsyncTeleBot,
    responder: Responder,
    message: types.Message,
    calendar: Calendar,
    factory: CallbackFactory,
) -> bool:
    # Handle address input
    if not message.text:
        return False

    responder.address = message.text
    responder.state = _retrieve_next_state(responder)

    # Proceed to next step
    now = datetime.now()
    text = format_form_text(responder, "Kindly provide your date of birth")
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=responder.message_id,
        text=text,
        reply_markup=calendar.create(
            name=factory.prefix,
            month=now.month,
            year=now.year,
            delete_upon_completion=False,
        ),
        parse_mode="HTML",
    )
    return True


async def process_date_of_birth(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    calendar: Calendar,
    callback_data: List[str],
) -> None:
    # Handles calendar callbacks
    name, action, day, month, year = callback_data
    response = await calendar.handle_callback(
        bot=bot,
        callback=callback,
        name=name,
        action=action,
        day=int(day),
        month=int(month),
        year=int(year),
    )

    if not isinstance(response, datetime):
        return

    responder = await database.get_responder(callback.from_user.id)
    responder.date_of_birth = str(response.date())
    responder.state = _retrieve_next_state(responder)
    await database.update_responder(responder)

    # Proceeds to next step
    genders = ["👦 Male", "👧 Female"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(gender, callback_data=f"gender {gender.lower()}")
        for gender in genders
    ]
    keyboard.add(*buttons, row_width=2)

    text = format_form_text(responder, "Kindly select your gender")
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=responder.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def process_gender(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    gender: str,
) -> None:
    # Handles gender selection
    responder = await database.get_responder(callback.from_user.id)
    message_id = responder.message_id
    responder.gender = gender

    # Proceeds to next step
    text = format_form_text(
        responder,
        "You've successfully onboarded to <b><i>ConnectID</i></b>, kindly head over to your profile to add any existing medical experience!",
    )

    # Update responder after formatting text, else step will become -1
    responder.state = CustomStates.NOOP
    await database.update_responder(responder)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
    )

    await asyncio.sleep(3)
    await process_welcome_message(bot, callback.message, True)
