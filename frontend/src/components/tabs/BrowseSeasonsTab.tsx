import { useState } from 'react';
import { raceApi } from '../../services/api';
import type { RaceScheduleItem, AIResponse } from '../../types/api';
import { Link } from 'react-router-dom';

export default function BrowseSeasonsTab() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schedule, setSchedule] = useState<RaceScheduleItem[]>([]);
  const [expandedRace, setExpandedRace] = useState<string | null>(null);
  const [raceSummary, setRaceSummary] = useState<AIResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const fetchSeason = async () => {
    setLoading(true);
    setError(null);
    setExpandedRace(null);
    setRaceSummary(null);
    try {
      const { data } = await raceApi.getSeasonSchedule(year);
      setSchedule(data.schedule);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load season schedule');
    } finally {
      setLoading(false);
    }
  };

  const toggleRace = async (round: string) => {
    const key = `${year}-${round}`;
    if (expandedRace === key) {
      setExpandedRace(null);
      setRaceSummary(null);
      return;
    }

    setExpandedRace(key);
    setSummaryLoading(true);
    try {
      const { data } = await raceApi.getRace(year, parseInt(round));
      setRaceSummary(data);
    } catch {
      setRaceSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <input
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-md w-32"
          placeholder="Year"
          min={1950}
          max={new Date().getFullYear() + 1}
        />
        <button
          onClick={fetchSeason}
          disabled={loading}
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Load Season'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {schedule.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="divide-y">
            {schedule.map((race) => {
              const key = `${year}-${race.round}`;
              const isExpanded = expandedRace === key;
              const isFuture = new Date(race.date) > new Date();

              return (
                <div key={race.round} className="p-4">
                  <button
                    onClick={() => toggleRace(race.round)}
                    className="w-full flex items-center justify-between hover:bg-gray-50 rounded-lg p-2 transition"
                  >
                    <div className="flex items-center space-x-3">
                      <span
                        className={`transform transition ${isExpanded ? 'rotate-90' : ''}`}
                      >
                        ▶
                      </span>
                      <span className="font-medium">Round {race.round}</span>
                      <Link
                        to={`/circuit/${race.circuit.circuitId}`}
                        className="text-red-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {race.raceName}
                      </Link>
                      {isFuture && (
                        <span className="text-sm text-gray-500">(Future)</span>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">{race.date}</span>
                  </button>

                  {isExpanded && (
                    <div className="mt-4 ml-8 p-4 bg-gray-50 rounded-lg">
                      <div className="mb-2">
                        <strong>Circuit:</strong>{' '}
                        <Link
                          to={`/circuit/${race.circuit.circuitId}`}
                          className="text-red-600 hover:underline"
                        >
                          {race.circuit.circuitName}
                        </Link>
                      </div>
                      <div className="mb-2">
                        <strong>Location:</strong> {race.circuit.location.locality},{' '}
                        {race.circuit.location.country}
                      </div>
                      <div className="mb-4">
                        <strong>Date:</strong> {race.date}
                        {race.time && ` at ${race.time}`}
                      </div>

                      {summaryLoading ? (
                        <div className="flex justify-center py-4">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
                        </div>
                      ) : raceSummary ? (
                        <div className="space-y-3">
                          <div>
                            <h4 className="font-semibold mb-1">Summary</h4>
                            <p className="text-gray-700 whitespace-pre-wrap">
                              {raceSummary.summary}
                            </p>
                          </div>
                          <div>
                            <h4 className="font-semibold mb-1">Highlights</h4>
                            <p className="text-gray-700 whitespace-pre-wrap">
                              {raceSummary.highlights}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-gray-500">No summary available</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
