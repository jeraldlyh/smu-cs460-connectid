export enum EGender {
  Male = "Male",
  Female = "Female",
}

interface IEmergencyContact {
  name: string;
  phone_number: string;
  relationship: string;
}

interface IPWID {
  name: string;
  emergency_contacts: IEmergencyContact[];
  gender: EGender;
  medical_condtions: string[];
}

interface ILocation {
  latitude: number;
  longitude: number;
  address: string;
}

export interface IMarkerProps {
  lat: number;
  lng: number;
  id: number;
  is_acknowledged: boolean;
  is_completed: boolean;
  pwid: IPWID;
  onClick: () => void;
}
interface IMedicalKnowledge {
  condition: string;
  created_at: string;
  description: string;
}

interface IResponser {
  address: string;
  date_of_birth: string;
  existing_medical_knowledge: IMedicalKnowledge[];
  gender: string;
  id: string;
  is_available: boolean;
  languages: string[];
  location: ILocation;
  message_id: number;
  name: string;
  nric: string;
  phone_number: string;
  state: number;
  telegram_id: number;
}

export type TMarkerResponse = Exclude<IMarkerProps, "onClick" | "id"> & {
  location: ILocation;
  group_chat_message_id: number;
  responder: IResponser;
  status: string;
};
