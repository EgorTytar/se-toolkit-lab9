import { useState, useRef, useEffect } from 'react';
import { compareApi } from '../../services/api';
import type { DriverComparisonResponse, H2HRaceDetail } from '../../types/api';

interface DriverOption {
  driver_id: string;
  code: string;
  full_name: string;
  nationality: string;
  permanent_number: string;
}

// ── Searchable Driver Selector ──

interface DriverSearchInputProps {
  label: string;
  value: string;
  onChange: (driverId: string) => void;
  placeholder?: string;
}

function DriverSearchInput({ label, value, onChange, placeholder }: DriverSearchInputProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<DriverOption[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Reset when parent clears the value (e.g. after compare)
  useEffect(() => {
    if (!value) {
      setQuery('');
    }
  }, [value]);

  const handleInputChange = (val: string) => {
    setQuery(val);
    if (val.trim()) onChange('');
    setShowSuggestions(true);

    if (timerRef.current) clearTimeout(timerRef.current);

    if (val.trim().length < 1) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    timerRef.current = setTimeout(async () => {
      try {
        const results = await compareApi.searchDrivers(val.trim());
        setSuggestions(results);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 200);
  };

  const selectDriver = (driver: DriverOption) => {
    setQuery(`${driver.full_name} (${driver.code})`);
    onChange(driver.driver_id);
    setShowSuggestions(false);
  };

  return (
    <div className="relative flex-1" ref={wrapperRef}>
      <label className="block text-sm text-gray-400 mb-1">{label}</label>
      <input
        type="text"
        value={query}
        onChange={(e) => handleInputChange(e.target.value)}
        onFocus={() => query.trim().length >= 1 && setShowSuggestions(true)}
        placeholder={placeholder}
        className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
      />
      {loading && (
        <div className="absolute right-3 top-9">
          <div className="animate-spin h-4 w-4 border-2 border-red-500 border-t-transparent rounded-full"></div>
        </div>
      )}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-gray-700 border border-gray-600 rounded shadow-xl max-h-60 overflow-y-auto">
          {suggestions.map((driver) => (
            <button
              key={driver.driver_id}
              onClick={() => selectDriver(driver)}
              className="w-full text-left px-3 py-2 hover:bg-gray-600 text-sm flex items-center justify-between transition"
            >
              <span className="text-gray-100">{driver.full_name}</span>
              <span className="text-gray-400 text-xs ml-2">
                {driver.code && `${driver.code} • `}
                {driver.nationality}
              </span>
            </button>
          ))}
        </div>
      )}
      {showSuggestions && suggestions.length === 0 && query.trim().length >= 1 && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-gray-700 border border-gray-600 rounded shadow-xl p-3 text-sm text-gray-400 text-center">
          No drivers found
        </div>
      )}
    </div>
  );
}

interface StatBarProps {
  label: string;
  valueA: number | string;
  valueB: number | string;
  maxVal: number;
  higherIsBetter?: boolean;
}

function StatBar({ label, valueA, valueB, maxVal, higherIsBetter = true }: StatBarProps) {
  const numA = typeof valueA === 'number' ? valueA : 0;
  const numB = typeof valueB === 'number' ? valueB : 0;
  const pctA = maxVal > 0 ? (numA / maxVal) * 100 : 0;
  const pctB = maxVal > 0 ? (numB / maxVal) * 100 : 0;

  const aWins = higherIsBetter ? numA > numB : numA < numB;
  const bWins = higherIsBetter ? numB > numA : numB < numA;
  const isDraw = numA === numB;

  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className={aWins ? 'text-green-400 font-semibold' : 'text-gray-300'}>
          {valueA}
        </span>
        <span className="text-gray-400 font-medium">{label}</span>
        <span className={bWins ? 'text-green-400 font-semibold' : 'text-gray-300'}>
          {valueB}
        </span>
      </div>
      <div className="flex h-2 rounded overflow-hidden bg-gray-700">
        <div
          className={`transition-all ${isDraw ? 'bg-gray-500' : aWins ? 'bg-green-500' : 'bg-gray-600'}`}
          style={{ width: `${pctA}%` }}
        />
        <div
          className={`transition-all ${isDraw ? 'bg-gray-500' : bWins ? 'bg-green-500' : 'bg-gray-600'}`}
          style={{ width: `${pctB}%` }}
        />
      </div>
    </div>
  );
}

