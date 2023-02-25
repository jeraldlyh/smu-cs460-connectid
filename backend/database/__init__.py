from typing import Any, Dict

from firebase_admin.firestore import firestore

from database.errors import AlreadyExistsException, NotFoundException
from database.models import PWID, Responder


class SingletonClass(object):
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(SingletonClass, cls).__new__(cls)
        return cls.instance


class Firestore(SingletonClass):
    def __init__(self) -> None:
        self.db = firestore.AsyncClient()
        self.RESPONDER_COLLECTION = "responder"
        self.PWID_COLLECTION = "pwid"

    def _validate_doc(
        self, doc: firestore.DocumentSnapshot, message: str, abort_if_created=False
    ) -> None:
        if doc.exists and abort_if_created:
            raise AlreadyExistsException(message)

        if not abort_if_created and not doc.exists:
            raise NotFoundException(message)

    def get_pwid_ref(self, name: str) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.PWID_COLLECTION).document(name)

    async def get_pwid(self, name: str) -> Dict[str, Any] | None:
        doc_ref = self.get_pwid_ref(name)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{name} does not exist")
        return doc.to_dict()

    async def create_pwid(self, data: PWID) -> None:
        doc_ref = self.get_pwid_ref(data.name)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{data.name} already exists", True)
        await doc_ref.set(data.to_dict())

    def get_responder_ref(self, name: str) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.RESPONDER_COLLECTION).document(name)

    async def get_responder(self, name: str) -> Dict[str, Any] | None:
        doc_ref = self.get_responder_ref(name)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{name} does not exist")
        return doc.to_dict()

    async def create_responder(self, data: Responder) -> None:
        doc_ref = self.get_responder_ref(data.name)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{data.name} already exists", True)
        await doc_ref.set(data.to_dict())
