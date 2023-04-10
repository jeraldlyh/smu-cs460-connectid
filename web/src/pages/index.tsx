import GoogleMapReact from "google-map-react";
import { useEffect, useState } from "react";
import {
  AiOutlineSortAscending,
  AiOutlineSortDescending,
} from "react-icons/ai";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { Marker, TMarkerResponse } from "../components";
import { SignalService } from "../services";

const SINGAPORE_CENTER_COORDINATES = {
  lat: 1.3521,
  lng: 103.8198,
};

export default function Home() {
  const [signals, setSignals] = useState<TMarkerResponse[]>([]);
  const [markers, setMarkers] = useState<TMarkerResponse[]>([]);
  const [isAscending, setIsAscending] = useState<boolean>(false);

  useEffect(() => {
    fetchSignals();
  }, []);

  useEffect(() => {
    if (signals && signals.length > 0) {
      handleMarkers(signals);
    }
  }, [signals]);

  const handleMarkers = (signals: TMarkerResponse[]): void => {
    // const markers = signals.filter((signal) => {
    //   return !signal.is_completed;
    // });

    setMarkers(signals);
  };

  const fetchSignals = async (): Promise<void> => {
    const data = await SignalService.fetchSignals();
    setSignals(data);
  };

  const handleSort = () => {
    let sortedSignals = signals;

    sortedSignals.sort((a, b) => {
      if (isAscending) {
        return a.status.localeCompare(b.status);
      }
      return b.status.localeCompare(a.status);
    });

    setSignals(sortedSignals);
    setIsAscending(!isAscending);
  };

  const renderTable = (): JSX.Element[] => {
    return signals.map((data) => {
      return (
        <tr key={data.group_chat_message_id}>
          <td>{data.group_chat_message_id}</td>
          <td>{data.pwid.name}</td>
          <td>{data.responder.name ? data.responder.name : "None"}</td>
          <td>{data.location.address}</td>
          <td>{data.status}</td>
        </tr>
      );
    });
  };

  return (
    <div className="flex h-screen w-screen">
      <div className="absolute card p-3 self-end z-[999]">
        <div className="overflow-x-auto max-h-56 overflow-y-scroll">
          <table className="relative table table-zebra w-full">
            <thead>
              <tr>
                <th className="sticky top-0">ID</th>
                <th className="sticky top-0">PWID</th>
                <th className="sticky top-0">Responder</th>
                <th className="sticky top-0">Location</th>
                <th className="sticky top-0" onClick={handleSort}>
                  <span className="mr-1">Status</span>
                  {isAscending ? (
                    <AiOutlineSortAscending size={15} />
                  ) : (
                    <AiOutlineSortDescending size={15} />
                  )}
                </th>
              </tr>
            </thead>
            <tbody>{renderTable()}</tbody>
          </table>
        </div>
      </div>
      <GoogleMapReact
        bootstrapURLKeys={{ key: process.env.NEXT_PUBLIC_API_KEY || "" }}
        defaultZoom={12}
        defaultCenter={SINGAPORE_CENTER_COORDINATES}
        options={{
          disableDoubleClickZoom: true,
          clickableIcons: false,
          maxZoom: 15,
          minZoom: 12,
        }}
      >
        {markers.map((props, index) => (
          <Marker
            key={index}
            {...props}
            id={props.group_chat_message_id}
            lat={props.location.latitude}
            lng={props.location.longitude}
          />
        ))}
      </GoogleMapReact>
      <ToastContainer />
    </div>
  );
}
