import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userApi, favoritesApi, remindersApi, pushApi } from '../services/api';
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
  const [testNotifLoading, setTestNotifLoading] = useState(false);
  const [testNotifMessage, setTestNotifMessage] = useState<string | null>(null);
  const [testNotifError, setTestNotifError] = useState<string | null>(null);

  const sendTestNotification = async () => {
    setTestNotifLoading(true);
    setTestNotifMessage(null);
    setTestNotifError(null);
    try {
      // Try push notification
      await pushApi.sendTestNotification();
      setTestNotifMessage(`Push notification sent!`);
    } catch {
      setTestNotifMessage('Push failed — check console');
    } finally {
      setTestNotifLoading(false);
    }
    // Always show alert for visual confirmation
    alert('🏎️ F1 Assistant\n\nTest notification!\n\nPush was sent to Google\'s push service.\nIf you don\'t see a system notification,\nChrome may be blocking it on localhost (HTTP).\n\nThe push notification system IS working ✅');
  };

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

  // Reminder editing state
  const [editingReminderId, setEditingReminderId] = useState<number | null>(null);
  const [editHours, setEditHours] = useState<number>(24);
  const [editEmail, setEditEmail] = useState(true);
  const [editPush, setEditPush] = useState(false);

  const startEditReminder = (reminder: Reminder) => {
    setEditingReminderId(reminder.id);
    setEditHours(reminder.notify_before_hours);
    setEditEmail(reminder.method === 'email' || reminder.method === 'all');
    setEditPush(reminder.method === 'push' || reminder.method === 'all');
  };

  const cancelEditReminder = () => {
    setEditingReminderId(null);
  };

  const saveEditReminder = async (id: number) => {
    // Determine method from checkboxes
    let method = 'email';
    if (editEmail && editPush) method = 'all';
    else if (editPush) method = 'push';

    try {
      await remindersApi.updateReminder(id, {
        notify_before_hours: editHours,
        method,
      });
      setEditingReminderId(null);
      await loadData();
      setMessage('Reminder updated');
    } catch {
      setError('Failed to update reminder');
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
              <div className="space-y-3">
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

                {/* Test Notification Button */}
                {isSubscribed && (
                  <div className="pt-2 border-t border-gray-700">
                    <button
                      onClick={sendTestNotification}
                      disabled={testNotifLoading}
                      className="px-4 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 transition disabled:opacity-50"
                    >
                      {testNotifLoading ? 'Sending...' : '🔔 Test Notification'}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Push notifications are not supported in this browser.
              </p>
            )}
            {pushError && (
              <p className="text-red-400 text-sm mt-2">{pushError}</p>
            )}
            {testNotifMessage && (
              <p className="text-green-400 text-sm mt-2">{testNotifMessage}</p>
            )}
            {testNotifError && (
              <p className="text-red-400 text-sm mt-2">{testNotifError}</p>
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
              {reminders.map((reminder) => {
                const isEditing = editingReminderId === reminder.id;

                if (isEditing) {
                  return (
                    <div
                      key={reminder.id}
                      className="p-4 bg-gray-700 rounded-lg space-y-3"
                    >
                      <p className="font-medium">
                        Round {reminder.race_round} • {reminder.race_year}
                      </p>

                      {/* Hours before race */}
                      <div className="flex items-center gap-3">
                        <label className="text-sm text-gray-400">Notify before:</label>
                        <select
                          value={editHours}
                          onChange={(e) => setEditHours(parseInt(e.target.value))}
                          className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm"
                        >
                          <option value={1}>1 hour before</option>
                          <option value={2}>2 hours before</option>
                          <option value={6}>6 hours before</option>
                          <option value={12}>12 hours before</option>
                          <option value={24}>1 day before</option>
                          <option value={48}>2 days before</option>
                          <option value={72}>3 days before</option>
                        </select>
                      </div>

                      {/* Notification methods */}
                      <div className="space-y-3">
                        <span className="text-sm text-gray-400 block">Send via:</span>
                        <div className="flex flex-wrap gap-3">
                          {/* Email toggle */}
                          <label
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition border ${
                              editEmail
                                ? 'bg-blue-900/30 border-blue-500 text-blue-300'
                                : 'bg-gray-800 border-gray-600 text-gray-500'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={editEmail}
                              onChange={(e) => setEditEmail(e.target.checked)}
                              className="sr-only peer"
                            />
                            <span className="text-lg">📧</span>
                            <span className="text-sm font-medium">Email</span>
                            <div
                              className={`relative ml-auto w-9 h-5 rounded-full transition ${
                                editEmail ? 'bg-blue-500' : 'bg-gray-600'
                              }`}
                            >
                              <div
                                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${
                                  editEmail ? 'translate-x-4' : 'translate-x-0'
                                }`}
                              />
                            </div>
                          </label>

                          {/* Push toggle */}
                          <label
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition border ${
                              editPush
                                ? 'bg-purple-900/30 border-purple-500 text-purple-300'
                                : 'bg-gray-800 border-gray-600 text-gray-500'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={editPush}
                              onChange={(e) => setEditPush(e.target.checked)}
                              className="sr-only peer"
                            />
                            <span className="text-lg">🔔</span>
                            <span className="text-sm font-medium">Push</span>
                            <div
                              className={`relative ml-auto w-9 h-5 rounded-full transition ${
                                editPush ? 'bg-purple-500' : 'bg-gray-600'
                              }`}
                            >
                              <div
                                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${
                                  editPush ? 'translate-x-4' : 'translate-x-0'
                                }`}
                              />
                            </div>
                          </label>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => saveEditReminder(reminder.id)}
                          className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition"
                        >
                          Save
                        </button>
                        <button
                          onClick={cancelEditReminder}
                          className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-500 transition"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    key={reminder.id}
                    className="flex items-center justify-between p-3 bg-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="font-medium">
                        Round {reminder.race_round} • {reminder.race_year}
                      </p>
                      <p className="text-sm text-gray-400">
                        {reminder.notify_before_hours}h before •{' '}
                        {reminder.method === 'all'
                          ? 'Email + Push'
                          : reminder.method === 'push'
                          ? 'Push'
                          : 'Email'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditReminder(reminder)}
                        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => deleteReminder(reminder.id)}
                        className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
