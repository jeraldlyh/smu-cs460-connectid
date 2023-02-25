from database import database
from database import Responder
from database.errors import NotFoundException
from flask import jsonify
from flask import request
from flask import Response
from routes import app


@app.route("/responder/<id>", methods=["GET"])
async def get_responder(id: str) -> Response:
    responder = await database.get_responder(id)
    return jsonify(responder)


@app.route("/responder", methods=["POST"])
async def create_responder() -> Response:
    if not request.is_json:
        return jsonify("Missing request body")
    payload = request.get_json()
    responder = Responder.from_dict(payload)
    await database.create_responder(responder)

    return jsonify(f"Succesfully created responder - {responder.name}")


@app.errorhandler(Exception)
def handle_exception(exception: Exception) -> tuple[Response, int]:
    error_message = str(exception)

    if isinstance(exception, NotFoundException):
        return jsonify(error_message), 404

    return jsonify(error_message), 500
