import asyncio
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from database import Firestore
from flask import jsonify
from utils import get_group_chat_id

from routes import app
from routes.sos import (
    get_available_responder,
    process_notify_dispatcher,
    process_notify_responder,
)
from routes.telegram import bot


@app.route("/process", methods=["GET"])
async def process_pending_distress_signals():
    database = Firestore()
    pending_distress_signals = await database.get_all_pending_distress()

    if len(pending_distress_signals) == 0:
        return jsonify("No pending signals")

    responders = await database.get_responders()
    for distress_signal in pending_distress_signals:
        available_responder = get_available_responder(
            pwid=distress_signal.pwid, responders=responders
        )

        if available_responder is None:
            continue

        print(f"Found {available_responder.name} for {distress_signal.pwid.name}")

        distress_signal.responder = available_responder
        await database.update_distress(distress_signal)

        # Notify responder
        await process_notify_responder(bot=bot, distress=distress_signal)

        # Responder group chat message
        await process_notify_dispatcher(
            bot=bot,
            responder=distress_signal.responder,
            pwid=distress_signal.pwid,
            address=distress_signal.location.address,
            distress=distress_signal,
        )
    return jsonify(f"{len(pending_distress_signals)} signals processed")


def wrap_async_func():
    asyncio.run(process_pending_distress_signals())


# cron = BackgroundScheduler(daemon=True)
# cron.add_job(func=wrap_async_func, trigger="interval", seconds=60)
# cron.start()


# # Shutdown cron thread if the web process is stopped
# atexit.register(lambda: cron.shutdown(wait=False))