function H2HRaceRow({ detail }: { detail: H2HRaceDetail }) {
  const winnerClass = (w: 'a' | 'b' | 'draw') => {
    if (w === 'a') return 'text-green-400';
    if (w === 'b') return 'text-green-400';
    return 'text-gray-400';
  };

  return (
    <tr className="border-b border-gray-700 hover:bg-gray-800 text-sm">
      <td className="py-2 px-3">{detail.season}</td>
      <td className="py-2 px-3">{detail.round}</td>
      <td className="py-2 px-3 max-w-[200px] truncate">{detail.race_name}</td>
      <td className={`py-2 px-3 text-center font-medium ${winnerClass(detail.winner === 'draw' ? (detail.driver_a.position === detail.driver_b.position ? 'draw' : 'a') : (detail.winner === 'a' ? 'a' : 'draw'))}`}>
        P{detail.driver_a.position || 'DNF'}
        <span className="text-gray-500 ml-1">({detail.driver_a.points} pts)</span>
      </td>
      <td className={`py-2 px-3 text-center font-medium ${winnerClass(detail.winner)}`}>
        {detail.winner === 'a' ? '✅' : detail.winner === 'b' ? '✅' : '—'}
      </td>
      <td className={`py-2 px-3 text-center font-medium ${detail.winner === 'b' ? 'text-green-400' : 'text-gray-300'}`}>
        P{detail.driver_b.position || 'DNF'}
        <span className="text-gray-500 ml-1">({detail.driver_b.points} pts)</span>
      </td>
    </tr>
  );
}

