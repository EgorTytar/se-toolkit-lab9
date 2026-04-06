// API Types matching ACTUAL backend responses

export interface AIResponse {
  summary: string;
  highlights: string;
  insights: string;
  answer?: string;
}

export interface LatestRaceResponse {
  race_name: string;
  circuit: string;
  date: string;
  season: string;
  round: number;
  ai_response: AIResponse;
}

export interface RaceScheduleItem {
  round: number;
  race_name: string;
  circuit: string;
  circuit_id: string;
  date: string;
}

export interface ScheduleResponse {
  season: number;
  race_count: number;
  races: RaceScheduleItem[];
}

export interface StandingEntry {
  position: number;
  driver_id: string;
  driver_code: string;
  driver_name: string;
  nationality: string;
  constructor: string;
  points: number;
  wins: number;
}

export interface StandingsResponse {
  season: number;
  type: string;
  standings: StandingEntry[];
}

export interface DriverProfile {
  driver_id: string;
  code: string;
  given_name: string;
  family_name: string;
  full_name: string;
  date_of_birth: string;
  nationality: string;
  permanent_number: string;
  url: string;
}

export interface DriverResult {
  round: number;
  race_name: string;
  circuit: string;
  circuit_id: string;
  date: string;
  position: string;
  grid: number;
  points: number;
  status: string;
}

export interface DriverResponse {
  driver: DriverProfile;
  season?: number;
  results?: DriverResult[];
}

export interface CircuitInfo {
  circuit_id: string;
  name: string;
  location: string;
  country: string;
  latitude: string;
  longitude: string;
  url: string;
}

export interface CircuitResult {
  season: string;
  round: number;
  race_name: string;
  date: string;
  position: string;
  driver_name: string;
  driver_id: string;
  constructor: string;
  grid: number;
  points: number;
  status: string;
}

export interface CircuitResponse {
  circuit: CircuitInfo;
  recent_results: CircuitResult[];
}

export interface User {
  id: number;
  email: string;
  display_name: string;
  created_at: string;
  last_login: string;
}

export interface FavoriteDriver {
  id: number;
  driver_id: string;
  driver_code: string;
  driver_name: string;
  created_at: string;
}

export interface Reminder {
  id: number;
  race_round: number;
  race_year: number;
  notify_before_hours: number;
  enabled: boolean;
  method: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
