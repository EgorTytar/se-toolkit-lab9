import { useState, useEffect, useCallback } from 'react';
import { pushApi } from '../services/api';

/**
 * Hook for managing browser push notification subscriptions.
 */
export function usePushNotifications() {
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if push notifications are supported
  useEffect(() => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true);
    }
  }, []);

  // Check current subscription status
  const checkSubscription = useCallback(async () => {
    if (!('serviceWorker' in navigator)) return false;
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      const hasLocalSubscription = !!subscription;
      
      // Also check backend to ensure sync
      try {
        const subs = await pushApi.getSubscriptions();
        const hasBackendSubscription = subs.subscriptions.length > 0;
        const isFullySubscribed = hasLocalSubscription && hasBackendSubscription;
        setIsSubscribed(isFullySubscribed);
        return isFullySubscribed;
      } catch {
        // Backend check failed, fall back to local check only
        setIsSubscribed(hasLocalSubscription);
        return hasLocalSubscription;
      }
    } catch (e) {
      console.error('Check subscription error:', e);
      return false;
    }
  }, []);

  // Convert base64 VAPID key to Uint8Array for PushManager
  function urlBase64ToUint8Array(base64String: string) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Subscribe to push notifications
  const subscribe = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Request notification permission first
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setError('Notification permission denied');
        return;
      }

      // Get VAPID public key from backend
      const { public_key } = await pushApi.getVapidPublicKey();

      // Register service worker
      const registration = await navigator.serviceWorker.register('/sw.js');
      await navigator.serviceWorker.ready;

      // Always create a fresh subscription by removing any existing one first
      let existingSubscription = await registration.pushManager.getSubscription();
      if (existingSubscription) {
        await existingSubscription.unsubscribe();
      }

      // Create new subscription with current VAPID keys
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key),
      });

      // Send subscription to backend
      await pushApi.subscribe(subscription.endpoint, {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')!))),
        auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth')!))),
      });

      setIsSubscribed(true);
    } catch (err: any) {
      console.error('Subscribe error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to subscribe to notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // Remove from backend
        await pushApi.unsubscribe(subscription.endpoint, {
          p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')!))),
          auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth')!))),
        });

        // Unsubscribe from PushManager
        await subscription.unsubscribe();
      }

      setIsSubscribed(false);
    } catch (err: any) {
      console.error('Unsubscribe error:', err);
      setError(err.response?.data?.detail || 'Failed to unsubscribe from notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    isSupported,
    isSubscribed,
    loading,
    error,
    subscribe,
    unsubscribe,
    checkSubscription,
  };
}
