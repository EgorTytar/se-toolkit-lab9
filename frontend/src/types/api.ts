// API Types for F1 Assistant

export interface RaceResult {
  season: string;
  round: string;
  raceName: string;
  circuit: {
    circuitId: string;
    circuitName: string;
    location: {
      lat: string;
      long: string;
      locality: string;
      country: string;
    };
  };
  date: string;
  time: string;
  Results: Array<{
    number: string;
    position: string;
    positionText: string;
    points: string;
    Driver: {
      driverId: string;
      code: string;
      givenName: string;
      familyName: string;
      dateOfBirth: string;
      nationality: string;
      permanentNumber?: string;
    };
    Constructor: {
      constructorId: string;
      name: string;
      nationality: string;
    };
    grid: string;
    laps: string;
    status: string;
    Time?: {
      millis: string;
      time: string;
    };
    FastestLap?: {
      rank: string;
      lap: string;
      Time: {
        time: string;
      };
      AverageSpeed: {
        units: string;
        speed: string;
      };
    };
  }>;
}

export interface StandingEntry {
  position: string;
  positionText: string;
  points: string;
  wins: string;
  Driver?: {
    driverId: string;
    code: string;
    givenName: string;
    familyName: string;
    dateOfBirth: string;
    nationality: string;
    permanentNumber?: string;
  };
  Constructor?: {
    constructorId: string;
    name: string;
    nationality: string;
  };
}

export interface RaceScheduleItem {
  season: string;
  round: string;
  raceName: string;
  circuit: {
    circuitId: string;
    circuitName: string;
    location: {
      locality: string;
      country: string;
    };
  };
  date: string;
  time: string;
}

export interface DriverProfile {
  driverId: string;
  code: string;
  givenName: string;
  familyName: string;
  dateOfBirth: string;
  nationality: string;
  permanentNumber?: string;
  url?: string;
}

export interface CircuitInfo {
  circuitId: string;
  circuitName: string;
  location: {
    lat: string;
    long: string;
    locality: string;
    country: string;
  };
}

export interface AIResponse {
  summary: string;
  highlights: string;
  insights: string;
  answer?: string;
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
  race_name: string;
  notify_before_hours: number;
  enabled: boolean;
  method: string;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
