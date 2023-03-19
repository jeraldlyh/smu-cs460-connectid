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

export type TMarkerResponse = Exclude<IMarkerProps, "onClick" | "id"> & {
  location: ILocation;
  group_chat_message_id: number;
};
