import { useEffect, useState } from 'react';
import { raceApi } from '../../services/api';
import type { AIResponse } from '../../types/api';

export default function LatestRaceTab() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AIResponse | null>(null);

  useEffect(() => {
    fetchLatest();
  }, []);

  const fetchLatest = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await raceApi.getLatestRace();
      setData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load latest race');
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

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error}</p>
        <button
          onClick={fetchLatest}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Race Summary</h2>
        <p className="text-gray-700 whitespace-pre-wrap">{data.summary}</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Highlights</h2>
        <p className="text-gray-700 whitespace-pre-wrap">{data.highlights}</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Insights</h2>
        <p className="text-gray-700 whitespace-pre-wrap">{data.insights}</p>
      </div>
    </div>
  );
}
