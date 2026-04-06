import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { driverApi, favoritesApi } from '../services/api';
import type { DriverProfile, DriverResult, FavoriteDriver } from '../types/api';
import { useAuth } from '../contexts/AuthContext';

export default function DriverPage() {
  const { driverId } = useParams<{ driverId: string }>();
  const { isAuthenticated } = useAuth();
  const currentYear = new Date().getFullYear();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [driver, setDriver] = useState<DriverProfile | null>(null);
  const [seasonResults, setSeasonResults] = useState<DriverResult[]>([]);
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteId, setFavoriteId] = useState<number | null>(null);

  useEffect(() => {
    if (driverId) {
      loadDriver(driverId, selectedYear);
    }
  }, [driverId, selectedYear]);

  const loadDriver = async (id: string, year: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await driverApi.getDriver(id, year);
      setDriver(data.driver);
      setSeasonResults(data.results || []);
      
      if (isAuthenticated) {
        checkIfFavorite(id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load driver');
    } finally {
      setLoading(false);
    }
  };

  const checkIfFavorite = async (driverId: string) => {
    try {
      const favs = await favoritesApi.getFavorites();
      const fav = favs.find((f: FavoriteDriver) => f.driver_id === driverId);
      if (fav) {
        setIsFavorite(true);
        setFavoriteId(fav.id);
      }
    } catch {
      // Not a critical feature
    }
  };

  const toggleFavorite = async () => {
    if (!driverId || !driver) return;
    
    try {
      if (isFavorite && favoriteId) {
        await favoritesApi.removeFavorite(favoriteId);
        setIsFavorite(false);
        setFavoriteId(null);
      } else {
        await favoritesApi.addFavorite(driverId);
        setIsFavorite(true);
        checkIfFavorite(driverId);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update favorite');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (error || !driver) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
        <p className="text-red-400">{error || 'Driver not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Driver Profile */}
      <div className="bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-2xl font-bold">
            {driver.full_name || `${driver.given_name} ${driver.family_name}`}
          </h2>
          {isAuthenticated && (
            <button
              onClick={toggleFavorite}
              className={`text-2xl transition ${
                isFavorite ? 'text-red-500' : 'text-gray-500 hover:text-red-400'
              }`}
            >
              {isFavorite ? '❤️' : '🤍'}
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-sm text-gray-400">Code</span>
            <p className="font-medium">{driver.code}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">Number</span>
            <p className="font-medium">#{driver.permanent_number}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">Nationality</span>
            <p className="font-medium">{driver.nationality}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">Date of Birth</span>
            <p className="font-medium">{driver.date_of_birth}</p>
          </div>
        </div>

        {/* Year selector */}
        <div className="mt-4 flex items-center gap-2">
          <label className="text-sm text-gray-400">Season:</label>
          <input
            type="number"
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="w-24 px-3 py-1 border border-gray-600 rounded bg-gray-700 text-gray-100"
            min={2000}
            max={currentYear}
          />
          <button
            onClick={() => driverId && loadDriver(driverId, selectedYear)}
            className="px-4 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
          >
            Load
          </button>
        </div>
      </div>

      {/* Season Results */}
      {seasonResults.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">{selectedYear} Season Results</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Round</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Race</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Pos</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Grid</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Points</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {seasonResults.map((result) => (
                  <tr key={result.round} className="hover:bg-gray-700">
                    <td className="px-4 py-3 text-sm">{result.round}</td>
                    <td className="px-4 py-3 text-sm">{result.race_name}</td>
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
