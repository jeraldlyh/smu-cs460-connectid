import json
import os

from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

# Firebase Initialisation
load_dotenv()
CREDENTIAL_PATH = str(os.getenv("CREDENTIAL_PATH"))


# Manually generate service account credentials
def get_firestore_credentials() -> dict:
    return {
        "type": str(os.getenv("FIRESTORE_TYPE")),
        "project_id": str(os.getenv("FIRESTORE_PROJECT_ID")),
        "private_key_id": str(os.getenv("FIRESTORE_PRIVATE_KEY_ID")),
        "private_key": str(os.getenv("FIRESTORE_PRIVATE_KEY")),
        "client_email": str(os.getenv("FIRESTORE_CLIENT_EMAIL")),
        "client_id": str(os.getenv("FIRESTORE_CLIENT_ID")),
        "auth_uri": str(os.getenv("FIRESTORE_AUTH_URI")),
        "token_uri": str(os.getenv("FIRESTORE_TOKEN_URI")),
        "auth_provider_x509_cert_url": str(
            os.getenv("FIRESTORE_AUTH_PROVIDER_X509_CERT_URL")
        ),
        "client_x509_cert_url": str(os.getenv("FIRESTORE_CLIENT_X509_CERT_URL")),
    }


# Manually generate service account credentials
def create_firestore_credentials() -> None:
    file = open(CREDENTIAL_PATH, "w")
    file.write(
        json.dumps(
            get_firestore_credentials(),
            indent=4,
        )
    )
    file.close()


if bool(os.getenv("DEV", False)):
    create_firestore_credentials()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIAL_PATH
    initialize_app()
else:
    initialize_app(credential=credentials.Certificate(get_firestore_credentials()))

from routes import app


@app.route("/healthcheck")
def hello():
    return "I'm alive"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(threaded=True, host="0.0.0.0", port=port)
