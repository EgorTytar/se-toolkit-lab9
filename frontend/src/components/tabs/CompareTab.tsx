import { useState, useRef, useEffect } from 'react';
import { compareApi } from '../../services/api';
import type { DriverComparisonResponse, H2HRaceDetail, TeammateInfo } from '../../types/api';

type CompareMode = 'h2h' | 'teammates';

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

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

// ── StatBar ──

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

// ── Averages Table ──

interface AvgRowProps {
  label: string;
  valA: number | null;
  valB: number | null;
  nameA: string;
  nameB: string;
  higherIsBetter: (a: number, b: number) => boolean;
}

function AvgRow({ label, valA, valB, nameA, nameB, higherIsBetter }: AvgRowProps) {
  const fmt = (v: number | null) =>
    v === null ? '—' : Number.isInteger(v) ? v.toString() : v.toFixed(2);

  let aClass = 'text-gray-300';
  let bClass = 'text-gray-300';
  let better = '—';

  if (valA !== null && valB !== null) {
    if (higherIsBetter(valA, valB)) {
      aClass = 'text-green-400 font-semibold';
      better = nameA;
    } else if (higherIsBetter(valB, valA)) {
      bClass = 'text-green-400 font-semibold';
      better = nameB;
    } else {
      better = 'Equal';
    }
  }

  return (
    <tr className="border-b border-gray-700 hover:bg-gray-750">
      <td className="py-2 px-3 text-gray-300">{label}</td>
      <td className={`py-2 px-3 text-center ${aClass}`}>{fmt(valA)}</td>
      <td className={`py-2 px-3 text-center ${bClass}`}>{fmt(valB)}</td>
      <td className="py-2 px-3 text-center text-xs text-gray-500">{better}</td>
    </tr>
  );
}

// ── H2H Race Row ──

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

// ── Comparison Result Component ──

function ComparisonResult({ data }: { data: DriverComparisonResponse }) {
  const [h2hLimit, setH2hLimit] = useState(20);

  return (
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
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400">
                <th className="py-2 px-3 text-left">Stat</th>
                <th className="py-2 px-3 text-center">{data.driver_a.info.given_name}</th>
                <th className="py-2 px-3 text-center">{data.driver_b.info.given_name}</th>
                <th className="py-2 px-3 text-center text-gray-500 text-xs">Better</th>
              </tr>
            </thead>
            <tbody>
              <AvgRow
                label="Avg Finish Position"
                valA={data.driver_a.career.avg_finish}
                valB={data.driver_b.career.avg_finish}
                nameA={data.driver_a.info.given_name}
                nameB={data.driver_b.info.given_name}
                higherIsBetter={(a, b) => a < b}
              />
              <AvgRow
                label="Avg Points / Race"
                valA={data.driver_a.career.avg_points}
                valB={data.driver_b.career.avg_points}
                nameA={data.driver_a.info.given_name}
                nameB={data.driver_b.info.given_name}
                higherIsBetter={(a, b) => a > b}
              />
              <AvgRow
                label="Avg Grid Position"
                valA={data.driver_a.career.avg_grid}
                valB={data.driver_b.career.avg_grid}
                nameA={data.driver_a.info.given_name}
                nameB={data.driver_b.info.given_name}
                higherIsBetter={(a, b) => a < b}
              />
              <AvgRow
                label="Win Rate"
                valA={data.driver_a.career.win_pct}
                valB={data.driver_b.career.win_pct}
                nameA={data.driver_a.info.given_name}
                nameB={data.driver_b.info.given_name}
                higherIsBetter={(a, b) => a > b}
              />
              <AvgRow
                label="Podium Rate"
                valA={data.driver_a.career.podium_pct}
                valB={data.driver_b.career.podium_pct}
                nameA={data.driver_a.info.given_name}
                nameB={data.driver_b.info.given_name}
                higherIsBetter={(a, b) => a > b}
              />
              <AvgRow
                label="DNF Rate"
                valA={data.driver_a.career.dnf_pct}
                valB={data.driver_b.career.dnf_pct}
                nameA={data.driver_a.info.given_name}
                nameB={data.driver_b.info.given_name}
                higherIsBetter={(a, b) => a < b}
              />
            </tbody>
          </table>
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
  );
}

// ── Main CompareTab ──

