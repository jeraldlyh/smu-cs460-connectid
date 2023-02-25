from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

from database.errors import NotFoundException
from database.models import PWID
from database.models import Responder
from firebase_admin.firestore import firestore


class Firestore:
    def __init__(self) -> None:
        self.db = firestore.AsyncClient()
        self.RESPONDER_COLLECTION = "responder"
        self.PWID_COLLECTION = "pwid"

    def get_pwid_ref(self, id: str) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.PWID_COLLECTION).document(id)

    async def create_pwid(self, data: PWID) -> None:
        doc_ref = self.get_pwid_ref(data.id)
        await doc_ref.set(data.to_dict())

    def get_responder_ref(self, id: str) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.RESPONDER_COLLECTION).document(id)

    async def get_responder(self, id: str) -> Dict[str, Any] | None:
        doc_ref = self.get_responder_ref(id)
        doc = await doc_ref.get()

        if not doc.exists:
            raise NotFoundException(f"${id} does not exist")
        return doc.to_dict()

    async def create_responder(self, data: Responder) -> None:
        doc_ref = self.get_responder_ref(data.id)
        await doc_ref.set(data.to_dict())


database = Firestore()
