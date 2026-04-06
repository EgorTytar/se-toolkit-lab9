import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { driverApi, favoritesApi } from '../services/api';
import type { DriverProfile, FavoriteDriver } from '../types/api';
import { useAuth } from '../contexts/AuthContext';

export default function DriverPage() {
  const { driverId } = useParams<{ driverId: string }>();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [driver, setDriver] = useState<DriverProfile | null>(null);
  const [seasonResults, setSeasonResults] = useState<any[]>([]);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteId, setFavoriteId] = useState<number | null>(null);

  useEffect(() => {
    if (driverId) {
      loadDriver(driverId);
    }
  }, [driverId]);

  const loadDriver = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await driverApi.getDriver(id);
      setDriver(data.driver);
      setSeasonResults(data.season_results || []);
      
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
      const { data } = await favoritesApi.getFavorites();
      const fav = data.find((f: FavoriteDriver) => f.driver_id === driverId);
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
        // Reload to get the favorite ID
        checkIfFavorite(driverId);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update favorite');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  if (error || !driver) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error || 'Driver not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Driver Profile */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-2xl font-bold">
            {driver.givenName} {driver.familyName}
          </h2>
          {isAuthenticated && (
            <button
              onClick={toggleFavorite}
              className={`text-2xl transition ${
                isFavorite ? 'text-red-600' : 'text-gray-300 hover:text-red-400'
              }`}
            >
              {isFavorite ? '❤️' : '🤍'}
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Code</span>
            <p className="font-medium">{driver.code}</p>
          </div>
          {driver.permanentNumber && (
            <div>
              <span className="text-sm text-gray-500">Number</span>
              <p className="font-medium">{driver.permanentNumber}</p>
            </div>
          )}
          <div>
            <span className="text-sm text-gray-500">Nationality</span>
            <p className="font-medium">{driver.nationality}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Date of Birth</span>
            <p className="font-medium">{driver.dateOfBirth}</p>
          </div>
        </div>
      </div>

      {/* Season Results */}
      {seasonResults.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">Season Results</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Race
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Pos
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Points
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Grid
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {seasonResults.map((result: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{result.raceName}</td>
                    <td className="px-4 py-3 text-sm font-medium">{result.position}</td>
                    <td className="px-4 py-3 text-sm">{result.points}</td>
                    <td className="px-4 py-3 text-sm">{result.grid}</td>
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
