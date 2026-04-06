import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { remindersApi, raceApi } from '../../services/api';
import type { Reminder, RaceScheduleItem } from '../../types/api';
import { Navigate } from 'react-router-dom';

export default function RemindersTab() {
  const { isAuthenticated } = useAuth();
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [upcomingRaces, setUpcomingRaces] = useState<RaceScheduleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [remindersRes, scheduleRes] = await Promise.all([
        remindersApi.getReminders(),
        raceApi.getSeasonSchedule(new Date().getFullYear()),
      ]);
      setReminders(remindersRes.data);
      
      // Filter upcoming races
      const now = new Date();
      const upcoming = scheduleRes.data.schedule.filter(
        (race) => new Date(race.date) > now
      );
      setUpcomingRaces(upcoming);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load reminders');
    } finally {
      setLoading(false);
    }
  };

  const addReminder = async (race: RaceScheduleItem) => {
    try {
      await remindersApi.addReminder({
        race_round: parseInt(race.round),
        race_year: parseInt(race.season),
        notify_before_hours: 24,
      });
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add reminder');
    }
  };

  const deleteReminder = async (id: number) => {
    try {
      await remindersApi.deleteReminder(id);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete reminder');
    }
  };

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Active Reminders */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Your Active Reminders</h2>
        {reminders.length === 0 ? (
          <p className="text-gray-500">No reminders set. Add one from the upcoming races below.</p>
        ) : (
          <div className="space-y-3">
            {reminders.map((reminder) => (
              <div
                key={reminder.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium">{reminder.race_name}</p>
                  <p className="text-sm text-gray-500">
                    Round {reminder.race_round} • {reminder.race_year} •{' '}
                    {reminder.notify_before_hours}h before
                  </p>
                </div>
                <button
                  onClick={() => deleteReminder(reminder.id)}
                  className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Races */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Upcoming Races</h2>
        {upcomingRaces.length === 0 ? (
          <p className="text-gray-500">No upcoming races scheduled.</p>
        ) : (
          <div className="space-y-3">
            {upcomingRaces.map((race) => {
              const hasReminder = reminders.some(
                (r) =>
                  r.race_round === parseInt(race.round) &&
                  r.race_year === parseInt(race.season)
              );

              return (
                <div
                  key={race.round}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium">
                      Round {race.round} - {race.raceName}
                    </p>
                    <p className="text-sm text-gray-500">
                      {race.circuit.circuitName} • {race.date}
                    </p>
                  </div>
                  {hasReminder ? (
                    <span className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded">
                      ✓ Reminder Set
                    </span>
                  ) : (
                    <button
                      onClick={() => addReminder(race)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
                    >
                      Add Reminder
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
