from enum import Enum
from typing import Dict, List

# class ExistingMedicalKnowledge:
#     def __init__(self, medical_condition: str, description: str) -> None:
#         self.medical_condition = medical_condition
#         self.description = description

#     @staticmethod
#     def from_dict(source):
#         return ExistingMedicalKnowledge(
#             source["medical_condition"],
#             source["description"],
#         )

#     def to_dict(self):
#         return {
#             "medical_condition": self.medical_condition,
#             "description": self.description,
#         }

#     def __repr__(self) -> str:
#         return str(vars(self))


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
            source["id"],
            source["name"],
            source["language_preference"],
            source["phone_number"],
            source["medical_conditions"],
            source["nric"],
            source["address"],
            source["date_of_birth"],
            source["gender"],
            source["gender_preference"],
            source["emergency_contacts"],
            source["location"],
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
        existing_medical_knowledge: List[Dict[str, str]] = [],
        is_available: bool = True,
        state: CustomStates = CustomStates.ONBOARD,
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

    @staticmethod
    def from_dict(source):
        return Responder(
            source["id"],
            source["telegram_id"],
            source["location"],
            source["name"],
            source["languages"],
            source["phone_number"],
            source["nric"],
            source["address"],
            source["date_of_birth"],
            source["gender"],
            source["existing_medical_knowledge"],
            source["is_available"],
            CustomStates(source["state"]),
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
            "existing_medical_knowledge": self.existing_medical_knowledge,
            "location": self.location,
            "is_available": self.is_available,
            "state": self.state.value,
        }

    def __repr__(self) -> str:
        return str(vars(self))