export default function CompareTab() {
  const [mode, setMode] = useState<CompareMode>('h2h');

  // H2H state
  const [driverA, setDriverA] = useState('');
  const [driverB, setDriverB] = useState('');
  const [data, setData] = useState<DriverComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Teammates state
  const [teammateDriverId, setTeammateDriverId] = useState('');
  const [teammates, setTeammates] = useState<TeammateInfo[]>([]);
  const [teammatesLoading, setTeammatesLoading] = useState(false);
  const [teammatesError, setTeammatesError] = useState<string | null>(null);

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!driverA.trim() || !driverB.trim()) {
      setError('Please select both drivers.');
      return;
    }
    if (driverA.trim().toLowerCase() === driverB.trim().toLowerCase()) {
      setError('Please select two different drivers.');
      return;
    }

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const result = await compareApi.compareDrivers(driverA.trim(), driverB.trim());
      setData(result);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string }; statusText?: string } })?.response?.data?.detail
        || (err as { response?: { statusText?: string } })?.response?.statusText
        || 'Failed to compare drivers.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleTeammatesFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teammateDriverId.trim()) {
      setTeammatesError('Please select a driver.');
      return;
    }

    setTeammatesLoading(true);
    setTeammatesError(null);
    setTeammates([]);

    try {
      const result = await compareApi.getDriverTeammates(teammateDriverId.trim());
      setTeammates(result);
    } catch {
      setTeammatesError('Failed to fetch teammates.');
    } finally {
      setTeammatesLoading(false);
    }
  };

  // Compare with a teammate: switch to H2H mode, pre-fill drivers, trigger compare
  const handleCompareWithTeammate = (teammateId: string) => {
    // Set both drivers
    setDriverA(teammateDriverId);
    setDriverB(teammateId);
    // Switch to H2H mode
    setMode('h2h');
    // Clear teammate results
    setTeammates([]);
    // Trigger the comparison
    setTimeout(async () => {
      setLoading(true);
      setError(null);
      setData(null);
      try {
        const result = await compareApi.compareDrivers(teammateDriverId.trim(), teammateId.trim());
        setData(result);
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
          || 'Failed to compare drivers.';
        setError(detail);
      } finally {
        setLoading(false);
      }
    }, 0);
  };

  return (
    <div>
      {/* Mode Selector */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setMode('h2h')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            mode === 'h2h'
              ? 'bg-red-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Compare Two Drivers
        </button>
        <button
          onClick={() => setMode('teammates')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            mode === 'teammates'
              ? 'bg-red-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Compare with Teammates
        </button>
      </div>

      {/* ── H2H Mode ── */}
      {mode === 'h2h' && (
        <div>
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

          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-red-500 border-t-transparent"></div>
              <p className="text-gray-400 mt-3">Fetching career data...</p>
            </div>
          )}

          {data && !loading && <ComparisonResult data={data} />}
        </div>
      )}

      {/* ── Teammates Mode ── */}
      {mode === 'teammates' && (
        <div>
          <form onSubmit={handleTeammatesFetch} className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Find All Teammates</h2>
            <div className="flex flex-col sm:flex-row gap-4">
              <DriverSearchInput
                label="Driver"
                value={teammateDriverId}
                onChange={setTeammateDriverId}
                placeholder="Type a driver name..."
              />
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={teammatesLoading || !teammateDriverId}
                  className="px-6 py-2 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {teammatesLoading ? 'Searching...' : 'Find Teammates'}
                </button>
              </div>
            </div>
            {teammatesError && <p className="text-red-400 text-sm mt-3">{teammatesError}</p>}
          </form>

          {teammatesLoading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-red-500 border-t-transparent"></div>
              <p className="text-gray-400 mt-3">Finding teammates...</p>
            </div>
          )}

          {teammates.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                {teammates.length} Teammate{teammates.length > 1 ? 's' : ''} Found
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-gray-400">
                      <th className="py-2 px-3 text-left">Driver</th>
                      <th className="py-2 px-3 text-left">Seasons</th>
                      <th className="py-2 px-3 text-left">Constructor{teammates.some(t => t.constructors.length > 1) ? 's' : ''}</th>
                      <th className="py-2 px-3 text-center">Races</th>
                      <th className="py-2 px-3 text-center"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {teammates.map((tm) => {
                      const yrs = tm.seasons.length > 1
                        ? `${tm.seasons[0]}–${tm.seasons[tm.seasons.length - 1]}`
                        : `${tm.seasons[0]}`;
                      const cons = tm.constructors.map(c => c.constructor_name).join(', ');
                      return (
                        <tr key={tm.driver_id} className="border-b border-gray-700 hover:bg-gray-750">
                          <td className="py-2 px-3">
                            <span className="font-medium text-red-400">{tm.full_name}</span>
                            {tm.code && <span className="text-gray-500 text-xs ml-2">({tm.code})</span>}
                          </td>
                          <td className="py-2 px-3">{yrs}</td>
                          <td className="py-2 px-3 text-gray-300">{cons}</td>
                          <td className="py-2 px-3 text-center">{tm.total_races}</td>
                          <td className="py-2 px-3 text-center">
                            <button
                              onClick={() => handleCompareWithTeammate(tm.driver_id)}
                              className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition"
                            >
                              Compare
                            </button>
                          </td>
                        </tr>
                      );
                    })}
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
