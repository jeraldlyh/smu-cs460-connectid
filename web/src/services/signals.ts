import { TMarkerResponse } from "../components";
import { axiosInstance } from "./axios";

interface ISignalResponse {
  message: string;
}

const acceptSignal = async (id: number): Promise<ISignalResponse> => {
  const response = await axiosInstance.post<ISignalResponse>(
    `/distress/accept/${id}`
  );

  return response.data;
};

const cancelSignal = async (id: number): Promise<ISignalResponse> => {
  const response = await axiosInstance.post<ISignalResponse>(
    `/distress/cancel/${id}`
  );

  return response.data;
};

const fetchSignals = async (): Promise<TMarkerResponse[]> => {
  const response = await axiosInstance.get<TMarkerResponse[]>("/distress");

  return response.data.map((data) => {
    if (data.is_completed) {
      data["status"] = "Completed";
    } else if (data.is_acknowledged) {
      data["status"] = "Acknowledged";
    } else {
      data["status"] = "Pending";
    }
    return data;
  });
};

export const SignalService = {
  acceptSignal,
  cancelSignal,
  fetchSignals,
};
