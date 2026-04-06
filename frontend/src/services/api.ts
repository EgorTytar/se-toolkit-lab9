// API service using fetch instead of axios to avoid connection issues
import type {
  LatestRaceResponse,
  ScheduleResponse,
  StandingsResponse,
  DriverResponse,
  CircuitResponse,
  User,
  FavoriteDriver,
  Reminder,
  AuthToken,
  ChatSession,
  ChatSessionWithMessages,
  ChatMessage,
} from '../types/api';

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token');
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  console.log(`[fetch] ${options?.method || 'GET'} ${url}`);

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw { response: { status: response.status, data: error, statusText: response.statusText } };
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

const BASE = window.location.origin;

// Race endpoints
export const raceApi = {
  getLatestRace: () => apiFetch<LatestRaceResponse>(`${BASE}/api/races/latest`),
  getLatestRaceResults: () => apiFetch(`${BASE}/api/races/latest/results`),
  getRace: (year: number, round: number) =>
    apiFetch<LatestRaceResponse>(`${BASE}/api/races/${year}/${round}`),
  getRaceResults: (year: number, round: number) =>
    apiFetch(`${BASE}/api/races/${year}/${round}/results`),
  getSeasonSchedule: (year: number) =>
    apiFetch<ScheduleResponse>(`${BASE}/api/seasons/${year}/schedule`),
};

// Standings endpoints
export const standingsApi = {
  getDriverStandings: (year?: number) => {
    const params = year ? `?year=${year}` : '';
    return apiFetch<StandingsResponse>(`${BASE}/api/standings/drivers${params}`);
  },
  getConstructorStandings: (year?: number) => {
    const params = year ? `?year=${year}` : '';
    return apiFetch<StandingsResponse>(`${BASE}/api/standings/constructors${params}`);
  },
};

// Driver endpoints
export const driverApi = {
  getDriver: (driverId: string, year?: number) => {
    const params = year ? `?year=${year}` : '';
    return apiFetch<DriverResponse>(`${BASE}/api/drivers/${driverId}${params}`);
  },
};

// Circuit endpoints
export const circuitApi = {
  getCircuit: (circuitId: string) =>
    apiFetch<CircuitResponse>(`${BASE}/api/circuits/${circuitId}`),
};

// Auth endpoints
export const authApi = {
  register: (email: string, password: string, display_name: string) =>
    apiFetch<AuthToken>(`${BASE}/api/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name }),
    }),
  login: (email: string, password: string) =>
    apiFetch<AuthToken>(`${BASE}/api/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
};

// User endpoints
export const userApi = {
  getMe: () => apiFetch<User>(`${BASE}/api/users/me`),
  updateMe: (data: { display_name?: string }) =>
    apiFetch<User>(`${BASE}/api/users/me`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

// Favorites endpoints
export const favoritesApi = {
  getFavorites: () => apiFetch<FavoriteDriver[]>(`${BASE}/api/users/me/favorites/`),
  addFavorite: (driver_id: string) =>
    apiFetch<FavoriteDriver>(`${BASE}/api/users/me/favorites/`, {
      method: 'POST',
      body: JSON.stringify({ driver_id }),
    }),
  removeFavorite: (favoriteId: number) =>
    apiFetch(`${BASE}/api/users/me/favorites/${favoriteId}`, {
      method: 'DELETE',
    }),
};

// Reminders endpoints
export const remindersApi = {
  getReminders: () => apiFetch<Reminder[]>(`${BASE}/api/reminders/`),
  addReminder: (data: { race_round: number; race_year: number; notify_before_hours?: number; method?: string }) =>
    apiFetch<Reminder>(`${BASE}/api/reminders/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateReminder: (id: number, data: Partial<Reminder>) =>
    apiFetch<Reminder>(`${BASE}/api/reminders/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteReminder: (id: number) =>
    apiFetch(`${BASE}/api/reminders/${id}`, {
      method: 'DELETE',
    }),
};

// Health check
export const healthApi = {
  check: () => apiFetch<{ status: string; db_healthy: boolean; ai_available: boolean }>(`${BASE}/health`),
};

// Chat endpoints
export const chatApi = {
  listSessions: () => apiFetch<ChatSession[]>(`${BASE}/api/chat/sessions`),
  createSession: (title?: string) =>
    apiFetch<ChatSession>(`${BASE}/api/chat/sessions`, {
      method: 'POST',
      body: JSON.stringify(title ? { title } : {}),
    }),
  getSession: (id: number) =>
    apiFetch<ChatSessionWithMessages>(`${BASE}/api/chat/sessions/${id}`),
  deleteSession: (id: number) =>
    apiFetch(`${BASE}/api/chat/sessions/${id}`, {
      method: 'DELETE',
    }),
  sendMessage: (sessionId: number, content: string) =>
    apiFetch<{ message: ChatMessage }>(`${BASE}/api/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
};
