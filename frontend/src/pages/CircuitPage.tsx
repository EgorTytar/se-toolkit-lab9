import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { circuitApi } from '../services/api';
import type { CircuitInfo } from '../types/api';

export default function CircuitPage() {
  const { circuitId } = useParams<{ circuitId: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [circuit, setCircuit] = useState<CircuitInfo | null>(null);
  const [recentResults, setRecentResults] = useState<any[]>([]);

  useEffect(() => {
    if (circuitId) {
      loadCircuit(circuitId);
    }
  }, [circuitId]);

  const loadCircuit = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await circuitApi.getCircuit(id);
      setCircuit(data.circuit);
      setRecentResults(data.recent_results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load circuit');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  if (error || !circuit) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error || 'Circuit not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Circuit Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">{circuit.circuitName}</h2>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Location</span>
            <p className="font-medium">
              {circuit.location.locality}, {circuit.location.country}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Coordinates</span>
            <p className="font-medium">
              {circuit.location.lat}, {circuit.location.long}
            </p>
          </div>
        </div>
      </div>

      {/* Recent Results */}
      {recentResults.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">Recent Races at This Circuit</h3>
          <div className="space-y-4">
            {recentResults.map((result: any, idx: number) => (
              <div key={idx} className="border-b pb-4 last:border-0">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{result.raceName}</h4>
                  <span className="text-sm text-gray-500">{result.date}</span>
                </div>
                {result.Results && result.Results.slice(0, 3).map((r: any) => (
                  <div key={r.position} className="flex items-center space-x-2 text-sm ml-4">
                    <span className="font-medium">P{r.position}:</span>
                    <Link
                      to={`/driver/${r.Driver.driverId}`}
                      className="text-red-600 hover:underline"
                    >
                      {r.Driver.givenName} {r.Driver.familyName}
                    </Link>
                    <span className="text-gray-500">({r.Constructor.name})</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
