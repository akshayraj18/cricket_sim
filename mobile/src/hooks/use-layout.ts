import { Platform, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ContentBottomInset, MaxContentWidth } from '@/constants/theme';

const WIDE_BREAKPOINT = MaxContentWidth + 48;

/**
 * Height of the tab bar itself, excluding the home-indicator inset below it.
 *
 * iOS 26 renders NativeTabs as a floating bar that sits ABOVE the home
 * indicator and overlays scroll content, so the space to reserve is the bar
 * plus its margin plus whatever the device's bottom inset is — not a single
 * fixed number. `expo-router/unstable-native-tabs` exposes no height API, so
 * this is measured against the rendered bar rather than read from it.
 */
const TAB_BAR_ALLOWANCE = Platform.select({ ios: 68, android: 72 }) ?? 0;

/**
 * Returns layout helpers for responsive screens.
 * On wide displays (iPad, Mac Catalyst, large Android tablets) content is
 * capped at MaxContentWidth (800) and centered. On narrow phones it fills
 * the full width as before.
 */
export function useLayout() {
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const isWide = width >= WIDE_BREAKPOINT;

  const contentContainerStyle = isWide
    ? ({
        alignSelf: 'center' as const,
        width: MaxContentWidth,
      } as const)
    : undefined;

  /**
   * Bottom padding for a screen's scrollable content.
   *
   * Prefer this over the static `ContentBottomInset`: that constant is a flat
   * 82pt on iOS and ignores safe-area entirely, which is ~20pt short on a
   * Face ID device once the home indicator is counted — enough to leave the
   * last row of a list clipped behind the floating tab bar. Falls back to the
   * constant on web, where the bar is a fixed-height pill handled in CSS.
   */
  const bottomInset =
    Platform.OS === 'web' ? ContentBottomInset : insets.bottom + TAB_BAR_ALLOWANCE;

  return { isWide, width, contentContainerStyle, bottomInset };
}
