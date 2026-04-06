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
    if (!isAuthenticated) return;
    setAiLoading(true);
    setError(null);
    try {
      const res = await raceApi.getLatestRace();
      setData(res);
      setFetched(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load AI summary');
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

      {/* Podium */}
      {results?.podium && results.podium.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {results.podium.map((r, i) => {
            const medalColors = [
              'border-yellow-500 bg-yellow-900/20',
              'border-gray-400 bg-gray-700/40',
              'border-amber-700 bg-amber-900/20',
            ];
            const medalEmojis = ['🥇', '🥈', '🥉'];
            return (
              <div key={r.position} className={`rounded-lg p-4 border-2 ${medalColors[i]}`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{medalEmojis[i]}</span>
                  <span className="font-bold text-lg">
                    <Link to={`/driver/${r.driver_id}`} className="hover:underline">
                      {r.name}
                    </Link>
                  </span>
                </div>
                <div className="text-sm text-gray-400">{r.constructor}</div>
                <div className="text-sm text-gray-400 mt-1">{r.points} pts</div>
              </div>
            );
          })}
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
          {aiLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Generating AI Summary...
            </>
          ) : (
            <>🤖 Get AI Summary</>
          )}
        </button>
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
