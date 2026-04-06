import { useState } from 'react';
import { raceApi } from '../../services/api';
import type { RaceScheduleItem, LatestRaceResponse } from '../../types/api';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface PodiumEntry {
  position: number;
  name: string;
  constructor: string;
  points: number;
  driver_id: string;
}

interface BasicRaceResults {
  race_name: string;
  circuit: string;
  circuit_id: string;
  date: string;
  season: string;
  round: number;
  total_drivers: number;
  winner: PodiumEntry;
  podium: PodiumEntry[];
}

export default function BrowseSeasonsTab() {
  const { isAuthenticated } = useAuth();
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [races, setRaces] = useState<RaceScheduleItem[]>([]);
  const [expandedRace, setExpandedRace] = useState<string | null>(null);
  const [raceSummary, setRaceSummary] = useState<LatestRaceResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [fetchedAi, setFetchedAi] = useState(false);
  const [basicResults, setBasicResults] = useState<BasicRaceResults | null>(null);
  const [loadingBasic, setLoadingBasic] = useState(false);

  const fetchSeason = async () => {
    setLoading(true);
    setError(null);
    setExpandedRace(null);
    setRaceSummary(null);
    setFetchedAi(false);
    setBasicResults(null);
    try {
      const data = await raceApi.getSeasonSchedule(year);
      setRaces(data.races);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load season schedule');
    } finally {
      setLoading(false);
    }
  };

  const toggleRace = async (round: number) => {
    const key = `${year}-${round}`;
    if (expandedRace === key) {
      setExpandedRace(null);
      setRaceSummary(null);
      setBasicResults(null);
      setFetchedAi(false);
      return;
    }

    setExpandedRace(key);
    setRaceSummary(null);
    setBasicResults(null);
    setFetchedAi(false);
    setSummaryLoading(false);
    setLoadingBasic(true);
    try {
      const response = await fetch(`${window.location.origin}/api/races/${year}/${round}/results`);
      if (!response.ok) throw new Error('Failed');
      const jsonData = await response.json();
      setBasicResults(jsonData);
    } catch {
      setBasicResults(null);
    } finally {
      setLoadingBasic(false);
    }
  };

  const fetchAiSummary = async (round: number) => {
    if (!isAuthenticated) return;
    setSummaryLoading(true);
    try {
      const data = await raceApi.getRace(year, round);
      setRaceSummary(data);
      setFetchedAi(true);
    } catch {
      setRaceSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  };

  const hasAi = !!raceSummary?.ai_response.summary;

  return (
    <div className="space-y-4">
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
          onClick={fetchSeason}
          disabled={loading}
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Load Season'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {races.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow">
          <div className="divide-y divide-gray-700">
            {races.map((race) => {
              const key = `${year}-${race.round}`;
              const isExpanded = expandedRace === key;
              const raceDate = new Date(race.date);
              const isRaceFuture = raceDate > new Date();

              return (
                <div key={race.round} className="p-4">
                  <button
                    onClick={() => toggleRace(race.round)}
                    className="w-full flex items-center justify-between hover:bg-gray-700 rounded-lg p-2 transition"
                  >
                    <div className="flex items-center space-x-3">
                      <span className={`transform transition ${isExpanded ? 'rotate-90' : ''}`}>
                        ▶
                      </span>
                      <span className="font-medium">Round {race.round}</span>
                      <Link
                        to={`/circuit/${race.circuit_id}`}
                        className="text-red-400 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {race.race_name}
                      </Link>
                      {isRaceFuture && (
                        <span className="text-sm text-green-400">⏳ Upcoming</span>
                      )}
                    </div>
                    <span className="text-sm text-gray-400">{race.date}</span>
                  </button>

                  {isExpanded && (
                    <div className="mt-4 ml-8 p-4 bg-gray-700 rounded-lg">
                      <div className="mb-2">
                        <strong>Circuit:</strong>{' '}
                        <Link
                          to={`/circuit/${race.circuit_id}`}
                          className="text-red-400 hover:underline"
                        >
                          {race.circuit}
                        </Link>
                      </div>
                      <div className="mb-2">
                        <strong>Date:</strong> {race.date}
                      </div>

                      {/* Reminder button for future races */}
                      {isRaceFuture && isAuthenticated && (
                        <div className="mb-4">
                          <AddReminderButton race={race} />
                        </div>
                      )}
                      {isRaceFuture && !isAuthenticated && (
                        <div className="mb-4 text-sm text-gray-400">
                          <Link to="/login" className="text-red-400 hover:underline">Login</Link> to add reminders
                        </div>
                      )}

                      {/* Basic results loading */}
                      {loadingBasic && (
                        <div className="flex justify-center py-4">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
                        </div>
                      )}

                      {/* Podium + Results */}
                      {basicResults?.podium && basicResults.podium.length > 0 && (
                        <RaceResults results={basicResults} />
                      )}

                      {/* AI Summary Button */}
                      {isAuthenticated && !hasAi && !fetchedAi && basicResults && (
                        <button
                          onClick={() => fetchAiSummary(race.round)}
                          disabled={summaryLoading}
                          className="w-full mb-4 py-2 bg-purple-700 hover:bg-purple-600 disabled:bg-purple-900 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
                        >
                          {summaryLoading ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              Generating AI Summary...
                            </>
                          ) : (
                            <>🤖 Get AI Summary</>
                          )}
                        </button>
                      )}

                      {hasAi && (
                        <div className="mb-4 space-y-3 bg-purple-900/20 rounded-lg p-4 border border-purple-800">
                          <div>
                            <h4 className="font-semibold text-purple-300 mb-1">Summary</h4>
                            <p className="text-gray-300 whitespace-pre-wrap text-sm">
                              {raceSummary!.ai_response.summary}
                            </p>
                          </div>
                          <div>
                            <h4 className="font-semibold text-purple-300 mb-1">Highlights</h4>
                            <p className="text-gray-300 whitespace-pre-wrap text-sm">
                              {raceSummary!.ai_response.highlights}
                            </p>
                          </div>
                        </div>
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

function AddReminderButton({ race }: { race: RaceScheduleItem }) {
  const [loading, setLoading] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addReminder = async () => {
    setLoading(true);
    setError(null);
    try {
      await fetch(`${window.location.origin}/api/reminders/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          race_round: race.round,
          race_year: new Date().getFullYear(),
          notify_before_hours: 24,
          method: 'email',
        }),
      });
      setAdded(true);
    } catch {
      setError('Failed to add reminder');
    } finally {
      setLoading(false);
    }
  };

  if (added) {
    return (
      <span className="px-3 py-1 text-sm bg-green-900 text-green-300 rounded flex items-center gap-1">
        ✓ Reminder Set
      </span>
    );
  }

  return (
    <div>
      <button
        onClick={addReminder}
        disabled={loading}
        className="px-4 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-orange-800 text-white rounded-lg transition text-sm"
      >
        {loading ? 'Adding...' : '⏰ Add Reminder'}
      </button>
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  );
}

function RaceResults({ results }: { results: BasicRaceResults }) {
  return (
    <div className="space-y-4">
      {/* Winner Banner */}
      {results.winner && (
        <div className="bg-green-900/20 border border-green-700 rounded-lg p-3">
          <span className="text-green-400 font-semibold">🏆 Winner:</span>{' '}
          <Link to={`/driver/${results.winner.driver_id}`} className="text-green-300 hover:underline font-medium">
            {results.winner.name}
          </Link>
          {' '}({results.winner.constructor}) — {results.winner.points} pts
        </div>
      )}

      {/* Podium Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {results.podium.map((r, i) => {
          const medalColors = [
            'border-yellow-500 bg-yellow-900/20',
            'border-gray-400 bg-gray-700/40',
            'border-amber-700 bg-amber-900/20',
          ];
          const medalEmojis = ['🥇', '🥈', '🥉'];
          return (
            <div key={r.position} className={`rounded-lg p-4 border-2 ${medalColors[i]}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{medalEmojis[i]}</span>
                <span className="font-bold text-lg">
                  <Link to={`/driver/${r.driver_id}`} className="hover:underline">
                    {r.name}
                  </Link>
                </span>
              </div>
              <div className="text-sm text-gray-400">{r.constructor}</div>
              <div className="text-sm text-gray-400 mt-1">{r.points} pts</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
