import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { compareApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface ConstructorInfo {
  constructor_id: string;
  name: string;
  nationality: string;
  url: string;
}

interface ConstructorResult {
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

interface ConstructorResponse {
  constructor: ConstructorInfo;
  season: number;
  results: ConstructorResult[];
  season_stats: {
    races: number;
    points: number;
    best_finish: number | null;
    wins: number;
  };
}

export default function ConstructorPage() {
  const { constructorId } = useParams<{ constructorId: string }>();
  const { isAuthenticated } = useAuth();
  const currentYear = new Date().getFullYear();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [constructor, setConstructor] = useState<ConstructorInfo | null>(null);
  const [season, setSeason] = useState<number>(currentYear);
  const [results, setResults] = useState<ConstructorResult[]>([]);
  const [seasonStats, setSeasonStats] = useState<ConstructorResponse['season_stats'] | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);

  // AI summary state
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSummary, setAiSummary] = useState<{
    summary: string;
    highlights: string;
    insights: string;
  } | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  useEffect(() => {
    if (constructorId) {
      // Only load constructor info, not season data
      loadConstructorBasic(constructorId);
    }
  }, [constructorId]);

  const loadConstructorBasic = async (id: string) => {
    setError(null);
    try {
      const info = await compareApi.getConstructorInfo(id);
      setConstructor(info.constructor);
      if (info.season) setSeason(info.season);
      // Don't set results/stats - user must click Load
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load constructor');
      setDataLoaded(false);
    }
  };

  const loadConstructor = async (id: string, year?: number) => {
    setLoading(true);
    setError(null);
    setAiSummary(null);
    setAiError(null);
    const targetYear = year !== undefined ? year : season;
    try {
      const data = await compareApi.getConstructorInfo(id, targetYear);
      setConstructor(data.constructor);
      setResults(data.results);
      setSeasonStats(data.season_stats);
      setDataLoaded(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load constructor');
      setDataLoaded(false);
    } finally {
      setLoading(false);
    }
  };

  const loadAiSummary = async () => {
    if (!constructorId || !season) return;
    setAiLoading(true);
    setAiError(null);
    setAiSummary(null);
    try {
      const data = await compareApi.getConstructorAiSummary(constructorId, season);
      if (data.ai_summary) {
        setAiSummary({
          summary: data.ai_summary.summary,
          highlights: data.ai_summary.highlights,
          insights: data.ai_summary.insights,
        });
      }
    } catch {
      setAiError('Failed to generate AI team info.');
    } finally {
      setAiLoading(false);
    }
  };

  if (error && !constructor) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
        <p className="text-red-400">{error || 'Constructor not found'}</p>
      </div>
    );
  }

  if (!constructor) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Constructor Profile */}
      <div className="bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">{constructor.name}</h2>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <span className="text-sm text-gray-400">Nationality</span>
            <p className="font-medium">{constructor.nationality}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">Constructor ID</span>
            <p className="font-medium">{constructor.constructor_id}</p>
          </div>
          {constructor.url && (
            <div>
              <span className="text-sm text-gray-400">Wiki</span>
              <p className="font-medium">
                <a
                  href={constructor.url}
                  className="text-red-400 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View
                </a>
              </p>
            </div>
          )}
        </div>

        {/* Year selector */}
        <div className="mt-4 flex items-center gap-2">
          <label className="text-sm text-gray-400">Season:</label>
          <input
            type="number"
            value={season}
            onChange={(e) => setSeason(parseInt(e.target.value))}
            onKeyDown={(e) => { if (e.key === 'Enter') constructorId && loadConstructor(constructorId); }}
            className="w-24 px-3 py-1 border border-gray-600 rounded bg-gray-700 text-gray-100"
            min={1950}
            max={currentYear}
          />
          <button
            onClick={() => constructorId && loadConstructor(constructorId)}
            disabled={loading}
            className="px-4 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load'}
          </button>
          {isAuthenticated && dataLoaded && (
            <button
              onClick={loadAiSummary}
              disabled={aiLoading || results.length === 0}
              className="px-4 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {aiLoading ? 'Generating...' : '🤖 AI Team Info'}
            </button>
          )}
        </div>
      </div>

      {/* AI Summary */}
      {aiError && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{aiError}</p>
        </div>
      )}

      {aiSummary && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">🤖 AI Team Info — {season} Season</h3>
          <div className="space-y-4 text-sm text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-1">Summary</h4>
              <p className="text-gray-300 leading-relaxed">{aiSummary.summary}</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-1">Highlights</h4>
              <p className="text-gray-300 leading-relaxed">{aiSummary.highlights}</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-1">Insights</h4>
              <p className="text-gray-300 leading-relaxed">{aiSummary.insights}</p>
            </div>
          </div>
        </div>
      )}

      {/* Season Stats */}
      {!dataLoaded && (
        <div className="bg-gray-800 rounded-lg shadow p-6 text-center text-gray-400">
          <p>Select a season and click <span className="text-red-400 font-medium">Load</span> to view season data.</p>
        </div>
      )}

      {dataLoaded && seasonStats && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">{season} Season Stats</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-gray-400">Races</span>
              <p className="font-medium">{seasonStats.races}</p>
            </div>
            <div>
              <span className="text-sm text-gray-400">Wins</span>
              <p className="font-medium">{seasonStats.wins}</p>
            </div>
            <div>
              <span className="text-sm text-gray-400">Points</span>
              <p className="font-medium">{seasonStats.points}</p>
            </div>
            <div>
              <span className="text-sm text-gray-400">Best Finish</span>
              <p className="font-medium">P{seasonStats.best_finish ?? '—'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Season Results */}
      {dataLoaded && results.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">{season} Season Results</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Round</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Race</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Driver</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Pos</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Grid</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Points</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {results.map((result) => (
                  <tr key={`${result.round}-${result.driver}`} className="hover:bg-gray-700">
                    <td className="px-4 py-3 text-sm">{result.round}</td>
                    <td className="px-4 py-3 text-sm">
                      {result.race_name}
                      <span className="text-gray-500 ml-1">({result.date})</span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {result.driver && (
                        <Link to={`/driver/${result.driver}`} className="text-red-400 hover:underline">
                          {result.driver}
                        </Link>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">P{result.position}</td>
                    <td className="px-4 py-3 text-sm">{result.grid}</td>
                    <td className="px-4 py-3 text-sm">{result.points}</td>
                    <td className="px-4 py-3 text-sm">{result.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
