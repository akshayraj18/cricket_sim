import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';

import { AnimatedSplashOverlay } from '@/components/animated-icon';
import { ErrorBoundary } from '@/components/error-boundary';
import { AuthProvider } from '@/context/AuthContext';
import { CareerProvider } from '@/context/CareerContext';
import { LeagueProvider } from '@/context/LeagueContext';
import { AppThemeProvider } from '@/context/ThemeContext';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { AnalyticsProvider } from '@/observability/analytics';
import { initSentry } from '@/observability/sentry';

// Start crash reporting before anything renders so early errors are captured.
initSentry();

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <AppThemeProvider>
        <ThemedStack />
      </AppThemeProvider>
    </ErrorBoundary>
  );
}

function ThemedStack() {
  const colorScheme = useColorScheme();
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AnimatedSplashOverlay />
      <AnalyticsProvider>
        <AuthProvider>
          <CareerProvider>
            <LeagueProvider>
              <Stack screenOptions={{ headerShown: false }}>
                <Stack.Screen name="(tabs)" />
                <Stack.Screen
                  name="new-career"
                  options={{ presentation: 'modal', headerShown: true, title: 'New Career' }}
                />
              </Stack>
            </LeagueProvider>
          </CareerProvider>
        </AuthProvider>
      </AnalyticsProvider>
    </ThemeProvider>
  );
}
