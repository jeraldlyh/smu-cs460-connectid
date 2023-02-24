from datetime import datetime
from typing import List


class ExistingMedicalKnowledge:
    def __init__(self, medical_condition: str, description: str) -> None:
        self.medical_condition = medical_condition
        self.description = description


class Location:
    def __init__(self, longitude: int, latitude: int) -> None:
        self.longitude = longitude
        self.latitude = latitude


class EmergencyContact:
    def __init__(self, name: str, phone_number: str, relationship: str) -> None:
        self.name = name
        self.phone_number = phone_number
        self.relationship = relationship


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