export default function CompareTab() {
  const [driverA, setDriverA] = useState('');
  const [driverB, setDriverB] = useState('');
  const [data, setData] = useState<DriverComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [h2hLimit, setH2hLimit] = useState(20);

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!driverA.trim() || !driverB.trim()) {
      setError('Please enter both driver IDs.');
      return;
    }
    if (driverA.trim().toLowerCase() === driverB.trim().toLowerCase()) {
      setError('Please select two different drivers.');
      return;
    }

    setLoading(true);
    setError(null);
    setData(null);
    setH2hLimit(20);

    try {
      const result = await compareApi.compareDrivers(driverA.trim(), driverB.trim());
      setData(result);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string }; statusText?: string } })?.response?.data?.detail
        || (err as { response?: { statusText?: string } })?.response?.statusText
        || 'Failed to compare drivers. Check the driver IDs and try again.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Input Form */}
      <form onSubmit={handleCompare} className="bg-gray-800 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Compare Two Drivers</h2>
        <div className="flex flex-col sm:flex-row gap-4">
          <DriverSearchInput
            label="Driver A"
            value={driverA}
            onChange={setDriverA}
            placeholder="Type a driver name..."
          />
          <DriverSearchInput
            label="Driver B"
            value={driverB}
            onChange={setDriverB}
            placeholder="Type a driver name..."
          />
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading || !driverA || !driverB}
              className="px-6 py-2 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Comparing...' : 'Compare'}
            </button>
          </div>
        </div>
        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
        <p className="text-gray-500 text-xs mt-2">
          Start typing to search — matches by name, code (e.g. VER), or driver ID.
        </p>
      </form>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-red-500 border-t-transparent"></div>
          <p className="text-gray-400 mt-3">Fetching career data...</p>
        </div>
      )}

      {/* Results */}
      {data && !loading && (
        <div>
          {/* Driver Headers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-5 text-center">
              <h3 className="text-xl font-bold text-red-400">
                {data.driver_a.info.full_name}
              </h3>
              <p className="text-gray-400 text-sm">
                {data.driver_a.info.nationality} • #{data.driver_a.info.permanent_number || 'N/A'}
              </p>
              <p className="text-gray-500 text-xs mt-1">
                {data.driver_a.info.code} • {data.driver_a.career.seasons_competed[0]}–
                {data.driver_a.career.seasons_competed[data.driver_a.career.seasons_competed.length - 1]}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-5 text-center">
              <h3 className="text-xl font-bold text-red-400">
                {data.driver_b.info.full_name}
              </h3>
              <p className="text-gray-400 text-sm">
                {data.driver_b.info.nationality} • #{data.driver_b.info.permanent_number || 'N/A'}
              </p>
              <p className="text-gray-500 text-xs mt-1">
                {data.driver_b.info.code} • {data.driver_b.career.seasons_competed[0]}–
                {data.driver_b.career.seasons_competed[data.driver_b.career.seasons_competed.length - 1]}
              </p>
            </div>
          </div>

          {/* Career Stats Comparison */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Career Statistics</h3>
            <StatBar
              label="Races"
              valueA={data.driver_a.career.races}
              valueB={data.driver_b.career.races}
              maxVal={Math.max(data.driver_a.career.races, data.driver_b.career.races)}
            />
            <StatBar
              label="Wins"
              valueA={data.driver_a.career.wins}
              valueB={data.driver_b.career.wins}
              maxVal={Math.max(data.driver_a.career.wins, data.driver_b.career.wins)}
            />
            <StatBar
              label="Podiums"
              valueA={data.driver_a.career.podiums}
              valueB={data.driver_b.career.podiums}
              maxVal={Math.max(data.driver_a.career.podiums, data.driver_b.career.podiums)}
            />
            <StatBar
              label="Pole Positions"
              valueA={data.driver_a.career.poles}
              valueB={data.driver_b.career.poles}
              maxVal={Math.max(data.driver_a.career.poles, data.driver_b.career.poles)}
            />
            <StatBar
              label="Points"
              valueA={data.driver_a.career.points}
              valueB={data.driver_b.career.points}
              maxVal={Math.max(data.driver_a.career.points, data.driver_b.career.points)}
            />
            <StatBar
              label="Championships"
              valueA={data.driver_a.career.championships}
              valueB={data.driver_b.career.championships}
              maxVal={Math.max(data.driver_a.career.championships, data.driver_b.career.championships)}
            />
            {data.driver_a.career.best_finish && data.driver_b.career.best_finish && (
              <StatBar
                label="Best Finish"
                valueA={data.driver_a.career.best_finish}
                valueB={data.driver_b.career.best_finish}
                maxVal={20}
                higherIsBetter={false}
              />
            )}
          </div>

          {/* Constructor History */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                {data.driver_a.info.given_name}'s Teams
              </h3>
              {data.driver_a.career.teams.map((team) => (
                <div key={team.constructor_id} className="border-b border-gray-700 pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-100">{team.constructor_name}</span>
                    <span className="text-xs text-gray-500">
                      {team.years[0]}–{team.years[team.years.length - 1]}
                    </span>
                  </div>
                  <div className="flex gap-3 text-xs text-gray-400 mt-1">
                    <span>{team.races} races</span>
                    <span className={team.wins > 0 ? 'text-green-400' : ''}>{team.wins}W</span>
                    <span>{team.podiums}P</span>
                    <span>{team.points} pts</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                {data.driver_b.info.given_name}'s Teams
              </h3>
              {data.driver_b.career.teams.map((team) => (
                <div key={team.constructor_id} className="border-b border-gray-700 pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-100">{team.constructor_name}</span>
                    <span className="text-xs text-gray-500">
                      {team.years[0]}–{team.years[team.years.length - 1]}
                    </span>
                  </div>
                  <div className="flex gap-3 text-xs text-gray-400 mt-1">
                    <span>{team.races} races</span>
                    <span className={team.wins > 0 ? 'text-green-400' : ''}>{team.wins}W</span>
                    <span>{team.podiums}P</span>
                    <span>{team.points} pts</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Average Stats */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Averages</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
              {/* Avg Finish */}
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">Avg Finish</p>
                <p className="text-xl font-bold">
                  {data.driver_a.career.avg_finish ?? '—'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {data.driver_b.career.avg_finish ?? '—'}
                </p>
              </div>
              {/* Avg Points/Race */}
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">Pts/Race</p>
                <p className="text-xl font-bold">{data.driver_a.career.avg_points}</p>
                <p className="text-xs text-gray-500 mt-1">{data.driver_b.career.avg_points}</p>
              </div>
              {/* Avg Grid */}
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">Avg Grid</p>
                <p className="text-xl font-bold">
                  {data.driver_a.career.avg_grid ?? '—'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {data.driver_b.career.avg_grid ?? '—'}
                </p>
              </div>
              {/* Win Rate */}
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">Win Rate</p>
                <p className="text-xl font-bold text-green-400">{data.driver_a.career.win_pct}%</p>
                <p className="text-xs text-gray-500 mt-1">{data.driver_b.career.win_pct}%</p>
              </div>
              {/* Podium Rate */}
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">Podium Rate</p>
                <p className="text-xl font-bold">{data.driver_a.career.podium_pct}%</p>
                <p className="text-xs text-gray-500 mt-1">{data.driver_b.career.podium_pct}%</p>
              </div>
              {/* DNF Rate */}
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">DNF Rate</p>
                <p className="text-xl font-bold text-red-400">{data.driver_a.career.dnf_pct}%</p>
                <p className="text-xs text-gray-500 mt-1">{data.driver_b.career.dnf_pct}%</p>
              </div>
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-500">
              <span>← {data.driver_a.info.given_name}</span>
              <span>{data.driver_b.info.given_name} →</span>
            </div>
          </div>

          {/* Head-to-Head Summary */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">
              Head-to-Head ({data.head_to_head.shared_races} shared races, {data.head_to_head.shared_seasons.length} seasons)
            </h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-3xl font-bold text-green-400">{data.head_to_head.driver_a_wins}</p>
                <p className="text-sm text-gray-400 mt-1">{data.driver_a.info.given_name}</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-3xl font-bold text-gray-300">{data.head_to_head.draws}</p>
                <p className="text-sm text-gray-400 mt-1">Draws</p>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-3xl font-bold text-green-400">{data.head_to_head.driver_b_wins}</p>
                <p className="text-sm text-gray-400 mt-1">{data.driver_b.info.given_name}</p>
              </div>
            </div>
            {/* H2H Bar */}
            {data.head_to_head.shared_races > 0 && (
              <div className="mt-4 flex h-4 rounded overflow-hidden bg-gray-700">
                <div
                  className="bg-green-500 transition-all"
                  style={{
                    width: `${(data.head_to_head.driver_a_wins / data.head_to_head.shared_races) * 100}%`,
                  }}
                  title={`${data.driver_a.info.given_name}: ${data.head_to_head.driver_a_wins}`}
                />
                <div
                  className="bg-gray-500 transition-all"
                  style={{
                    width: `${(data.head_to_head.draws / data.head_to_head.shared_races) * 100}%`,
                  }}
                  title={`Draws: ${data.head_to_head.draws}`}
                />
                <div
                  className="bg-blue-500 transition-all"
                  style={{
                    width: `${(data.head_to_head.driver_b_wins / data.head_to_head.shared_races) * 100}%`,
                  }}
                  title={`${data.driver_b.info.given_name}: ${data.head_to_head.driver_b_wins}`}
                />
              </div>
            )}
          </div>

          {/* Race-by-Race Breakdown */}
          {data.head_to_head.race_details.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Race-by-Race Breakdown</h3>
                {data.head_to_head.race_details.length > h2hLimit && (
                  <button
                    onClick={() => setH2hLimit((prev) => prev + 50)}
                    className="text-sm text-red-400 hover:text-red-300 transition"
                  >
                    Show more ({data.head_to_head.race_details.length - h2hLimit} remaining)
                  </button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-gray-400">
                      <th className="py-2 px-3 text-left">Year</th>
                      <th className="py-2 px-3 text-left">Rnd</th>
                      <th className="py-2 px-3 text-left">Race</th>
                      <th className="py-2 px-3 text-center">{data.driver_a.info.given_name}</th>
                      <th className="py-2 px-3 text-center">W</th>
                      <th className="py-2 px-3 text-center">{data.driver_b.info.given_name}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.head_to_head.race_details.slice(0, h2hLimit).map((detail, idx) => (
                      <H2HRaceRow key={idx} detail={detail} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
