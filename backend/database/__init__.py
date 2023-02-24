from datetime import datetime
from typing import List

from firebase_admin import credentials, firestore, initialize_app


class Firestore:
    def __init__(self) -> None:
        credential = credentials.Certificate("key.json")
        firebase_app = initialize_app(credential)

        self.db = firestore.client()
        self.RESPONDER_COLLECTION = "responder"
        self.PWID_COLLECTION = "pwid"

    def get_responser_ref(self, id: str) -> None:
        pass

    def get_pwid_ref(self, id: str) -> None:
        pass


database = Firestore()
