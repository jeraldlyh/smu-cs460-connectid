import axios from "axios";

const BASE_URL =
  process.env.NODE_ENV === "production"
    ? process.env.PROD_URL
    : process.env.DEV_URL;

export const axiosInstance = axios.create({
  baseURL: BASE_URL || "http://localhost:5000",
  headers: {
    "Content-Type": "application/json",
    Accept: "*/*",
  },
});
