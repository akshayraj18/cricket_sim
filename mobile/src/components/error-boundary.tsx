import { Component, type ReactNode } from 'react';
import { Appearance, Pressable, StyleSheet, Text, View } from 'react-native';

import { Colors, Radius, Spacing } from '@/constants/theme';

/**
 * Reporter hook for a caught render error. Wired to Sentry in
 * `src/observability/sentry.ts`; defaults to a console log so the boundary is
 * useful even before crash reporting is configured.
 */
let reporter: (error: Error, componentStack?: string) => void = (error) => {
  console.error('[ErrorBoundary]', error);
};

export function setErrorReporter(fn: (error: Error, componentStack?: string) => void) {
  reporter = fn;
}

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Top-level error boundary: catches render-time crashes anywhere in the tree
 * and shows a recoverable fallback screen instead of a blank white screen,
 * while reporting the error (to Sentry once configured). "Try Again" remounts
 * the subtree so a transient error can recover without a full app restart.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack?: string | null }) {
    reporter(error, info.componentStack ?? undefined);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;

    // Class components can't use hooks, so resolve the scheme statically.
    const scheme = Appearance.getColorScheme() === 'light' ? 'light' : 'dark';
    const c = Colors[scheme];

    return (
      <View style={[styles.container, { backgroundColor: c.bg }]}>
        <Text style={styles.emoji}>🏏</Text>
        <Text style={[styles.title, { color: c.text }]}>Something went wrong</Text>
        <Text style={[styles.body, { color: c.textDim }]}>
          The app hit an unexpected error. Your saved game is safe — try again, and if it keeps happening, restart
          the app.
        </Text>
        <Pressable
          onPress={this.reset}
          style={({ pressed }) => [styles.button, { backgroundColor: c.green, opacity: pressed ? 0.85 : 1 }]}>
          <Text style={styles.buttonText}>Try Again</Text>
        </Pressable>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.four,
    gap: Spacing.three,
  },
  emoji: {
    fontSize: 48,
    lineHeight: 56,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    textAlign: 'center',
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },
  button: {
    borderRadius: Radius.sm,
    paddingVertical: 14,
    paddingHorizontal: Spacing.five,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontWeight: '700',
    fontSize: 15,
    color: '#1a1404',
  },
});
