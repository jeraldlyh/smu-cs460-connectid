import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, cast

from database import Firestore
from database.models import CustomStates, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils.calendar import Calendar, CallbackFactory
from utils.text import format_form_text

CANCEL_BUTTON = types.InlineKeyboardButton("Cancel", callback_data="cancel")
MEDICAL_CONDITIONS = [
    "Fragile X syndrome",
    "Down syndrome",
    "Developmental delay",
    "Prader-Willi Syndrome (PWS)",
    "Fetal alcohol spectrum disorder (FASD)",
]


def _retrieve_next_state(responder: Responder) -> CustomStates:
    return CustomStates(responder.to_dict()["state"] + 1)


async def process_welcome_message(
    bot: AsyncTeleBot,
    message: types.Message | int,
    is_edit=False,
    is_delete=False,
    database: Optional[Firestore] = None,
    chat_id: Optional[int] = None,
) -> None:
    is_onboarded = True

    try:
        if database:
            await database.get_responder(cast(types.Message, message).chat.id)
    except Exception:
        is_onboarded = False

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
    if not is_onboarded:
        keyboard.add(onboard_button)
    keyboard.add(profile_button)
    keyboard.add(check_in_button, check_out_button, row_width=2)

    is_integer = isinstance(message, int)
    if is_edit and not is_delete:
        await bot.edit_message_text(
            chat_id=chat_id if is_integer else message.chat.id,
            message_id=message if is_integer else message.id,
            text="Welcome to ConnectID, below are a list of actions available.",
            reply_markup=keyboard,
        )
        return

    # Special case to handle for location updates, need to delete normal message without inline keyboard
    # else unable to edit the mssage
    if is_delete:
        await bot.delete_message(
            chat_id=cast(int, chat_id) if is_integer else message.chat.id,
            message_id=message if is_integer else message.id,
        )

    message = await bot.send_message(
        chat_id=cast(int, chat_id) if is_integer else message.chat.id,
        text="Welcome to ConnectID, below are a list of actions available.",
        reply_markup=keyboard,
    )
    if database:
        await database.update_latest_bot_message(message.chat.id, message.id)


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

    await asyncio.sleep(10)
    await process_welcome_message(bot, callback.message, True)


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
    text += f"<b>Medical Knowledge</b>"

    # Handle inexperienced responders
    if len(responder.existing_medical_knowledge) == 0:
        text += "None"
    else:
        text += "\n"

    for index, medical_knowledge in enumerate(responder.existing_medical_knowledge):
        has_description = "description" in medical_knowledge
        medical_description = (
            f" - <i>{medical_knowledge['description']}</i>" if has_description else ""
        )
        text += f"{index + 1}. {medical_knowledge['name']}{medical_description}\n"
    text = text.rstrip("\n")
    options = ["➕ Add", "➖ Remove"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            option, callback_data=f"option {option.split(' ')[1].lower()}"
        )
        for option in options
    ]
    keyboard.add(*buttons, row_width=2)
    keyboard.add(CANCEL_BUTTON)

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
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    existing_experience = (
        [condition["name"] for condition in responder.existing_medical_knowledge]
        if len(responder.existing_medical_knowledge) != 0
        else []
    )

    keyboard = types.InlineKeyboardMarkup()
    options = list(
        filter(
            lambda x: x not in existing_experience,
            MEDICAL_CONDITIONS,
        )
    )

    if len(options) == 0:
        message = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=(
                "You already possess all the medical conditions available in the system. Do contact our staffs at +65 9812 3456 if you deem that this condition is necessary."
            ),
        )
        await asyncio.sleep(3)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.id)
        return

    buttons = [
        types.InlineKeyboardButton(option, callback_data=f"option add {option}")
        for option in options
    ]
    keyboard.add(*buttons, row_width=2)
    keyboard.add(CANCEL_BUTTON)

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
    # Add a new condition
    responder = await database.get_responder(callback.from_user.id)
    responder.existing_medical_knowledge.append(
        {"name": condition, "created_at": str(datetime.now())}
    )
    responder.state = CustomStates.EXISTING_MEDICAL_KNOWLEDGE
    await database.update_responder(responder)

    # Proceeds to next step of adding condition description
    keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Skip", callback_data="option skip")
    keyboard.add(cancel_button)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(
            f"Kindly provide a short description with <b>{condition}</b> in less than 30 words. If you do not have any description, do proceed to press skip."
        ),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def process_skip_description(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    responder.state = CustomStates.NOOP
    await database.update_responder(responder)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(f"You have successfully updated your profile."),
    )

    await asyncio.sleep(3)
    await process_welcome_message(bot=bot, message=callback.message, is_edit=True)


async def process_add_medical_condition_description(
    bot: AsyncTeleBot, responder: Responder, message: types.Message
) -> bool:
    sorted_medical_conditions = sorted(
        responder.existing_medical_knowledge,
        key=lambda x: x["created_at"],
        reverse=True,
    )

    sorted_medical_conditions[0] = {
        **sorted_medical_conditions[0],
        "description": message.text,
    }
    responder.existing_medical_knowledge = sorted_medical_conditions

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=responder.message_id,
        text=(
            f"You have successfully added a description to {sorted_medical_conditions[0]['name']}."
        ),
    )
    await asyncio.sleep(3)
    await process_welcome_message(
        bot=bot, message=responder.message_id, chat_id=message.chat.id, is_edit=True
    )
    return True


def _get_check_in_out_message(check_in=True):
    return f"You have successfully checked {'in' if check_in else 'out'}. You'll{'' if check_in else ' not'} receive any notifications if a distress signal is issued in the vicinity."


async def process_check_in(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button = types.KeyboardButton(text="Send location", request_location=True)
    markup.add(button)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.message.id
    )
    message = await bot.send_message(
        chat_id=callback.message.chat.id,
        text="❗ Click on the button below to send your location",
        reply_markup=markup,
    )
    print(message.id)

    responder = await database.get_responder(callback.message.chat.id)
    responder.message_id = message.id
    await database.update_responder(responder)


async def process_check_out(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.message.chat.id)

    responder.is_available = False
    await database.update_responder(responder)

    notification = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=_get_check_in_out_message(False),
    )
    await asyncio.sleep(3)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=notification.id
    )


async def process_location(
    bot: AsyncTeleBot, database: Firestore, message: types.Message
) -> None:
    responder = await database.get_responder(message.chat.id)

    responder.is_available = True
    responder.location = {
        "longitude": cast(types.Location, message.location).longitude,
        "latitude": cast(types.Location, message.location).latitude,
    }
    await database.update_responder(responder)

    notification = await bot.send_message(
        chat_id=message.chat.id,
        text=_get_check_in_out_message(),
    )
    await asyncio.sleep(3)
    await bot.delete_message(chat_id=message.chat.id, message_id=notification.id)
    await process_welcome_message(
        bot=bot,
        message=responder.message_id,
        is_edit=True,
        chat_id=message.chat.id,
        is_delete=True,
    )
