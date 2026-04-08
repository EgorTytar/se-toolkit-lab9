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
  constructor_id: string;
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

// Chat types
export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatSessionWithMessages extends ChatSession {
  messages: ChatMessage[];
}

// Comparison types
export interface ConstructorTeam {
  constructor_id: string;
  constructor_name: string;
  years: number[];
  races: number;
  wins: number;
  podiums: number;
  points: number;
}

export interface DriverCareerStats {
  races: number;
  wins: number;
  podiums: number;
  poles: number;
  points: number;
  championships: number;
  best_finish: number | null;
  worst_finish: number | null;
  dnfs: number;
  seasons_competed: number[];
  teams: ConstructorTeam[];
  avg_finish: number | null;
  avg_points: number;
  avg_grid: number | null;
  win_pct: number;
  podium_pct: number;
  dnf_pct: number;
}

export interface H2HRaceDetail {
  season: number;
  round: number;
  race_name: string;
  date: string;
  driver_a: {
    position: string;
    points: number;
    status: string;
  };
  driver_b: {
    position: string;
    points: number;
    status: string;
  };
  winner: 'a' | 'b' | 'draw';
}

export interface HeadToHead {
  shared_seasons: number[];
  shared_races: number;
  driver_a_wins: number;
  driver_b_wins: number;
  draws: number;
  race_details: H2HRaceDetail[];
}

export interface DriverComparisonResponse {
  driver_a: {
    info: DriverProfile;
    career: DriverCareerStats;
  };
  driver_b: {
    info: DriverProfile;
    career: DriverCareerStats;
  };
  head_to_head: HeadToHead;
}

export interface TeammateInfo {
  driver_id: string;
  code: string;
  full_name: string;
  seasons: number[];
  constructors: {
    constructor_id: string;
    constructor_name: string;
  }[];
  total_races: number;
}

// Constructor comparison types
export interface ConstructorProfile {
  constructor_id: string;
  name: string;
  nationality: string;
  url: string;
}

export interface ConstructorCareerStats {
  races: number;
  wins: number;
  podiums: number;
  poles: number;
  points: number;
  championships: number;
  best_finish: number | null;
  worst_finish: number | null;
  dnfs: number;
  seasons_active: number[];
  avg_finish: number | null;
  avg_points: number;
  avg_grid: number | null;
  win_pct: number;
  podium_pct: number;
  dnf_pct: number;
}

export interface ConstructorH2HRaceDetail {
  season: number;
  round: number;
  race_name: string;
  date: string;
  constructor_a: {
    position: string;
    points: number;
    status: string;
    driver: string;
  };
  constructor_b: {
    position: string;
    points: number;
    status: string;
    driver: string;
  };
  winner: 'a' | 'b' | 'draw';
}

export interface ConstructorH2H {
  shared_seasons: number[];
  shared_races: number;
  constructor_a_wins: number;
  constructor_b_wins: number;
  draws: number;
  race_details: ConstructorH2HRaceDetail[];
}

export interface ConstructorComparisonResponse {
  constructor_a: {
    info: ConstructorProfile;
    career: ConstructorCareerStats;
  };
  constructor_b: {
    info: ConstructorProfile;
    career: ConstructorCareerStats;
  };
  head_to_head: ConstructorH2H;
}

export interface ConstructorOption {
  constructor_id: string;
  name: string;
  nationality: string;
  url: string;
}

export interface ConstructorResult {
  season: number;
  round: number;
  race_name: string;
  circuit: string;
  date: string;
  position: string;
  grid: number;
  points: number;
  status: string;
  driver: string;
}

export interface ConstructorResponse {
  constructor: ConstructorProfile;
  season: number;
  results: ConstructorResult[];
  season_stats: {
    races: number;
    points: number;
    best_finish: number | null;
    wins: number;
  };
}

// Prediction types
export interface DriverFormAnalysis {
  races_analyzed: number;
  avg_points: number;
  total_points: number;
  wins: number;
  podiums: number;
  dnfs: number;
  win_pct: number;
  podium_pct: number;
  dnf_pct: number;
}

export interface ConstructorFormAnalysis {
  races_analyzed: number;
  avg_points_per_race: number;
  total_points_recent: number;
}

export interface PredictionContender {
  id: string;
  name: string;
  predicted_points: number;
  chance_pct?: number;
}

export interface DriverPredictionChampion {
  driver_id: string;
  name: string;
  current_points: number;
  predicted_final_points: number;
  confidence: number;
}

export interface ConstructorPredictionChampion {
  constructor_id: string;
  name: string;
  current_points: number;
  predicted_final_points: number;
  confidence: number;
}

export interface PredictionResponse {
  season: number;
  type: 'drivers' | 'constructors';
  races_completed: number;
  races_remaining: number;
  predicted_champion: DriverPredictionChampion | ConstructorPredictionChampion | null;
  top_contenders: PredictionContender[];
  form_analysis: Record<string, DriverFormAnalysis | ConstructorFormAnalysis>;
  ai_reasoning: string;
  error?: string;
}
