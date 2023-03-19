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

export const SignalService = {
  acceptSignal,
  cancelSignal,
};
