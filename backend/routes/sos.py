import sys

from database import Firestore
from database.models import Responder
from flask import Response, jsonify, request

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

    smallest_latitude, smallest_longitude = (
        sys.maxsize - pwid_latitude,
        sys.maxsize - pwid_longitude,
    )

    # TODO- add matching for language and medical condition

    for responder in responders:
        responder_latitude = int(responder.location.get("latitude", 0))
        responder_longitude = int(responder.location.get("longitude", 0))

        latitude = abs(pwid_latitude - responder_latitude)
        longitude = abs(pwid_longitude - responder_longitude)

        if latitude < smallest_latitude and longitude < smallest_longitude:
            available_responder = responder

    if not available_responder:
        # TODO: blast out telegram message
        return jsonify("Unable to find an available responder right now")

    # TODO: notify repsonder
    return jsonify(f"{available_responder.name} will be attending to {pwid.name}")
