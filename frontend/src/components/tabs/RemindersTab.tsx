import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { remindersApi, raceApi } from '../../services/api';
import type { Reminder, RaceScheduleItem } from '../../types/api';
import { Link } from 'react-router-dom';

export default function RemindersTab() {
  const { isAuthenticated } = useAuth();
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [upcomingRaces, setUpcomingRaces] = useState<RaceScheduleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Listen for reminder changes from other tabs
  useEffect(() => {
    const handler = () => {
      if (isAuthenticated) loadData();
    };
    window.addEventListener('reminders-changed', handler);
    return () => window.removeEventListener('reminders-changed', handler);
  }, [isAuthenticated]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [remindersData, scheduleData] = await Promise.all([
        remindersApi.getReminders(),
        raceApi.getSeasonSchedule(new Date().getFullYear()),
      ]);
      setReminders(remindersData);
      
      // Filter upcoming races
      const now = new Date();
      const upcoming = scheduleData.races.filter(
        (race: RaceScheduleItem) => new Date(race.date) > now
      );
      setUpcomingRaces(upcoming);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const addReminder = async (race: RaceScheduleItem) => {
    // Check if reminder already exists
    const existing = reminders.find(
      (r) => r.race_round === race.round && r.race_year === new Date().getFullYear()
    );
    if (existing) {
      setError(`Reminder already set for ${race.race_name}`);
      return;
    }

    try {
      await remindersApi.addReminder({
        race_round: race.round,
        race_year: new Date().getFullYear(),
        notify_before_hours: 24,
        method: 'email',
      });
      await loadData();
      window.dispatchEvent(new Event('reminders-changed'));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add reminder');
    }
  };

  const deleteReminder = async (id: number) => {
    try {
      await remindersApi.deleteReminder(id);
      await loadData();
      window.dispatchEvent(new Event('reminders-changed'));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete reminder');
    }
  };

  const getRaceName = (round: number, year: number): string => {
    const race = upcomingRaces.find(r => r.round === round);
    if (race) return race.race_name;
    return `Round ${round} (${year})`;
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 mb-4">
          Please log in to manage reminders.
        </p>
        <Link
          to="/login"
          className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
        >
          Login
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Active Reminders */}
      <div className="bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Your Active Reminders</h2>
        {reminders.length === 0 ? (
          <p className="text-gray-400">No reminders set. Add one from the upcoming races below.</p>
        ) : (
          <div className="space-y-3">
            {reminders.map((reminder) => (
              <div
                key={reminder.id}
                className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
              >
                <div>
                  <p className="font-medium">
                    {getRaceName(reminder.race_round, reminder.race_year)}
                  </p>
                  <p className="text-sm text-gray-400">
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
      <div className="bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Upcoming Races</h2>
        {upcomingRaces.length === 0 ? (
          <p className="text-gray-400">No upcoming races scheduled.</p>
        ) : (
          <div className="space-y-3">
            {upcomingRaces.map((race) => {
              const hasReminder = reminders.some(
                (r) =>
                  r.race_round === race.round &&
                  r.race_year === new Date().getFullYear()
              );

              return (
                <div
                  key={race.round}
                  className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
                >
                  <div>
                    <p className="font-medium">
                      Round {race.round} - {race.race_name}
                    </p>
                    <p className="text-sm text-gray-400">
                      {race.circuit} • {race.date}
                    </p>
                  </div>
                  {hasReminder ? (
                    <span className="px-3 py-1 text-sm bg-green-900 text-green-300 rounded">
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
