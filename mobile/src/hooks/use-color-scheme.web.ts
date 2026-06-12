import { useAppTheme } from '@/context/ThemeContext';

/** Resolved color scheme, accounting for the user's in-app light/dark/system theme override. */
export function useColorScheme(): 'light' | 'dark' {
  return useAppTheme().scheme;
}
