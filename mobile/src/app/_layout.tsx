import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';

import { AnimatedSplashOverlay } from '@/components/animated-icon';
import { AuthProvider } from '@/context/AuthContext';
import { CareerProvider } from '@/context/CareerContext';
import { LeagueProvider } from '@/context/LeagueContext';
import { AppThemeProvider } from '@/context/ThemeContext';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function RootLayout() {
  return (
    <AppThemeProvider>
      <ThemedStack />
    </AppThemeProvider>
  );
}

function ThemedStack() {
  const colorScheme = useColorScheme();
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AnimatedSplashOverlay />
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
    </ThemeProvider>
  );
}
