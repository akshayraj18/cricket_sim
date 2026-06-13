import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

/**
 * Local (on-device) re-engagement reminders. No server / APNs involved — the
 * app schedules these through iOS's UserNotifications framework and the OS
 * delivers them even when the app is closed. The user still controls delivery
 * style (banner/sound/lock screen) from Settings; our in-app toggle is a soft
 * opt-out layered on top of the OS permission.
 */

export const IDLE_REMINDER_DAYS = 3;
const SECONDS_PER_DAY = 24 * 60 * 60;

/**
 * How notifications behave if one fires while the app is foregrounded. Re-engagement
 * reminders are only meaningful when the app is closed, but showing an alert is the
 * safe default (the OS still lets the user control style in Settings).
 */
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

/** A reminder we know how to schedule. `kind` is echoed back on tap (analytics). */
export type ReminderKind = 'season_waiting' | 'transfer_window';

export interface ScheduledReminder {
  kind: ReminderKind;
  title: string;
  body: string;
  /** Delay from "now" in seconds before the OS fires the notification. */
  delaySeconds: number;
}

interface PlanInput {
  /** Phase of the user's active career, or null if they have no active career. */
  activePhase: string | null;
  /** OS notification permission has been granted. */
  permissionGranted: boolean;
  /** User hasn't opted out via the in-app toggle. */
  enabled: boolean;
}

/**
 * Pure planner: given the user's state, return the reminders to schedule.
 * Empty when reminders are off (no permission or opted out) or there's nothing
 * worth nudging about. Extracted from the side-effecting scheduler so the
 * trigger rules are unit-testable.
 */
export function planReminders({ activePhase, permissionGranted, enabled }: PlanInput): ScheduledReminder[] {
  if (!permissionGranted || !enabled || !activePhase) return [];

  // Transfer/retention window open: nudge sooner so they don't miss it.
  if (activePhase === 'retention') {
    return [
      {
        kind: 'transfer_window',
        title: 'Your transfer window is open 🔁',
        body: 'Lock in your retentions and shape your squad before the next season.',
        delaySeconds: IDLE_REMINDER_DAYS * SECONDS_PER_DAY,
      },
    ];
  }

  // Mid-season / anything in progress: remind them their season is waiting.
  if (activePhase !== 'league_complete') {
    return [
      {
        kind: 'season_waiting',
        title: 'Your season is waiting 🏏',
        body: 'Jump back in — your league needs you in the dugout.',
        delaySeconds: IDLE_REMINDER_DAYS * SECONDS_PER_DAY,
      },
    ];
  }

  return [];
}

/** Whether the OS has granted permission to post notifications. */
export async function hasPermission(): Promise<boolean> {
  const { granted } = await Notifications.getPermissionsAsync();
  return granted;
}

/**
 * Prompt for OS notification permission (the system dialog). Call this once,
 * after the first career is created, when the user has something to be
 * reminded about. Returns whether permission ended up granted.
 */
export async function requestPermission(): Promise<boolean> {
  const existing = await Notifications.getPermissionsAsync();
  if (existing.granted) return true;
  // Don't re-prompt if the user has explicitly denied at the OS level.
  if (!existing.canAskAgain) return false;
  const { granted } = await Notifications.requestPermissionsAsync();
  return granted;
}

/**
 * Cancel any previously scheduled reminders and schedule the current plan.
 * Idempotent — safe to call on every app-foreground / career change so the
 * "3 days from your last visit" timer keeps sliding forward.
 */
export async function rescheduleReminders(input: PlanInput): Promise<ScheduledReminder[]> {
  await Notifications.cancelAllScheduledNotificationsAsync();
  if (Platform.OS === 'web') return [];

  const reminders = planReminders(input);
  for (const r of reminders) {
    await Notifications.scheduleNotificationAsync({
      content: { title: r.title, body: r.body, data: { kind: r.kind } },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
        seconds: r.delaySeconds,
        repeats: false,
      },
    });
  }
  return reminders;
}

/** Cancel all scheduled reminders (e.g. user turns reminders off). */
export async function cancelAllReminders(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
}
