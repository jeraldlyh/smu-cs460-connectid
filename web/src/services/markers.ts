import { TMarkerResponse } from "../components";
import { axiosInstance } from "./axios";

const fetchMarkers = async (): Promise<TMarkerResponse[]> => {
  const response = await axiosInstance.get<TMarkerResponse[]>("/distress");

  return response.data;
};

export const MarkerService = {
  fetchMarkers,
};
