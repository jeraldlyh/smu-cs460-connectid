import uuid
from datetime import datetime
from typing import List


class ExistingMedicalKnowledge:
    def __init__(self, medical_condition: str, description: str) -> None:
        self.medical_condition = medical_condition
        self.description = description

    @staticmethod
    def from_dict(source):
        return ExistingMedicalKnowledge(
            source["medical_condition"],
            source["description"],
        )

    def to_dict(self):
        return {
            "medical_condition": self.medical_condition,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return str(vars(self))


class Location:
    def __init__(self, longitude: int, latitude: int) -> None:
        self.longitude = longitude
        self.latitude = latitude

    @staticmethod
    def from_dict(source):
        return Location(
            source["longitude"],
            source["latitude"],
        )

    def to_dict(self):
        return {
            "longitude": self.longitude,
            "latitude": self.latitude,
        }


class EmergencyContact:
    def __init__(self, name: str, phone_number: str, relationship: str) -> None:
        self.name = name
        self.phone_number = phone_number
        self.relationship = relationship

    @staticmethod
    def from_dict(source):
        return EmergencyContact(
            source["name"],
            source["phone_number"],
            source["relationship"],
        )

    def to_dict(self):
        return {
            "name": self.name,
            "phone_number": self.phone_number,
            "relationship": self.relationship,
        }

    def __repr__(self) -> str:
        return str(vars(self))


class PWID:
    def __init__(
        self,
        id: str,
        name: str,
        language_preference: str,
        phone_number: str,
        medical_condition: List[str],
        nric: str,
        address: str,
        date_of_birth: datetime,
        gender_preference: str,
        emergency_contact: List[EmergencyContact],
        location: Location,
    ) -> None:
        self.id = id
        self.name = name
        self.language_preference = language_preference
        self.phone_number = phone_number
        self.medical_condition = medical_condition
        self.nric = nric
        self.address = address
        self.date_of_birth = date_of_birth
        self.gender_preference = gender_preference
        self.emergency_contact = emergency_contact
        self.location = location

    @staticmethod
    def from_dict(source):
        return PWID(
            source["id"],
            source["name"],
            source["language_preference"],
            source["phone_number"],
            source["medical_condition"],
            source["nric"],
            source["address"],
            source["date_of_birth"],
            source["gender_preference"],
            source["emergency_contact"],
            source["location"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "language_preference": self.language_preference,
            "phone_number": self.phone_number,
            "medical_condition": self.medical_condition,
            "nric": self.nric,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "gender_preference": self.gender_preference,
            "emergency_contact": [x.to_dict() for x in self.emergency_contact],
            "location": self.location.to_dict(),
        }

    def __repr__(self) -> str:
        return str(vars(self))


class Responder:
    def __init__(
        self,
        id: str,
        name: str,
        language: str,
        phone_number: str,
        telegram_id: str,
        nric: str,
        address: str,
        date_of_birth: datetime,
        gender: str,
        existing_medical_knowledge: List[ExistingMedicalKnowledge],
        location: Location,
    ) -> None:
        self.id = id
        self.name = name
        self.language = language
        self.phone_number = phone_number
        self.telegram_id = telegram_id
        self.nric = nric
        self.address = address
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.existing_medical_knowledge = existing_medical_knowledge
        self.location = location

    @staticmethod
    def from_dict(source):
        return Responder(
            str(uuid.uuid4()),
            source["name"],
            source["language"],
            source["phone_number"],
            source["telegram_id"],
            source["nric"],
            source["address"],
            source["date_of_birth"],
            source["gender"],
            source["existing_medical_knowledge"],
            source["location"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "phone_number": self.phone_number,
            "telegram_id": self.telegram_id,
            "nric": self.nric,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "existing_medical_knowledge": self.existing_medical_knowledge,
            "location": self.location,
        }

    def __repr__(self) -> str:
        return str(vars(self))
