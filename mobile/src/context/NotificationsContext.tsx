import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { AppState } from 'react-native';

import { useCareer } from '@/context/CareerContext';
import { useAnalytics } from '@/observability/analytics';
import {
  cancelAllReminders,
  hasPermission,
  requestPermission,
  rescheduleReminders,
} from '@/services/notifications';

/**
 * Owns the re-engagement reminder lifecycle: the user's in-app opt-out
 * preference, the OS permission state, and (re)scheduling the local reminders
 * whenever the app comes to the foreground or the active career changes — so
 * the "3 days from your last visit" timer always slides forward from now.
 */
const REMINDERS_ENABLED_KEY = 'cricket_sim.reminders_enabled';
const PERMISSION_PROMPTED_KEY = 'cricket_sim.notif_permission_prompted';

interface NotificationsContextValue {
  /** OS permission granted. */
  permissionGranted: boolean;
  /** In-app opt-in (defaults true; respects OS permission to actually fire). */
  enabled: boolean;
  /** Toggle the in-app preference (from the account sheet). */
  setEnabled: (next: boolean, source?: 'settings') => Promise<void>;
  /**
   * Ask the OS for permission the first time only — call after a career is
   * created. No-ops on subsequent calls so it's safe to fire every time.
   */
  promptPermission: () => Promise<void>;
}

const NotificationsContext = createContext<NotificationsContextValue | null>(null);

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const { activeCareer } = useCareer();
  const analytics = useAnalytics();
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [enabled, setEnabledState] = useState(true);
  const activePhase = activeCareer?.phase ?? null;

  // Load persisted preference + current OS permission once.
  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem(REMINDERS_ENABLED_KEY);
      setEnabledState(stored !== 'false');
      setPermissionGranted(await hasPermission());
    })();
  }, []);

  // Reschedule whenever inputs change or the app returns to the foreground.
  const reschedule = useCallback(() => {
    rescheduleReminders({ activePhase, permissionGranted, enabled });
  }, [activePhase, permissionGranted, enabled]);

  useEffect(() => {
    reschedule();
  }, [reschedule]);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      // On foreground, refresh permission (user may have changed it in
      // Settings) and slide the idle timer forward from now.
      if (state === 'active') {
        hasPermission().then((granted) => {
          setPermissionGranted(granted);
          reschedule();
        });
      }
    });
    return () => sub.remove();
  }, [reschedule]);

  // Route a tapped reminder into analytics.
  const listenerSet = useRef(false);
  useEffect(() => {
    if (listenerSet.current) return;
    listenerSet.current = true;
    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      const kind = response.notification.request.content.data?.kind;
      analytics.capture('notification_opened', { kind: typeof kind === 'string' ? kind : 'unknown' });
    });
    return () => sub.remove();
  }, [analytics]);

  const setEnabled = useCallback(
    async (next: boolean, source: 'settings' = 'settings') => {
      setEnabledState(next);
      await AsyncStorage.setItem(REMINDERS_ENABLED_KEY, String(next));
      if (next) {
        analytics.capture('notifications_enabled', { source });
        await rescheduleReminders({ activePhase, permissionGranted, enabled: true });
      } else {
        analytics.capture('notifications_disabled', { source });
        await cancelAllReminders();
      }
    },
    [activePhase, analytics, permissionGranted]
  );

  const promptPermission = useCallback(async () => {
    // Only ever show the OS prompt once (after the first career is created).
    const alreadyPrompted = await AsyncStorage.getItem(PERMISSION_PROMPTED_KEY);
    if (alreadyPrompted === 'true') return;
    await AsyncStorage.setItem(PERMISSION_PROMPTED_KEY, 'true');

    const granted = await requestPermission();
    setPermissionGranted(granted);
    if (granted) {
      analytics.capture('notifications_enabled', { source: 'prompt' });
      await rescheduleReminders({ activePhase, permissionGranted: true, enabled });
    }
  }, [activePhase, analytics, enabled]);

  const value = useMemo(
    () => ({ permissionGranted, enabled, setEnabled, promptPermission }),
    [permissionGranted, enabled, setEnabled, promptPermission]
  );

  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>;
}

export function useNotifications(): NotificationsContextValue {
  const ctx = useContext(NotificationsContext);
  if (!ctx) throw new Error('useNotifications must be used within a NotificationsProvider');
  return ctx;
}
