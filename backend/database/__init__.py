from typing import List

from firebase_admin.firestore import firestore

from database.errors import AlreadyExistsException, NotFoundException
from database.models import PWID, Distress, Responder
from database.singleton import SingletonClass


class Firestore(SingletonClass):
    def __init__(self) -> None:
        self.db = firestore.AsyncClient()
        self.RESPONDER_COLLECTION = "responder"
        self.PWID_COLLECTION = "pwid"
        self.DISTRESS_COLLECTION = "distress"

    def _validate_doc(
        self, doc: firestore.DocumentSnapshot, message: str, abort_if_created=False
    ) -> None:
        if doc.exists and abort_if_created:
            raise AlreadyExistsException(message)

        if not abort_if_created and not doc.exists:
            raise NotFoundException(message)

    def _get_pwid_ref(self, name: str) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.PWID_COLLECTION).document(name)

    async def get_pwid(self, name: str) -> PWID:
        doc_ref = self._get_pwid_ref(name)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{name} does not exist")
        return PWID.from_dict(doc.to_dict())

    async def create_pwid(self, data: PWID) -> None:
        doc_ref = self._get_pwid_ref(data.name)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{data.name} already exists", True)
        await doc_ref.set(data.to_dict())

    def _get_responder_ref(self, telegram_id: int) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.RESPONDER_COLLECTION).document(str(telegram_id))

    async def get_responder(self, telegram_id: int) -> Responder:
        doc_ref = self._get_responder_ref(telegram_id)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{telegram_id} does not exist")
        return Responder.from_dict(doc.to_dict())

    async def create_responder(self, data: Responder) -> None:
        doc_ref = self._get_responder_ref(data.telegram_id)
        doc = await doc_ref.get()

        self._validate_doc(doc, f"{data.name} already exists", True)
        await doc_ref.set(data.to_dict())

    async def get_responders(self) -> List[Responder]:
        docs = (
            self.db.collection(self.RESPONDER_COLLECTION)
            .where("is_available", "==", True)
            .stream()
        )

        responders = []
        async for x in docs:  # type: ignore
            responders.append(Responder.from_dict(x.to_dict()))

        return responders

    async def update_responder(self, data: Responder) -> None:
        doc_ref = self._get_responder_ref(data.telegram_id)
        await doc_ref.update(data.to_dict())

    async def update_latest_bot_message(
        self, data: Responder | int, message_id: int
    ) -> None:
        responder = (
            await self.get_responder(data.telegram_id)
            if isinstance(data, Responder)
            else await self.get_responder(data)
        )
        responder.message_id = message_id

        await self.update_responder(responder)

    async def get_latest_bot_message(self, data: Responder) -> int:
        responder = await self.get_responder(data.telegram_id)

        return responder.message_id

    def _get_distress_ref(self, doc_id: int) -> firestore.AsyncDocumentReference:
        return self.db.collection(self.DISTRESS_COLLECTION).document(str(doc_id))

    async def create_distress(self, data: Distress) -> None:
        doc_ref = self._get_distress_ref(data.group_chat_message_id)
        await doc_ref.set(data.to_dict())

    async def get_distress(self, group_chat_message_id: int) -> Distress:
        doc_ref = self._get_distress_ref(group_chat_message_id)
        doc = await doc_ref.get()

        return Distress.from_dict(doc.to_dict())

    async def update_distress(self, data: Distress) -> None:
        doc_ref = self._get_distress_ref(data.group_chat_message_id)
        await doc_ref.update(data.to_dict())

    async def get_all_pending_distress(self) -> List[Distress]:
        docs = (
            self.db.collection(self.DISTRESS_COLLECTION)
            .where("is_acknowledged", "==", False)
            .where("responder", "==", {})
            .stream()
        )

        distress_signals = []
        async for x in docs:  # type: ignore
            distress_signals.append(Distress.from_dict(x.to_dict()))
        return distress_signals
