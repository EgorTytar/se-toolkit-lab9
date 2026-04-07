import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userApi, favoritesApi, remindersApi } from '../services/api';
import type { FavoriteDriver, Reminder } from '../types/api';
import { Link, Navigate } from 'react-router-dom';
import { usePushNotifications } from '../hooks/usePushNotifications';

type AccountTab = 'profile' | 'favorites' | 'reminders';

export default function AccountPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<AccountTab>('profile');
  const [displayName, setDisplayName] = useState('');
  const [updating, setUpdating] = useState(false);
  const [favorites, setFavorites] = useState<FavoriteDriver[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Push notifications
  const {
    isSupported,
    isSubscribed,
    loading: pushLoading,
    error: pushError,
    subscribe,
    unsubscribe,
    checkSubscription,
  } = usePushNotifications();

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
    }
  }, [user]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated && isSupported && activeTab === 'profile') {
      checkSubscription();
    }
  }, [isAuthenticated, isSupported, activeTab, checkSubscription]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [favsRes, remsRes] = await Promise.all([
        favoritesApi.getFavorites(),
        remindersApi.getReminders(),
      ]);
      setFavorites(favsRes);
      setReminders(remsRes);
    } catch {
      // Non-critical
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async () => {
    setUpdating(true);
    setError(null);
    setMessage(null);
    try {
      await userApi.updateMe({ display_name: displayName });
      setMessage('Profile updated successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setUpdating(false);
    }
  };

  const removeFavorite = async (id: number) => {
    try {
      await favoritesApi.removeFavorite(id);
      await loadData();
      setMessage('Favorite removed');
    } catch {
      setError('Failed to remove favorite');
    }
  };

  const deleteReminder = async (id: number) => {
    try {
      await remindersApi.deleteReminder(id);
      await loadData();
      setMessage('Reminder deleted');
    } catch {
      setError('Failed to delete reminder');
    }
  };

  if (!isAuthenticated && !isLoading) {
    return <Navigate to="/login" replace />;
  }

  if (!user) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Account</h1>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {(['profile', 'favorites', 'reminders'] as AccountTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === tab
                  ? 'border-red-500 text-red-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {message && (
        <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
          <p className="text-green-400">{message}</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Profile</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Email
              </label>
              <input
                type="email"
                value={user.email}
                disabled
                className="w-full px-4 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-300"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-600 rounded-md bg-gray-700"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Member Since
              </label>
              <p className="text-gray-300">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
            <button
              onClick={updateProfile}
              disabled={updating}
              className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50"
            >
              {updating ? 'Updating...' : 'Update Profile'}
            </button>
          </div>

          {/* Push Notifications Toggle */}
          <div className="mt-8 pt-6 border-t border-gray-700">
            <h3 className="text-lg font-bold mb-3">Notifications</h3>
            {isSupported ? (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Browser Push Notifications</p>
                  <p className="text-sm text-gray-400">
                    {isSubscribed
                      ? 'Enabled — you will receive race reminders'
                      : 'Click to enable race reminder notifications'}
                  </p>
                </div>
                <button
                  onClick={isSubscribed ? unsubscribe : subscribe}
                  disabled={pushLoading}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                    isSubscribed ? 'bg-green-600' : 'bg-gray-600'
                  } disabled:opacity-50`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      isSubscribed ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Push notifications are not supported in this browser.
              </p>
            )}
            {pushError && (
              <p className="text-red-400 text-sm mt-2">{pushError}</p>
            )}
          </div>
        </div>
      )}

      {/* Favorites Tab */}
      {activeTab === 'favorites' && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Favorite Drivers</h2>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
            </div>
          ) : favorites.length === 0 ? (
            <p className="text-gray-400">
              No favorites yet. Visit a{' '}
              <Link to="/" className="text-red-400 hover:underline">
                driver page
              </Link>{' '}
              and click the heart icon!
            </p>
          ) : (
            <div className="space-y-3">
              {favorites.map((fav) => (
                <div
                  key={fav.id}
                  className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
                >
                  <Link
                    to={`/driver/${fav.driver_id}`}
                    className="text-red-400 hover:underline font-medium"
                  >
                    {fav.driver_name} ({fav.driver_code})
                  </Link>
                  <button
                    onClick={() => removeFavorite(fav.id)}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reminders Tab */}
      {activeTab === 'reminders' && (
        <div className="bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Your Reminders</h2>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
            </div>
          ) : reminders.length === 0 ? (
            <p className="text-gray-400">
              No reminders set. Go to the Reminders tab on the dashboard to add one!
            </p>
          ) : (
            <div className="space-y-3">
              {reminders.map((reminder) => (
                <div
                  key={reminder.id}
                  className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
                >
                  <div>
                    <p className="font-medium">
                      Round {reminder.race_round} • {reminder.race_year}
                    </p>
                    <p className="text-sm text-gray-400">
                      {reminder.notify_before_hours}h before • {reminder.method}
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
      )}
    </div>
  );
}
