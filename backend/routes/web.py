from datetime import datetime

from database import Firestore
from database.models import Location, Responder
from flask import jsonify, request

from routes import app

SYSTEM = Responder(id="-1", telegram_id=-1, location=Location(-1, -1), name="System")


@app.route("/distress", methods=["GET"])
async def get_all_distress_signals():
    database = Firestore()
    distress_signals = await database.get_all_distress()

    return jsonify([distress.to_dict() for distress in distress_signals])


@app.route("/distress/accept/<id>", methods=["POST"])
async def accept_distress_signals(id: int):
    database = Firestore()
    distress_signal = await database.get_distress(id)
    distress_signal.acknowledged_at = str(datetime.now())
    distress_signal.is_acknowledged = True
    distress_signal.responder = SYSTEM

    await database.update_distress(distress_signal)

    return jsonify({"message": f"Distress signal {id} has been acknowledged"})


@app.route("/distress/cancel/<id>", methods=["POST"])
async def cancel_distress_signals(id: int):
    database = Firestore()
    distress_signal = await database.get_distress(id)
    distress_signal.is_completed = True
    distress_signal.responder = SYSTEM

    await database.update_distress(distress_signal)

    return jsonify({"message": f"Distress signal {id} has been cancelled"})
