from database.errors import NotFoundException
from flask import Flask, Response, jsonify

app = Flask(__name__)


import routes.pwid
import routes.responder
import routes.telegram


@app.errorhandler(Exception)
def handle_exception(exception: Exception) -> tuple[Response, int]:
    if isinstance(exception, NotFoundException):
        return jsonify(exception.description), exception.code

    return jsonify(str(exception)), 500
