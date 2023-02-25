import os

from dotenv import load_dotenv
from firebase_admin import initialize_app

# Firebase Initialisation
load_dotenv()
credential_path = str(os.getenv("CREDENTIAL_PATH"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
initialize_app()

from routes import app


@app.route("/healthcheck")
def hello():
    return "I'm alive"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(threaded=True, host="0.0.0.0", port=port)
