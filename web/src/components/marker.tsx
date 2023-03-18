import { useState } from "react";
import { BsGenderFemale, BsGenderMale } from "react-icons/bs";
import { EGender, IMarkerProps, TMarkerResponse } from "./types";

export const Marker = ({
  location,
  lat,
  lng,
  is_acknowledged,
  is_completed,
  pwid,
  onClick,
}: IMarkerProps & TMarkerResponse) => {
  console.log(lat, lng);
  const [display, setDisplay] = useState<boolean>(false);

  const handleOnClick = () => {
    onClick && onClick();
    setDisplay(!display);
  };

  const renderCard = (): JSX.Element | undefined => {
    if (!display) {
      return;
    }

    const formatEmergencyContacts = () => {
      return pwid.emergency_contacts.map((contact, index) => (
        <span key={index}>
          {contact.name} ({contact.relationship}) - {contact.phone_number}
        </span>
      ));
    };

    const formatMedicalConditions = () => {
      if (!pwid.medical_condtions || pwid.medical_condtions.length === 0) {
        return <span>None</span>;
      }
      return pwid.medical_condtions.map((condition, index) => {
        return <span key={index}>{condition}</span>;
      });
    };

    const formatGender = () => {
      if (pwid.gender === EGender.Female) {
        return <BsGenderFemale className="stroke-1 text-pink-500" />;
      }
      return <BsGenderMale className="stroke-1 text-blue-500" />;
    };

    return (
      <div className="card w-64 bg-base-100 shadow-xl">
        <div className="card-body">
          <h2 className="card-title">
            <span>{pwid.name}</span>
            {formatGender()}
          </h2>
          <div className="flex flex-col">
            <span className="font-semibold text-md underline">
              Medical Conditions
            </span>
            {formatMedicalConditions()}
          </div>
          <div className="flex flex-col">
            <span className="font-semibold underline">Emergency Contacts</span>
            {formatEmergencyContacts()}
          </div>
          <div className="card-actions mt-3 flex justify-between">
            <button className="btn bg-green-700">Accept</button>
            <button className="btn bg-red-700">Cancel</button>
          </div>
        </div>
      </div>
    );
  };

  const renderColor = () => {
    if (is_completed) {
      return "bg-green-600";
    }
    if (is_acknowledged) {
      return "bg-orange-600";
    }
    return "bg-red-600";
  };

  return (
    <div
      className={`rounded-full h-5 w-5 ${renderColor()}`}
      onClick={handleOnClick}
    >
      {renderCard()}
    </div>
  );
};
