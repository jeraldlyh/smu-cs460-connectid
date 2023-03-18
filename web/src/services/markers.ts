import axios from "axios";
import { TMarkerResponse } from "../components";

const BASE_URL =
  process.env.NODE_ENV === "production"
    ? process.env.PROD_URL
    : process.env.DEV_URL;

const axiosInstance = axios.create({
  baseURL: BASE_URL || "http://localhost:5000",
  headers: {
    "Content-Type": "application/json",
    Accept: "*/*",
  },
});

const fetchMarkers = async (): Promise<TMarkerResponse[]> => {
  const response = await axiosInstance.get<TMarkerResponse[]>("/distress");

  return response.data;
};

export const MarkerService = {
  fetchMarkers,
};
