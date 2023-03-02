import os
import sys
import uuid
from typing import Optional, Tuple

import requests
from database import Firestore
from database.models import PWID, Distress, Location, Responder
from flask import jsonify, request
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from utils.medical import _get_list_of_existing_experience
from utils.url import _get_google_maps_link

from routes import app
from routes.telegram import bot

GROUP_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", -1))


def _get_location_of_ip_address(ip_address: str) -> Tuple[Location, str]:
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

    return (
        Location(longitude=result["lon"], latitude=result["lat"]),
        f"{result['district']}, (S){result['zip']}",
    )


async def _create_distress(
    database: Firestore,
    location: str,
    pwid: PWID,
    responder: Optional[Responder] = None,
) -> str:
    distress = Distress(
        id=str(uuid.uuid4()), location=location, pwid=pwid, responder=responder
    )
    await database.create_distress(distress)

    return distress.id


@app.route("/sos", methods=["GET"])
async def request_help():
    args = request.args
    name = args.get("name")

    if not name:
        return jsonify("Missing query parameters"), 400

    database = Firestore()
    pwid = await database.get_pwid(name)
    pwid_ip_address = request.remote_addr

    if not pwid_ip_address:
        return jsonify("Unable to retrieve IP address"), 400

    location, address = _get_location_of_ip_address("219.75.78.138")
    pwid.location = location
    responders = await database.get_responders()

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

    if not available_responder:
        await _create_distress(database=database, location=address, pwid=pwid)
        # TODO: blast out telegram message
        return jsonify("Unable to find an available responder right now"), 400

    distress_id = await _create_distress(
        database=database, location=address, pwid=pwid, responder=available_responder
    )

    await process_notify_responder(
        bot=bot,
        responder=available_responder,
        pwid=pwid,
        address=address,
        distress_id=distress_id,
    )
    return jsonify(f"{available_responder.name} will be attending to {pwid.name}")


async def process_notify_responder(
    bot: AsyncTeleBot, responder: Responder, pwid: PWID, address: str, distress_id: str
) -> None:
    keyboard = types.InlineKeyboardMarkup()
    accept = types.InlineKeyboardButton(
        text="✅ Accept", callback_data=f"distress accept {distress_id}"
    )
    decline = types.InlineKeyboardButton(
        text="❌ Decline", callback_data=f"distress decline {distress_id}"
    )
    keyboard.add(accept, decline, row_width=2)

    text = "<b>Distress Signal</b>\n\n"
    text += f"<b>{pwid.name}</b> is in need of help now. He's currently located at <a href='{_get_google_maps_link(address)}'>{address}</a>. Kindly acknowledge this message within 30 seconds."

    await bot.send_message(
        chat_id=responder.telegram_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
