import { useState } from 'react';
import { predictionsApi } from '../../services/api';
import type {
  PredictionResponse,
  DriverPredictionChampion,
  ConstructorPredictionChampion,
  DriverFormAnalysis,
  ConstructorFormAnalysis,
} from '../../types/api';
import { Link } from 'react-router-dom';

type PredictionType = 'drivers' | 'constructors';

export default function PredictionsTab() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [predictionType, setPredictionType] = useState<PredictionType>('drivers');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);

  const fetchPrediction = async (type: PredictionType, yr: number) => {
    setLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const data =
        type === 'drivers'
          ? await predictionsApi.getDriverPrediction(yr)
          : await predictionsApi.getConstructorPrediction(yr);
      setPrediction(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load prediction');
    } finally {
      setLoading(false);
    }
  };

  const handleTypeChange = (type: PredictionType) => {
    setPredictionType(type);
    fetchPrediction(type, year);
  };

  const handlePredict = () => {
    fetchPrediction(predictionType, year);
  };

  const champion = prediction?.predicted_champion;
  const confidencePct = champion ? Math.round(champion.confidence * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="number"
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handlePredict();
          }}
          className="px-4 py-2 border border-gray-600 rounded-md w-32 bg-gray-800 text-gray-100"
          placeholder="Year"
          min={1950}
          max={currentYear}
        />

        <div className="flex space-x-2">
          <button
            onClick={() => handleTypeChange('drivers')}
            className={`px-4 py-2 rounded-md transition ${
              predictionType === 'drivers'
                ? 'bg-red-600 text-white'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Drivers
          </button>
          <button
            onClick={() => handleTypeChange('constructors')}
            className={`px-4 py-2 rounded-md transition ${
              predictionType === 'constructors'
                ? 'bg-red-600 text-white'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Constructors
          </button>
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition"
        >
          {loading ? 'Generating...' : 'Predict Championship'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-red-500 mb-4"></div>
          <p className="text-gray-400">
            AI is analyzing current form and remaining races...
          </p>
        </div>
      )}

      {/* Prediction Results */}
      {prediction && !loading && (
        <div className="space-y-6">
          {/* Season Info */}
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>
              Season: <strong className="text-gray-200">{prediction.season}</strong>
            </span>
            <span>•</span>
            <span>
              Races completed: <strong className="text-gray-200">{prediction.races_completed}</strong>
            </span>
            <span>•</span>
            <span>
              Races remaining: <strong className="text-gray-200">{prediction.races_remaining}</strong>
            </span>
          </div>

          {/* Predicted Champion */}
          {champion && (
            <div className="bg-gradient-to-r from-yellow-900/30 to-gray-800 border border-yellow-700/50 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">🏆</span>
                <div>
                  <h3 className="text-xl font-bold text-yellow-400">Predicted Champion</h3>
                  <p className="text-sm text-gray-400">
                    {predictionType === 'drivers' ? 'Driver' : 'Constructor'} Championship
                  </p>
                </div>
              </div>

              <div className="flex items-baseline gap-4 mb-2">
                <h2 className="text-2xl font-bold text-gray-100">
                  {'name' in champion ? champion.name : champion.name}
                </h2>
                <span className="text-lg font-semibold text-yellow-400">{confidencePct}% confidence</span>
              </div>

              <div className="flex items-center gap-6 text-sm">
                <div>
                  <span className="text-gray-400">Current points: </span>
                  <span className="font-semibold text-gray-200">{champion.current_points}</span>
                </div>
                <div>
                  <span className="text-gray-400">Predicted final: </span>
                  <span className="font-semibold text-green-400">{champion.predicted_final_points}</span>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mt-4">
                <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-yellow-600 to-yellow-400 transition-all duration-500"
                    style={{ width: `${confidencePct}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {/* Top Contenders */}
          {prediction.top_contenders && prediction.top_contenders.length > 0 && (
            <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-gray-100">Top Contenders</h3>
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
                    <tr key={contender.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-100">
                        {idx + 1}
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
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                          {Math.round(contender.chance_pct * 100)}%
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
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-100 mb-3">🤖 AI Analysis</h3>
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {prediction.ai_reasoning}
              </p>
            </div>
          )}

          {/* Form Analysis */}
          {prediction.form_analysis && Object.keys(prediction.form_analysis).length > 0 && (
            <div className="bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-gray-100">📊 Form Analysis (Last 5 Races)</h3>
              </div>
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(prediction.form_analysis).map(([id, form]) => {
                  const driverForm = form as DriverFormAnalysis;
                  const constructorForm = form as ConstructorFormAnalysis;

                  return (
                    <div
                      key={id}
                      className="bg-gray-700/50 rounded-lg p-4 space-y-2"
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
                            <span className="text-gray-400">Avg Points</span>
                            <span className="text-gray-200 font-medium">{driverForm.avg_points}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Wins</span>
                            <span className="text-gray-200 font-medium">{driverForm.wins}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Podiums</span>
                            <span className="text-gray-200 font-medium">{driverForm.podiums}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Win Rate</span>
                            <span className="text-gray-200 font-medium">{driverForm.win_pct}%</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">DNF Rate</span>
                            <span className="text-gray-200 font-medium">{driverForm.dnf_pct}%</span>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Avg Points/Race</span>
                            <span className="text-gray-200 font-medium">
                              {constructorForm.avg_points_per_race}
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Recent Total</span>
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

      {/* Empty State */}
      {!loading && !prediction && !error && (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <span className="text-5xl mb-4 block">🏎️</span>
          <h3 className="text-xl font-semibold text-gray-100 mb-2">
            Championship Predictor
          </h3>
          <p className="text-gray-400 max-w-md mx-auto">
            Select a season and click &quot;Predict Championship&quot; to get AI-powered predictions
            with form analysis and championship odds.
          </p>
        </div>
      )}
    </div>
  );
}
