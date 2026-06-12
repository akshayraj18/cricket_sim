import { NativeTabs } from 'expo-router/unstable-native-tabs';
import { useColorScheme } from 'react-native';

import { Colors } from '@/constants/theme';

export default function AppTabs() {
  const scheme = useColorScheme();
  const colors = Colors[scheme === 'dark' ? 'dark' : 'light'];

  return (
    <NativeTabs
      backgroundColor={colors.bgElevated}
      indicatorColor={colors.backgroundSelected}
      labelStyle={{ selected: { color: colors.text } }}
      tintColor={colors.green}>
      <NativeTabs.Trigger name="index">
        <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          sf={{ default: 'house', selected: 'house.fill' }}
          md={{ default: 'home', selected: 'home_filled' }}
        />
      </NativeTabs.Trigger>

      <NativeTabs.Trigger name="squad">
        <NativeTabs.Trigger.Label>Squad</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          sf={{ default: 'person.2', selected: 'person.2.fill' }}
          md={{ default: 'group', selected: 'group' }}
        />
      </NativeTabs.Trigger>

      <NativeTabs.Trigger name="season">
        <NativeTabs.Trigger.Label>Season</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          sf={{ default: 'calendar', selected: 'calendar' }}
          md={{ default: 'calendar_month', selected: 'calendar_month' }}
        />
      </NativeTabs.Trigger>

      <NativeTabs.Trigger name="stats">
        <NativeTabs.Trigger.Label>Stats</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          sf={{ default: 'chart.bar', selected: 'chart.bar.fill' }}
          md={{ default: 'bar_chart', selected: 'bar_chart' }}
        />
      </NativeTabs.Trigger>

      <NativeTabs.Trigger name="history">
        <NativeTabs.Trigger.Label>History</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          sf={{ default: 'trophy', selected: 'trophy.fill' }}
          md={{ default: 'emoji_events', selected: 'emoji_events' }}
        />
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
