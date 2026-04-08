import { useState } from 'react';
import { predictionsApi } from '../../services/api';
import type {
  PredictionResponse,
  DriverFormAnalysis,
  ConstructorFormAnalysis,
} from '../../types/api';
import { Link } from 'react-router-dom';

type PredictionType = 'drivers' | 'constructors';

export default function PredictionsTab() {
  const [predictionType, setPredictionType] = useState<PredictionType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);

  const fetchPrediction = async (type: PredictionType) => {
    setLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const data =
        type === 'drivers'
          ? await predictionsApi.getDriverPrediction()
          : await predictionsApi.getConstructorPrediction();
      setPredictionType(type);
      setPrediction(data);
    } catch (err: any) {
      setPredictionType(type);
      setError(err.response?.data?.detail || 'Failed to load prediction');
    } finally {
      setLoading(false);
    }
  };

  const champion = prediction?.predicted_champion;
  const confidencePct = champion ? Math.round(champion.confidence * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Type Selector */}
      <div className="flex space-x-2">
        <button
          onClick={() => fetchPrediction('drivers')}
          disabled={loading}
          className={`px-6 py-3 rounded-lg font-medium transition ${
            predictionType === 'drivers'
              ? 'bg-red-600 text-white shadow-lg'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
          } disabled:opacity-50`}
        >
          {loading && predictionType === 'drivers' ? (
            <span className="flex items-center gap-2">
              <span className="inline-block animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
              Analyzing Drivers...
            </span>
          ) : (
            '🏎️ Drivers Championship'
          )}
        </button>
        <button
          onClick={() => fetchPrediction('constructors')}
          disabled={loading}
          className={`px-6 py-3 rounded-lg font-medium transition ${
            predictionType === 'constructors'
              ? 'bg-red-600 text-white shadow-lg'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
          } disabled:opacity-50`}
        >
          {loading && predictionType === 'constructors' ? (
            <span className="flex items-center gap-2">
              <span className="inline-block animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
              Analyzing Teams...
            </span>
          ) : (
            '🏢 Constructors Championship'
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !prediction && !error && (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <span className="text-5xl mb-4 block">🔮</span>
          <h3 className="text-xl font-semibold text-gray-100 mb-2">
            Championship Predictor
          </h3>
          <p className="text-gray-400 max-w-md mx-auto">
            Select Drivers or Constructors above to get AI-powered predictions
            for the {new Date().getFullYear()} season championship.
          </p>
        </div>
      )}

      {/* Prediction Results */}
      {prediction && !loading && (
        <div className="space-y-6">
          {/* Season Info Bar */}
          <div className="flex items-center gap-4 text-sm text-gray-400 bg-gray-800 rounded-lg px-4 py-3">
            <span>
              Season: <strong className="text-gray-200">{prediction.season}</strong>
            </span>
            <span className="text-gray-600">|</span>
            <span>
              Races: <strong className="text-green-400">{prediction.races_completed}</strong> / {prediction.races_completed + prediction.races_remaining} completed
            </span>
          </div>

          {/* Predicted Champion Card */}
          {champion && (
            <div className="bg-gradient-to-r from-yellow-900/30 via-gray-800 to-gray-800 border border-yellow-700/50 rounded-xl p-6 shadow-lg">
              <div className="flex items-start gap-4 mb-4">
                <span className="text-4xl">🏆</span>
                <div className="flex-1">
                  <div className="flex items-baseline justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-yellow-400 uppercase tracking-wide mb-1">Predicted Champion</h3>
                      <h2 className="text-2xl font-bold text-gray-100">{champion.name}</h2>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-yellow-400">{confidencePct}%</div>
                      <div className="text-xs text-gray-400">confidence</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Stats Row */}
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="bg-gray-900/50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 uppercase">Current Points</div>
                  <div className="text-xl font-bold text-gray-200">{champion.current_points}</div>
                </div>
                <div className="bg-gray-900/50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 uppercase">Predicted Final</div>
                  <div className="text-xl font-bold text-green-400">{champion.predicted_final_points}</div>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mt-4">
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-yellow-600 to-yellow-400 transition-all duration-700"
                    style={{ width: `${confidencePct}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {/* Top Contenders Table */}
          {prediction.top_contenders && prediction.top_contenders.length > 0 && (
            <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-gray-100">📊 Top Contenders</h3>
              </div>
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      {predictionType === 'drivers' ? 'Driver' : 'Team'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Predicted Points
                    </th>
                    {prediction.top_contenders[0].chance_pct !== undefined && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Chance
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {prediction.top_contenders.map((contender, idx) => (
                    <tr key={contender.id} className={`hover:bg-gray-700 ${idx === 0 ? 'bg-yellow-900/10' : ''}`}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">
                        {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `${idx + 1}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                        {predictionType === 'drivers' ? (
                          <Link
                            to={`/driver/${contender.id}`}
                            className="text-red-400 hover:underline"
                          >
                            {contender.name}
                          </Link>
                        ) : (
                          <Link
                            to={`/constructor/${contender.id}`}
                            className="text-red-400 hover:underline"
                          >
                            {contender.name}
                          </Link>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100 font-semibold">
                        {contender.predicted_points}
                      </td>
                      {contender.chance_pct !== undefined && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className="text-yellow-400 font-medium">
                            {Math.round(contender.chance_pct * 100)}%
                          </span>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* AI Reasoning */}
          {prediction.ai_reasoning && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-gray-100 mb-3 flex items-center gap-2">
                🤖 AI Analysis
              </h3>
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {prediction.ai_reasoning}
              </p>
            </div>
          )}

          {/* Form Analysis Grid */}
          {prediction.form_analysis && Object.keys(prediction.form_analysis).length > 0 && (
            <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-gray-100">📈 Season Form Analysis</h3>
                <p className="text-sm text-gray-400 mt-1">Based on all {prediction.races_completed} completed races</p>
              </div>
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(prediction.form_analysis).map(([id, form]) => {
                  const driverForm = form as DriverFormAnalysis;
                  const constructorForm = form as ConstructorFormAnalysis;

                  return (
                    <div
                      key={id}
                      className="bg-gray-700/50 rounded-lg p-4 space-y-3 border border-gray-600/50"
                    >
                      <h4 className="font-semibold text-gray-100">
                        {predictionType === 'drivers' ? (
                          <Link to={`/driver/${id}`} className="text-red-400 hover:underline">
                            {id}
                          </Link>
                        ) : (
                          <Link to={`/constructor/${id}`} className="text-red-400 hover:underline">
                            {id}
                          </Link>
                        )}
                      </h4>

                      {predictionType === 'drivers' ? (
                        <>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Races</span>
                            <span className="text-gray-200 font-medium">{driverForm.races_analyzed}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Avg Points</span>
                            <span className="text-gray-200 font-medium">{driverForm.avg_points}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Total Points</span>
                            <span className="text-gray-200 font-medium">{driverForm.total_points}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Wins</span>
                            <span className="text-gray-200 font-medium">{driverForm.wins}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Podiums</span>
                            <span className="text-gray-200 font-medium">{driverForm.podiums}</span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-600/50">
                            <div className="text-center">
                              <div className="text-xs text-gray-500">Win%</div>
                              <div className="text-sm font-medium text-green-400">{driverForm.win_pct}%</div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-gray-500">Pod%</div>
                              <div className="text-sm font-medium text-yellow-400">{driverForm.podium_pct}%</div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-gray-500">DNF%</div>
                              <div className="text-sm font-medium text-red-400">{driverForm.dnf_pct}%</div>
                            </div>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Races</span>
                            <span className="text-gray-200 font-medium">{constructorForm.races_analyzed}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Avg Points/Race</span>
                            <span className="text-gray-200 font-medium">
                              {constructorForm.avg_points_per_race}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Total Points</span>
                            <span className="text-gray-200 font-medium">
                              {constructorForm.total_points_recent}
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
