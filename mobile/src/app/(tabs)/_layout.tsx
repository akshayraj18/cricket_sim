import AppTabs from '@/components/app-tabs';
import { SignInScreen } from '@/components/sign-in-screen';
import { SplashScreen } from '@/components/splash-screen';
import { useAuth } from '@/context/AuthContext';

export default function TabLayout() {
  const { status } = useAuth();

  if (status === 'loading') return <SplashScreen />;
  if (status === 'signed-out') return <SignInScreen />;
  return <AppTabs />;
}
