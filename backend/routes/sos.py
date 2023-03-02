import sys

from database import Firestore
from database.models import Responder
from flask import Response, jsonify, request
from utils.medical import _get_list_of_existing_experience

from routes import app


@app.route("/sos", methods=["GET"])
async def request_help():
    args = request.args
    name = args.get("name")

    if not name:
        return jsonify("Missing query parameters"), 400

    database = Firestore()
    pwid = await database.get_pwid(name)
    responders = await database.get_responders()

    available_responder = None
    pwid_latitude = int(pwid.location.get("latitude", 0))
    pwid_longitude = int(pwid.location.get("longitude", 0))

    smallest_latitude, smallest_longitude, largest_intersection = (
        sys.maxsize - pwid_latitude,
        sys.maxsize - pwid_longitude,
        0,
    )

    for responder in responders:
        if responder.is_available:
            responder_latitude = int(responder.location.get("latitude", 0))
            responder_longitude = int(responder.location.get("longitude", 0))

            latitude = abs(pwid_latitude - responder_latitude)
            longitude = abs(pwid_longitude - responder_longitude)
            intersections = set(
                _get_list_of_existing_experience(responder)
            ).intersection(pwid.medical_conditions)
            matches_language_preference = (
                pwid.language_preference in responder.languages
            )

            if (
                latitude < smallest_latitude
                and longitude < smallest_longitude
                and len(intersections) > largest_intersection
                and matches_language_preference
            ):
                available_responder = responder

    if not available_responder:
        # TODO: blast out telegram message
        return jsonify("Unable to find an available responder right now")

    # TODO: notify repsonder
    return jsonify(f"{available_responder.name} will be attending to {pwid.name}")
