import GoogleMapReact from "google-map-react";
import { useEffect, useState } from "react";
import { Marker, TMarkerResponse } from "../components";
import { MarkerService } from "../services";

const SINGAPORE_CENTER_COORDINATES = {
  lat: 1.3521,
  lng: 103.8198,
};

export default function Home() {
  const [markers, setMarkers] = useState<TMarkerResponse[]>([]);

  useEffect(() => {
    fetchMarkers();
  }, []);

  const fetchMarkers = async () => {
    const data = await MarkerService.fetchMarkers();
    setMarkers(data);
  };

  return (
    <div className="flex flex-col h-screen w-screen">
      <GoogleMapReact
        bootstrapURLKeys={{ key: "" }}
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
    </div>
  );
}
