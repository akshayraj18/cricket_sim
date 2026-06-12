import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useColorScheme as useRNColorScheme } from 'react-native';

export type ThemeMode = 'light' | 'dark' | 'system';

const THEME_MODE_KEY = 'cricket_sim.theme_mode';

interface ThemeContextValue {
  /** User-selected preference: 'light', 'dark', or 'system'. */
  mode: ThemeMode;
  /** The resolved scheme to actually render, after applying 'system'. */
  scheme: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const systemScheme = useRNColorScheme();
  const [mode, setModeState] = useState<ThemeMode>('system');

  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem(THEME_MODE_KEY);
      if (stored === 'light' || stored === 'dark' || stored === 'system') {
        setModeState(stored);
      }
    })();
  }, []);

  const setMode = (next: ThemeMode) => {
    setModeState(next);
    AsyncStorage.setItem(THEME_MODE_KEY, next);
  };

  const scheme = mode === 'system' ? (systemScheme === 'dark' ? 'dark' : 'light') : mode;

  const value = useMemo(() => ({ mode, scheme, setMode }), [mode, scheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useAppTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useAppTheme must be used within an AppThemeProvider');
  return ctx;
}
