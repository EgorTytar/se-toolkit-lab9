import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { circuitApi } from '../services/api';
import type { CircuitInfo, CircuitResult } from '../types/api';

export default function CircuitPage() {
  const { circuitId } = useParams<{ circuitId: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [circuit, setCircuit] = useState<CircuitInfo | null>(null);
  const [recentResults, setRecentResults] = useState<CircuitResult[]>([]);

  useEffect(() => {
    if (circuitId) {
      loadCircuit(circuitId);
    }
  }, [circuitId]);

  const loadCircuit = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await circuitApi.getCircuit(id);
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (error || !circuit) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
        <p className="text-red-400">{error || 'Circuit not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Circuit Info */}
      <div className="bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">{circuit.name}</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-sm text-gray-400">Location</span>
            <p className="font-medium">{circuit.location}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">Country</span>
            <p className="font-medium">{circuit.country}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">Coordinates</span>
            <p className="font-medium">{circuit.latitude}, {circuit.longitude}</p>
          </div>
          <div>
            <span className="text-sm text-gray-400">More Info</span>
            <p className="font-medium">
              <a href={circuit.url} className="text-red-400 hover:underline" target="_blank">
                Wikipedia ↗
              </a>
            </p>
          </div>
        </div>
      </div>

      {/* Recent Results */}
      {recentResults.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">Recent Races at This Circuit</h3>
          <div className="space-y-6">
            {recentResults.map((result, idx) => (
              <div key={idx} className="border-b border-gray-700 pb-4 last:border-0">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">
                    {result.race_name} ({result.season})
                  </h4>
                  <span className="text-sm text-gray-400">Round {result.round}</span>
                </div>
                <div className="ml-4">
                  <div className="flex items-center space-x-2 text-sm">
                    <span className="font-medium text-green-400">P{result.position}:</span>
                    <Link
                      to={`/driver/${result.driver_id}`}
                      className="text-red-400 hover:underline"
                    >
                      {result.driver_name}
                    </Link>
                    <span className="text-gray-400">({result.constructor})</span>
                    <span className="text-gray-500">• {result.points} pts</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
