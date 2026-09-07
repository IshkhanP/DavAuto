// Axios client for BlackSharkCars backend.
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
});

const ACCESS_KEY = "bsc_access_token";
const REFRESH_KEY = "bsc_refresh_token";

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccess();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return null;
  try {
    const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refresh });
    const { access_token, refresh_token } = res.data;
    tokenStore.set(access_token, refresh_token);
    return access_token;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original?._retry && tokenStore.getRefresh()) {
      original._retry = true;
      refreshing = refreshing || refreshAccessToken();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess && original.headers) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api.request(original);
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data: any = err.response?.data;
    if (typeof data === "string") return data;
    if (data?.message) return data.message;
    if (data?.detail) return Array.isArray(data.detail) ? data.detail.map((d: any) => d.msg).join(", ") : data.detail;
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong";
}