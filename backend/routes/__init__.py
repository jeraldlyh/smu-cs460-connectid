from database.errors import NotFoundException
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

import routes.pwid
import routes.responder
import routes.scheduler
import routes.sos
import routes.telegram

# @app.errorhandler(Exception)
# def handle_exception(exception: Exception) -> tuple[Response, int]:
#     if isinstance(exception, NotFoundException):
#         return jsonify(exception.description), exception.code

#     return jsonify(str(exception)), 500
