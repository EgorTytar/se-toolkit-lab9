import axios from 'axios';
import type {
  RaceResult,
  StandingEntry,
  RaceScheduleItem,
  DriverProfile,
  CircuitInfo,
  AIResponse,
  User,
  FavoriteDriver,
  Reminder,
  AuthToken,
} from '../types/api';

const api = axios.create({
  baseURL: '',
  timeout: 30000,
});

// Auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Race endpoints
export const raceApi = {
  getLatestRace: () => api.get<AIResponse>('/api/races/latest'),
  getLatestRaceResults: () => api.get<{ results: RaceResult }>('/api/races/latest/results'),
  getRace: (year: number, round: number) =>
    api.get<AIResponse>(`/api/races/${year}/${round}`),
  getRaceResults: (year: number, round: number) =>
    api.get<{ results: RaceResult; circuit_id: string }>(`/api/races/${year}/${round}/results`),
  getSeasonSchedule: (year: number) =>
    api.get<{ schedule: RaceScheduleItem[] }>(`/api/seasons/${year}/schedule`),
};

// Standings endpoints
export const standingsApi = {
  getDriverStandings: (year?: number) => {
    const params = year ? `?year=${year}` : '';
    return api.get<{ standings: StandingEntry[] }>(`/api/standings/drivers${params}`);
  },
  getConstructorStandings: (year?: number) => {
    const params = year ? `?year=${year}` : '';
    return api.get<{ standings: StandingEntry[] }>(`/api/standings/constructors${params}`);
  },
};

// Driver endpoints
export const driverApi = {
  getDriver: (driverId: string) =>
    api.get<{ driver: DriverProfile; season_results: any[] }>(`/api/drivers/${driverId}`),
};

// Circuit endpoints
export const circuitApi = {
  getCircuit: (circuitId: string) =>
    api.get<{ circuit: CircuitInfo; recent_results: any[] }>(`/api/circuits/${circuitId}`),
};

// Auth endpoints
export const authApi = {
  register: (email: string, password: string, display_name: string) =>
    api.post<AuthToken>('/api/auth/register', { email, password, display_name }),
  login: (email: string, password: string) =>
    api.post<AuthToken>('/api/auth/login', { email, password }),
};

// User endpoints
export const userApi = {
  getMe: () => api.get<User>('/api/users/me'),
  updateMe: (data: { display_name?: string }) => api.put<User>('/api/users/me', data),
};

// Favorites endpoints
export const favoritesApi = {
  getFavorites: () => api.get<FavoriteDriver[]>('/api/users/me/favorites/'),
  addFavorite: (driver_id: string) =>
    api.post<FavoriteDriver>('/api/users/me/favorites/', { driver_id }),
  removeFavorite: (favoriteId: number) =>
    api.delete(`/api/users/me/favorites/${favoriteId}`),
};

// Reminders endpoints
export const remindersApi = {
  getReminders: () => api.get<Reminder[]>('/api/reminders/'),
  addReminder: (data: { race_round: number; race_year: number; notify_before_hours?: number }) =>
    api.post<Reminder>('/api/reminders/', data),
  updateReminder: (id: number, data: Partial<Reminder>) =>
    api.put<Reminder>(`/api/reminders/${id}`, data),
  deleteReminder: (id: number) => api.delete(`/api/reminders/${id}`),
};

// Health check
export const healthApi = {
  check: () => api.get<{ status: string; db_healthy: boolean; ai_available: boolean }>('/health'),
};

export default api;
