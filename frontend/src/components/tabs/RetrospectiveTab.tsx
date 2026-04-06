import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../../contexts/AuthContext';
import { Link } from 'react-router-dom';

interface RetrospectiveData {
  year: number;
  total_races: number;
  races_completed: number;
  is_ongoing: boolean;
  champion: { driver_name: string; constructor: string; points: number } | null;
  constructors_champion: { constructor: string; points: number } | null;
  retrospective: string;
}

export default function RetrospectiveTab() {
  const { isAuthenticated } = useAuth();
  const [year, setYear] = useState(2024);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrospectiveData | null>(null);

  const generateRetrospective = async () => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch(
        `${window.location.origin}/api/seasons/${year}/retrospective`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to generate retrospective');
      }

      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to generate retrospective');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 mb-4">
          Please log in to use the Season Retrospective feature.
        </p>
        <Link
          to="/login"
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
        >
          Login
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Year Selector */}
      <div className="flex items-center space-x-4">
        <input
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-600 rounded-md w-32 bg-gray-800 text-gray-100"
          placeholder="Year"
          min={1950}
          max={new Date().getFullYear() + 1}
        />
        <button
          onClick={generateRetrospective}
          disabled={loading}
          className="px-6 py-2 bg-purple-700 hover:bg-purple-600 disabled:bg-purple-900 disabled:opacity-50 text-white rounded-md transition font-medium"
        >
          {loading ? 'Generating...' : '📖 Generate Retrospective'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-400"></div>
            <div className="text-center">
              <p className="text-gray-200 font-medium">
                AI is analyzing the {year} season...
              </p>
              <p className="text-gray-400 text-sm mt-1">
                This may take 15–30 seconds as the AI reviews all races and standings.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {data && (
        <>
          {/* Season Overview Banner */}
          <div className="bg-gray-800 rounded-lg shadow p-6 border-l-4 border-purple-500">
            <h2 className="text-2xl font-bold mb-2">
              {data.year} F1 Season Retrospective
              {data.is_ongoing && (
                <span className="ml-3 text-sm font-normal text-yellow-400">(Season In Progress)</span>
              )}
            </h2>
            <div className="flex flex-wrap gap-4 text-sm text-gray-400">
              <span>🏁 {data.total_races} races ({data.races_completed} completed)</span>
              {data.champion && (
                <span>
                  {data.is_ongoing ? '🏆 Standings Leader:' : '🏆 Champion:'}{' '}
                  <Link to={`/driver/${data.champion.driver_name.toLowerCase().replace(/ /g, '_')}`} className="text-purple-400 hover:underline">
                    {data.champion.driver_name}
                  </Link>{' '}
                  ({data.champion.constructor}) — {data.champion.points} pts
                </span>
              )}
              {data.constructors_champion && (
                <span>
                  {data.is_ongoing ? '🏅 Constructors Standings:' : '🏅 Constructors:'}{' '}
                  {data.constructors_champion.constructor} — {data.constructors_champion.points} pts
                </span>
              )}
            </div>
          </div>

          {/* AI Retrospective */}
          <div className="bg-gray-800 rounded-lg shadow p-6">
            <div className="markdown-content text-sm leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                allowedElements={[
                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'p', 'br', 'hr',
                  'strong', 'em', 'del', 'code',
                  'ul', 'ol', 'li',
                  'blockquote',
                  'table', 'thead', 'tbody', 'tr', 'th', 'td',
                  'a',
                ]}
                unwrapDisallowed={true}
              >
                {data.retrospective}
              </ReactMarkdown>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
