import { useState } from 'react';
import { standingsApi } from '../../services/api';
import type { StandingEntry } from '../../types/api';
import { Link } from 'react-router-dom';

type StandingType = 'drivers' | 'constructors';

export default function StandingsTab() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [standingType, setStandingType] = useState<StandingType>('drivers');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [standings, setStandings] = useState<StandingEntry[]>([]);

  const fetchStandings = async (type: StandingType, yr: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = type === 'drivers'
        ? await standingsApi.getDriverStandings(yr)
        : await standingsApi.getConstructorStandings(yr);
      setStandings(data.standings);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load standings');
    } finally {
      setLoading(false);
    }
  };

  const handleTypeChange = (type: StandingType) => {
    setStandingType(type);
    fetchStandings(type, year);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          onKeyDown={(e) => { if (e.key === 'Enter') handleTypeChange(standingType); }}
          className="px-4 py-2 border border-gray-600 rounded-md w-32 bg-gray-800 text-gray-100"
          placeholder="Year"
          min={1950}
          max={new Date().getFullYear() + 1}
        />

        <div className="flex space-x-2">
          <button
            onClick={() => handleTypeChange('drivers')}
            className={`px-4 py-2 rounded-md transition ${
              standingType === 'drivers'
                ? 'bg-red-600 text-white'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {loading ? 'Loading...' : 'Drivers'}
          </button>
          <button
            onClick={() => handleTypeChange('constructors')}
            className={`px-4 py-2 rounded-md transition ${
              standingType === 'constructors'
                ? 'bg-red-600 text-white'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {loading ? 'Loading...' : 'Constructors'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {standings.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Pos
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  {standingType === 'drivers' ? 'Driver' : 'Team'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Nationality
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Points
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Wins
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {standings.map((entry, idx) => (
                <tr key={idx} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">
                    {entry.position}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                    {standingType === 'drivers' ? (
                      <Link
                        to={`/driver/${entry.driver_id}`}
                        className="text-red-400 hover:underline"
                      >
                        {entry.driver_name} ({entry.driver_code})
                      </Link>
                    ) : (
                      <Link
                        to={`/constructor/${entry.constructor_id}`}
                        className="text-red-400 hover:underline"
                      >
                        {entry.constructor}
                      </Link>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {entry.nationality}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100 font-semibold">
                    {entry.points}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                    {entry.wins}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
