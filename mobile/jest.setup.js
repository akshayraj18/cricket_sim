// AsyncStorage ships an official mock for Jest; register it so modules that
// import it (e.g. hooks reading persisted flags) load under the test runner.
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);
