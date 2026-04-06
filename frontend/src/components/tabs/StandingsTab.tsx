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

  const fetchStandings = async () => {
    setLoading(true);
    setError(null);
    try {
      const api = standingType === 'drivers' 
        ? standingsApi.getDriverStandings(year)
        : standingsApi.getConstructorStandings(year);
      const { data } = await api;
      setStandings(data.standings);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load standings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-md w-32"
          placeholder="Year"
          min={1950}
          max={new Date().getFullYear() + 1}
        />
        
        <div className="flex space-x-2">
          <button
            onClick={() => setStandingType('drivers')}
            className={`px-4 py-2 rounded-md transition ${
              standingType === 'drivers'
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
          >
            Drivers
          </button>
          <button
            onClick={() => setStandingType('constructors')}
            className={`px-4 py-2 rounded-md transition ${
              standingType === 'constructors'
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
          >
            Constructors
          </button>
        </div>

        <button
          onClick={fetchStandings}
          disabled={loading}
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Load Standings'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {standings.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pos
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {standingType === 'drivers' ? 'Driver' : 'Team'}
                </th>
                {standingType === 'drivers' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nationality
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Points
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Wins
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {standings.map((entry, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {entry.position}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {standingType === 'drivers' && entry.Driver ? (
                      <Link
                        to={`/driver/${entry.Driver.driverId}`}
                        className="text-red-600 hover:underline"
                      >
                        {entry.Driver.givenName} {entry.Driver.familyName}
                      </Link>
                    ) : entry.Constructor ? (
                      entry.Constructor.name
                    ) : (
                      'Unknown'
                    )}
                  </td>
                  {standingType === 'drivers' && entry.Driver && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {entry.Driver.nationality}
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">
                    {entry.points}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
