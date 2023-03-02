from enum import Enum
from typing import Dict, List, Optional


class ExistingMedicalKnowledge:
    def __init__(
        self,
        condition: str,
        created_at: str,
        description: Optional[str] = "",
    ) -> None:
        self.condition = condition
        self.description = description
        self.created_at = created_at

    @staticmethod
    def from_dict(source):
        return ExistingMedicalKnowledge(
            condition=source["condition"],
            created_at=source["created_at"],
            description=source["description"],
        )

    def to_dict(self):
        return {
            "condition": self.condition,
            "description": self.description,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return str(vars(self))


# class Location:
#     def __init__(self, longitude: int, latitude: int) -> None:
#         self.longitude = longitude
#         self.latitude = latitude

#     @staticmethod
#     def from_dict(source):
#         return Location(
#             source["longitude"],
#             source["latitude"],
#         )

#     def to_dict(self):
#         return {
#             "longitude": self.longitude,
#             "latitude": self.latitude,
#         }


# class EmergencyContact:
#     def __init__(self, name: str, phone_number: str, relationship: str) -> None:
#         self.name = name
#         self.phone_number = phone_number
#         self.relationship = relationship

#     @staticmethod
#     def from_dict(source):
#         return EmergencyContact(
#             source["name"],
#             source["phone_number"],
#             source["relationship"],
#         )

#     def to_dict(self):
#         return {
#             "name": self.name,
#             "phone_number": self.phone_number,
#             "relationship": self.relationship,
#         }

#     def __repr__(self) -> str:
#         return str(vars(self))


class CustomStates(Enum):
    NOOP = -1
    ONBOARD = 0
    NAME = 1
    LANGUAGE = 2
    PHONE_NUMBER = 3
    NRIC = 4
    ADDRESS = 5
    DATE_OF_BIRTH = 6
    GENDER = 7
    EXISTING_MEDICAL_KNOWLEDGE = 8


class PWID:
    def __init__(
        self,
        id: str,
        name: str,
        language_preference: str,
        phone_number: str,
        medical_conditions: List[str],
        nric: str,
        address: str,
        date_of_birth: str,
        gender: str,
        gender_preference: str,
        emergency_contacts: List[Dict[str, str]],
        location: Dict[str, str],
    ) -> None:
        self.id = id
        self.name = name
        self.language_preference = language_preference
        self.phone_number = phone_number
        self.medical_conditions = medical_conditions
        self.nric = nric
        self.address = address
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.gender_preference = gender_preference
        self.emergency_contacts = emergency_contacts
        self.location = location

    @staticmethod
    def from_dict(source):
        return PWID(
            id=source["id"],
            name=source["name"],
            language_preference=source["language_preference"],
            phone_number=source["phone_number"],
            medical_conditions=source["medical_conditions"],
            nric=source["nric"],
            address=source["address"],
            date_of_birth=source["date_of_birth"],
            gender=source["gender"],
            gender_preference=source["gender_preference"],
            emergency_contacts=source["emergency_contacts"],
            location=source["location"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "language_preference": self.language_preference,
            "phone_number": self.phone_number,
            "medical_conditions": self.medical_conditions,
            "nric": self.nric,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "gender_preference": self.gender_preference,
            "emergency_contacts": self.emergency_contacts,
            "location": self.location,
        }

    def __repr__(self) -> str:
        return str(vars(self))


class Responder:
    def __init__(
        self,
        id: str,
        telegram_id: int,
        location: Dict[str, float],
        name: str = "",
        languages: List[str] = [],
        phone_number: str = "",
        nric: str = "",
        address: str = "",
        date_of_birth: str = "",
        gender: str = "",
        existing_medical_knowledge: List[ExistingMedicalKnowledge] = [],
        is_available: bool = True,
        state: CustomStates = CustomStates.ONBOARD,
        message_id: int = -1,  # Used to keep track of last message sent by bot
    ) -> None:
        self.id = id
        self.telegram_id = telegram_id
        self.location = location
        self.name = name
        self.languages = languages
        self.phone_number = phone_number
        self.nric = nric
        self.address = address
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.existing_medical_knowledge = existing_medical_knowledge
        self.is_available = is_available
        self.state = state
        self.message_id = message_id

    @staticmethod
    def from_dict(source):
        return Responder(
            id=source["id"],
            telegram_id=source["telegram_id"],
            location=source["location"],
            name=source["name"],
            languages=source["languages"],
            phone_number=source["phone_number"],
            nric=source["nric"],
            address=source["address"],
            date_of_birth=source["date_of_birth"],
            gender=source["gender"],
            existing_medical_knowledge=[
                ExistingMedicalKnowledge.from_dict(x)
                for x in source["existing_medical_knowledge"]
            ],
            is_available=source["is_available"],
            state=CustomStates(source["state"]),
            message_id=source["message_id"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "languages": self.languages,
            "phone_number": self.phone_number,
            "telegram_id": self.telegram_id,
            "nric": self.nric,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "existing_medical_knowledge": [
                x.to_dict() for x in self.existing_medical_knowledge
            ],
            "location": self.location,
            "is_available": self.is_available,
            "state": self.state.value,
            "message_id": self.message_id,
        }

    def __repr__(self) -> str:
        return str(vars(self))
