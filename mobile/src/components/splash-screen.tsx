import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useTheme } from '@/hooks/use-theme';

export function SplashScreen() {
  const theme = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <ActivityIndicator color={theme.green} size="large" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
