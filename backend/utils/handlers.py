import asyncio
import uuid
from datetime import datetime
from typing import List

from database import Firestore
from database.models import CustomStates, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils.calendar import Calendar, CallbackFactory
from utils.text import format_form_text


def _retrieve_next_state(responder: Responder) -> CustomStates:
    return CustomStates(responder.to_dict()["state"] + 1)


async def process_welcome_message(
    bot: AsyncTeleBot, message: types.Message, is_edit=False
) -> None:
    onboard_button = types.InlineKeyboardButton(
        text="📝 Onboard", callback_data="onboard"
    )
    check_in_button = types.InlineKeyboardButton(
        text="✅ Check-In", callback_data="check_in"
    )
    check_out_button = types.InlineKeyboardButton(
        text="❌ Check-Out", callback_data="check_out"
    )
    profile_button = types.InlineKeyboardButton(
        text="📖 Profile", callback_data="profile"
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(onboard_button)
    keyboard.add(profile_button)
    keyboard.add(check_in_button, check_out_button, row_width=2)

    if is_edit:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.id,
            text="Welcome to ConnectID, below are a list of actions available.",
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text="Welcome to ConnectID, below are a list of actions available.",
            reply_markup=keyboard,
        )


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
    responder.message_id = -1
    await database.update_responder(responder)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
    )

    await asyncio.sleep(10)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.message.id
    )


async def process_profile(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)

    text = "<b>📖  Profile</b>\n\n"
    text += f"<b>Name</b>: {responder.name}\n"
    text += f"<b>Gender</b>: {responder.gender}\n"
    text += f"<b>Date of Birth</b>: {responder.date_of_birth}\n"
    text += f"<b>NRIC</b>: {responder.nric}\n"
    text += f"<b>Phone Number</b>: {responder.phone_number}\n"
    text += f"<b>Address</b>: {responder.address}\n"
    text += f"<b>Medical Knowledge</b>: "

    for medical_knowledge in responder.existing_medical_knowledge:
        text += f"{medical_knowledge['name']} ({medical_knowledge['description']}), "
    text.rstrip(", ")

    options = ["➕ Add", "➖ Remove"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            option, callback_data=f"option {option.split(' ')[1].lower()}"
        )
        for option in options
    ]
    keyboard.add(*buttons, row_width=2)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def process_cancel(bot: AsyncTeleBot, callback: types.CallbackQuery) -> None:
    await process_welcome_message(bot=bot, message=callback.message, is_edit=True)


async def process_list_medical_conditions(
    bot: AsyncTeleBot, callback: types.CallbackQuery
) -> None:
    options = [
        "Fragile X syndrome",
        "Down syndrome",
        "Developmental delay",
        "Prader-Willi Syndrome (PWS)",
        "Fetal alcohol spectrum disorder (FASD)",
        "Inexperienced",
    ]
    keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Cancel", callback_data="cancel")
    buttons = [
        types.InlineKeyboardButton(option, callback_data=f"option add {option}")
        for option in options
    ]
    keyboard.add(*buttons, row_width=2)
    keyboard.add(cancel_button)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=("Kindly choose one of the options below."),
        reply_markup=keyboard,
    )


async def process_add_medical_condition(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    condition: str,
) -> None:
    await database.get_responder(callback.from_user.id)


async def process_add_medical_condition_description(
    bot: AsyncTeleBot, callback: types.CallbackQuery
) -> None:
    pass
