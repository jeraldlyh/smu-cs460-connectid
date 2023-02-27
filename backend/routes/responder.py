import uuid

from database import Firestore
from database.models import CustomStates, Responder
from flask import Response, jsonify, request

from routes import app


@app.route("/responder/<id>", methods=["GET"])
async def get_responder(telegram_id: int) -> Response:
    database = Firestore()
    responder = await database.get_responder(telegram_id)
    return jsonify(responder)


@app.route("/responder", methods=["POST"])
async def create_responder() -> Response:
    if not request.is_json:
        return jsonify("Missing request body")

    payload = request.get_json()
    payload["id"] = str(uuid.uuid4())
    payload["is_available"] = True
    payload["state"] = CustomStates.ONBOARD
    responder = Responder.from_dict(payload)

    database = Firestore()
    await database.create_responder(responder)

    return jsonify(f"Succesfully created responder - {responder.name}")
