import { useEffect, useState } from 'react';
import { raceApi } from '../../services/api';
import type { LatestRaceResponse } from '../../types/api';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface PodiumEntry {
  position: number;
  name: string;
  constructor: string;
  points: number;
  driver_id: string;
}

interface WinnerInfo {
  name: string;
  constructor: string;
  points: number;
  driver_id: string;
}

interface BasicResults {
  race_name: string;
  circuit: string;
  circuit_id: string;
  date: string;
  season: string;
  round: number;
  total_drivers: number;
  winner: WinnerInfo;
  podium: PodiumEntry[];
}

export default function LatestRaceTab() {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LatestRaceResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [fetched, setFetched] = useState(false);
  const [results, setResults] = useState<BasicResults | null>(null);

  useEffect(() => {
    fetchBasic();
  }, []);

  const fetchBasic = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${window.location.origin}/api/races/latest/results`);
      if (!response.ok) throw new Error('Failed to load');
      const jsonData = await response.json();
      setResults(jsonData);
      setData({
        race_name: jsonData.race_name,
        circuit: jsonData.circuit,
        date: jsonData.date,
        season: jsonData.season,
        round: jsonData.round,
        ai_response: { summary: '', highlights: '', insights: '' },
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load latest race');
    } finally {
      setLoading(false);
    }
  };

  const fetchAiSummary = async () => {
    if (!isAuthenticated || !data) return;
    setAiLoading(true);
    setError(null);
    // Show immediate acknowledgment
    setData({
      race_name: data.race_name,
      circuit: data.circuit,
      date: data.date,
      season: data.season,
      round: data.round,
      ai_response: { summary: '', highlights: '', insights: '' },
    });
    setFetched(true);
    // Fetch in background
    try {
      const res = await raceApi.getLatestRace();
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load AI summary');
      setFetched(false);
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
        <button onClick={fetchBasic} className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition">
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const hasAi = !!data.ai_response.summary;

  return (
    <div className="space-y-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold">{data.race_name}</h2>
        <p className="text-gray-400">{data.circuit} • {data.date}</p>
      </div>

      {/* Podium — 2nd, 1st, 3rd order */}
      {results?.podium && results.podium.length > 0 && (
        <div className="flex items-end justify-center gap-3">
          {/* 2nd Place */}
          {results.podium[1] && (
            <div className="flex-1 max-w-xs rounded-lg p-4 border-2 border-gray-400 bg-gray-700/40">
              <div className="flex flex-col items-center">
                <span className="text-2xl">🥈</span>
                <span className="text-lg font-bold mt-1">
                  <Link to={`/driver/${results.podium[1].driver_id}`} className="hover:underline">
                    {results.podium[1].name}
                  </Link>
                </span>
                <span className="text-sm text-gray-400">{results.podium[1].constructor}</span>
                <span className="text-sm text-gray-400 mt-1">{results.podium[1].points} pts</span>
              </div>
            </div>
          )}

          {/* 1st Place — bigger */}
          {results.podium[0] && (
            <div className="flex-1 max-w-xs rounded-lg p-5 border-2 border-yellow-500 bg-yellow-900/20 -mt-4">
              <div className="flex flex-col items-center">
                <span className="text-3xl">🥇</span>
                <span className="text-xl font-bold mt-1">
                  <Link to={`/driver/${results.podium[0].driver_id}`} className="hover:underline">
                    {results.podium[0].name}
                  </Link>
                </span>
                <span className="text-sm text-gray-400">{results.podium[0].constructor}</span>
                <span className="text-sm text-gray-400 mt-1">{results.podium[0].points} pts</span>
              </div>
            </div>
          )}

          {/* 3rd Place */}
          {results.podium[2] && (
            <div className="flex-1 max-w-xs rounded-lg p-4 border-2 border-amber-700 bg-amber-900/20">
              <div className="flex flex-col items-center">
                <span className="text-2xl">🥉</span>
                <span className="text-lg font-bold mt-1">
                  <Link to={`/driver/${results.podium[2].driver_id}`} className="hover:underline">
                    {results.podium[2].name}
                  </Link>
                </span>
                <span className="text-sm text-gray-400">{results.podium[2].constructor}</span>
                <span className="text-sm text-gray-400 mt-1">{results.podium[2].points} pts</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Winner info */}
      {results?.winner && (
        <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
          <span className="text-green-400 font-semibold">🏆 Winner:</span>{' '}
          <Link to={`/driver/${results.winner.driver_id}`} className="text-green-300 hover:underline font-medium">
            {results.winner.name}
          </Link>
          {' '}({results.winner.constructor}) — {results.winner.points} pts
        </div>
      )}

      {/* AI Summary Button */}
      {isAuthenticated && !hasAi && !fetched && (
        <button
          onClick={fetchAiSummary}
          disabled={aiLoading}
          className="w-full py-3 bg-purple-700 hover:bg-purple-600 disabled:bg-purple-900 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
        >
          🤖 Get AI Summary
        </button>
      )}

      {/* AI Loading Acknowledgment */}
      {aiLoading && (
        <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-6 text-center">
          <div className="flex flex-col items-center gap-3">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400"></div>
              <span className="text-purple-300 font-medium">AI is analyzing this race...</span>
            </div>
            <p className="text-gray-400 text-sm">
              This may take 10–30 seconds. We'll notify you when it's ready.
            </p>
          </div>
        </div>
      )}

      {!isAuthenticated && !hasAi && (
        <div className="bg-gray-800 rounded-lg shadow p-6 text-center">
          <p className="text-gray-400 mb-3">🤖 AI Summary requires an account</p>
          <Link to="/login" className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition">
            Login to view
          </Link>
        </div>
      )}

      {hasAi && (
        <>
          <div className="bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Race Summary</h2>
            <p className="text-gray-300 whitespace-pre-wrap">{data.ai_response.summary}</p>
          </div>

          <div className="bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Highlights</h2>
            <p className="text-gray-300 whitespace-pre-wrap">{data.ai_response.highlights}</p>
          </div>

          <div className="bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Insights</h2>
            <p className="text-gray-300 whitespace-pre-wrap">{data.ai_response.insights}</p>
          </div>
        </>
      )}
    </div>
  );
}
