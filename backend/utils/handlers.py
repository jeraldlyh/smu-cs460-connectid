import uuid
from datetime import datetime

from database import Firestore
from database.models import CustomStates, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot_calendar import Calendar, CallbackData


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
    await bot.send_message(callback.message.chat.id, f"Kindly enter your full name")


async def process_name(
    bot: AsyncTeleBot, message: types.Message, responder: Responder
) -> None:
    if not message.text:
        return

    responder.name = message.text
    languages = ["Chinese", "English", "Malay"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            language, callback_data=f"language {language.lower()}"
        )
        for language in languages
    ]
    keyboard.add(*buttons, row_width=3)

    await bot.send_message(
        message.chat.id, "Kindly pick your language", reply_markup=keyboard
    )


async def process_language(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    languages: list[str],
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    # TODO - allow multiple languages
    responder.languages = languages
    responder.state = _retrieve_next_state(responder)

    await database.update_responder(responder)
    await bot.send_message(
        callback.message.chat.id, f"Kindly provide your phone number"
    )


async def process_phone_number(
    bot: AsyncTeleBot, responder: Responder, message: types.Message
) -> None:
    if not message.text:
        return

    responder.phone_number = message.text
    await bot.send_message(message.chat.id, "Kindly provide your NRIC")


async def process_nric(
    bot: AsyncTeleBot, responder: Responder, message: types.Message
) -> None:
    if not message.text:
        return

    responder.nric = message.text
    await bot.send_message(message.chat.id, "Kindly provide your address")


async def process_address(
    bot: AsyncTeleBot,
    responder: Responder,
    message: types.Message,
    calendar: Calendar,
    calendar_callback: CallbackData,
) -> None:
    if not message.text:
        return

    responder.address = message.text
    await bot.send_message(
        message.chat.id,
        "Kindly provide your date of birth",
        reply_markup=calendar.create_calendar(
            name=calendar_callback.prefix,
            year=datetime.now().year,
            month=datetime.now().month,
        ),
    )


async def process_date_of_birth(
    bot: AsyncTeleBot,
    callback: types.CallbackQuery,
    calendar: Calendar,
    calendar_callback: CallbackData,
    callback_data: str,
) -> None:
    # TODO - create custom calendar module

    genders = ["Male", "Female"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(gender, callback_data=f"gender {gender.lower()}")
        for gender in genders
    ]
    keyboard.add(*buttons, row_width=2)

    await bot.send_message(
        callback.message.chat.id, "Kindly select your gender", reply_markup=keyboard
    )


async def process_gender(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    gender: str,
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    responder.gender = gender
    responder.state = _retrieve_next_state(responder)

    await database.update_responder(responder)
    await bot.send_message(
        callback.message.chat.id,
        f"You've successfully onboarded to ConnectID, kindly head over to your profile to add any existing experience",
    )
