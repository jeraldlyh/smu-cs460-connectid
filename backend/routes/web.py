from database import Firestore
from flask import jsonify, request

from routes import app


@app.route("/distress", methods=["GET"])
async def get_distress_signals():
    database = Firestore()
    distress_signals = await database.get_all_incomplete_distress()

    return jsonify([distress.to_dict() for distress in distress_signals])
