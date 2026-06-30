import { useWindowDimensions } from 'react-native';

import { MaxContentWidth } from '@/constants/theme';

const WIDE_BREAKPOINT = MaxContentWidth + 48;

/**
 * Returns layout helpers for responsive screens.
 * On wide displays (iPad, Mac Catalyst, large Android tablets) content is
 * capped at MaxContentWidth (800) and centered. On narrow phones it fills
 * the full width as before.
 */
export function useLayout() {
  const { width } = useWindowDimensions();
  const isWide = width >= WIDE_BREAKPOINT;

  const contentContainerStyle = isWide
    ? ({
        alignSelf: 'center' as const,
        width: MaxContentWidth,
      } as const)
    : undefined;

  return { isWide, width, contentContainerStyle };
}
