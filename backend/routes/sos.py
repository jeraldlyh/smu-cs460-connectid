import sys
from typing import List, cast

import requests
from backend.utils import get_is_mock_location
from database import Firestore
from database.models import PWID, Distress, Location, Responder
from flask import jsonify, request
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from utils import get_group_chat_id
from utils.medical import _get_list_of_existing_experience
from utils.text import _get_pwid_contacts
from utils.url import _get_google_maps_link

from routes import app
from routes.telegram import bot


def _get_location_of_ip_address(ip_address: str) -> Location:
    fields = [
        "status",
        "message",
        "regionName",
        "district",
        "zip",
        "lat",
        "lon",
        "query",
    ]
    response = requests.get(
        f"http://ip-api.com/json/{ip_address}?fields={','.join(fields)}"
    )
    result = response.json()
    print(result)

    return Location(
        longitude=1.2939 if get_is_mock_location() else result["lon"],
        latitude=103.8466 if get_is_mock_location() else result["lat"],
        address="Fort Canning Park, (S)179037, infront of the handicap sign and below the tree"
        if get_is_mock_location()
        else f"{result['district']}, (S){result['zip']}",
    )


def get_available_responder(
    pwid: PWID, responders: List[Responder]
) -> Responder | None:
    available_responder = None
    pwid_latitude = pwid.location.latitude
    pwid_longitude = pwid.location.longitude

    smallest_latitude, smallest_longitude, largest_intersection = (
        sys.maxsize - pwid_latitude,
        sys.maxsize - pwid_longitude,
        0,
    )

    for responder in responders:
        if responder.is_available:
            latitude = abs(pwid_latitude - responder.location.latitude)
            longitude = abs(pwid_longitude - responder.location.longitude)
            intersections = set(
                _get_list_of_existing_experience(responder)
            ).intersection(pwid.medical_conditions)
            matches_language_preference = (
                pwid.language_preference in responder.languages
            )
            matches_gender_preference = pwid.gender_preference == responder.gender

            if (
                latitude < smallest_latitude
                and longitude < smallest_longitude
                and len(intersections) > largest_intersection
                and matches_language_preference
                and matches_gender_preference
            ):
                available_responder = responder
    return available_responder


@app.route("/sos", methods=["GET"])
async def request_help():
    args = request.args
    name = args.get("name")

    if not name:
        return jsonify("Missing query parameters"), 400

    database = Firestore()
    pwid = await database.get_pwid(name)

    pwid_ip_address = (
        request.environ["REMOTE_ADDR"]
        if request.environ.get("HTTP_X_FORWARDED_FOR") is None
        else request.environ["HTTP_X_FORWARDED_FOR"]
    )

    if "," in pwid_ip_address:
        pwid_ip_address = pwid_ip_address.split(",")[0]

    if not pwid_ip_address:
        return jsonify("Unable to retrieve IP address"), 400

    location = _get_location_of_ip_address(pwid_ip_address)
    pwid.location = location
    responders = await database.get_responders()

    available_responder = get_available_responder(pwid=pwid, responders=responders)

    group_chat_message_id = await process_notify_dispatcher(
        bot=bot, responder=available_responder, pwid=pwid, address=location.address
    )

    distress = Distress(
        group_chat_message_id=group_chat_message_id,
        message_id=-1,
        location=location,
        pwid=pwid,
        responder=available_responder,
    )

    if not available_responder:
        await database.create_distress(distress)
        return jsonify("Unable to find an available responder right now"), 400

    message_id = await process_notify_responder(bot=bot, distress=distress)
    distress.message_id = message_id
    await database.create_distress(distress)

    return available_responder.name


async def process_notify_responder(bot: AsyncTeleBot, distress: Distress) -> int:
    keyboard = types.InlineKeyboardMarkup()
    accept = types.InlineKeyboardButton(
        text="✅ Accept",
        callback_data=f"distress accept {distress.group_chat_message_id}",
    )
    decline = types.InlineKeyboardButton(
        text="❌ Decline",
        callback_data=f"distress decline {distress.group_chat_message_id}",
    )
    keyboard.add(accept, decline, row_width=2)

    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += f"<b>{distress.pwid.name}</b> is in need of help now. He's currently located at <a href='{_get_google_maps_link(distress.pwid.location.address)}'>{distress.pwid.location.address}</a>. Kindly acknowledge this message within 30 seconds."

    message = await bot.send_message(
        chat_id=cast(Responder, distress.responder).telegram_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return message.id


async def process_notify_dispatcher(
    bot: AsyncTeleBot,
    responder: Responder | None,
    pwid: PWID,
    address: str,
    distress: Distress | None = None,
) -> int:
    group_chat_message_id = (
        distress.group_chat_message_id if distress is not None else -1
    )
    keyboard = types.InlineKeyboardMarkup()
    accept = types.InlineKeyboardButton(
        text="✅ Accept", callback_data=f"dispatcher accept {group_chat_message_id}"
    )
    decline = types.InlineKeyboardButton(
        text="❌ Cancel", callback_data=f"dispatcher cancel {group_chat_message_id}"
    )
    keyboard.add(accept, decline, row_width=2)

    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += "<b>Status: </b> 🔴 Not Acknowledged\n\n"
    text += _get_pwid_contacts(pwid)
    text += f"<b>{pwid.name}</b> is in need of help now. He's currently located at <a href='{_get_google_maps_link(address)}'>{address}</a>.\n\n"

    if responder is None:
        text += "There's no responders available at this moment. Kindly handle this signal manually or wait for the system to look for a responder."
    else:
        text += f"A message has been sent out to <b>{responder.name}</b> to request for assistance."
    text += "\n\n<i>If you think that this is a false signal, please proceed to cancel this signal.</i>"

    if distress is not None:
        await bot.edit_message_text(
            chat_id=get_group_chat_id(),
            message_id=distress.group_chat_message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return -1

    message = await bot.send_message(
        chat_id=get_group_chat_id(),
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    # Hacky method to include message id in payload
    keyboard = types.InlineKeyboardMarkup()
    accept = types.InlineKeyboardButton(
        text="✅ Accept", callback_data=f"dispatcher accept {message.id}"
    )
    decline = types.InlineKeyboardButton(
        text="❌ Cancel", callback_data=f"dispatcher cancel {message.id}"
    )
    keyboard.add(accept, decline, row_width=2)

    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += "<b>Status: </b> 🔴 Not Acknowledged\n\n"
    text += _get_pwid_contacts(pwid)
    text += f"<b>{pwid.name}</b> is in need of help now. He's currently located at <a href='{_get_google_maps_link(address)}'>{address}</a>.\n\n"

    if responder is None:
        text += "There's no responders available at this moment. Kindly handle this signal manually or wait for the system to look for a responder."
    else:
        text += f"A message has been sent out to <b>{responder.name}</b> to request for assistance."
    text += "\n\n<i>If you think that this is a false signal, please proceed to cancel this signal.</i>"

    await bot.edit_message_text(
        chat_id=get_group_chat_id(),
        message_id=message.id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return message.id
