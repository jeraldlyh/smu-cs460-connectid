import uuid

from database import Firestore
from database.errors import NotFoundException
from database.models import PWID, Responder
from flask import Response, jsonify, request

from routes import app


@app.route("/pwid/<id>", methods=["GET"])
async def get_pwid(id: str) -> Response:
    database = Firestore()
    pwid = await database.get_pwid(id)
    return jsonify(pwid)


@app.route("/pwid", methods=["POST"])
async def create_pwid() -> Response:
    if not request.is_json:
        return jsonify("Missing request body")

    payload = request.get_json()
    payload["id"] = str(uuid.uuid4())
    pwid = PWID.from_dict(payload)

    database = Firestore()
    await database.create_pwid(pwid)

    return jsonify(f"Succesfully created pwid - {pwid.name}")
